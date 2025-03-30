import random
import pymongo
import yfinance as yf
from bson import ObjectId
from bson.int64 import Int64
from datetime import datetime, UTC
import logging
from models.models import MissionModel, AsteroidElementModel, MissionDay
from config import MongoDBConfig, LoggingConfig
from amos.event_processor import EventProcessor

db = MongoDBConfig.get_database()
LoggingConfig.setup_logging(log_to_file=False)

COMMODITIES = ["Copper", "Silver", "Palladium", "Platinum", "Gold"]
TROY_OUNCES_PER_KG = 32.1507

def fetch_market_prices() -> dict:
    symbols = {"Copper": "HG=F", "Silver": "SI=F", "Palladium": "PA=F", "Platinum": "PL=F", "Gold": "GC=F"}
    prices = {}
    logging.info("Fetching fresh market prices from yfinance (per troy ounce)...")
    try:
        for name, symbol in symbols.items():
            ticker = yf.Ticker(symbol)
            price_per_oz = ticker.history(period="1d")["Close"].iloc[-1]
            price_per_kg = price_per_oz * TROY_OUNCES_PER_KG
            prices[name] = round(price_per_kg, 2)
            logging.info(f"Fetched {name} ({symbol}): ${price_per_oz:.2f}/oz -> ${price_per_kg:.2f}/kg")
    except Exception as e:
        logging.error(f"yfinance failed: {e}")
        logging.info("Using realistic static prices (per kg)...")
        prices = {"Copper": 192.92, "Silver": 984.13, "Palladium": 31433.42, "Platinum": 31433.42, "Gold": 99233.42}
        for name, price in prices.items():
            logging.info(f"Static {name}: ${price:.2f}/kg")
    
    db.market_prices.insert_one({"timestamp": datetime.now(UTC).isoformat() + "Z", "prices": prices})
    return prices

def simulate_travel_day(mission: MissionModel, day: int, is_return: bool = False) -> MissionDay:
    note = "Travel - No incident" if not is_return else "Return Travel - No incident"
    day_summary = MissionDay(day=day, total_kg=Int64(0), note=note)
    day_summary = EventProcessor.apply_daily_events(mission, day_summary, {}, None)
    return day_summary

def simulate_mining_day(mission: MissionModel, day: int, weighted_elements: list, elements_mined: dict, api_event: dict = None) -> MissionDay:
    max_daily_kg = 500
    daily_yield_kg = random.randint(max_daily_kg - 50, max_daily_kg + 50)
    active_elements = random.sample(weighted_elements, k=min(random.randint(1, 3), len(weighted_elements)))

    daily_elements = {}
    for elem in active_elements:
        elem_name = elem["name"]
        yield_kg = Int64(min(daily_yield_kg * random.uniform(0.05, 0.3), daily_yield_kg // len(active_elements)))
        if elem["mass_kg"] < yield_kg:
            yield_kg = elem["mass_kg"]
        db.asteroids.update_one(
            {"full_name": mission.asteroid_full_name, "elements.name": elem_name},
            {"$inc": {"elements.$.mass_kg": -yield_kg}}
        )
        daily_elements[elem_name] = daily_elements.get(elem_name, 0) + yield_kg
        elements_mined[elem_name] = elements_mined.get(elem_name, 0) + yield_kg

    day_summary = MissionDay(day=day, total_kg=Int64(daily_yield_kg), note="Mining - Steady operation")
    day_summary = EventProcessor.apply_daily_events(mission, day_summary, daily_elements, api_event)
    return day_summary

def mine_asteroid(mission_id: str, day: int = None, api_event: dict = None) -> dict:
    mission_raw = db.missions.find_one({"_id": ObjectId(mission_id)})
    if not mission_raw:
        logging.error(f"No mission found with ID {mission_id}")
        return {"error": f"No mission found with ID {mission_id}"}
    
    mission = MissionModel(**mission_raw)
    mission.yield_multiplier = 1.0
    mission.revenue_multiplier = 1.0
    mission.travel_yield_mod = 1.0
    mission.ship_repair_cost = Int64(0)
    mission.events = []
    mission.daily_summaries = []
    mission.previous_debt = mission_raw.get("previous_debt", 0)
    mission.travel_delays = 0
    
    logging.info(f"Mission raw data: {mission_raw}")  # Debug mission data
    
    config = db.config.find_one({"name": "mining_globals"})
    if not config:
        logging.error("No mining_globals config found")
        return {"error": "No mining_globals config found"}
    config_vars = config["variables"]
    
    ship = db.ships.find_one({"ship_id": mission_raw.get("ship_id")})
    if not ship:
        logging.error(f"No ship found with ID {mission_raw.get('ship_id')}")
        return {"error": f"No ship found with ID {mission_raw.get('ship_id')}"}
    mission.target_yield_kg = Int64(ship["capacity"])
    
    asteroid = db.asteroids.find_one({"full_name": mission.asteroid_full_name})
    if not asteroid:
        logging.error(f"No asteroid found with full_name {mission.asteroid_full_name}")
        return {"error": f"400: No asteroid found with full_name {mission.asteroid_full_name}"}
    
    logging.info(f"Asteroid data: {asteroid}")  # Debug asteroid data
    
    elements = asteroid["elements"]
    commodity_factor = asteroid.get("commodity_factor", 1.0)
    base_travel_days = asteroid["moid_days"]
    
    # Calculate scheduled days
    daily_yield_rate = 500
    estimated_mining_days = mission.target_yield_kg // daily_yield_rate  # e.g., 50,000 / 500 = 100
    mission.scheduled_days = (base_travel_days * 2) + estimated_mining_days
    mission.travel_days_allocated = base_travel_days
    mission.mining_days_allocated = estimated_mining_days

    base_cost = Int64(config_vars["base_cost"]) if not mission.rocket_owned else Int64(int(config_vars["base_cost"]) - 200000000)
    deadline_overrun_fine_per_day = Int64(config_vars["deadline_overrun_fine_per_day"])

    weighted_elements = []
    for elem in elements:
        if elem["name"] in ["Platinum", "Gold"]:
            weight = config_vars["commodity_factor_platinum_gold"] * commodity_factor * 2  # Boost Gold/Platinum
        elif elem["name"] in COMMODITIES:
            weight = config_vars["commodity_factor_other"] * commodity_factor
        else:
            weight = config_vars["non_commodity_weight"]
        weighted_elements.extend([elem] * int(weight))

    elements_mined = {}
    events = mission.events
    daily_summaries = mission.daily_summaries

    if day:  # API day-by-day mode
        if day <= len(daily_summaries):
            return {"error": f"Day {day} already simulated"}
        if day <= base_travel_days:
            day_summary = simulate_travel_day(mission, day)
        elif day <= (base_travel_days + mission.mining_days_allocated):
            day_summary = simulate_mining_day(mission, day - base_travel_days + 1, weighted_elements, elements_mined, api_event)
        else:
            day_summary = simulate_travel_day(mission, day - base_travel_days - mission.mining_days_allocated + 1, is_return=True)
        daily_summaries.append(day_summary)
        events.extend(day_summary.events)
        for event in day_summary.events:
            if "delay_days" in event["effect"]:
                mission.travel_delays += event["effect"]["delay_days"]
                logging.info(f"Day {day_summary.day} Delay: +{event['effect']['delay_days']} days")
            elif "reduce_days" in event["effect"]:
                mission.travel_delays = max(0, mission.travel_delays - event["effect"]["reduce_days"])
                logging.info(f"Day {day_summary.day} Recovery: -{event['effect']['reduce_days']} days")
    else:  # Full simulation
        # Outbound travel
        for d in range(1, base_travel_days + 1):
            day_summary = simulate_travel_day(mission, d)
            daily_summaries.append(day_summary)
            events.extend(day_summary.events)
            for event in day_summary.events:
                if "delay_days" in event["effect"]:
                    mission.travel_delays += event["effect"]["delay_days"]
                    logging.info(f"Day {day_summary.day} Delay: +{event['effect']['delay_days']} days")
                elif "reduce_days" in event["effect"]:
                    mission.travel_delays = max(0, mission.travel_delays - event["effect"]["reduce_days"])
                    logging.info(f"Day {day_summary.day} Recovery: -{event['effect']['reduce_days']} days")
        
        # Mining
        mining_start_day = base_travel_days + 1
        for d in range(1, mission.mining_days_allocated + 1):
            day_summary = simulate_mining_day(mission, mining_start_day + d - 1, weighted_elements, elements_mined)
            daily_summaries.append(day_summary)
            events.extend(day_summary.events)
        
        # Return travel
        return_start_day = base_travel_days + mission.mining_days_allocated + 1
        total_days_so_far = return_start_day - 1
        for d in range(1, base_travel_days + mission.travel_delays + 1):
            day_summary = simulate_travel_day(mission, total_days_so_far + d, is_return=True)
            daily_summaries.append(day_summary)
            events.extend(day_summary.events)
            for event in day_summary.events:
                if "delay_days" in event["effect"]:
                    mission.travel_delays += event["effect"]["delay_days"]
                    logging.info(f"Day {day_summary.day} Delay: +{event['effect']['delay_days']} days")
                elif "reduce_days" in event["effect"]:
                    mission.travel_delays = max(0, mission.travel_delays - event["effect"]["reduce_days"])
                    logging.info(f"Day {day_summary.day} Recovery: -{event['effect']['reduce_days']} days")

    commodity_total_kg = Int64(sum(kg for name, kg in elements_mined.items() if name in COMMODITIES))
    non_commodity_total_kg = Int64(sum(kg for name, kg in elements_mined.items() if name not in COMMODITIES))
    target_commodity_kg = Int64(int(mission.target_yield_kg * 0.5))
    target_non_commodity_kg = mission.target_yield_kg - target_commodity_kg
    
    if commodity_total_kg != target_commodity_kg:
        scale = target_commodity_kg / commodity_total_kg if commodity_total_kg > 0 else 1
        for name in list(elements_mined.keys()):
            if name in COMMODITIES:
                elements_mined[name] = Int64(int(elements_mined[name] * scale))
        commodity_total_kg = Int64(sum(kg for name, kg in elements_mined.items() if name in COMMODITIES))
    
    total_yield_kg = Int64(min(mission.target_yield_kg, commodity_total_kg + non_commodity_total_kg))
    if total_yield_kg < mission.target_yield_kg:
        shortfall = mission.target_yield_kg - total_yield_kg
        non_commodity_count = sum(1 for n in elements_mined if n not in COMMODITIES)
        if non_commodity_count > 0:
            per_non_commodity = Int64(shortfall // non_commodity_count)
            for name in elements_mined:
                if name not in COMMODITIES:
                    elements_mined[name] += per_non_commodity
        total_yield_kg = Int64(sum(elements_mined.values()))
    
    for summary in daily_summaries:
        if summary.day > base_travel_days and summary.day <= (base_travel_days + mission.mining_days_allocated):
            summary.total_kg = Int64(int(summary.total_kg * (total_yield_kg / sum(s.total_kg for s in daily_summaries if s.day > base_travel_days and s.day <= (base_travel_days + mission.mining_days_allocated)))))

    mined_elements = [
        AsteroidElementModel(
            name=name,
            mass_kg=kg,
            number=[e["number"] for e in elements if e["name"] == name][0]
        )
        for name, kg in elements_mined.items() if kg > 0
    ]

    total_cost = Int64(base_cost)
    cost_reduction_applied = False
    investor_boost_count = 0
    for event in events:
        if "cost_reduction" in event["effect"] and not cost_reduction_applied:
            total_cost = Int64(int(total_cost * event["effect"]["cost_reduction"]))
            cost_reduction_applied = True
        if "revenue_multiplier" in event["effect"]:
            investor_boost_count += 1
            if investor_boost_count <= 2:
                mission.revenue_multiplier *= event["effect"]["revenue_multiplier"]

    total_duration = (base_travel_days * 2) + mission.mining_days_allocated + mission.travel_delays
    deadline_overrun = max(0, total_duration - mission.scheduled_days)
    penalties = Int64(deadline_overrun * deadline_overrun_fine_per_day)
    budget_overrun = max(0, total_cost - mission.budget)
    penalties += Int64(budget_overrun)

    investor_loan = Int64(600000000) if not mission.rocket_owned else Int64(0)
    interest_rate = 0.05 if not mission.rocket_owned else 0.20
    investor_repayment = Int64(int(investor_loan * (1 + interest_rate)))
    previous_debt_repayment = Int64(0)
    ship_repair_cost = mission.ship_repair_cost or Int64(0)
    total_expenses = Int64(total_cost + penalties + investor_repayment + ship_repair_cost + previous_debt_repayment)

    prices = fetch_market_prices()
    logging.info("Calculating revenue from mined elements...")
    total_revenue = Int64(0)
    for name, kg in elements_mined.items():
        price_per_kg = prices.get(name, 0) if name in COMMODITIES else 0
        element_value = int(kg * price_per_kg)
        total_revenue += element_value
        logging.info(f"{name}: {kg} kg x ${price_per_kg:.2f}/kg = ${element_value}")
    total_revenue = Int64(int(total_revenue * mission.revenue_multiplier))

    profit = Int64(total_revenue - total_expenses)

    next_launch_cost = Int64(436000000)
    if profit < next_launch_cost and mission.rocket_owned:
        logging.info(f"Profit {profit} below {next_launch_cost} - taking $600M loan at 20% interest")
        investor_loan = Int64(600000000)
        investor_repayment = Int64(int(investor_loan * 1.20))
        total_expenses += investor_repayment
        profit = Int64(total_revenue - total_expenses)

    previous_debt = Int64(0 if profit >= 0 else -profit)

    logging.info(f"Total cost: {total_cost}, Penalties: {penalties}, Investor repayment: {investor_repayment}, Ship repair: {ship_repair_cost}, Previous debt: {previous_debt_repayment}, Total expenses: {total_expenses}, Revenue: {total_revenue}")

    update_data = {
        "user_id": mission.user_id,
        "company": mission.company,
        "asteroid_full_name": mission.asteroid_full_name,
        "name": mission.name,
        "travel_days_allocated": base_travel_days,
        "mining_days_allocated": mission.mining_days_allocated,
        "total_duration_days": total_duration,
        "scheduled_days": mission.scheduled_days,
        "budget": mission.budget,
        "status": 1 if not day else 0,
        "elements": [elem.model_dump() for elem in mined_elements],
        "cost": total_cost,
        "revenue": total_revenue,
        "profit": profit,
        "penalties": penalties,
        "investor_repayment": investor_repayment,
        "ship_repair_cost": ship_repair_cost,
        "previous_debt": previous_debt,
        "events": events,
        "daily_summaries": [summary.__dict__ for summary in daily_summaries],
        "rocket_owned": True,
        "yield_multiplier": mission.yield_multiplier,
        "revenue_multiplier": mission.revenue_multiplier,
        "travel_yield_mod": mission.travel_yield_mod,
        "travel_delays": mission.travel_delays,
        "target_yield_kg": mission.target_yield_kg
    }
    db.missions.update_one({"_id": ObjectId(mission_id)}, {"$set": update_data})

    db.asteroids.update_one(
        {"full_name": mission.asteroid_full_name},
        {"$addToSet": {"mined_by": {"mission_id": mission_id, "company": mission.company}}}
    )

    logging.info(f"Mission {mission_id} mined {total_yield_kg} kg from {mission.asteroid_full_name}, profit: {profit}")
    return update_data

if __name__ == "__main__":
    mission_id = "6612a3b8f9e8d4c7b9a1f2e3"
    mine_asteroid(mission_id)