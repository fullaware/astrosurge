import pymongo
from bson import ObjectId
from datetime import datetime, UTC
import logging
import re
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from models.models import MissionModel, AsteroidElementModel, MissionDay, ShipModel, PyInt64, User
from config import MongoDBConfig, LoggingConfig
from amos.mine_asteroid import fetch_market_prices, simulate_travel_day, simulate_mining_day, HOURS_PER_DAY, calculate_confidence
from amos.event_processor import EventProcessor

db = MongoDBConfig.get_database()
LoggingConfig.setup_logging(log_to_file=False)

COMMODITIES = ["Copper", "Silver", "Palladium", "Platinum", "Gold"]
VALIDATION_PATTERN = re.compile(r'^[a-zA-Z0-9]{1,30}$')

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
        "location": PyInt64(0),
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
        mission_raw_adjusted["target_yield_kg"] = PyInt64(mission_raw_adjusted["target_yield_kg"])
    mission_raw_adjusted["confidence"] = mission_raw_adjusted.get("confidence", 0.0)
    mission_raw_adjusted["predicted_profit_max"] = mission_raw_adjusted.get("predicted_profit_max", 0)
    mission_raw_adjusted["ship_location"] = PyInt64(mission_raw_adjusted.get("ship_location", 0))
    mission = MissionModel(**mission_raw_adjusted)
    mission.yield_multiplier = mission_raw.get("yield_multiplier", 1.0)
    mission.revenue_multiplier = mission_raw.get("revenue_multiplier", 1.0)
    mission.travel_yield_mod = mission_raw.get("travel_yield_mod", 1.0)
    mission.ship_repair_cost = PyInt64(mission_raw.get("ship_repair_cost", 0))
    mission.events = mission_raw.get("events", [])
    mission.daily_summaries = mission_raw.get("daily_summaries", [])
    mission.previous_debt = PyInt64(mission_raw.get("previous_debt", 0))
    mission.travel_delays = PyInt64(mission_raw.get("travel_delays", 0))
    ship_name = mission_raw.get("ship_name")

    logging.info(f"User {username}: Processing mission {mission_id} to {mission.asteroid_full_name} for company {company_name} with ship {ship_name}")

    try:
        config = db.config.find_one({"name": "mining_globals"})
        if not config:
            raise RuntimeError("Mining globals config not found in asteroids.config")
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to fetch config from MongoDB: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
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
    mission.target_yield_kg = PyInt64(ship_model.capacity)
    logging.info(f"User {username}: Using ship {ship_name} with capacity {ship_model.capacity} kg, mining_power {ship_model.mining_power} kg/hour for company {company_name}")

    try:
        asteroid = db.asteroids.find_one({"full_name": mission.asteroid_full_name})
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to fetch asteroid {mission.asteroid_full_name}: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not asteroid:
        logging.error(f"User {username}: No asteroid found with full_name {mission.asteroid_full_name}")
        return {"error": f"400: No asteroid found with full_name {mission.asteroid_full_name}"}
    logging.info(f"User {username}: Asteroid {mission.asteroid_full_name} loaded, moid_days: {asteroid['moid_days']} for company {company_name}, elements: {asteroid['elements']}")

    try:
        user_dict = db.users.find_one({"_id": ObjectId(mission.user_id)})
        user = User(**{**user_dict, "_id": str(user_dict["_id"])})  # Convert dict to User object
        if user and "company_name" in user_dict and not company_name:
            company_name = user.company_name
        elif not company_name:
            company_name = mission.company
        max_overrun_days = user.max_overrun_days if user.max_overrun_days is not None else 10
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to fetch user for user_id {mission.user_id}: {e}")
        company_name = mission.company
        max_overrun_days = 10

    daily_yield_rate = PyInt64(ship_model.mining_power * HOURS_PER_DAY * config_vars["max_element_percentage"])
    confidence, profit_min, profit_max = calculate_confidence(asteroid["moid_days"], ship_model.mining_power, mission.target_yield_kg, daily_yield_rate, max_overrun_days, len(ship_model.missions) > 0)
    confidence = confidence if confidence is not None else 0.0
    profit_max = PyInt64(profit_max if profit_max is not None else 0)
    logging.info(f"User {username}: Confidence: {confidence:.2f}%, Predicted profit range: ${profit_min:,} to ${profit_max:,} for company {company_name}, ship {ship_name}")

    elements = asteroid["elements"]
    commodity_factor = asteroid.get("commodity_factor", 1.0)
    base_travel_days = PyInt64(asteroid["moid_days"])
    estimated_mining_days = PyInt64(int(mission.target_yield_kg / daily_yield_rate))
    scheduled_days = PyInt64((base_travel_days * 2) + estimated_mining_days)

    deadline_overrun_fine_per_day = PyInt64(config_vars["deadline_overrun_fine_per_day"])
    prices = fetch_market_prices()

    # Include all elements with weights, not repetitions
    weighted_elements = []
    for elem in elements:
        elem_name = elem["name"] if isinstance(elem, dict) else elem
        if elem["mass_kg"] > 0:  # Only include elements present in the asteroid
            if elem_name in ["Platinum", "Gold"]:
                weight = config_vars["commodity_factor_platinum_gold"] * commodity_factor * random.uniform(5, 10)
            elif elem_name in COMMODITIES:
                weight = config_vars["commodity_factor_other"] * commodity_factor * random.uniform(3, 5)
            else:
                weight = config_vars["non_commodity_weight"] * random.uniform(1, 2)
            weighted_elements.append({"name": elem_name, "mass_kg": elem["mass_kg"], "weight": weight})

    elements_mined = mission_raw.get("elements_mined", {})
    events = mission_raw.get("events", [])
    daily_summaries = mission_raw.get("daily_summaries", [])

    total_yield_kg = PyInt64(mission_raw.get("total_yield_kg", sum(int(kg) for kg in elements_mined.values())))
    days_into_mission = PyInt64(len(daily_summaries))
    ship_location = PyInt64(mission_raw.get("ship_location", ship_model.location))
    mission_cost = PyInt64(mission_raw.get("mission_cost", 0))
    mission_projection = PyInt64(mission_raw.get("mission_projection", profit_max))

    total_cost = PyInt64(0)
    total_revenue = PyInt64(0)
    profit = PyInt64(0)
    penalties = PyInt64(0)
    investor_repayment = PyInt64(0)
    ship_repair_cost = PyInt64(0)
    total_duration = PyInt64(0)
    confidence_result = ""
    graph_html = ""
    mined_elements = []

    logging.info(f"User {username}: Day {day}, Ship Location: {ship_location}, Total Yield: {total_yield_kg} kg, Base Travel: {base_travel_days}, Mining Days: {estimated_mining_days}, Scheduled: {scheduled_days}, Delays: {mission.travel_delays}, Elements Mined: {elements_mined}")

    if day:
        if day <= days_into_mission:
            return {"error": f"Day {day} already simulated for mission {mission_id}"}
        overrun_threshold = scheduled_days + max_overrun_days
        should_return = days_into_mission >= overrun_threshold and total_yield_kg < mission.target_yield_kg and ship_location > 0
        if should_return:
            logging.info(f"User {username}: Mission {mission_id} exceeded max overrun ({max_overrun_days} days past {scheduled_days}), completing return on day {day}")
            remaining_days = int(ship_location)
            for i in range(remaining_days):
                travel_day = day + i
                day_summary = simulate_travel_day(mission, travel_day, is_return=True)
                daily_summaries.append(day_summary)
                ship_location = PyInt64(max(0, ship_location - 1))
                mission_cost += PyInt64(config_vars["daily_mission_cost"])
                logging.info(f"User {username}: Day {travel_day} - Forced return due to overrun, Ship Location: {ship_location}")
            days_into_mission = PyInt64(len(daily_summaries))
            if ship_location == 0:
                prices = fetch_market_prices()
                total_revenue = PyInt64(0)
                logging.info(f"User {username}: Ship returned to Earth, selling cargo: {elements_mined}")
                for name, kg in elements_mined.items():
                    price_per_kg = prices.get(name, 0) if name in COMMODITIES else PyInt64(0)
                    element_value = PyInt64(kg * price_per_kg)
                    total_revenue += element_value
                    logging.info(f"User {username}: Sold {name}: {kg} kg x ${price_per_kg}/kg = ${element_value} for company {company_name}, ship {ship_name}")
                total_revenue = PyInt64(int(total_revenue * mission.revenue_multiplier))
                total_cost = PyInt64(mission_cost)
                profit = PyInt64(total_revenue - total_cost)
                minimum_funding = PyInt64(config_vars["minimum_funding"])
                if profit < minimum_funding:
                    investor_loan = PyInt64(config_vars["investor_loan_amount"])
                    interest_rate = config_vars["loan_interest_rates"][min(user.loan_count, len(config_vars["loan_interest_rates"]) - 1)]
                    investor_repayment = PyInt64(int(investor_loan * interest_rate))
                    total_cost += investor_repayment
                    profit = PyInt64(total_revenue - total_cost)
                    logging.info(f"User {username}: Profit {profit} below {minimum_funding} - took ${investor_loan:,} loan at {interest_rate}x")
                mission.status = 1
                mission.completed_at = datetime.now(UTC)
                logging.info(f"User {username}: Revenue: ${total_revenue:,}, Cost: ${total_cost:,}, Profit: ${profit:,}")
        elif day <= base_travel_days:
            day_summary = simulate_travel_day(mission, day)
            ship_location = PyInt64(ship_location + 1)
            mission_cost += PyInt64(config_vars["daily_mission_cost"])
            logging.info(f"User {username}: Day {day} - Travel out, Ship Location: {ship_location}")
        elif total_yield_kg < mission.target_yield_kg:
            day_summary = simulate_mining_day(mission, day, weighted_elements, elements_mined, api_event, ship_model.mining_power, prices, base_travel_days)
            ship_location = base_travel_days
            total_yield_kg = PyInt64(total_yield_kg + day_summary.total_kg)
            mission_cost += PyInt64(config_vars["daily_mission_cost"])
            logging.info(f"User {username}: Day {day} - Mining, Elements Mined: {day_summary.elements_mined}, Total Yield: {total_yield_kg}, Events: {day_summary.events}")
            if total_yield_kg >= mission.target_yield_kg:
                logging.info(f"User {username}: Target yield {mission.target_yield_kg} kg reached, initiating return")
        else:
            day_summary = simulate_travel_day(mission, day, is_return=True)
            ship_location = PyInt64(max(0, ship_location - 1))
            mission_cost += PyInt64(config_vars["daily_mission_cost"])
            logging.info(f"User {username}: Day {day} - Return, Ship Location: {ship_location}")
            if ship_location == 0:
                prices = fetch_market_prices()
                total_revenue = PyInt64(0)
                logging.info(f"User {username}: Ship returned to Earth, selling cargo: {elements_mined}")
                for name, kg in elements_mined.items():
                    price_per_kg = prices.get(name, 0) if name in COMMODITIES else PyInt64(0)
                    element_value = PyInt64(kg * price_per_kg)
                    total_revenue += element_value
                    logging.info(f"User {username}: Sold {name}: {kg} kg x ${price_per_kg}/kg = ${element_value} for company {company_name}, ship {ship_name}")
                total_revenue = PyInt64(int(total_revenue * mission.revenue_multiplier))
                total_cost = PyInt64(mission_cost)
                profit = PyInt64(total_revenue - total_cost)
                minimum_funding = PyInt64(config_vars["minimum_funding"])
                if profit < minimum_funding:
                    investor_loan = PyInt64(config_vars["investor_loan_amount"])
                    interest_rate = config_vars["loan_interest_rates"][min(user.loan_count, len(config_vars["loan_interest_rates"]) - 1)]
                    investor_repayment = PyInt64(int(investor_loan * interest_rate))
                    total_cost += investor_repayment
                    profit = PyInt64(total_revenue - total_cost)
                    logging.info(f"User {username}: Profit {profit} below {minimum_funding} - took ${investor_loan:,} loan at {interest_rate}x")
                mission.status = 1
                mission.completed_at = datetime.now(UTC)
                logging.info(f"User {username}: Revenue: ${total_revenue:,}, Cost: ${total_cost:,}, Profit: ${profit:,}")
        
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
                mission.travel_delays += PyInt64(event["effect"]["delay_days"])
                logging.info(f"User {username}: Day {day} Delay: +{event['effect']['delay_days']} days for company {company_name}, ship {ship_name}")
            elif "reduce_days" in event["effect"]:
                mission.travel_delays = PyInt64(max(0, mission.travel_delays - event["effect"]["reduce_days"]))
                logging.info(f"User {username}: Day {day} Recovery: -{event['effect']['reduce_days']} days for company {company_name}, ship {ship_name}")
        days_into_mission = PyInt64(len(daily_summaries))
        days_left = PyInt64(max(0, scheduled_days + mission.travel_delays - days_into_mission) if total_yield_kg < mission.target_yield_kg and not should_return else base_travel_days - ship_location)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        days = [f"Day {get_day(d)}" for d in daily_summaries]
        all_elements = set()
        for summary in daily_summaries:
            all_elements.update(get_elements_mined(summary).keys())
        elements = list(all_elements)
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'] * (len(elements) // 5 + 1)
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
            title_text=f"Mining Progress (All Elements) - Mission {mission_id}",
            xaxis_title="Day",
            yaxis_title="Mass Mined (kg)",
            yaxis2_title="Value ($)",
            template="plotly_dark",
            height=400
        )
        graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        mined_elements = [
            AsteroidElementModel(
                name=name,
                mass_kg=kg,
                number=int([e["number"] for e in elements if isinstance(e, dict) and e.get("name") == name][0]) if any(isinstance(e, dict) and e.get("name") == name for e in elements) else 0
            )
            for name, kg in elements_mined.items() if kg > 0
        ]
    else:
        commodity_total_kg = PyInt64(sum(kg for name, kg in elements_mined.items() if name in COMMODITIES))
        non_commodity_total_kg = PyInt64(sum(kg for name, kg in elements_mined.items() if name not in COMMODITIES))
        target_commodity_kg = PyInt64(int(mission.target_yield_kg * random.uniform(0.4, 0.6)))
        target_non_commodity_kg = PyInt64(mission.target_yield_kg - target_commodity_kg)
        
        if commodity_total_kg != target_commodity_kg:
            scale = target_commodity_kg / commodity_total_kg if commodity_total_kg > 0 else 1
            for name in list(elements_mined.keys()):
                if name in COMMODITIES:
                    elements_mined[name] = PyInt64(int(elements_mined[name] * scale))
            commodity_total_kg = PyInt64(sum(kg for name, kg in elements_mined.items() if name in COMMODITIES))
        
        total_yield_kg = PyInt64(commodity_total_kg + non_commodity_total_kg)
        if total_yield_kg < mission.target_yield_kg:
            shortfall = PyInt64(mission.target_yield_kg - total_yield_kg)
            non_commodity_count = sum(1 for n in elements_mined if n not in COMMODITIES)
            if non_commodity_count > 0:
                per_non_commodity = PyInt64(shortfall // non_commodity_count)
                for name in elements_mined:
                    if name not in COMMODITIES:
                        elements_mined[name] += per_non_commodity
            total_yield_kg = PyInt64(sum(elements_mined.values()))
        
        for summary in daily_summaries:
            summary_day = get_day(summary)
            if summary_day > base_travel_days and summary_day <= (base_travel_days + estimated_mining_days):
                total_kg_sum = sum(get_day(s) > base_travel_days and get_day(s) <= (base_travel_days + estimated_mining_days) and s.total_kg or 0 for s in daily_summaries)
                summary.total_kg = PyInt64(int(summary.total_kg * (total_yield_kg / total_kg_sum)) if total_kg_sum > 0 else summary.total_kg)
                elements_mined_dict = get_elements_mined(summary)
                if elements_mined_dict:
                    for elem_name in elements_mined_dict:
                        elements_mined_dict[elem_name] = int(elements_mined_dict[elem_name] * scale)
                    summary.daily_value = PyInt64(sum(elements_mined_dict.get(name, 0) * prices.get(name, 0) for name in elements_mined_dict))

        mined_elements = [
            AsteroidElementModel(
                name=name,
                mass_kg=kg,
                number=int([e["number"] for e in elements if isinstance(e, dict) and e.get("name") == name][0]) if any(isinstance(e, dict) and e.get("name") == name for e in elements) else 0
            )
            for name, kg in elements_mined.items() if kg > 0
        ]

        total_cost = PyInt64(mission_cost)
        cost_reduction_applied = False
        investor_boost_count = 0
        for event in events:
            if "cost_reduction" in event["effect"] and not cost_reduction_applied:
                total_cost = PyInt64(int(total_cost * event["effect"]["cost_reduction"]))
                cost_reduction_applied = True
            if "revenue_multiplier" in event["effect"]:
                investor_boost_count += 1
                if investor_boost_count <= 2:
                    mission.revenue_multiplier *= event["effect"]["revenue_multiplier"]

        total_duration = PyInt64((base_travel_days * 2) + estimated_mining_days + mission.travel_delays)
        deadline_overrun = PyInt64(max(0, total_duration - scheduled_days))
        penalties = PyInt64(deadline_overrun * deadline_overrun_fine_per_day)
        budget_overrun = PyInt64(max(0, total_cost - mission.budget))
        penalties += budget_overrun

        investor_loan = PyInt64(config_vars["investor_loan_amount"]) if not mission.rocket_owned else PyInt64(0)
        interest_rate = config_vars["loan_interest_rates"][min(user.loan_count, len(config_vars["loan_interest_rates"]) - 1)] if not mission.rocket_owned else 0
        investor_repayment = PyInt64(int(investor_loan * interest_rate))
        ship_repair_cost = mission.ship_repair_cost or PyInt64(0)
        total_expenses = PyInt64(total_cost + penalties + investor_repayment + ship_repair_cost + mission.previous_debt)

        logging.info(f"User {username}: Calculating revenue from mined elements for company {company_name}, ship {ship_name}")
        total_revenue = PyInt64(0)
        for name, kg in elements_mined.items():
            price_per_kg = prices.get(name, 0) if name in COMMODITIES else PyInt64(0)
            element_value = PyInt64(kg * price_per_kg)
            total_revenue += element_value
            if name in COMMODITIES:
                logging.info(f"User {username}: {name}: {kg} kg x ${price_per_kg}/kg = ${element_value} for company {company_name}, ship {ship_name}")
        total_revenue = PyInt64(int(total_revenue * mission.revenue_multiplier))

        profit = PyInt64(total_revenue - total_expenses)

        minimum_funding = PyInt64(config_vars["minimum_funding"])
        if profit < minimum_funding:
            logging.info(f"User {username}: Profit {profit} below {minimum_funding} - taking ${investor_loan:,} loan at {interest_rate}x for company {company_name}, ship {ship_name}")
            investor_loan = PyInt64(config_vars["investor_loan_amount"])
            interest_rate = config_vars["loan_interest_rates"][min(user.loan_count, len(config_vars["loan_interest_rates"]) - 1)]
            investor_repayment = PyInt64(int(investor_loan * interest_rate))
            total_expenses += investor_repayment
            profit = PyInt64(total_revenue - total_expenses)

        mission.previous_debt = PyInt64(0 if profit >= 0 else -profit)
        mission_cost = total_cost
        mission_projection = profit_max if days_into_mission == 0 else total_revenue - total_expenses

        confidence_result = f"Exceeded (${profit:,} vs. ${profit_max:,})" if profit > profit_max else f"Missed (${profit:,} vs. ${profit_max:,})"
        logging.info(f"User {username}: Total cost: {total_cost}, Penalties: {penalties}, Investor repayment: {investor_repayment}, Ship repair: {ship_repair_cost}, Previous debt: {mission.previous_debt}, Total expenses: {total_expenses}, Revenue: {total_revenue} for company {company_name}, ship {ship_name}")
        logging.info(f"User {username}: Confidence result: {confidence_result} for company {company_name}, ship {ship_name}")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        days = [f"Day {get_day(d)}" for d in daily_summaries]
        all_elements = set()
        for summary in daily_summaries:
            all_elements.update(get_elements_mined(summary).keys())
        elements = list(all_elements)
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'] * (len(elements) // 5 + 1)
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
            title_text=f"Mining Progress (All Elements) - Mission {mission_id}",
            xaxis_title="Day",
            yaxis_title="Mass Mined (kg)",
            yaxis2_title="Value ($)",
            template="plotly_dark",
            height=400
        )
        graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    days_left = PyInt64(max(0, scheduled_days + mission.travel_delays - days_into_mission) if total_yield_kg < mission.target_yield_kg and not should_return else base_travel_days - ship_location)

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
        "elements_mined": elements_mined,
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
        "mission_projection": mission_projection,
        "completed_at": mission.completed_at
    }
    try:
        db.missions.update_one({"_id": ObjectId(mission_id)}, {"$set": update_data})
        if total_yield_kg < mission.target_yield_kg or (days_into_mission >= scheduled_days + mission.travel_delays and ship_location > 0):
            db.ships.update_one({"_id": ObjectId(ship_model.id)}, {"$set": {"location": ship_location}}, upsert=False)
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