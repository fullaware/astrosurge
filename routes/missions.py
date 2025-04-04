import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from datetime import datetime, UTC
from config import MongoDBConfig
from amos.manage_mission import process_single_mission, mine_asteroid
from amos.mine_asteroid import calculate_confidence, HOURS_PER_DAY
from utils.auth import get_current_user
from models.models import MissionModel, PyInt64, User
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from amos.manage_mission import get_elements_mined, get_daily_value

router = APIRouter()
templates = Jinja2Templates(directory="templates")
db = MongoDBConfig.get_database()

@router.post("/missions/start", response_class=RedirectResponse)
async def start_mission(
    asteroid_full_name: str = Form(...),
    ship_name: str = Form(...),
    travel_days: int = Form(...),
    user: User = Depends(get_current_user),
    response: Response = None
):
    from utils.auth import validate_alphanumeric
    if isinstance(user, RedirectResponse):
        return user
    logging.info(f"User {user.username}: Starting mission with asteroid {asteroid_full_name}, ship {ship_name}, travel_days {travel_days}")
    validate_alphanumeric(ship_name, "Ship Name")
    
    existing_ship = db.ships.find_one({"user_id": user.id, "name": ship_name, "location": 0.0, "active": True})
    if not existing_ship:
        logging.warning(f"User {user.username}: Ship {ship_name} is unavailable or does not exist")
        return RedirectResponse(url=f"/?travel_days={travel_days}&error=Ship {ship_name} is currently unavailable (not at Earth or inactive) or does not exist", status_code=status.HTTP_303_SEE_OTHER)
    ship_id = str(existing_ship["_id"])

    asteroid = db.asteroids.find_one({"full_name": asteroid_full_name})
    if not asteroid:
        logging.error(f"User {user.username}: No asteroid found with full_name {asteroid_full_name}")
        return RedirectResponse(url=f"/?travel_days={travel_days}&error=No asteroid found with name {asteroid_full_name}", status_code=status.HTTP_303_SEE_OTHER)
    
    # Determine the mission number by checking existing missions for this asteroid
    existing_missions = list(db.missions.find({"user_id": user.id, "asteroid_full_name": asteroid_full_name}))
    mission_number = 1
    for mission in existing_missions:
        # Extract the number from the mission name (e.g., "1 Ceres Mission 2" -> 2)
        name_parts = mission["name"].split("Mission")
        if len(name_parts) > 1:
            try:
                number = int(name_parts[-1].strip())
                mission_number = max(mission_number, number + 1)
            except ValueError:
                continue
    mission_name = f"{asteroid_full_name} Mission {mission_number}"

    mining_power = existing_ship["mining_power"]
    target_yield_kg = existing_ship["capacity"]
    max_daily_yield = mining_power * HOURS_PER_DAY * 0.5  # max_element_percentage = 0.5
    average_daily_yield = max_daily_yield / 2  # Average of random.randint(1, max)
    estimated_mining_days = int(target_yield_kg / average_daily_yield)  # ~17 days for 50,000 kg at ~3,000 kg/day
    scheduled_days = PyInt64((travel_days * 2) + estimated_mining_days)
    daily_yield_rate = PyInt64(average_daily_yield)  # For consistency in profit calc
    confidence, profit_min, profit_max = calculate_confidence(travel_days, mining_power, target_yield_kg, daily_yield_rate, user.max_overrun_days, len(existing_ship["missions"]) > 0)
    mission_projection = profit_max

    config = db.config.find_one({"name": "mining_globals"})["variables"]
    ship_cost = config["ship_cost"] * (config["ship_reuse_discount"] if len(existing_ship["missions"]) > 0 else 1)
    mission_budget = PyInt64(ship_cost + (config["daily_mission_cost"] * scheduled_days))
    minimum_funding = PyInt64(config["minimum_funding"])

    if user.bank >= minimum_funding:
        pass
    else:
        loan_amount = mission_budget
        interest_rate = config["loan_interest_rates"][min(user.loan_count, len(config["loan_interest_rates"]) - 1)]
        repayment_amount = PyInt64(int(loan_amount * interest_rate))
        db.users.update_one({"_id": ObjectId(user.id)}, {"$set": {"current_loan": repayment_amount}, "$inc": {"loan_count": 1}})
        logging.info(f"User {user.username}: Mission funded with loan of ${loan_amount:,} at {interest_rate}x, repayment ${repayment_amount:,} (Loan #{user.loan_count + 1})")

    mission_data = {
        "_id": ObjectId(),
        "user_id": user.id,
        "company": user.company_name,
        "ship_name": ship_name,
        "ship_id": ship_id,
        "asteroid_full_name": asteroid_full_name,
        "name": mission_name,
        "travel_days_allocated": travel_days,
        "mining_days_allocated": 0,
        "total_duration_days": 0,
        "scheduled_days": scheduled_days,
        "budget": mission_budget,
        "status": 0,
        "elements": [],
        "elements_mined": {},
        "cost": 0,
        "revenue": 0,
        "profit": 0,
        "penalties": 0,
        "investor_repayment": 0,
        "ship_repair_cost": 0,
        "previous_debt": 0,
        "events": [],
        "daily_summaries": [],
        "rocket_owned": True,
        "yield_multiplier": 1.0,
        "revenue_multiplier": 1.0,
        "travel_yield_mod": 1.0,
        "travel_delays": 0,
        "target_yield_kg": PyInt64(target_yield_kg),
        "ship_location": 0.0,
        "total_yield_kg": PyInt64(0),
        "days_into_mission": 0,
        "days_left": scheduled_days,
        "mission_cost": PyInt64(0),
        "mission_projection": mission_projection,
        "confidence": confidence,
        "completed_at": None
    }
    result = db.missions.insert_one(mission_data)
    mission_id = str(result.inserted_id)
    
    db.ships.update_one({"_id": ObjectId(ship_id)}, {"$push": {"missions": mission_id}})
    
    logging.info(f"User {user.username}: Created mission {mission_id} for asteroid {asteroid_full_name} with ship {ship_name}, Projected Profit: ${mission_projection:,}, Confidence: {confidence:.2f}%")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/missions/advance", response_class=RedirectResponse)
async def advance_all_missions(user: User = Depends(get_current_user)):
    if isinstance(user, RedirectResponse):
        return user
    active_missions = list(db.missions.find({"user_id": user.id, "status": 0}))
    if not active_missions:
        logging.info(f"User {user.username}: No active missions to advance")
        return RedirectResponse(url="/missions?message=No active missions to advance", status_code=status.HTTP_303_SEE_OTHER)
    next_day = max([len(m.get("daily_summaries", [])) for m in active_missions], default=0) + 1
    logging.info(f"User {user.username}: Advancing day {next_day} for {len(active_missions)} active missions")
    result = mine_asteroid(user.id, day=next_day, username=user.username, company_name=user.company_name)
    if "error" in result:
        return RedirectResponse(url=f"/missions?error={result['error']}", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/missions", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/missions/complete", response_class=RedirectResponse)
async def complete_all_missions(user: User = Depends(get_current_user)):
    if isinstance(user, RedirectResponse):
        return user
    active_missions = list(db.missions.find({"user_id": user.id, "status": 0}))
    if not active_missions:
        logging.info(f"User {user.username}: No active missions to complete")
        return RedirectResponse(url="/missions?message=No active missions to complete", status_code=status.HTTP_303_SEE_OTHER)
    
    logging.info(f"User {user.username}: Running simulation to complete {len(active_missions)} active missions")
    results = {}
    for mission_raw in active_missions:
        mission_id = str(mission_raw["_id"])
        days_into_mission = len(mission_raw.get("daily_summaries", []))
        while True:
            days_into_mission += 1
            result = process_single_mission(mission_raw, day=days_into_mission, username=user.username, company_name=user.company_name)
            mission_raw = db.missions.find_one({"_id": ObjectId(mission_id)})
            if "status" in result and result["status"] == 1 and result["ship_location"] == 0:
                profit = result.get("profit", 0)
                if profit > 0 and user.current_loan > 0:
                    net_profit = max(0, profit - user.current_loan)
                    db.users.update_one({"_id": ObjectId(user.id)}, {"$inc": {"bank": PyInt64(net_profit)}, "$set": {"current_loan": PyInt64(0)}})
                    logging.info(f"User {user.username}: Mission {mission_id} completed, profit ${profit:,}, repaid loan ${user.current_loan:,}, net to bank ${net_profit:,}")
                elif profit > 0:
                    db.users.update_one({"_id": ObjectId(user.id)}, {"$inc": {"bank": PyInt64(profit)}})
                    logging.info(f"User {user.username}: Mission {mission_id} completed, added profit ${profit:,} to bank")
                results[mission_id] = result
                break
            results[mission_id] = result
    if "error" in results.get(list(results.keys())[0], {}):
        return RedirectResponse(url=f"/missions?error={results[list(results.keys())[0]]['error']}", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/missions", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/missions", response_class=HTMLResponse)
async def get_missions(request: Request, user: User = Depends(get_current_user), message: str = None, error: str = None):
    if isinstance(user, RedirectResponse):
        return user
    missions = [MissionModel(**m) for m in db.missions.find({"user_id": user.id})]
    for mission in missions:
        ship = db.ships.find_one({"name": mission.ship_name, "user_id": user.id})
        mission.ship_id = str(ship["_id"]) if ship else None
    
    missions.sort(key=lambda m: (
        m.status != 1,
        m.completed_at if m.completed_at else datetime.min if m.status == 1 else datetime.max,
        m.days_into_mission if m.status == 0 else 0
    ), reverse=True)
    
    logging.info(f"User {user.username}: Loaded {len(missions)} missions for missions page")
    return templates.TemplateResponse("missions.html", {"request": request, "missions": missions, "user": user, "message": message, "error": error})

@router.get("/missions/{mission_id}", response_class=HTMLResponse)
async def get_mission_details(request: Request, mission_id: str, user: User = Depends(get_current_user)):
    if isinstance(user, RedirectResponse):
        return user
    mission_dict = db.missions.find_one({"_id": ObjectId(mission_id), "user_id": user.id})
    if not mission_dict:
        raise HTTPException(status_code=404, detail="Mission not found")
    mission = MissionModel(**mission_dict)
    ship = db.ships.find_one({"name": mission.ship_name, "user_id": user.id})
    ship_id = str(ship["_id"]) if ship else None

    # Debug: Log daily summaries to verify commodities
    logging.info(f"User {user.username}: Mission {mission_id} daily_summaries: {[s.get('elements_mined') for s in mission.daily_summaries]}")

    # Build graph with day-to-yield mapping
    daily_yields = {}
    for summary in mission.daily_summaries:
        day = summary["day"]
        elements = get_elements_mined(summary) or {}
        daily_yields[day] = elements

    days = sorted(daily_yields.keys())
    all_elements = set()
    for yields in daily_yields.values():
        all_elements.update(yields.keys())
    elements = list(all_elements)
    logging.info(f"User {user.username}: Mission {mission_id} all_elements: {elements}")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'] * (len(elements) // 5 + 1)
    for i, element in enumerate(elements):
        y_values = [daily_yields.get(day, {}).get(element, 0) for day in days]
        logging.info(f"User {user.username}: Mission {mission_id} element {element} y_values: {y_values[:5]}...")  # Log first 5
        fig.add_trace(
            go.Bar(
                x=[f"Day {day}" for day in days],
                y=y_values,
                name=element,
                marker_color=colors[i % len(colors)]
            )
        )
    value_data = [sum(get_daily_value({**daily_yields[day], "day": day}) for day in days[:i+1]) for i in range(len(days))]
    fig.add_trace(
        go.Scatter(
            x=[f"Day {day}" for day in days],
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

    logging.info(f"User {user.username}: Loaded mission {mission_id} details with ship ID {ship_id}")
    return templates.TemplateResponse("mission_details.html", {"request": request, "mission": mission, "ship_id": ship_id, "user": user, "graph_html": graph_html})