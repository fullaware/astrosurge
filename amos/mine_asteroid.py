import logging
import random
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Optional
import yfinance as yf
from models.models import MissionModel, MissionDay, PyInt64
from config import MongoDBConfig

HOURS_PER_DAY = 24
COMMODITIES = ["Copper", "Silver", "Palladium", "Platinum", "Gold"]

db = MongoDBConfig.get_database()

def fetch_mining_config() -> Dict:
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
    logging.info("Checking cached market prices...")
    cache = db.market_prices.find_one({"name": "commodity_prices"})
    now = datetime.now(UTC)
    
    # Ensure cache["timestamp"] is UTC-aware
    cache_age = float("inf")
    if cache and "timestamp" in cache:
        # Convert naive or string timestamp to UTC-aware datetime
        if isinstance(cache["timestamp"], str):
            timestamp = datetime.fromisoformat(cache["timestamp"].replace("Z", "+00:00"))
        elif isinstance(cache["timestamp"], datetime) and cache["timestamp"].tzinfo is None:
            timestamp = cache["timestamp"].replace(tzinfo=UTC)
        else:
            timestamp = cache["timestamp"]
        cache_age = (now - timestamp).days

    if cache and cache_age < 4:
        logging.info(f"Using cached market prices (age: {cache_age} days)")
        return cache["prices"]

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

    # Update cache with UTC-aware timestamp
    db.market_prices.update_one(
        {"name": "commodity_prices"},
        {"$set": {"prices": prices, "timestamp": now}},
        upsert=True
    )
    logging.info("Updated market_prices cache")
    return prices

def calculate_confidence(travel_days: int, mining_power: int, target_yield_kg: int, daily_yield_rate: int, max_overrun_days: int, ship_reused: bool) -> tuple[float, int, int]:
    config = fetch_mining_config()
    daily_mission_cost = config["daily_mission_cost"]
    ship_cost = config["ship_cost"] * (config["ship_reuse_discount"] if ship_reused else 1)
    deadline_overrun_fine_per_day = config["deadline_overrun_fine_per_day"]
    commodity_weights = config["commodity_weights"]

    avg_yield_per_hour = mining_power / 2
    daily_yield = avg_yield_per_hour * HOURS_PER_DAY * config["max_element_percentage"]
    mining_days_needed = target_yield_kg / daily_yield
    total_mission_days = (travel_days * 2) + mining_days_needed

    delay_risk = 0.05 * travel_days * 2
    risk_factor = 0.05 * travel_days + 0.01 * mining_days_needed + delay_risk
    confidence = max(0.0, min(100.0, 95 - (risk_factor * 100)))

    # Estimate commodity yields (50% of target_yield_kg split by weights)
    total_weight = sum(commodity_weights.values())
    commodity_yields = {}
    commodity_fraction = 0.5 * target_yield_kg
    for commodity, weight in commodity_weights.items():
        commodity_yields[commodity] = PyInt64(int(commodity_fraction * (weight / total_weight)))

    # Calculate gross revenue from market prices
    prices = fetch_market_prices()
    gross_revenue = PyInt64(sum(kg * prices.get(commodity, 0) for commodity, kg in commodity_yields.items()))

    # Calculate costs
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
        daily_value=PyInt64(0),
        note=note
    )

def simulate_mining_day(mission: MissionModel, day: int, weighted_elements: List, elements_mined: dict, api_event: Optional[dict], mining_power: int, prices: Dict[str, int], base_travel_days: int) -> MissionDay:
    config = fetch_mining_config()
    max_element_percentage = 0.5  # Increased from 0.1 to 0.5 for higher yield
    element_yield_min = config["element_yield_min"]

    daily_yield = PyInt64(sum(random.randint(1, mining_power) for _ in range(HOURS_PER_DAY)))
    # Removed mission.yield_multiplier application here, as it's now handled day-specifically in EventProcessor

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
        # Filter elements with non-zero mass
        valid_elements = [e for e in weighted_elements if e["mass_kg"] > 0]
        logging.info(f"Day {day}: Weighted elements received: {[e['name'] for e in valid_elements]}")
        
        num_elements = len(valid_elements)
        if num_elements == 0:
            logging.warning(f"Day {day}: No elements with mass > 0 provided!")
            return MissionDay(day=day, total_kg=PyInt64(0), elements_mined={}, events=events, daily_value=PyInt64(0), note=note)

        # Assign base yield of 1 kg to each element
        base_yield = PyInt64(1)
        base_total = PyInt64(num_elements * base_yield)
        remaining_yield = PyInt64(max(0, element_yield - base_total))

        # Calculate total weight for distribution
        total_weight = sum(e["weight"] for e in valid_elements)
        if total_weight == 0:
            total_weight = 1  # Avoid division by zero

        for elem in valid_elements:
            elem_name = elem["name"]
            weight = elem["weight"]
            # Base yield plus weighted share of remaining yield
            extra_yield = PyInt64(int(remaining_yield * (weight / total_weight)))
            mined[elem_name] = base_yield + extra_yield

        # Adjust to match element_yield exactly
        current_total = sum(mined.values())
        if current_total != element_yield:
            adjustment = element_yield - current_total
            adjust_elem = random.choice(list(mined.keys()))
            mined[adjust_elem] = PyInt64(max(0, mined[adjust_elem] + adjustment))

        logging.info(f"Day {day}: Mined elements: {mined}")

        # Update mission-wide elements_mined
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