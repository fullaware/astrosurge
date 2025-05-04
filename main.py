import simpy
import random
import colorama
from colorama import Fore, Style
from datetime import datetime
import uuid
import yfinance as yf

# Initialize colorama for cross-platform colored output
colorama.init()

class AsteroidMiningShip:
    def __init__(self, env, ship_id, fleet):
        self.env = env
        self.ship_id = ship_id
        self.fleet = fleet
        self.asteroid = None
        self.travel_days = 0
        self.current_phase = "Initialization"
        self.mining_site_setup = False
        self.extracted_material = 0
        self.ship_capacity = 50000  # kg
        self.log = []
        self.damage_count = 0
        self.off_course_days = 0
        self.total_mining_days = 0
        self.luck = 10  # Initial luck value
        self.commodity_prices = {}  # Store prices per kg

    def log_event(self, message, event_type="Nominal"):
        """Log an event with timestamp and color-coded output."""
        timestamp = datetime(2025, 5, 4).toordinal() + int(self.env.now)
        date_str = datetime.fromordinal(timestamp).strftime("%Y-%m-%d")
        log_entry = f"Day {self.env.now:3d} [{date_str}]: Ship {self.ship_id}: {message}"
        self.log.append((self.env.now, log_entry, event_type))

        # Color-code based on event type
        if event_type == "Nominal":
            color = Fore.GREEN
        elif event_type == "Hazard":
            color = Fore.RED
        elif event_type == "Milestone":
            color = Fore.CYAN
        elif event_type == "Geo-Political":
            color = Fore.MAGENTA
        else:
            color = Fore.YELLOW

        print(f"{color}{log_entry}{Style.RESET_ALL}")

    def roll_luck(self):
        """Roll a d20 to set daily luck and log it."""
        self.luck = random.randint(1, 20)
        luck_color = Fore.RED if self.luck < 5 else Fore.CYAN if self.luck > 15 else Fore.GREEN
        self.log_event(f"Luck roll (d20): {self.luck}", "Nominal")
        print(f"{luck_color}Ship {self.ship_id} Luck value: {self.luck}/20{Style.RESET_ALL}")

    def fetch_commodity_prices(self):
        """Fetch real-time commodity prices using yfinance, with fallback prices."""
        tickers = {
            "gold": "GC=F",
            "platinum": "PL=F",
            "palladium": "PA=F",
            "silver": "SI=F",
            "copper": "HG=F"
        }
        fallback_prices = {
            "gold": 3255.95,  # USD/troy oz
            "platinum": 982.35,  # USD/troy oz
            "palladium": 937.00,  # USD/troy oz
            "silver": 32.63,  # USD/troy oz
            "copper": 5.15  # USD/lb
        }
        prices_per_kg = {}

        try:
            for commodity, ticker in tickers.items():
                data = yf.Ticker(ticker).history(period="1d")
                if not data.empty:
                    price = data["Close"].iloc[-1]
                    if commodity == "copper":
                        # Convert USD/lb to USD/troy oz (1 lb = 14.5833 troy oz)
                        price *= 14.5833
                    # Convert USD/troy oz to USD/kg (1 troy oz = 0.0311035 kg)
                    price_per_kg = price / 0.0311035
                    prices_per_kg[commodity] = price_per_kg
                else:
                    raise ValueError(f"No data for {commodity}")
        except Exception as e:
            self.log_event(f"Failed to fetch prices: {e}. Using fallback prices.", "Hazard")
            for commodity in tickers:
                price = fallback_prices[commodity]
                if commodity == "copper":
                    price *= 14.5833  # Convert to troy oz
                prices_per_kg[commodity] = price / 0.0311035

        self.commodity_prices = prices_per_kg
        self.log_event(
            f"Commodity prices (USD/kg): Gold=${prices_per_kg['gold']:,.2f}, "
            f"Platinum=${prices_per_kg['platinum']:,.2f}, "
            f"Palladium=${prices_per_kg['palladium']:,.2f}, "
            f"Silver=${prices_per_kg['silver']:,.2f}, "
            f"Copper=${prices_per_kg['copper']:,.2f}",
            "Milestone"
        )

    def prepare_launch(self):
        """Simulate launch preparation with geo-political delays."""
        self.roll_luck()
        delay_prob = 0.3 if self.luck < 5 else 0.1 if self.luck > 15 else 0.2
        if random.random() < delay_prob:
            delay_days = random.randint(1, 5)
            issue = random.choice(["Export control disputes", "Regulatory permitting delays"])
            self.log_event(
                f"Geo-political issue: {issue}. Launch delayed by {delay_days} days.",
                "Geo-Political"
            )
            yield self.env.timeout(delay_days)
        else:
            self.log_event("Launch preparation complete.", "Nominal")
            yield self.env.timeout(1)
        self.current_phase = "Selection"

    def select_asteroid(self):
        """Simulate selecting a unique asteroid from the fleet's pool."""
        self.roll_luck()
        if self.fleet.available_asteroids:
            self.asteroid = random.choice(self.fleet.available_asteroids)
            self.fleet.available_asteroids.remove(self.asteroid)
            self.log_event(
                f"Selected {self.asteroid['name']} (Distance: {self.asteroid['distance']:,} km, "
                f"Resource Value: {self.asteroid['resource_value']:,} kg)",
                "Milestone"
            )
            self.current_phase = "Planning"
            yield self.env.timeout(1)
        else:
            self.log_event("No asteroids available. Mission aborted.", "Hazard")
            self.current_phase = "Complete"
            yield self.env.timeout(0)

    def plan_travel(self):
        """Plan the travel to the asteroid."""
        self.roll_luck()
        self.travel_days = max(1, int(self.asteroid["distance"] / 50000))
        self.log_event(
            f"Travel plan complete. Estimated travel time: {self.travel_days} days",
            "Milestone"
        )
        self.current_phase = "Travel"
        yield self.env.timeout(1)

    def travel(self, direction="to asteroid"):
        """Simulate travel with luck-based hazards."""
        days = self.travel_days
        if direction == "to asteroid":
            self.log_event(f"Beginning travel to {self.asteroid['name']}.", "Milestone")
        else:
            self.log_event("Beginning return journey to Earth.", "Milestone")
            days += self.off_course_days

        day = 0
        while day < days:
            self.roll_luck()
            hazard_prob = 0.2 if self.luck < 5 else 0.05 if self.luck > 15 else 0.1
            if random.random() < hazard_prob:
                severe_prob = 0.7 if self.luck < 5 else 0.3 if self.luck > 15 else 0.5
                if random.random() < severe_prob:
                    repair_days = random.randint(1, 3)
                    self.damage_count += 1
                    self.log_event(
                        f"Micrometeorite strike caused severe damage. Repairing for {repair_days} days. "
                        f"Damage count: {self.damage_count}.",
                        "Hazard"
                    )
                    yield self.env.timeout(repair_days)
                    day += repair_days
                else:
                    self.off_course_days += 1
                    self.log_event(
                        f"Micrometeorite strike knocked ship off course. Correcting (1 extra day). "
                        f"Total extra days: {self.off_course_days}.",
                        "Hazard"
                    )
                    yield self.env.timeout(1)
                    day += 1
            else:
                self.log_event(f"Nominal travel day {direction}.", "Nominal")
                yield self.env.timeout(1)
                day += 1

        if direction == "to asteroid":
            self.current_phase = "Landing"
            self.log_event(f"Arrived at {self.asteroid['name']}. Preparing for landing.", "Milestone")
        else:
            self.current_phase = "Re-Entry"
            self.log_event("Arrived in Earth orbit. Preparing for re-entry.", "Milestone")

    def land(self):
        """Simulate landing with luck-based success."""
        self.roll_luck()
        success_prob = 0.7 if self.luck < 5 else 0.95 if self.luck > 15 else 0.9
        if random.random() < success_prob:
            self.log_event("Landing successful. Beginning site setup.", "Milestone")
            self.current_phase = "Setup"
            yield self.env.timeout(1)
        else:
            self.log_event("Landing failure: Surface instability detected. Retrying.", "Hazard")
            yield self.env.timeout(2)
            self.roll_luck()
            self.log_event("Retry successful. Beginning site setup.", "Milestone")
            self.current_phase = "Setup"

    def setup_mining_site(self):
        """Simulate setting up the mining site with luck-based issues."""
        setup_days = 3
        for day in range(setup_days):
            self.roll_luck()
            issue_prob = 0.3 if self.luck < 5 else 0.1 if self.luck > 15 else 0.2
            if random.random() < issue_prob:
                self.log_event("Setup issue: Equipment calibration required.", "Hazard")
                yield self.env.timeout(1)
            else:
                self.log_event(f"Setup progress: Day {day + 1} of {setup_days}.", "Nominal")
                yield self.env.timeout(1)
        self.mining_site_setup = True
        self.current_phase = "Extraction"
        self.log_event("Mining site setup complete. Beginning extraction.", "Milestone")

    def extract_material(self):
        """Simulate extraction with luck-based events."""
        while self.extracted_material < self.ship_capacity:
            self.roll_luck()
            vein_prob = 0.05 if self.luck < 5 else 0.2 if self.luck > 15 else 0.1
            pocket_prob = 0.2 if self.luck < 5 else 0.05 if self.luck > 15 else 0.1
            if random.random() < vein_prob:
                vein_days = random.randint(2, 3)
                self.log_event(
                    f"Struck a rich vein! Extracting at high yield for {vein_days} days.",
                    "Milestone"
                )
                for day in range(vein_days):
                    if self.extracted_material >= self.ship_capacity:
                        break
                    daily_yield = min(
                        random.randint(800, 1000),
                        self.ship_capacity - self.extracted_material
                    )
                    self.extracted_material += daily_yield
                    self.log_event(
                        f"Rich vein day {day + 1}/{vein_days}: Extracted {daily_yield} kg. "
                        f"Total: {self.extracted_material}/{self.ship_capacity} kg.",
                        "Nominal"
                    )
                    yield self.env.timeout(1)
                    if day + 1 < vein_days:
                        self.roll_luck()
            elif random.random() < pocket_prob:
                halt_days = random.randint(1, 2)
                self.log_event(
                    f"Hit a hydrogen pocket. Extraction halted for {halt_days} days for safety.",
                    "Hazard"
                )
                yield self.env.timeout(halt_days)
            else:
                yield_range = (50, 600) if self.luck < 5 else (200, 1000) if self.luck > 15 else (100, 800)
                daily_yield = min(
                    random.randint(*yield_range),
                    self.ship_capacity - self.extracted_material
                )
                self.extracted_material += daily_yield
                self.log_event(
                    f"Extracted {daily_yield} kg. Total: {self.extracted_material}/{self.ship_capacity} kg.",
                    "Nominal"
                )
                yield self.env.timeout(1)
        self.total_mining_days = int(self.env.now)
        self.current_phase = "Return"
        self.log_event(
            f"Ship capacity reached ({self.extracted_material} kg). Preparing for return to Earth.",
            "Milestone"
        )

    def re_entry(self):
        """Simulate re-entry with geo-political delays."""
        self.roll_luck()
        delay_prob = 0.3 if self.luck < 5 else 0.1 if self.luck > 15 else 0.2
        if random.random() < delay_prob:
            delay_days = random.randint(1, 3)
            issue = random.choice(["Sanctions or airspace restrictions", "Safety regulation disputes"])
            self.log_event(
                f"Geo-political issue: {issue}. Re-entry delayed by {delay_days} days.",
                "Geo-Political"
            )
            yield self.env.timeout(delay_days)
        else:
            self.log_event("Re-entry successful.", "Nominal")
            yield self.env.timeout(1)
        self.current_phase = "Post-Mission"

    def sell_resources(self):
        """Simulate selling resources for this ship (handled by fleet)."""
        self.roll_luck()
        self.current_phase = "Selling"
        self.log_event("Awaiting fleet to sell resources.", "Nominal")
        yield self.env.timeout(1)

    def repair_ship(self):
        """Simulate repairing the ship."""
        self.roll_luck()
        repair_days = self.damage_count
        if repair_days > 0:
            self.log_event(
                f"Repairing ship for {repair_days} damages. Repair time: {repair_days} days.",
                "Nominal"
            )
            yield self.env.timeout(repair_days)
        else:
            self.log_event("No repairs needed.", "Nominal")
            yield self.env.timeout(1)

    def prepare_next_mission(self):
        """Simulate preparing for the next mission."""
        self.roll_luck()
        self.log_event("Preparing for next mission: Restocking supplies and crew training.", "Nominal")
        yield self.env.timeout(2)
        self.current_phase = "Complete"
        self.log_event("Mission complete. Ready for next mission.", "Milestone")

    def mission(self):
        """Run the full mission process for this ship."""
        yield self.env.process(self.prepare_launch())
        yield self.env.process(self.select_asteroid())
        if self.current_phase == "Complete":  # Mission aborted due to no asteroids
            return
        yield self.env.process(self.plan_travel())
        yield self.env.process(self.travel(direction="to asteroid"))
        yield self.env.process(self.land())
        yield self.env.process(self.setup_mining_site())
        yield self.env.process(self.extract_material())
        yield self.env.process(self.travel(direction="to Earth"))
        yield self.env.process(self.re_entry())
        yield self.env.process(self.sell_resources())
        yield self.env.process(self.repair_ship())
        yield self.env.process(self.prepare_next_mission())

class Fleet:
    def __init__(self, env, num_ships=3):
        self.env = env
        self.num_ships = num_ships
        self.ships = [AsteroidMiningShip(env, i + 1, self) for i in range(num_ships)]
        self.available_asteroids = [
            {"name": f"Asteroid {chr(65+i)}", "distance": random.randint(500000, 3000000), "resource_value": random.randint(100000, 200000)}
            for i in range(10)
        ]
        self.total_extracted = 0
        self.total_capacity = self.num_ships * 50000  # kg
        self.commodity_prices = {}

    def log_fleet_event(self, message, event_type="Nominal"):
        """Log a fleet-level event."""
        timestamp = datetime(2025, 5, 4).toordinal() + int(self.env.now)
        date_str = datetime.fromordinal(timestamp).strftime("%Y-%m-%d")
        log_entry = f"Day {self.env.now:3d} [{date_str}]: Fleet: {message}"
        # Use first ship's log for simplicity
        self.ships[0].log.append((self.env.now, log_entry, event_type))

        color = Fore.CYAN if event_type == "Milestone" else Fore.MAGENTA if event_type == "Geo-Political" else Fore.YELLOW
        print(f"{color}{log_entry}{Style.RESET_ALL}")

    def fetch_commodity_prices(self):
        """Fetch real-time commodity prices (called once for fleet)."""
        tickers = {
            "gold": "GC=F",
            "platinum": "PL=F",
            "palladium": "PA=F",
            "silver": "SI=F",
            "copper": "HG=F"
        }
        fallback_prices = {
            "gold": 3255.95,  # USD/troy oz
            "platinum": 982.35,  # USD/troy oz
            "palladium": 937.00,  # USD/troy oz
            "silver": 32.63,  # USD/troy oz
            "copper": 5.15  # USD/lb
        }
        prices_per_kg = {}

        try:
            for commodity, ticker in tickers.items():
                data = yf.Ticker(ticker).history(period="1d")
                if not data.empty:
                    price = data["Close"].iloc[-1]
                    if commodity == "copper":
                        price *= 14.5833  # Convert to troy oz
                    price_per_kg = price / 0.0311035
                    prices_per_kg[commodity] = price_per_kg
                else:
                    raise ValueError(f"No data for {commodity}")
        except Exception as e:
            self.log_fleet_event(f"Failed to fetch prices: {e}. Using fallback prices.", "Geo-Political")
            for commodity in tickers:
                price = fallback_prices[commodity]
                if commodity == "copper":
                    price *= 14.5833
                prices_per_kg[commodity] = price / 0.0311035

        self.commodity_prices = prices_per_kg
        self.log_fleet_event(
            f"Commodity prices (USD/kg): Gold=${prices_per_kg['gold']:,.2f}, "
            f"Platinum=${prices_per_kg['platinum']:,.2f}, "
            f"Palladium=${prices_per_kg['palladium']:,.2f}, "
            f"Silver=${prices_per_kg['silver']:,.2f}, "
            f"Copper=${prices_per_kg['copper']:,.2f}",
            "Milestone"
        )

    def sell_fleet_resources(self):
        """Sell resources for all ships."""
        self.fetch_commodity_prices()
        composition = {
            "gold": 0.70,
            "platinum": 0.20,
            "palladium": 0.05,
            "silver": 0.04,
            "copper": 0.01
        }
        # Average luck across ships
        avg_luck = sum(ship.luck for ship in self.ships) / len(self.ships)
        market_impact = random.uniform(0.5, 0.8) if avg_luck < 5 else random.uniform(0.6, 0.9) if avg_luck <= 15 else random.uniform(0.8, 1.0)
        trade_barrier_prob = 0.3 if avg_luck < 5 else 0.1 if avg_luck > 15 else 0.2
        trade_barrier_factor = random.uniform(0.7, 0.9) if random.random() < trade_barrier_prob else 1.0

        total_revenue = 0
        total_weight = sum(ship.extracted_material for ship in self.ships)
        for commodity, fraction in composition.items():
            weight = total_weight * fraction
            price_per_kg = self.commodity_prices[commodity] * market_impact * trade_barrier_factor
            revenue = weight * price_per_kg
            total_revenue += revenue
            self.log_fleet_event(
                f"Sold {weight:,.0f} kg of {commodity} at ${price_per_kg:,.2f}/kg for ${revenue:,.2f}.",
                "Milestone"
            )

        self.log_fleet_event(
            f"Total revenue: ${total_revenue:,.2f}. "
            f"Market impact: {int((1-market_impact)*100)}% price reduction due to flooding. "
            f"Trade barriers: {int((1-trade_barrier_factor)*100)}% penalty.",
            "Milestone"
        )
        self.log_fleet_event(
            "Warning: Flooding markets with gold/platinum may crash prices, severely impacting "
            "resource-rich economies (e.g., South Africa, DRC).",
            "Geo-Political"
        )
        yield self.env.timeout(1)

    def run_missions(self):
        """Run missions for all ships and handle fleet-level selling."""
        # Start all ship missions concurrently
        for ship in self.ships:
            self.env.process(ship.mission())

        # Wait for all ships to reach selling phase or complete
        while not all(ship.current_phase in ["Selling", "Complete"] for ship in self.ships):
            yield self.env.timeout(1)

        # Sell resources for the fleet
        yield self.env.process(self.sell_fleet_resources())

        # Allow ships to proceed to repair and next mission
        for ship in self.ships:
            if ship.current_phase == "Selling":
                self.env.process(ship.repair_ship())
                self.env.process(ship.prepare_next_mission())

def run_simulation(num_ships=3):
    """Initialize and run the fleet simulation."""
    env = simpy.Environment()
    fleet = Fleet(env, num_ships)
    env.process(fleet.run_missions())
    env.run()
    total_mining_days = max(ship.total_mining_days for ship in fleet.ships if ship.total_mining_days > 0)
    print(
        f"{Fore.MAGENTA}=== Total days to mine {fleet.total_capacity:,} kg across {num_ships} ships: "
        f"{total_mining_days} ==={Style.RESET_ALL}"
    )

if __name__ == "__main__":
    print(f"{Fore.BLUE}=== Asteroid Mining Simulation Started ==={Style.RESET_ALL}")
    run_simulation(num_ships=3)
    print(f"{Fore.BLUE}=== Simulation Completed ==={Style.RESET_ALL}")