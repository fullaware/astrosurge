import random
import pymongo
import yfinance as yf
from bson import ObjectId
from bson.int64 import Int64
from datetime import datetime, UTC
import logging
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from models.models import MissionModel, AsteroidElementModel, MissionDay, ShipModel
from config import MongoDBConfig, LoggingConfig
from amos.event_processor import EventProcessor

db = MongoDBConfig.get_database()
LoggingConfig.setup_logging(log_to_file=False)

COMMODITIES = ["Copper", "Silver", "Palladium", "Platinum", "Gold"]
TROY_OUNCES_PER_KG = 32.1507
VALIDATION_PATTERN = re.compile(r'^[a-zA-Z0-9]{1,30}$')

def fetch_market_prices() -> dict:
    symbols = {"Copper": "HG=F", "Silver": "SI=F", "Palladium": "PA=F", "Platinum": "PL=F", "Gold": "GC=F"}
    prices = {}
    logging.info("Fetching fresh market prices from yfinance (per troy ounce)...")
    try:
        for name, symbol in symbols.items():
            ticker = yf.Ticker(symbol)
            price_per_oz = ticker.history(period="1d")["Close"].iloc[-1]
            price_per_kg = Int64(round(price_per_oz * TROY_OUNCES_PER_KG))
            prices[name] = price_per_kg
            logging.info(f"Fetched {name} ({symbol}): ${price_per_oz:.2f}/oz -> ${price_per_kg}/kg")
    except Exception as e:
        logging.error(f"yfinance failed: {e}")
        logging.info("Using static prices (per kg)...")
        prices = {"Copper": Int64(193), "Silver": Int64(984), "Palladium": Int64(31433), "Platinum": Int64(31433), "Gold": Int64(99233)}
        for name, price in prices.items():
            logging.info(f"Static {name}: ${price}/kg")
    
    try:
        db.market_prices.insert_one({"timestamp": datetime.now(UTC).isoformat() + "Z", "prices": prices})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to insert market prices into MongoDB: {e}")
    return prices

def simulate_travel_day(mission: MissionModel, day: int, is_return: bool = False) -> MissionDay:
    note = "Travel - No incident" if not is_return else "Return Travel - No incident"
    day_summary = MissionDay(day=day, total_kg=Int64(0), note=note)
    day_summary = EventProcessor.apply_daily_events(mission, day_summary, {}, None)
    return day_summary

def simulate_mining_day(mission: MissionModel, day: int, weighted_elements: list, elements_mined: dict, api_event: dict = None, mining_power: int = 500, prices: dict = None, base_travel_days: int = 0, estimated_mining_days: int = 0) -> MissionDay:
    current_yield = Int64(sum(int(kg) for kg in elements_mined.values()))
    remaining_capacity = Int64(max(0, mission.target_yield_kg - current_yield))
    remaining_mining_days = max(1, (base_travel_days + estimated_mining_days) - day)
    
    max_daily_kg = Int64(mining_power * 24)
    target_daily_kg = Int64(min(remaining_capacity // remaining_mining_days, max_daily_kg))
    daily_yield_kg = Int64(min(random.randint(max(0, target_daily_kg - 100), target_daily_kg + 100), remaining_capacity))
    
    active_elements = random.sample(weighted_elements, k=min(random.randint(1, 4), len(weighted_elements)))
    
    daily_elements = {}
    daily_value = Int64(0)
    for elem in active_elements:
        elem_name = elem["name"]
        yield_kg = Int64(min(daily_yield_kg * random.uniform(0.05, 0.4), daily_yield_kg // len(active_elements)))
        if elem["mass_kg"] < yield_kg:
            yield_kg = elem["mass_kg"]
        try:
            db.asteroids.update_one(
                {"full_name": mission.asteroid_full_name, "elements.name": elem_name},
                {"$inc": {"elements.$.mass_kg": -yield_kg}}
            )
        except pymongo.errors.AutoReconnect as e:
            logging.error(f"Failed to update asteroid {mission.asteroid_full_name} for {elem_name}: {e}")
            return {"error": "Trouble accessing the database, please try again later"}
        daily_elements[elem_name] = daily_elements.get(elem_name, 0) + yield_kg
        elements_mined[elem_name] = elements_mined.get(elem_name, 0) + yield_kg
        if prices and elem_name in prices:
            daily_value += Int64(yield_kg * prices[elem_name])

    day_summary = MissionDay(day=day, total_kg=daily_yield_kg, note="Mining - Steady operation")
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
    
    avg_commodity_value = Int64(sum([193, 984, 31433, 31433, 99233]) // 5)
    estimated_revenue = Int64(target_yield_kg * avg_commodity_value * random.uniform(0.4, 0.6))
    estimated_cost = Int64(random.randint(350000000, 450000000) + (moid_days * 1000000))
    base_profit = Int64(estimated_revenue - estimated_cost)
    profit_variance = Int64((100 - confidence) * 15000000)
    profit_min = Int64(base_profit - profit_variance - 400000000)
    profit_max = Int64(base_profit + profit_variance + 200000000)
    
    return confidence, profit_min, profit_max

def validate_ship_name(ship_name: str) -> bool:
    return bool(VALIDATION_PATTERN.match(ship_name))

def create_new_ship(user_id: str, ship_name: str, username: str, company_name: str) -> ShipModel:
    if not validate_ship_name(ship_name):
        raise ValueError(f"Ship name '{ship_name}' must be alphanumeric and up to 30 characters")
    ship_data = {
        "_id": ObjectId(),
        "name": ship_name,
        "user_id": user_id,
        "shield": 100,
        "mining_power": 500,
        "created": datetime.now(UTC),
        "days_in_service": 0,
        "location": Int64(0),
        "mission": 0,
        "hull": 100,
        "cargo": [],
        "capacity": 50000,
        "active": True,
        "missions": []
    }
    db.ships.insert_one(ship_data)
    logging.info(f"User {username}: Created new ship {ship_name} for company {company_name}")
    return ShipModel(**ship_data)

def get_day(summary) -> int:
    return summary.day if isinstance(summary, MissionDay) else summary["day"]

def get_elements_mined(summary) -> dict:
    elements = summary.elements_mined if isinstance(summary, MissionDay) else summary.get("elements_mined")
    return elements if elements is not None else {}

def get_daily_value(summary) -> int:
    value = summary.daily_value if isinstance(summary, MissionDay) else summary.get("daily_value", 0)
    return value if value is not None else 0

def process_single_mission(mission_raw: dict, day: int = None, api_event: dict = None, username: str = None, company_name: str = None) -> dict:
    mission_id = str(mission_raw["_id"])
    mission_raw_adjusted = mission_raw.copy()
    if "target_yield_kg" in mission_raw_adjusted:
        mission_raw_adjusted["target_yield_kg"] = Int64(mission_raw_adjusted["target_yield_kg"])
    mission_raw_adjusted["confidence"] = mission_raw_adjusted.get("confidence", 0.0)
    mission_raw_adjusted["predicted_profit_max"] = mission_raw_adjusted.get("predicted_profit_max", 0)
    mission_raw_adjusted["ship_location"] = Int64(mission_raw_adjusted.get("ship_location", 0))
    mission = MissionModel(**mission_raw_adjusted)
    mission.yield_multiplier = mission_raw.get("yield_multiplier", 1.0)
    mission.revenue_multiplier = mission_raw.get("revenue_multiplier", 1.0)
    mission.travel_yield_mod = mission_raw.get("travel_yield_mod", 1.0)
    mission.ship_repair_cost = Int64(mission_raw.get("ship_repair_cost", 0))
    mission.events = mission_raw.get("events", [])
    mission.daily_summaries = mission_raw.get("daily_summaries", [])
    mission.previous_debt = Int64(mission_raw.get("previous_debt", 0))
    mission.travel_delays = Int64(mission_raw.get("travel_delays", 0))
    ship_name = mission_raw.get("ship_name")

    logging.info(f"User {username}: Processing mission {mission_id} to {mission.asteroid_full_name} for company {company_name} with ship {ship_name}")

    try:
        config = db.config.find_one({"name": "mining_globals"})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to fetch config from MongoDB: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not config:
        logging.error(f"User {username}: No mining_globals config found")
        return {"error": "No mining_globals config found"}
    config_vars = config["variables"]

    try:
        ship = db.ships.find_one({"user_id": mission.user_id, "name": ship_name})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to fetch ship {ship_name} for user_id {mission.user_id}: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not ship:
        logging.error(f"User {username}: Ship {ship_name} not found for mission {mission_id}")
        return {"error": f"Ship {ship_name} not found"}
    ship_model = ShipModel(**ship)
    mission.target_yield_kg = Int64(ship_model.capacity)
    logging.info(f"User {username}: Using ship {ship_name} with capacity {ship_model.capacity} kg, mining_power {ship_model.mining_power} kg/hour for company {company_name}")

    try:
        asteroid = db.asteroids.find_one({"full_name": mission.asteroid_full_name})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to fetch asteroid {mission.asteroid_full_name}: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not asteroid:
        logging.error(f"User {username}: No asteroid found with full_name {mission.asteroid_full_name}")
        return {"error": f"400: No asteroid found with full_name {mission.asteroid_full_name}"}
    
    logging.info(f"User {username}: Asteroid {mission.asteroid_full_name} loaded, moid_days: {asteroid['moid_days']} for company {company_name}")

    try:
        user = db.users.find_one({"_id": ObjectId(mission.user_id)})
        if user and "company_name" in user and not company_name:
            company_name = user["company_name"]
        elif not company_name:
            company_name = mission.company
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to fetch user for user_id {mission.user_id}: {e}")
        company_name = mission.company

    daily_yield_rate = Int64(random.randint(ship_model.mining_power, ship_model.mining_power * 2))
    confidence, profit_min, profit_max = calculate_confidence(asteroid["moid_days"], ship_model.mining_power, mission.target_yield_kg, daily_yield_rate)
    confidence = confidence if confidence is not None else 0.0
    profit_max = Int64(profit_max if profit_max is not None else 0)
    logging.info(f"User {username}: Confidence: {confidence:.2f}%, Predicted profit range: ${profit_min:,} to ${profit_max:,} for company {company_name}, ship {ship_name}")

    elements = asteroid["elements"]
    commodity_factor = asteroid.get("commodity_factor", 1.0)
    base_travel_days = Int64(asteroid["moid_days"])
    estimated_mining_days = Int64(mission.target_yield_kg // daily_yield_rate)
    scheduled_days = Int64((base_travel_days * 2) + estimated_mining_days)

    base_cost = Int64(random.randint(350000000, 450000000))
    deadline_overrun_fine_per_day = Int64(config_vars["deadline_overrun_fine_per_day"])
    prices = fetch_market_prices()

    weighted_elements = []
    for elem in elements:
        if elem["name"] in ["Platinum", "Gold"]:
            weight = config_vars["commodity_factor_platinum_gold"] * commodity_factor * random.uniform(2, 4)
        elif elem["name"] in COMMODITIES:
            weight = config_vars["commodity_factor_other"] * commodity_factor * random.uniform(1, 2)
        else:
            weight = config_vars["non_commodity_weight"]
        weighted_elements.extend([elem] * int(weight))

    elements_mined = mission_raw.get("elements_mined", {})
    events = mission.events
    daily_summaries = mission.daily_summaries

    total_yield_kg = Int64(mission_raw.get("total_yield_kg", sum(int(kg) for kg in elements_mined.values())))
    days_into_mission = Int64(len(daily_summaries))
    ship_location = Int64(mission_raw.get("ship_location", ship_model.location))
    mission_cost = Int64(mission_raw.get("mission_cost", 0))
    mission_projection = Int64(mission_raw.get("mission_projection", profit_max))

    if day:
        if day <= days_into_mission:
            return {"error": f"Day {day} already simulated for mission {mission_id}"}
        if day <= base_travel_days:
            day_summary = simulate_travel_day(mission, day)
            ship_location = Int64(ship_location + 1)
        elif day <= (base_travel_days + estimated_mining_days):
            day_summary = simulate_mining_day(mission, day, weighted_elements, elements_mined, api_event, ship_model.mining_power, prices, base_travel_days, estimated_mining_days)
            ship_location = base_travel_days
            total_yield_kg = Int64(min(total_yield_kg + day_summary.total_kg, ship_model.capacity))
            mission_cost += day_summary.daily_value if day_summary.daily_value else Int64(0)
        else:
            day_summary = simulate_travel_day(mission, day, is_return=True)
            ship_location = Int64(max(0, ship_location - 1))
            if ship_location == 0:  # Back at Earth, sell cargo
                prices = fetch_market_prices()
                total_revenue = Int64(0)
                for name, kg in elements_mined.items():
                    price_per_kg = prices.get(name, 0) if name in COMMODITIES else Int64(0)
                    element_value = Int64(kg * price_per_kg)
                    total_revenue += element_value
                    logging.info(f"User {username}: Sold {name}: {kg} kg x ${price_per_kg}/kg = ${element_value} for company {company_name}, ship {ship_name}")
                total_revenue = Int64(int(total_revenue * mission.revenue_multiplier))
                total_cost = mission_cost
                profit = Int64(total_revenue - total_cost)
                mission.status = 1
        
        if isinstance(day_summary, dict) and "error" in day_summary:
            return day_summary
        daily_summaries.append(day_summary)
        updated_events = []
        for event in day_summary.events:
            event_with_day = event.copy()
            event_with_day["day"] = day
            updated_events.append(event_with_day)
        events.extend(updated_events)
        for event in updated_events:
            if "delay_days" in event["effect"]:
                mission.travel_delays += Int64(event["effect"]["delay_days"])
                logging.info(f"User {username}: Day {day} Delay: +{event['effect']['delay_days']} days for company {company_name}, ship {ship_name}")
            elif "reduce_days" in event["effect"]:
                mission.travel_delays = Int64(max(0, mission.travel_delays - event["effect"]["reduce_days"]))
                logging.info(f"User {username}: Day {day} Recovery: -{event['effect']['reduce_days']} days for company {company_name}, ship {ship_name}")
        days_into_mission = Int64(len(daily_summaries))
        days_left = Int64(scheduled_days + mission.travel_delays - days_into_mission if days_into_mission < scheduled_days + mission.travel_delays else 0)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        days = [f"Day {get_day(d)}" for d in daily_summaries]
        elements = [elem for elem in COMMODITIES if any(elem in get_elements_mined(d) for d in daily_summaries)]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD']
        for i, element in enumerate(elements):
            fig.add_trace(
                go.Bar(
                    x=days,
                    y=[get_elements_mined(d).get(element, 0) for d in daily_summaries],
                    name=element,
                    marker_color=colors[i % len(colors)]
                )
            )
        value_data = [sum(get_daily_value(d) for d in daily_summaries[:i+1]) for i in range(len(daily_summaries))]
        fig.add_trace(
            go.Scatter(
                x=days,
                y=value_data,
                name="Value Accrued ($)",
                line=dict(color="#00d4ff", width=2),
                yaxis="y2"
            ),
            secondary_y=True
        )
        fig.update_layout(
            barmode='stack',
            title_text=f"Mining Progress (Valued Elements) - Mission {mission_id}",
            xaxis_title="Day",
            yaxis_title="Mass Mined (kg)",
            yaxis2_title="Value ($)",
            template="plotly_dark",
            height=400
        )
        graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        mission.travel_days_allocated = base_travel_days
        mission.mining_days_allocated = estimated_mining_days
        mission.scheduled_days = scheduled_days
        daily_summaries = []
        events = []
        total_yield_kg = Int64(0)
        total_cost = Int64(0)
        total_revenue = Int64(0)
        profit = Int64(0)
        penalties = Int64(0)
        investor_repayment = Int64(0)
        ship_repair_cost = Int64(0)
        total_duration = Int64(0)
        confidence_result = ""
        graph_html = ""
        ship_location = Int64(0)

    days_left = Int64(scheduled_days + mission.travel_delays - days_into_mission if days_into_mission < scheduled_days + mission.travel_delays else 0)

    if not day:  # Full mission calculation
        commodity_total_kg = Int64(sum(kg for name, kg in elements_mined.items() if name in COMMODITIES))
        non_commodity_total_kg = Int64(sum(kg for name, kg in elements_mined.items() if name not in COMMODITIES))
        target_commodity_kg = Int64(int(mission.target_yield_kg * random.uniform(0.4, 0.6)))
        target_non_commodity_kg = Int64(mission.target_yield_kg - target_commodity_kg)
        
        if commodity_total_kg != target_commodity_kg:
            scale = target_commodity_kg / commodity_total_kg if commodity_total_kg > 0 else 1
            for name in list(elements_mined.keys()):
                if name in COMMODITIES:
                    elements_mined[name] = Int64(int(elements_mined[name] * scale))
            commodity_total_kg = Int64(sum(kg for name, kg in elements_mined.items() if name in COMMODITIES))
        
        total_yield_kg = Int64(min(mission.target_yield_kg, commodity_total_kg + non_commodity_total_kg))
        if total_yield_kg < mission.target_yield_kg:
            shortfall = Int64(mission.target_yield_kg - total_yield_kg)
            non_commodity_count = sum(1 for n in elements_mined if n not in COMMODITIES)
            if non_commodity_count > 0:
                per_non_commodity = Int64(shortfall // non_commodity_count)
                for name in elements_mined:
                    if name not in COMMODITIES:
                        elements_mined[name] += per_non_commodity
            total_yield_kg = Int64(sum(elements_mined.values()))
        
        for summary in daily_summaries:
            summary_day = get_day(summary)
            if summary_day > base_travel_days and summary_day <= (base_travel_days + estimated_mining_days):
                total_kg_sum = sum(get_day(s) > base_travel_days and get_day(s) <= (base_travel_days + estimated_mining_days) and s.total_kg or 0 for s in daily_summaries)
                summary.total_kg = Int64(int(summary.total_kg * (total_yield_kg / total_kg_sum)) if total_kg_sum > 0 else summary.total_kg)
                elements_mined_dict = get_elements_mined(summary)
                if elements_mined_dict:
                    for elem_name in elements_mined_dict:
                        elements_mined_dict[elem_name] = int(elements_mined_dict[elem_name] * scale)
                    summary.daily_value = Int64(sum(elements_mined_dict.get(name, 0) * prices.get(name, 0) for name in elements_mined_dict))

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

        total_duration = Int64((base_travel_days * 2) + estimated_mining_days + mission.travel_delays)
        deadline_overrun = Int64(max(0, total_duration - scheduled_days))
        penalties = Int64(deadline_overrun * deadline_overrun_fine_per_day)
        budget_overrun = Int64(max(0, total_cost - mission.budget))
        penalties += budget_overrun

        investor_loan = Int64(600000000) if not mission.rocket_owned else Int64(0)
        interest_rate = 0.05 if not mission.rocket_owned else 0.20
        investor_repayment = Int64(int(investor_loan * (1 + interest_rate)))
        ship_repair_cost = mission.ship_repair_cost or Int64(0)
        total_expenses = Int64(total_cost + penalties + investor_repayment + ship_repair_cost + mission.previous_debt)

        logging.info(f"User {username}: Calculating revenue from mined elements for company {company_name}, ship {ship_name}")
        total_revenue = Int64(0)
        for name, kg in elements_mined.items():
            price_per_kg = prices.get(name, 0) if name in COMMODITIES else Int64(0)
            element_value = Int64(kg * price_per_kg)
            total_revenue += element_value
            if name in COMMODITIES:
                logging.info(f"User {username}: {name}: {kg} kg x ${price_per_kg}/kg = ${element_value} for company {company_name}, ship {ship_name}")
        total_revenue = Int64(int(total_revenue * mission.revenue_multiplier))

        profit = Int64(total_revenue - total_expenses)

        next_launch_cost = Int64(436000000)
        if profit < next_launch_cost and mission.rocket_owned:
            logging.info(f"User {username}: Profit {profit} below {next_launch_cost} - taking $600M loan at 20% interest for company {company_name}, ship {ship_name}")
            investor_loan = Int64(600000000)
            investor_repayment = Int64(int(investor_loan * 1.20))
            total_expenses += investor_repayment
            profit = Int64(total_revenue - total_expenses)

        mission.previous_debt = Int64(0 if profit >= 0 else -profit)
        mission_cost = total_expenses
        mission_projection = profit_max if days_into_mission == 0 else total_revenue - total_expenses

        confidence_result = f"Exceeded (${profit:,} vs. ${profit_max:,})" if profit > profit_max else f"Missed (${profit:,} vs. ${profit_max:,})"
        logging.info(f"User {username}: Total cost: {total_cost}, Penalties: {penalties}, Investor repayment: {investor_repayment}, Ship repair: {ship_repair_cost}, Previous debt: {mission.previous_debt}, Total expenses: {total_expenses}, Revenue: {total_revenue} for company {company_name}, ship {ship_name}")
        logging.info(f"User {username}: Confidence result: {confidence_result} for company {company_name}, ship {ship_name}")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        days = [f"Day {get_day(d)}" for d in daily_summaries]
        elements = [elem for elem in COMMODITIES if any(elem in get_elements_mined(d) for d in daily_summaries)]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD']
        for i, element in enumerate(elements):
            fig.add_trace(
                go.Bar(
                    x=days,
                    y=[get_elements_mined(d).get(element, 0) for d in daily_summaries],
                    name=element,
                    marker_color=colors[i % len(colors)]
                )
            )
        value_data = [sum(get_daily_value(d) for d in daily_summaries[:i+1]) for i in range(len(daily_summaries))]
        fig.add_trace(
            go.Scatter(
                x=days,
                y=value_data,
                name="Value Accrued ($)",
                line=dict(color="#00d4ff", width=2),
                yaxis="y2"
            ),
            secondary_y=True
        )
        fig.update_layout(
            barmode='stack',
            title_text=f"Mining Progress (Valued Elements) - Mission {mission_id}",
            xaxis_title="Day",
            yaxis_title="Mass Mined (kg)",
            yaxis2_title="Value ($)",
            template="plotly_dark",
            height=400
        )
        graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        mined_elements = []
        total_cost = mission_cost
        total_revenue = Int64(0)
        profit = Int64(0)
        penalties = Int64(0)
        investor_repayment = Int64(0)
        ship_repair_cost = Int64(0)
        total_duration = days_into_mission

    days_left = Int64(scheduled_days + mission.travel_delays - days_into_mission if days_into_mission < scheduled_days + mission.travel_delays else 0)

    serialized_summaries = []
    for summary in daily_summaries:
        if isinstance(summary, MissionDay):
            serialized_summaries.append(summary.dict())
        elif isinstance(summary, dict):
            serialized_summaries.append(summary)
        else:
            logging.error(f"Unexpected type in daily_summaries: {type(summary)}")
            return {"error": "Invalid daily summary format"}

    update_data = {
        "user_id": mission.user_id,
        "company": company_name,
        "ship_name": ship_name,
        "asteroid_full_name": mission.asteroid_full_name,
        "name": mission.name,
        "travel_days_allocated": base_travel_days,
        "mining_days_allocated": estimated_mining_days,
        "total_duration_days": total_duration,
        "scheduled_days": scheduled_days,
        "budget": mission.budget,
        "status": mission.status,
        "elements": [elem.model_dump() for elem in mined_elements],
        "cost": total_cost,
        "revenue": total_revenue,
        "profit": profit,
        "penalties": penalties,
        "investor_repayment": investor_repayment,
        "ship_repair_cost": ship_repair_cost,
        "previous_debt": mission.previous_debt,
        "events": events,
        "daily_summaries": serialized_summaries,
        "rocket_owned": True,
        "yield_multiplier": mission.yield_multiplier,
        "revenue_multiplier": mission.revenue_multiplier,
        "travel_yield_mod": mission.travel_yield_mod,
        "travel_delays": mission.travel_delays,
        "target_yield_kg": mission.target_yield_kg,
        "graph_html": graph_html,
        "confidence": confidence,
        "predicted_profit_max": profit_max,
        "confidence_result": confidence_result if not day else mission_raw.get("confidence_result", ""),
        "ship_location": ship_location,
        "total_yield_kg": total_yield_kg,
        "days_into_mission": days_into_mission,
        "days_left": days_left,
        "mission_cost": mission_cost,
        "mission_projection": mission_projection
    }
    try:
        db.missions.update_one({"_id": ObjectId(mission_id)}, {"$set": update_data})
        if days_into_mission >= scheduled_days + mission.travel_delays and ship_location > 0:
            db.ships.update_one(
                {"user_id": mission.user_id, "name": ship_name},
                {"$set": {"location": ship_location}},
                upsert=False
            )
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to update mission or ship in MongoDB: {e} for company {company_name}, ship {ship_name}")
        return {"error": "Trouble accessing the database, please try again later"}

    logging.info(f"User {username}: Mission {mission_id} processed {total_yield_kg} kg from {mission.asteroid_full_name}, days into mission: {days_into_mission}, days left: {days_left} for company {company_name}, ship {ship_name}")
    return update_data

def mine_asteroid(user_id: str, day: int = None, api_event: dict = None, username: str = None, company_name: str = None) -> dict:
    try:
        active_missions = list(db.missions.find({"user_id": user_id, "status": 0}))
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to fetch active missions for user {user_id}: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not active_missions:
        logging.info(f"User {username}: No active missions found for user {user_id}")
        return {"message": "No active missions to process"}

    results = {}
    for mission_raw in active_missions:
        mission_id = str(mission_raw["_id"])
        result = process_single_mission(mission_raw, day, api_event, username, company_name)
        results[mission_id] = result
    return results

if __name__ == "__main__":
    user_id = "some_user_id"
    mine_asteroid(user_id)