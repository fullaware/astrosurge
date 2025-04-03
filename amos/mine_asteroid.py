import logging
import random
from datetime import datetime
from typing import List, Dict, Optional
import yfinance as yf
from models.models import MissionModel, MissionDay, PyInt64
from config import MongoDBConfig

HOURS_PER_DAY = 24
COMMODITIES = ["Copper", "Silver", "Palladium", "Platinum", "Gold"]

def fetch_mining_config() -> Dict:
    db = MongoDBConfig.get_database()
    try:
        config = db.config.find_one({"name": "mining_globals"})
        if not config:
            raise RuntimeError("Mining globals config not found in asteroids.config")
        variables = config["variables"]
        logging.info(f"Fetched mining_globals: {variables}")
        return variables
    except Exception as e:
        logging.error(f"Failed to fetch mining globals from MongoDB: {e}")
        raise RuntimeError("Critical failure: Unable to access mining globals configuration")

def fetch_market_prices() -> Dict[str, int]:
    logging.info("Fetching fresh market_prices from yfinance (per troy ounce)...")
    prices = {}
    commodity_tickers = {
        "Copper": "HG=F",
        "Silver": "SI=F",
        "Palladium": "PA=F",
        "Platinum": "PL=F",
        "Gold": "GC=F"
    }
    for commodity, ticker in commodity_tickers.items():
        try:
            data = yf.download(ticker, period="1d", interval="1d")["Close"].iloc[-1]
            price_per_oz = float(data)
            price_per_kg = PyInt64(int(price_per_oz * 32.1507))
            prices[commodity] = price_per_kg
            logging.info(f"Fetched {commodity} ({ticker}): ${price_per_oz:.2f}/oz -> ${price_per_kg}/kg")
        except Exception as e:
            logging.error(f"Failed to fetch {commodity} price: {e}")
            prices[commodity] = PyInt64(0)
    return prices

def calculate_confidence(travel_days: int, mining_power: int, target_yield_kg: int, daily_yield_rate: int, max_overrun_days: int, ship_reused: bool) -> tuple[float, int, int]:
    config = fetch_mining_config()
    profit_per_kg = config["profit_per_kg"]
    daily_mission_cost = config["daily_mission_cost"]
    ship_cost = config["ship_cost"] * (config["ship_reuse_discount"] if ship_reused else 1)
    deadline_overrun_fine_per_day = config["deadline_overrun_fine_per_day"]

    avg_yield_per_hour = mining_power / 2
    daily_yield = avg_yield_per_hour * HOURS_PER_DAY * config["max_element_percentage"]
    mining_days_needed = target_yield_kg / daily_yield
    total_mission_days = (travel_days * 2) + mining_days_needed

    delay_risk = 0.05 * travel_days * 2
    risk_factor = 0.05 * travel_days + 0.01 * mining_days_needed + delay_risk
    confidence = max(0.0, min(100.0, 95 - (risk_factor * 100)))
    
    gross_revenue = target_yield_kg * profit_per_kg
    mission_cost = ship_cost + (daily_mission_cost * total_mission_days)
    max_penalties = max_overrun_days * deadline_overrun_fine_per_day
    profit_max = PyInt64(int(gross_revenue - mission_cost - max_penalties))
    profit_min = PyInt64(int(-mission_cost * risk_factor))
    return confidence, profit_min, profit_max

def simulate_travel_day(mission: MissionModel, day: int, is_return: bool = False) -> MissionDay:
    config = fetch_mining_config()
    daily_mission_cost = config["daily_mission_cost"]

    events = []
    note = "Travel outbound" if not is_return else "Travel return"
    if random.random() < 0.05:
        delay_days = random.randint(1, 3)
        events.append({"type": "Travel Delay", "effect": {"delay_days": delay_days}})
        note += f" - Delayed {delay_days} days"
    elif random.random() < 0.02 and not is_return:
        events.append({"type": "Tailwind", "effect": {"reduce_days": 1}})
        note += " - Speed boost"
    logging.info(f"Day {day}: Applied {len(events)} events")
    return MissionDay(
        day=day,
        total_kg=PyInt64(0),
        elements_mined={},
        events=events,
        daily_value=PyInt64(0),  # No revenue during travel
        note=note
    )

def simulate_mining_day(mission: MissionModel, day: int, weighted_elements: List, elements_mined: dict, api_event: Optional[dict], mining_power: int, prices: Dict[str, int], base_travel_days: int) -> MissionDay:
    config = fetch_mining_config()
    max_element_percentage = config["max_element_percentage"]
    element_yield_min = config["element_yield_min"]
    commodity_weights = config["commodity_weights"]
    non_commodity_weight = config["non_commodity_weight"]

    daily_yield = PyInt64(sum(random.randint(1, mining_power) for _ in range(HOURS_PER_DAY)))
    daily_yield = PyInt64(int(daily_yield * mission.yield_multiplier))

    max_element_yield = PyInt64(int(daily_yield * max_element_percentage))
    element_yield = PyInt64(random.randint(element_yield_min, max_element_yield))

    regolith = PyInt64(daily_yield - element_yield)

    mined = {}
    events = []
    note = f"Mining day - {element_yield} kg elements, {regolith} kg regolith discarded"

    if api_event:
        events.append(api_event)
        note += f" - {api_event['type']}"

    if weighted_elements and element_yield > 0:
        element_choices = []
        weights = []
        for elem in weighted_elements:
            elem_name = elem["name"] if isinstance(elem, dict) else elem
            weight = commodity_weights.get(elem_name, non_commodity_weight)
            element_choices.append(elem_name)
            weights.append(weight)

        num_elements = max(1, int(element_yield / 10))
        mined_elements = random.choices(element_choices, weights=weights, k=num_elements)
        for elem_name in mined_elements:
            mined[elem_name] = mined.get(elem_name, 0) + PyInt64(10)

        current_total = sum(mined.values())
        if current_total != element_yield:
            adjustment = element_yield - current_total
            adjust_elem = random.choice(list(mined.keys()))
            mined[adjust_elem] = PyInt64(max(0, mined[adjust_elem] + adjustment))

        for name, kg in mined.items():
            elements_mined[name] = elements_mined.get(name, 0) + kg

    daily_value = PyInt64(sum(kg * prices.get(name, 0) for name, kg in mined.items() if name in COMMODITIES))
    logging.info(f"Day {day}: Applied {len(events)} events")
    return MissionDay(
        day=day,
        total_kg=element_yield,
        elements_mined=mined,
        events=events,
        daily_value=daily_value,
        note=note
    )