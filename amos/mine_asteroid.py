import random
import pymongo
import yfinance as yf
from datetime import datetime, UTC
import logging
from models.models import MissionModel, MissionDay, PyInt64
from config import MongoDBConfig, LoggingConfig
from amos.event_processor import EventProcessor

db = MongoDBConfig.get_database()
LoggingConfig.setup_logging(log_to_file=False)

COMMODITIES = ["Copper", "Silver", "Palladium", "Platinum", "Gold"]
TROY_OUNCES_PER_KG = 32.1507
HOURS_PER_DAY = 24

def fetch_market_prices() -> dict:
    symbols = {"Copper": "HG=F", "Silver": "SI=F", "Palladium": "PA=F", "Platinum": "PL=F", "Gold": "GC=F"}
    prices = {}
    logging.info("Fetching fresh market prices from yfinance (per troy ounce)...")
    try:
        for name, symbol in symbols.items():
            ticker = yf.Ticker(symbol)
            price_per_oz = ticker.history(period="1d")["Close"].iloc[-1]
            price_per_kg = PyInt64(round(price_per_oz * TROY_OUNCES_PER_KG))
            prices[name] = price_per_kg
            logging.info(f"Fetched {name} ({symbol}): ${price_per_oz:.2f}/oz -> ${price_per_kg}/kg")
    except Exception as e:
        logging.error(f"yfinance failed: {e}")
        logging.info("Using static prices (per kg)...")
        prices = {"Copper": PyInt64(193), "Silver": PyInt64(984), "Palladium": PyInt64(31433), "Platinum": PyInt64(31433), "Gold": PyInt64(99233)}
        for name, price in prices.items():
            logging.info(f"Static {name}: ${price}/kg")
    
    try:
        db.market_prices.insert_one({"timestamp": datetime.now(UTC).isoformat() + "Z", "prices": prices})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to insert market prices into MongoDB: {e}")
    return prices

def simulate_travel_day(mission: MissionModel, day: int, is_return: bool = False) -> MissionDay:
    note = "Travel - No incident" if not is_return else "Return Travel - No incident"
    day_summary = MissionDay(day=day, total_kg=PyInt64(0), note=note)
    day_summary = EventProcessor.apply_daily_events(mission, day_summary, {}, None)
    return day_summary

def simulate_mining_day(mission: MissionModel, day: int, weighted_elements: list, elements_mined: dict, api_event: dict = None, mining_power: int = 500, prices: dict = None, base_travel_days: int = 0) -> MissionDay:
    total_daily_material = PyInt64(mining_power * HOURS_PER_DAY)  # e.g., 12,000 kg/day
    element_fraction = random.uniform(0.01, 0.10)  # 1-10% elements
    daily_yield_kg = PyInt64(int(total_daily_material * element_fraction * 3))  # ~360-3,600 kg/day
    
    current_yield = PyInt64(sum(int(kg) for kg in elements_mined.values()))
    remaining_capacity = PyInt64(max(0, mission.target_yield_kg - current_yield))
    daily_yield_kg = PyInt64(min(daily_yield_kg, remaining_capacity))
    
    daily_elements = {}
    daily_value = PyInt64(0)
    for hour in range(HOURS_PER_DAY):
        if daily_yield_kg <= 0 or current_yield >= mission.target_yield_kg:
            break
        hour_yield = PyInt64(daily_yield_kg // HOURS_PER_DAY)
        if hour_yield <= 0:
            hour_yield = PyInt64(1)  # Minimum 1 kg/hour
        active_elements = random.sample(weighted_elements, k=min(random.randint(1, 4), len(weighted_elements)))
        for elem in active_elements:
            if current_yield >= mission.target_yield_kg:
                break
            elem_name = elem["name"] if isinstance(elem, dict) else elem
            elem_yield = PyInt64(hour_yield // len(active_elements))
            if isinstance(elem, dict) and elem["mass_kg"] < elem_yield:
                elem_yield = elem["mass_kg"]
            adjusted_yield = PyInt64(min(elem_yield, mission.target_yield_kg - current_yield))
            if adjusted_yield <= 0:
                continue
            try:
                db.asteroids.update_one(
                    {"full_name": mission.asteroid_full_name, "elements.name": elem_name},
                    {"$inc": {"elements.$.mass_kg": -adjusted_yield}}
                )
            except pymongo.errors.AutoReconnect as e:
                logging.error(f"Failed to update asteroid {mission.asteroid_full_name} for {elem_name}: {e}")
                return {"error": "Trouble accessing the database, please try again later"}
            daily_elements[elem_name] = daily_elements.get(elem_name, 0) + adjusted_yield
            elements_mined[elem_name] = elements_mined.get(elem_name, 0) + adjusted_yield
            current_yield += adjusted_yield
            if prices and elem_name in prices:
                daily_value += PyInt64(adjusted_yield * prices[elem_name])
        daily_yield_kg -= hour_yield * len(active_elements)

    day_summary = MissionDay(day=day, total_kg=sum(daily_elements.values()), note="Mining - Steady operation")
    day_summary = EventProcessor.apply_daily_events(mission, day_summary, daily_elements, api_event)
    day_summary.elements_mined = daily_elements
    day_summary.daily_value = daily_value
    return day_summary

def calculate_confidence(moid_days: int, mining_power: int, target_yield_kg: int, daily_yield_rate: int) -> tuple:
    try:
        event_risk = sum(event["probability"] for event in db.events.find()) / (db.events.count_documents({}) or 1)
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to fetch events for confidence calculation: {e}")
        event_risk = random.uniform(0.3, 0.7)
    travel_factor = max(0, 100 - moid_days * 2)
    mining_factor = min(100, mining_power / 5)
    risk_factor = (1 - event_risk) * 100
    yield_factor = min(100, (daily_yield_rate / (target_yield_kg / 100)) * 100)
    confidence = (travel_factor * 0.25 + mining_factor * 0.25 + risk_factor * 0.25 + yield_factor * 0.25)
    
    avg_commodity_value = PyInt64(sum([193, 984, 31433, 31433, 99233]) // 5)
    estimated_revenue = PyInt64(target_yield_kg * avg_commodity_value * random.uniform(0.4, 0.6))
    estimated_cost = PyInt64(200000000 + (moid_days * 50000 * 2))  # Base cost + travel days
    base_profit = PyInt64(estimated_revenue - estimated_cost)
    profit_variance = PyInt64((100 - confidence) * 15000000)
    profit_min = PyInt64(base_profit - profit_variance - 400000000)
    profit_max = PyInt64(base_profit + profit_variance + 2000000000)
    
    return confidence, profit_min, profit_max