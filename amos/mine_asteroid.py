import random
import pymongo
import yfinance as yf
from bson import ObjectId
from bson.int64 import Int64
from datetime import datetime, UTC
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from models.models import MissionModel, AsteroidElementModel, MissionDay, ShipModel
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

def simulate_mining_day(mission: MissionModel, day: int, weighted_elements: list, elements_mined: dict, api_event: dict = None, mining_power: int = 500, prices: dict = None) -> MissionDay:
    max_daily_kg = random.randint(mining_power, mining_power * 2)
    daily_yield_kg = random.randint(max_daily_kg - 100, max_daily_kg + 100)
    active_elements = random.sample(weighted_elements, k=min(random.randint(1, 4), len(weighted_elements)))

    daily_elements = {}
    daily_value = 0
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
            daily_value += int(yield_kg * prices[elem_name])

    day_summary = MissionDay(day=day, total_kg=Int64(daily_yield_kg), note="Mining - Steady operation")
    day_summary = EventProcessor.apply_daily_events(mission, day_summary, daily_elements, api_event)
    day_summary.elements_mined = daily_elements
    day_summary.daily_value = daily_value
    return day_summary

def calculate_confidence(moid_days: int, mining_power: int, target_yield_kg: int, daily_yield_rate: int) -> tuple:
    # Dynamic confidence: 0-100%, based on travel days, mining power, event risk, yield variance
    try:
        event_risk = sum(event["probability"] for event in db.events.find()) / (db.events.count_documents({}) or 1)
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to fetch events for confidence calculation: {e}")
        event_risk = random.uniform(0.3, 0.7)  # Dynamic fallback
    travel_factor = max(0, 100 - moid_days * 2)
    mining_factor = min(100, mining_power / 5)
    risk_factor = (1 - event_risk) * 100
    yield_factor = min(100, (daily_yield_rate / (target_yield_kg / 100)) * 100)
    confidence = (travel_factor * 0.25 + mining_factor * 0.25 + risk_factor * 0.25 + yield_factor * 0.25)
    
    # Dynamic profit range: wider and centered on volatility, only max shown
    avg_commodity_value = sum([192.92, 984.13, 31433.42, 31433.42, 99233.42]) / 5
    estimated_revenue = target_yield_kg * avg_commodity_value * random.uniform(0.4, 0.6)
    estimated_cost = random.randint(350000000, 450000000) + (moid_days * 1000000)
    base_profit = estimated_revenue - estimated_cost
    profit_variance = (100 - confidence) * 15000000
    profit_min = base_profit - profit_variance - 400000000  # Kept internally
    profit_max = base_profit + profit_variance + 200000000
    
    return confidence, profit_min, profit_max

def mine_asteroid(mission_id: str, day: int = None, api_event: dict = None) -> dict:
    try:
        mission_raw = db.missions.find_one({"_id": ObjectId(mission_id)})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to fetch mission {mission_id} from MongoDB: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
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
    
    logging.info(f"Starting mission {mission_id} to {mission.asteroid_full_name}")
    
    try:
        config = db.config.find_one({"name": "mining_globals"})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to fetch config from MongoDB: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not config:
        logging.error("No mining_globals config found")
        return {"error": "No mining_globals config found"}
    config_vars = config["variables"]
    
    try:
        ship = db.ships.find_one({"user_id": mission.user_id, "active": True})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to fetch ship for user_id {mission.user_id}: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not ship:
        logging.error(f"No active ship found for user_id {mission.user_id}")
        return {"error": f"No active ship found for user_id {mission.user_id}"}
    ship_model = ShipModel(**ship)
    mission.target_yield_kg = Int64(ship_model.capacity)
    
    logging.info(f"Using ship {ship_model.name} with capacity {ship_model.capacity} kg, mining_power {ship_model.mining_power}")
    
    try:
        asteroid = db.asteroids.find_one({"full_name": mission.asteroid_full_name})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to fetch asteroid {mission.asteroid_full_name}: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not asteroid:
        logging.error(f"No asteroid found with full_name {mission.asteroid_full_name}")
        return {"error": f"400: No asteroid found with full_name {mission.asteroid_full_name}"}
    
    logging.info(f"Asteroid {mission.asteroid_full_name} loaded, moid_days: {asteroid['moid_days']}")
    
    try:
        user = db.users.find_one({"_id": ObjectId(mission.user_id)})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to fetch user for user_id {mission.user_id}: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not user or "company_name" not in user:
        logging.error(f"No user or company_name found for user_id {mission.user_id}")
        company_name = mission.company
    else:
        company_name = user["company_name"]
    
    # Pre-simulation variables for confidence
    daily_yield_rate = random.randint(ship_model.mining_power, ship_model.mining_power * 2)
    confidence, profit_min, profit_max = calculate_confidence(asteroid["moid_days"], ship_model.mining_power, mission.target_yield_kg, daily_yield_rate)
    logging.info(f"Confidence: {confidence:.2f}%, Predicted profit range: ${profit_min:,.0f} to ${profit_max:,.0f}")
    
    elements = asteroid["elements"]
    commodity_factor = asteroid.get("commodity_factor", 1.0)
    base_travel_days = asteroid["moid_days"]
    
    estimated_mining_days = mission.target_yield_kg // daily_yield_rate
    mission.scheduled_days = (base_travel_days * 2) + estimated_mining_days
    mission.travel_days_allocated = base_travel_days
    mission.mining_days_allocated = estimated_mining_days

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

    elements_mined = {}
    events = mission.events
    daily_summaries = mission.daily_summaries

    if day:
        if day <= len(daily_summaries):
            return {"error": f"Day {day} already simulated"}
        if day <= base_travel_days:
            day_summary = simulate_travel_day(mission, day)
        elif day <= (base_travel_days + mission.mining_days_allocated):
            day_summary = simulate_mining_day(mission, day - base_travel_days + 1, weighted_elements, elements_mined, api_event, ship_model.mining_power, prices)
        else:
            day_summary = simulate_travel_day(mission, day - base_travel_days - mission.mining_days_allocated + 1, is_return=True)
        if isinstance(day_summary, dict) and "error" in day_summary:
            return day_summary
        daily_summaries.append(day_summary)
        events.extend(day_summary.events)
        for event in day_summary.events:
            if "delay_days" in event["effect"]:
                mission.travel_delays += event["effect"]["delay_days"]
                logging.info(f"Day {day_summary.day} Delay: +{event['effect']['delay_days']} days")
            elif "reduce_days" in event["effect"]:
                mission.travel_delays = max(0, mission.travel_delays - event["effect"]["reduce_days"])
                logging.info(f"Day {day_summary.day} Recovery: -{event['effect']['reduce_days']} days")
    else:
        for d in range(1, base_travel_days + 1):
            day_summary = simulate_travel_day(mission, d)
            day_summary.elements_mined = {}
            day_summary.daily_value = 0
            daily_summaries.append(day_summary)
            events.extend(day_summary.events)
            for event in day_summary.events:
                if "delay_days" in event["effect"]:
                    mission.travel_delays += event["effect"]["delay_days"]
                    logging.info(f"Day {day_summary.day} Delay: +{event['effect']['delay_days']} days")
                elif "reduce_days" in event["effect"]:
                    mission.travel_delays = max(0, mission.travel_delays - event["effect"]["reduce_days"])
                    logging.info(f"Day {day_summary.day} Recovery: -{event['effect']['reduce_days']} days")
        
        mining_start_day = base_travel_days + 1
        for d in range(1, mission.mining_days_allocated + 1):
            day_summary = simulate_mining_day(mission, mining_start_day + d - 1, weighted_elements, elements_mined, mining_power=ship_model.mining_power, prices=prices)
            if isinstance(day_summary, dict) and "error" in day_summary:
                return day_summary
            daily_summaries.append(day_summary)
            events.extend(day_summary.events)
        
        return_start_day = base_travel_days + mission.mining_days_allocated + 1
        total_days_so_far = return_start_day - 1
        for d in range(1, base_travel_days + mission.travel_delays + 1):
            day_summary = simulate_travel_day(mission, total_days_so_far + d, is_return=True)
            day_summary.elements_mined = {}
            day_summary.daily_value = 0
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
    target_commodity_kg = Int64(int(mission.target_yield_kg * random.uniform(0.4, 0.6)))
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
            if hasattr(summary, 'elements_mined'):
                for elem_name in summary.elements_mined:
                    summary.elements_mined[elem_name] = int(summary.elements_mined[elem_name] * scale)
                summary.daily_value = int(sum(summary.elements_mined.get(name, 0) * prices.get(name, 0) for name in summary.elements_mined))

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

    logging.info("Calculating revenue from mined elements...")
    total_revenue = Int64(0)
    for name, kg in elements_mined.items():
        price_per_kg = prices.get(name, 0) if name in COMMODITIES else 0
        element_value = int(kg * price_per_kg)
        total_revenue += element_value
        if name in COMMODITIES:
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

    # Evaluate confidence result
    confidence_result = f"Exceeded (${profit:,.0f} vs. ${profit_max:,.0f})" if profit > profit_max else f"Missed (${profit:,.0f} vs. ${profit_max:,.0f})"
    logging.info(f"Total cost: {total_cost}, Penalties: {penalties}, Investor repayment: {investor_repayment}, Ship repair: {ship_repair_cost}, Previous debt: {previous_debt_repayment}, Total expenses: {total_expenses}, Revenue: {total_revenue}")
    logging.info(f"Confidence result: {confidence_result}")

    # Generate Plotly graph with only valued elements (COMMODITIES)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    days = [f"Day {day.day}" for day in daily_summaries]
    elements = [elem for elem in COMMODITIES if any(elem in (day.elements_mined or {}) for day in daily_summaries)]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD']
    for i, element in enumerate(elements):
        fig.add_trace(
            go.Bar(
                x=days,
                y=[day.elements_mined.get(element, 0) if hasattr(day, 'elements_mined') else 0 for day in daily_summaries],
                name=element,
                marker_color=colors[i % len(colors)]
            )
        )
    value_data = [sum(d.daily_value or 0 for d in daily_summaries[:i+1]) for i in range(len(daily_summaries))]
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
        title_text="Mining Progress (Valued Elements)",
        xaxis_title="Day",
        yaxis_title="Mass Mined (kg)",
        yaxis2_title="Value ($)",
        template="plotly_dark",
        height=400
    )
    graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    update_data = {
        "user_id": mission.user_id,
        "company": company_name,
        "ship_name": ship_model.name,
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
        "daily_summaries": [vars(summary) for summary in daily_summaries],
        "rocket_owned": True,
        "yield_multiplier": mission.yield_multiplier,
        "revenue_multiplier": mission.revenue_multiplier,
        "travel_yield_mod": mission.travel_yield_mod,
        "travel_delays": mission.travel_delays,
        "target_yield_kg": mission.target_yield_kg,
        "graph_html": graph_html,
        "confidence": confidence,
        "predicted_profit_max": profit_max,  # Only max shown
        "confidence_result": confidence_result
    }
    try:
        db.missions.update_one({"_id": ObjectId(mission_id)}, {"$set": update_data})
        db.asteroids.update_one(
            {"full_name": mission.asteroid_full_name},
            {"$addToSet": {"mined_by": {"mission_id": mission_id, "company": company_name}}}
        )
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"Failed to update mission or asteroid in MongoDB: {e}")
        return {"error": "Trouble accessing the database, please try again later"}

    logging.info(f"Mission {mission_id} mined {total_yield_kg} kg from {mission.asteroid_full_name}, profit: {profit}")
    return update_data

if __name__ == "__main__":
    mission_id = "6612a3b8f9e8d4c7b9a1f2e3"
    mine_asteroid(mission_id)