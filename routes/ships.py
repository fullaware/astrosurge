import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from config import MongoDBConfig
from amos.manage_mission import create_new_ship, get_elements_mined, get_daily_value
from amos.mine_asteroid import calculate_confidence, HOURS_PER_DAY
from auth.auth import get_current_user, validate_alphanumeric
from models.models import User, PyInt64
import plotly.graph_objects as go
from plotly.subplots import make_subplots

router = APIRouter()
templates = Jinja2Templates(directory="templates")
db = MongoDBConfig.get_database()

@router.post("/ships/create", response_class=RedirectResponse)
async def create_ship(
    ship_name: str = Form(...),
    travel_days: int = Form(...),
    asteroid_full_name: str = Form(...),
    user: User = Depends(get_current_user)
):
    if isinstance(user, RedirectResponse):
        return user
    validate_alphanumeric(ship_name, "Ship Name")
    
    if db.ships.find_one({"user_id": user.id, "name": ship_name}):
        return RedirectResponse(url=f"/?travel_days={travel_days}&error=Ship name {ship_name} already exists", status_code=status.HTTP_303_SEE_OTHER)
    
    try:
        ship = create_new_ship(user.id, ship_name, user.username, user.company_name)
        logging.info(f"User {user.username}: Created new ship {ship_name} for company {user.company_name}")
        logging.info(f"User {user.username}: Created new ship {ship_name} for mission planning")
    except ValueError as e:
        return RedirectResponse(url=f"/?travel_days={travel_days}&error={str(e)}", status_code=status.HTTP_303_SEE_OTHER)
    
    # Use dot notation to access ship.id
    ship_id = ship.id  # Changed from str(ship["_id"]) to ship.id
    asteroid = db.asteroids.find_one({"full_name": asteroid_full_name})
    if not asteroid:
        logging.error(f"User {user.username}: No asteroid found with full_name {asteroid_full_name}")
        return RedirectResponse(url=f"/?travel_days={travel_days}&error=No asteroid found with name {asteroid_full_name}", status_code=status.HTTP_303_SEE_OTHER)

    existing_missions = list(db.missions.find({"user_id": user.id, "asteroid_full_name": asteroid_full_name}))
    mission_number = 1
    for mission in existing_missions:
        name_parts = mission["name"].split("Mission")
        if len(name_parts) > 1:
            try:
                number = int(name_parts[-1].strip())
                mission_number = max(mission_number, number + 1)
            except ValueError:
                continue
    mission_name = f"{asteroid_full_name} Mission {mission_number}"

    db.ships.update_one({"_id": ObjectId(ship_id)}, {"$set": {"active": True}})
    mining_power = ship.mining_power
    target_yield_kg = ship.capacity
    max_daily_yield = mining_power * HOURS_PER_DAY * 0.5
    average_daily_yield = max_daily_yield / 2
    estimated_mining_days = int(target_yield_kg / average_daily_yield)
    scheduled_days = PyInt64((travel_days * 2) + estimated_mining_days)
    daily_yield_rate = PyInt64(average_daily_yield)
    confidence, profit_min, profit_max = calculate_confidence(travel_days, mining_power, target_yield_kg, daily_yield_rate, user.max_overrun_days, len(ship.missions) > 0)
    mission_projection = profit_max

    config = db.config.find_one({"name": "mining_globals"})["variables"]
    ship_cost = config["ship_cost"] * (config["ship_reuse_discount"] if len(ship.missions) > 0 else 1)
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

@router.get("/ships/{ship_id}", response_class=HTMLResponse)
async def get_ship_details(request: Request, ship_id: str, user: User = Depends(get_current_user)):
    if not request.cookies.get("access_token") or isinstance(user, RedirectResponse):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    ship = db.ships.find_one({"_id": ObjectId(ship_id), "user_id": user.id})
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")
    
    missions = list(db.missions.find({"ship_name": ship["name"], "user_id": user.id}))
    daily_yields = {}
    for mission in missions:
        for summary in mission.get("daily_summaries", []):
            day = summary["day"]
            elements = get_elements_mined(summary) or {}
            daily_yields[day] = daily_yields.get(day, {})
            for elem, kg in elements.items():
                daily_yields[day][elem] = daily_yields[day].get(elem, 0) + kg

    # Debug: Log daily yields to verify commodities
    logging.info(f"User {user.username}: Ship {ship_id} daily_yields sample: {dict(list(daily_yields.items())[:2])}")

    days = sorted(daily_yields.keys())
    all_elements = set()
    for yields in daily_yields.values():
        all_elements.update(yields.keys())
    elements = list(all_elements)
    logging.info(f"User {user.username}: Ship {ship_id} all_elements: {elements}")

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'] * (len(elements) // 5 + 1)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for i, element in enumerate(elements):
        y_values = [daily_yields.get(day, {}).get(element, 0) for day in days]
        logging.info(f"User {user.username}: Ship {ship_id} element {element} y_values: {y_values[:5]}...")
        fig.add_trace(
            go.Bar(
                x=days,
                y=y_values,
                name=element,
                marker_color=colors[i % len(colors)]
            )
        )
    total_yield = [sum(daily_yields.get(day, {}).values()) for day in days]
    fig.add_trace(
        go.Scatter(
            x=days,
            y=total_yield,
            name="Total Yield (kg)",
            line=dict(color="#00d4ff", width=2),
            yaxis="y2"
        ),
        secondary_y=True
    )
    fig.update_layout(
        barmode='stack',
        title_text=f"Yield History for Ship {ship['name']}",
        xaxis_title="Day",
        yaxis_title="Mass Mined (kg)",
        yaxis2_title="Total Yield (kg)",
        template="plotly_dark",
        height=400
    )
    graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    logging.info(f"User {user.username}: Loaded ship {ship_id} details with {len(missions)} missions")
    return templates.TemplateResponse("ship_details.html", {"request": request, "ship": ship, "missions": missions, "graph_html": graph_html, "user": user})