import simpy
import random
import logging
from bson import ObjectId
from datetime import datetime, UTC
from bson.int64 import Int64
from models.models import MissionModel, MissionDay, ShipModel, PyInt64
from amos.event_processor import EventProcessor
from config import MongoDBConfig
from amos.mine_asteroid import fetch_market_prices, simulate_travel_day, simulate_mining_day

class MissionSimulator:
    """
    Simulates asteroid mining missions using SimPy's discrete event simulation.
    
    This class replaces the complex procedural logic in process_single_mission with
    a process-based simulation that handles events, ship movement, mining operations,
    and various mission phases in a more maintainable and extensible way.
    """

    def __init__(self, mission_data, username=None, company_name=None):
        """
        Initialize the mission simulator with mission data.
        
        Args:
            mission_data (dict): Raw mission data from the database
            username (str, optional): Username for logging purposes
            company_name (str, optional): Company name for logging purposes
        """
        self.db = MongoDBConfig.get_database()
        self.mission_raw = mission_data
        self.mission_id = str(mission_data["_id"])
        self.username = username
        self.company_name = company_name
        
        # Load configuration
        self.config = self.db.config.find_one({"name": "mining_globals"})
        if not self.config:
            raise RuntimeError("Mining globals config not found in asteroids.config")
        self.config_vars = self.config["variables"]
        
        # Initialize mission model from raw data
        self._prepare_mission_model()
        
        # Load ship and asteroid data
        self._load_ship()
        self._load_asteroid()
        self._load_user()
        
        # Initialize simulation state
        self.elements_mined = self.mission_raw.get("elements_mined", {})
        self.events = self.mission_raw.get("events", [])
        self.daily_summaries = self.mission_raw.get("daily_summaries", [])
        self.total_yield_kg = PyInt64(self.mission_raw.get("total_yield_kg", 0))
        self.days_into_mission = PyInt64(len(self.daily_summaries))
        self.ship_location = PyInt64(self.mission_raw.get("ship_location", self.ship_model.location))
        self.mission_cost = PyInt64(self.mission_raw.get("mission_cost", 0))
        self.ship_destroyed = False
        
        # Calculate mission parameters
        self.daily_yield_rate = PyInt64(self.ship_model.mining_power * 24 * self.config_vars["max_element_percentage"])
        self.base_travel_days = PyInt64(self.asteroid["moid_days"])
        self.estimated_mining_days = PyInt64(int(self.mission.target_yield_kg / self.daily_yield_rate))
        self.scheduled_days = PyInt64((self.base_travel_days * 2) + self.estimated_mining_days)
        
        # Prepare mining elements
        self._prepare_weighted_elements()
        
        # Financial tracking
        self.total_revenue = PyInt64(0)
        self.total_cost = PyInt64(0)
        self.penalties = PyInt64(0)
        self.investor_repayment = PyInt64(0)
        
        # Results
        self.graph_html = ""
        self.confidence_result = ""

    def _prepare_mission_model(self):
        """Prepare the mission model from raw data"""
        mission_raw_adjusted = self.mission_raw.copy()
        if "target_yield_kg" in mission_raw_adjusted:
            mission_raw_adjusted["target_yield_kg"] = PyInt64(mission_raw_adjusted["target_yield_kg"])
        mission_raw_adjusted["confidence"] = mission_raw_adjusted.get("confidence", 0.0)
        mission_raw_adjusted["predicted_profit_max"] = mission_raw_adjusted.get("predicted_profit_max", 0)
        mission_raw_adjusted["ship_location"] = PyInt64(mission_raw_adjusted.get("ship_location", 0))
        
        self.mission = MissionModel(**mission_raw_adjusted)
        self.mission.yield_multiplier = self.mission_raw.get("yield_multiplier", 1.0)
        self.mission.revenue_multiplier = self.mission_raw.get("revenue_multiplier", 1.0)
        self.mission.travel_yield_mod = self.mission_raw.get("travel_yield_mod", 1.0)
        self.mission.ship_repair_cost = PyInt64(self.mission_raw.get("ship_repair_cost", 0))
        self.mission.events = self.mission_raw.get("events", [])
        self.mission.daily_summaries = self.mission_raw.get("daily_summaries", [])
        self.mission.previous_debt = PyInt64(self.mission_raw.get("previous_debt", 0))
        self.mission.travel_delays = PyInt64(self.mission_raw.get("travel_delays", 0))
        self.ship_name = self.mission_raw.get("ship_name")

    def _load_ship(self):
        """Load ship data from database"""
        ship = self.db.ships.find_one({"user_id": self.mission.user_id, "name": self.ship_name})
        if not ship:
            raise ValueError(f"Ship {self.ship_name} not found for mission {self.mission_id}")
        self.ship = ship
        self.ship_model = ShipModel(**ship)
        self.mission.target_yield_kg = PyInt64(self.ship_model.capacity)
        logging.info(f"User {self.username}: Using ship {self.ship_name} with capacity {self.ship_model.capacity} kg, mining_power {self.ship_model.mining_power}")

    def _load_asteroid(self):
        """Load asteroid data from database"""
        asteroid = self.db.asteroids.find_one({"full_name": self.mission.asteroid_full_name})
        if not asteroid:
            raise ValueError(f"No asteroid found with full_name {self.mission.asteroid_full_name}")
        self.asteroid = asteroid
        logging.info(f"User {self.username}: Asteroid {self.mission.asteroid_full_name} loaded, moid_days: {asteroid['moid_days']}")

    def _load_user(self):
        """Load user data for mission context"""
        user_dict = self.db.users.find_one({"_id": ObjectId(self.mission.user_id)})
        if user_dict:
            if "company_name" in user_dict and not self.company_name:
                self.company_name = user_dict["company_name"]
            self.max_overrun_days = user_dict.get("max_overrun_days", 10)
            self.loan_count = user_dict.get("loan_count", 0)
        else:
            self.company_name = self.mission.company if not self.company_name else self.company_name
            self.max_overrun_days = 10
            self.loan_count = 0

    def _prepare_weighted_elements(self):
        """Prepare weighted elements for mining simulation"""
        COMMODITIES = ["Copper", "Silver", "Palladium", "Platinum", "Gold"]
        elements = self.asteroid["elements"]
        commodity_factor = self.asteroid.get("commodity_factor", 1.0)
        
        self.weighted_elements = []
        for elem in elements:
            elem_name = elem["name"] if isinstance(elem, dict) else elem
            if elem["mass_kg"] > 0:  # Only include elements present in the asteroid
                if elem_name in ["Platinum", "Gold"]:
                    weight = self.config_vars["commodity_factor_platinum_gold"] * commodity_factor * random.uniform(5, 10)
                elif elem_name in COMMODITIES:
                    weight = self.config_vars["commodity_factor_other"] * commodity_factor * random.uniform(3, 5)
                else:
                    weight = self.config_vars["non_commodity_weight"] * random.uniform(1, 2)
                self.weighted_elements.append({"name": elem_name, "mass_kg": elem["mass_kg"], "weight": weight})

    def travel_process(self, env, is_return=False):
        """
        SimPy process for ship travel (outbound or return journey).
        
        Args:
            env: SimPy environment
            is_return (bool): Whether this is the return journey
        """
        days_to_travel = self.ship_location if is_return else (self.base_travel_days - self.ship_location)
        
        for _ in range(days_to_travel):
            current_day = int(env.now)
            
            # Create day summary
            day_summary = simulate_travel_day(self.mission, current_day, is_return=is_return)
            
            # Apply events
            day_summary, ship_destroyed = EventProcessor.apply_daily_events(
                self.mission, day_summary, self.elements_mined, self.ship, None
            )
            
            # Update state
            if ship_destroyed:
                self.handle_ship_destruction(current_day)
                self.ship_destroyed = True
                return
            
            # Update position
            if is_return:
                self.ship_location = PyInt64(max(0, self.ship_location - 1))
            else:
                self.ship_location = PyInt64(self.ship_location + 1)
            
            # Update mission cost
            self.mission_cost += PyInt64(self.config_vars["daily_mission_cost"])
            
            # Record day summary
            self.daily_summaries.append(day_summary)
            self._record_events(day_summary, current_day)
            
            # Log progress
            phase = "return" if is_return else "outbound"
            logging.info(f"User {self.username}: Day {current_day} - Travel {phase}, Ship Location: {self.ship_location}")
            
            # Wait for next day
            yield env.timeout(1)
        
        if is_return and self.ship_location == 0:
            self.process_mission_completion()

    def mining_process(self, env):
        """
        SimPy process for asteroid mining operations.
        
        Args:
            env: SimPy environment
        """
        while self.total_yield_kg < self.mission.target_yield_kg:
            current_day = int(env.now)
            
            # Check for mission overrun
            if current_day > (self.scheduled_days + self.max_overrun_days):
                logging.info(f"User {self.username}: Mission overrun limit reached on day {current_day}, initiating return")
                break
                
            # Create day summary
            day_summary = simulate_mining_day(
                self.mission, current_day, self.weighted_elements, 
                self.elements_mined, None, self.ship_model.mining_power, 
                fetch_market_prices(), self.base_travel_days
            )
            
            # Apply events
            day_summary, ship_destroyed = EventProcessor.apply_daily_events(
                self.mission, day_summary, self.elements_mined, self.ship, None
            )
            
            # Update state
            if ship_destroyed:
                self.handle_ship_destruction(current_day)
                self.ship_destroyed = True
                return
            
            # Update yield
            self.total_yield_kg = PyInt64(self.total_yield_kg + day_summary.total_kg)
            
            # Update mission cost
            self.mission_cost += PyInt64(self.config_vars["daily_mission_cost"])
            
            # Record day summary
            self.daily_summaries.append(day_summary)
            self._record_events(day_summary, current_day)
            
            # Log progress
            logging.info(f"User {self.username}: Day {current_day} - Mining, Elements Mined: {day_summary.elements_mined}, Total Yield: {self.total_yield_kg}, Events: {day_summary.events}")
            
            # Wait for next day
            yield env.timeout(1)

    def mission_process(self, env):
        """
        Main SimPy process for mission execution.
        
        This is the central process that coordinates the different mission phases:
        1. Travel to asteroid
        2. Mining operations
        3. Return journey to Earth
        
        Args:
            env: SimPy environment
        """
        # Start with current mission state (day)
        yield env.timeout(self.days_into_mission)
        
        # Phase 1: Travel to asteroid if not there yet
        if self.ship_location < self.base_travel_days:
            outbound_travel = env.process(self.travel_process(env, is_return=False))
            yield outbound_travel
            if self.ship_destroyed:
                return

        # Phase 2: Mining operations
        if self.total_yield_kg < self.mission.target_yield_kg:
            mining_op = env.process(self.mining_process(env))
            yield mining_op
            if self.ship_destroyed:
                return
        
        # Phase 3: Return journey
        return_journey = env.process(self.travel_process(env, is_return=True))
        yield return_journey

    def handle_ship_destruction(self, day):
        """
        Handle ship destruction event.
        
        Args:
            day (int): The day when ship was destroyed
        """
        self.mission.status = 2  # Failed
        self.mission.completed_at = datetime.now(UTC)
        
        # Update ship in the database
        self.db.ships.update_one(
            {"_id": ObjectId(self.ship_model.id)},
            {"$set": {"active": False, "destroyed": True, "shield": self.ship["shield"], "hull": self.ship["hull"]}}
        )
        
        # Calculate cost of new ship and add to user's debt
        new_ship_cost = self.config_vars["ship_cost"]
        self.db.users.update_one(
            {"_id": ObjectId(self.mission.user_id)},
            {"$inc": {"current_loan": PyInt64(new_ship_cost)}}
        )
        
        logging.info(f"User {self.username}: Ship {self.ship_name} destroyed on day {day}. Mission {self.mission_id} failed. Added ${new_ship_cost:,} debt for new ship.")

    def process_mission_completion(self):
        """Process mission completion and calculate financial results"""
        # Ship returned to Earth with cargo
        prices = fetch_market_prices()
        COMMODITIES = ["Copper", "Silver", "Palladium", "Platinum", "Gold"]
        
        # Calculate revenue
        self.total_revenue = PyInt64(0)
        logging.info(f"User {self.username}: Ship returned to Earth, selling cargo: {self.elements_mined}")
        
        for name, kg in self.elements_mined.items():
            price_per_kg = prices.get(name, 0) if name in COMMODITIES else PyInt64(0)
            element_value = PyInt64(kg * price_per_kg)
            self.total_revenue += element_value
            logging.info(f"User {self.username}: Sold {name}: {kg} kg x ${price_per_kg}/kg = ${element_value}")
        
        # Apply revenue multiplier
        self.total_revenue = PyInt64(int(self.total_revenue * self.mission.revenue_multiplier))
        
        # Calculate final costs
        self.total_cost = PyInt64(self.mission_cost)
        profit = PyInt64(self.total_revenue - self.total_cost)
        
        # Check if investor funding is needed
        minimum_funding = PyInt64(self.config_vars["minimum_funding"])
        if profit < minimum_funding:
            investor_loan = PyInt64(self.config_vars["investor_loan_amount"])
            interest_rate = self.config_vars["loan_interest_rates"][
                min(self.loan_count, len(self.config_vars["loan_interest_rates"]) - 1)
            ]
            self.investor_repayment = PyInt64(int(investor_loan * interest_rate))
            self.total_cost += self.investor_repayment
            profit = PyInt64(self.total_revenue - self.total_cost)
            logging.info(f"User {self.username}: Profit {profit} below {minimum_funding} - took ${investor_loan:,} loan at {interest_rate}x")
        
        # Mark mission as completed
        self.mission.status = 1
        self.mission.completed_at = datetime.now(UTC)
        logging.info(f"User {self.username}: Revenue: ${self.total_revenue:,}, Cost: ${self.total_cost:,}, Profit: ${profit:,}")

    def _record_events(self, day_summary, day):
        """Record events from day_summary into mission events collection"""
        updated_events = []
        for event in day_summary.events:
            event_with_day = event.copy()
            event_with_day["day"] = day
            updated_events.append(event_with_day)
        
        self.events.extend(updated_events)
        
        for event in updated_events:
            if "delay_days" in event["effect"]:
                self.mission.travel_delays += PyInt64(event["effect"]["delay_days"])
                logging.info(f"User {self.username}: Day {day} Delay: +{event['effect']['delay_days']} days")
            elif "reduce_days" in event["effect"]:
                self.mission.travel_delays = PyInt64(max(0, self.mission.travel_delays - event["effect"]["reduce_days"]))
                logging.info(f"User {self.username}: Day {day} Recovery: -{event['effect']['reduce_days']} days")

    def generate_visualizations(self):
        """Generate mission visualization graphs"""
        # Your existing visualization code here
        # This would create the graph_html output
        pass

    def run_simulation(self, target_day=None):
        """
        Run the mission simulation.
        
        Args:
            target_day (int, optional): Target day to simulate until
            
        Returns:
            dict: Updated mission data
        """
        # Create SimPy environment
        env = simpy.Environment(initial_time=self.days_into_mission)
        
        # Run simulation
        if target_day:
            # Run until specific day - make sure to advance at least one day
            next_day = max(target_day, self.days_into_mission + 1)
            mission_proc = env.process(self.mission_process(env))
            env.run(until=next_day)
        else:
            # Run until completion
            mission_proc = env.process(self.mission_process(env))
            env.run(until=mission_proc)
        
        # Generate visualizations
        self.generate_visualizations()
        
        # Prepare and return updated mission data
        return self.get_updated_mission_data()

    def get_updated_mission_data(self):
        """Prepare updated mission data for database update"""
        update_data = {
            "status": self.mission.status,
            "yield_multiplier": self.mission.yield_multiplier,
            "revenue_multiplier": self.mission.revenue_multiplier,
            "travel_yield_mod": self.mission.travel_yield_mod,
            "ship_repair_cost": self.mission.ship_repair_cost,
            "events": self.events,
            "daily_summaries": self.daily_summaries,
            "previous_debt": self.mission.previous_debt,
            "travel_delays": self.mission.travel_delays,
            "ship_location": self.ship_location,
            "total_yield_kg": self.total_yield_kg,
            "days_into_mission": len(self.daily_summaries),
            "days_left": self.scheduled_days - len(self.daily_summaries),
            "mission_cost": self.mission_cost,
            "elements_mined": self.elements_mined,
            "completed_at": self.mission.completed_at
        }
        
        # Add financial details if mission is complete
        if self.mission.status in [1, 2]:  # Completed or Failed
            update_data.update({
                "cost": self.total_cost,
                "revenue": self.total_revenue,
                "profit": self.total_revenue - self.total_cost,
                "penalties": self.penalties,
                "investor_repayment": self.investor_repayment,
                "graph_html": self.graph_html,
                "confidence_result": self.confidence_result
            })
            
        return update_data


def simulate_mission(mission_data, day=None, api_event=None, username=None, company_name=None):
    """
    Simulate a mission using SimPy.
    
    Args:
        mission_data (dict): Raw mission data from database
        day (int, optional): Day to simulate until
        api_event (dict, optional): Manually triggered event
        username (str, optional): Username for logging
        company_name (str, optional): Company name
        
    Returns:
        dict: Updated mission data
    """
    try:
        simulator = MissionSimulator(mission_data, username, company_name)
        return simulator.run_simulation(day)
    except Exception as e:
        logging.error(f"User {username}: Error simulating mission {mission_data.get('_id')}: {e}")
        return {"error": str(e)}