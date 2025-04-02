import logging
import re
from datetime import datetime, timedelta, UTC
from fastapi import FastAPI, Depends, HTTPException, Request, status, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from bson import ObjectId
from bson.int64 import Int64
import os
import jwt
from passlib.context import CryptContext
from config import MongoDBConfig
from amos.mine_asteroid import mine_asteroid, process_single_mission, calculate_confidence
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from models.models import MissionModel, PyInt64

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

db = MongoDBConfig.get_database()
users_collection = db["users"]
login_attempts_collection = db["login_attempts"]

SECRET_KEY = os.environ.get("JWT_SECRET", "SUPERSECRETKEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=5)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

VALIDATION_PATTERN = re.compile(r'^[a-zA-Z0-9]{1,30}$')

def validate_alphanumeric(value: str, field_name: str):
    if not VALIDATION_PATTERN.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be alphanumeric (A-Z, a-z, 0-9) and up to 30 characters long"
        )

class User(BaseModel):
    id: str = Field(alias="_id")
    username: str
    email: str
    hashed_password: str
    company_name: str = "Unnamed Company"
    bank: PyInt64 = PyInt64(0)
    loan_count: int = 0
    current_loan: PyInt64 = PyInt64(0)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    company_name: Optional[str] = "Unnamed Company"

class UserUpdate(BaseModel):
    company_name: Optional[str]

class MissionStart(BaseModel):
    asteroid_full_name: str
    ship_name: str
    travel_days: int

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, required: bool = True):
    token = request.cookies.get("access_token")
    if not token:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            if required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
    except jwt.PyJWTError:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    user_dict = {
        "_id": str(user["_id"]),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "hashed_password": user.get("hashed_password", user.get("password_hash", "")),
        "company_name": user.get("company_name", "Unnamed Company"),
        "bank": PyInt64(user.get("bank", 0)),
        "loan_count": user.get("loan_count", 0),
        "current_loan": PyInt64(user.get("current_loan", 0))
    }
    return User(**user_dict)

async def get_optional_user(request: Request):
    return await get_current_user(request, required=False)

def record_login_attempt(username: str, success: bool):
    now = datetime.utcnow()
    attempt = {"username": username, "timestamp": now, "success": success}
    login_attempts_collection.insert_one(attempt)
    login_attempts_collection.delete_many({"timestamp": {"$lt": now - LOCKOUT_DURATION}})

def check_login_attempts(username: str) -> tuple[int, Optional[datetime]]:
    now = datetime.utcnow()
    recent_attempts = login_attempts_collection.find({
        "username": username,
        "timestamp": {"$gte": now - LOCKOUT_DURATION},
        "success": False
    })
    failed_attempts = list(recent_attempts)
    count = len(failed_attempts)
    if count >= MAX_LOGIN_ATTEMPTS:
        earliest_attempt = min(attempt["timestamp"] for attempt in failed_attempts)
        unlock_time = earliest_attempt + LOCKOUT_DURATION
        if now < unlock_time:
            return count, unlock_time
    return count, None

def get_random_asteroids(travel_days: int, limit: int = 3) -> List[dict]:
    logging.info(f"Fetching asteroids with moid_days = {travel_days}")
    matching_asteroids = list(db.asteroids.find({"moid_days": travel_days}))
    if not matching_asteroids:
        logging.warning(f"No asteroids found with moid_days = {travel_days}")
        return []
    return random.sample(matching_asteroids, min(limit, len(matching_asteroids)))

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request, show_register: bool = False, error: str = None, travel_days: int = None, current_user: Optional[User] = Depends(get_optional_user)):
    missions = list(db.missions.find({"user_id": current_user.id})) if current_user else []
    asteroids = get_random_asteroids(travel_days) if travel_days and current_user else []
    logging.info(f"User {current_user.username if current_user else 'Anonymous'}: Loaded {len(missions)} missions and {len(asteroids)} asteroids")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "show_register": show_register,
        "error": error,
        "user": current_user,
        "missions": missions,
        "asteroids": asteroids,
        "travel_days": travel_days
    })

@app.post("/register", response_class=RedirectResponse)
async def register(
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    company_name: str = Form(default="Unnamed Company")
):
    validate_alphanumeric(username, "Username")
    validate_alphanumeric(company_name, "Company Name")
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_dict = {
        "_id": ObjectId(),
        "username": username,
        "email": email,
        "hashed_password": pwd_context.hash(password),
        "company_name": company_name,
        "bank": Int64(0),
        "loan_count": 0,
        "current_loan": Int64(0)
    }
    users_collection.insert_one(user_dict)
    access_token = create_access_token(data={"sub": str(user_dict["_id"])})
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.post("/login", response_class=RedirectResponse)
async def login(response: Response, request: Request, username: str = Form(...), password: str = Form(...)):
    validate_alphanumeric(username, "Username")
    attempt_count, lockout_until = check_login_attempts(username)
    if lockout_until:
        remaining_time = (lockout_until - datetime.utcnow()).total_seconds() // 60
        error_msg = f"Too many failed attempts. Locked out until {lockout_until.strftime('%H:%M:%S UTC')} (~{int(remaining_time)} minutes)"
        logging.warning(f"User {username} login locked out until {lockout_until}")
        return RedirectResponse(url=f"/?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)

    user = users_collection.find_one({"username": username})
    if not user:
        record_login_attempt(username, success=False)
        error_msg = f"Invalid credentials. {MAX_LOGIN_ATTEMPTS - attempt_count - 1} attempts remaining"
        logging.info(f"User {username} login failed: no such user, {MAX_LOGIN_ATTEMPTS - attempt_count - 1} attempts left")
        return RedirectResponse(url=f"/?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)
    
    hashed_pw = user.get("hashed_password", user.get("password_hash"))
    if not hashed_pw or not pwd_context.verify(password, hashed_pw):
        record_login_attempt(username, success=False)
        attempt_count += 1
        if attempt_count >= MAX_LOGIN_ATTEMPTS:
            error_msg = f"Too many failed attempts. Locked out for {LOCKOUT_DURATION.total_seconds() // 60} minutes"
            logging.warning(f"User {username} login failed: max attempts reached, locked out")
        else:
            error_msg = f"Invalid credentials. {MAX_LOGIN_ATTEMPTS - attempt_count} attempts remaining"
            logging.info(f"User {username} login failed: wrong password, {MAX_LOGIN_ATTEMPTS - attempt_count} attempts left")
        return RedirectResponse(url=f"/?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)
    
    record_login_attempt(username, success=True)
    access_token = create_access_token(data={"sub": str(user["_id"])})
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    logging.info(f"User {username} logged in successfully")
    return response

@app.get("/logout", response_class=RedirectResponse)
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@app.patch("/users/me", response_model=User)
async def update_user(update: UserUpdate, user: User = Depends(get_current_user)):
    update_dict = update.dict(exclude_unset=True)
    if "company_name" in update_dict:
        validate_alphanumeric(update_dict["company_name"], "Company Name")
    users_collection.update_one({"_id": ObjectId(user.id)}, {"$set": update_dict})
    if "company_name" in update_dict:
        db.missions.update_many(
            {"user_id": user.id},
            {"$set": {"company": update_dict["company_name"]}}
        )
        logging.info(f"User {user.username}: Updated company name to {update_dict['company_name']} for all missions")
    updated_user = users_collection.find_one({"_id": ObjectId(user.id)})
    updated_user_dict = {
        "_id": str(updated_user["_id"]),
        "username": updated_user.get("username", ""),
        "email": updated_user.get("email", ""),
        "hashed_password": updated_user.get("hashed_password", user.get("password_hash", "")),
        "company_name": updated_user.get("company_name", "Unnamed Company"),
        "bank": PyInt64(updated_user.get("bank", 0)),
        "loan_count": updated_user.get("loan_count", 0),
        "current_loan": PyInt64(updated_user.get("current_loan", 0))
    }
    return User(**updated_user_dict)

@app.post("/missions/start", response_class=RedirectResponse)
async def start_mission(
    asteroid_full_name: str = Form(...),
    ship_name: str = Form(...),
    travel_days: int = Form(...),
    user: User = Depends(get_current_user),
    response: Response = None
):
    logging.info(f"User {user.username}: Starting mission with asteroid {asteroid_full_name}, ship {ship_name}, travel_days {travel_days}")
    validate_alphanumeric(ship_name, "Ship Name")
    
    existing_ship = db.ships.find_one({
        "user_id": user.id,
        "name": ship_name,
        "location": 0.0,
        "active": True
    })
    
    if existing_ship:
        ship_id = str(existing_ship["_id"])
        logging.info(f"User {user.username}: Reusing existing ship {ship_name} with ID {ship_id}")
    else:
        unavailable_ship = db.ships.find_one({"user_id": user.id, "name": ship_name})
        if unavailable_ship:
            logging.warning(f"User {user.username}: Ship {ship_name} exists but is unavailable (location: {unavailable_ship['location']}, active: {unavailable_ship['active']})")
            return RedirectResponse(url="/?error=Ship is currently unavailable (not at Earth or inactive)", status_code=status.HTTP_303_SEE_OTHER)
        
        ship_data = {
            "_id": ObjectId(),
            "name": ship_name,
            "user_id": user.id,
            "shield": 100,
            "mining_power": 500,
            "created": datetime.now(UTC),
            "days_in_service": 0,
            "location": 0.0,
            "mission": 0,
            "hull": 100,
            "cargo": [],
            "capacity": 50000,
            "active": True,
            "missions": []
        }
        db.ships.insert_one(ship_data)
        ship_id = str(ship_data["_id"])
        logging.info(f"User {user.username}: Created new ship {ship_name} with ID {ship_id}")

    # Fetch asteroid for moid_days
    asteroid = db.asteroids.find_one({"full_name": asteroid_full_name})
    if not asteroid:
        logging.error(f"User {user.username}: No asteroid found with full_name {asteroid_full_name}")
        return RedirectResponse(url=f"/?error=No asteroid found with name {asteroid_full_name}", status_code=status.HTTP_303_SEE_OTHER)
    
    # Calculate profit projection
    mining_power = existing_ship["mining_power"] if existing_ship else ship_data["mining_power"]
    target_yield_kg = existing_ship["capacity"] if existing_ship else ship_data["capacity"]
    daily_yield_rate = Int64(mining_power * 24 * 0.10)  # Max 10% elements/day
    confidence, profit_min, profit_max = calculate_confidence(
        moid_days=asteroid["moid_days"],
        mining_power=mining_power,
        target_yield_kg=target_yield_kg,
        daily_yield_rate=daily_yield_rate
    )
    mission_projection = Int64(profit_max)  # Optimistic projection

    mission_budget = 400000000
    MINIMUM_FUNDING = 436000000
    if user.bank >= MINIMUM_FUNDING:
        pass
    else:
        # Slower loan escalation for 4/5 success: 1.1x, 1.2x, 1.3x, 1.5x, 1.75x, 2.0x, 2.5x
        loan_multipliers = [1.1, 1.2, 1.3, 1.5, 1.75, 2.0, 2.5]
        multiplier_index = min(user.loan_count, len(loan_multipliers) - 1)
        repayment_rate = loan_multipliers[multiplier_index]
        loan_amount = Int64(int(mission_budget * repayment_rate))
        db.users.update_one(
            {"_id": ObjectId(user.id)},
            {"$set": {"current_loan": loan_amount}, "$inc": {"loan_count": 1}}
        )
        logging.info(f"User {user.username}: Mission funded with loan of ${loan_amount:,} at {repayment_rate}x (Loan #{user.loan_count + 1})")

    mission_data = {
        "_id": ObjectId(),
        "user_id": user.id,
        "company": user.company_name,
        "ship_name": ship_name,
        "ship_id": ship_id,
        "asteroid_full_name": asteroid_full_name,
        "name": f"{asteroid_full_name} Mission",
        "travel_days_allocated": travel_days,
        "mining_days_allocated": 0,
        "total_duration_days": 0,
        "scheduled_days": 0,
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
        "target_yield_kg": Int64(target_yield_kg),
        "ship_location": 0.0,
        "total_yield_kg": Int64(0),
        "days_into_mission": 0,
        "days_left": 0,
        "mission_cost": Int64(0),
        "mission_projection": mission_projection,
        "confidence": confidence
    }
    result = db.missions.insert_one(mission_data)
    mission_id = str(result.inserted_id)
    
    if existing_ship:
        db.ships.update_one(
            {"_id": ObjectId(ship_id)},
            {"$push": {"missions": mission_id}}
        )
    
    logging.info(f"User {user.username}: Created mission {mission_id} for asteroid {asteroid_full_name} with ship {ship_name}, Projected Profit: ${mission_projection:,}, Confidence: {confidence:.2f}%")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request, user: User = Depends(get_current_user)):
    missions = [MissionModel(**m) for m in db.missions.find({"user_id": user.id})]
    for mission in missions:
        ship = db.ships.find_one({"name": mission.ship_name, "user_id": user.id})
        mission.ship_id = str(ship["_id"]) if ship else None
    logging.info(f"User {user.username}: Loaded {len(missions)} missions for dashboard")
    return templates.TemplateResponse("dashboard.html", {"request": request, "missions": missions, "user": user})

@app.get("/dashboard/{mission_id}", response_class=HTMLResponse)
async def get_mission_details(request: Request, mission_id: str, user: User = Depends(get_current_user)):
    mission_dict = db.missions.find_one({"_id": ObjectId(mission_id), "user_id": user.id})
    if not mission_dict:
        raise HTTPException(status_code=404, detail="Mission not found")
    mission = MissionModel(**mission_dict)
    ship = db.ships.find_one({"name": mission.ship_name, "user_id": user.id})
    ship_id = str(ship["_id"]) if ship else None
    logging.info(f"User {user.username}: Loaded mission {mission_id} details with ship ID {ship_id}")
    return templates.TemplateResponse("mission_details.html", {"request": request, "mission": mission, "ship_id": ship_id})

@app.get("/ships/{ship_id}", response_class=HTMLResponse)
async def get_ship_details(request: Request, ship_id: str, user: User = Depends(get_current_user)):
    ship = db.ships.find_one({"_id": ObjectId(ship_id), "user_id": user.id})
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")
    
    missions = list(db.missions.find({"ship_name": ship["name"], "user_id": user.id}))
    daily_yields = {}
    for mission in missions:
        for summary in mission.get("daily_summaries", []):
            day = summary["day"]
            elements = summary.get("elements_mined", {}) or {}
            daily_yields[day] = daily_yields.get(day, {})
            for elem, kg in elements.items():
                daily_yields[day][elem] = daily_yields[day].get(elem, 0) + kg

    days = sorted(daily_yields.keys())
    elements = set()
    for yields in daily_yields.values():
        elements.update(yields.keys())
    elements = list(elements)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD']
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for i, element in enumerate(elements):
        fig.add_trace(
            go.Bar(
                x=days,
                y=[daily_yields.get(day, {}).get(element, 0) for day in days],
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
    return templates.TemplateResponse("ship_details.html", {
        "request": request,
        "ship": ship,
        "missions": missions,
        "graph_html": graph_html
    })

@app.post("/missions/advance", response_class=JSONResponse)
async def advance_all_missions(user: User = Depends(get_current_user)):
    active_missions = list(db.missions.find({"user_id": user.id, "status": 0}))
    if not active_missions:
        logging.info(f"User {user.username}: No active missions to advance")
        return JSONResponse(content={"message": "No active missions to advance"}, status_code=200)
    next_day = max([len(m.get("daily_summaries", [])) for m in active_missions], default=0) + 1
    logging.info(f"User {user.username}: Advancing day {next_day} for {len(active_missions)} active missions")
    result = mine_asteroid(user.id, day=next_day, username=user.username, company_name=user.company_name)
    return result

@app.post("/missions/complete", response_class=JSONResponse)
async def complete_all_missions(user: User = Depends(get_current_user)):
    active_missions = list(db.missions.find({"user_id": user.id, "status": 0}))
    if not active_missions:
        logging.info(f"User {user.username}: No active missions to complete")
        return JSONResponse(content={"message": "No active missions to complete"}, status_code=200)
    
    logging.info(f"User {user.username}: Running simulation to complete {len(active_missions)} active missions")
    results = {}
    for mission_raw in active_missions:
        mission_id = str(mission_raw["_id"])
        days_into_mission = len(mission_raw.get("daily_summaries", []))
        base_travel_days = Int64(mission_raw["travel_days_allocated"])
        mining_days = Int64(mission_raw["mining_days_allocated"])
        total_days = Int64(base_travel_days * 2 + mining_days + mission_raw.get("travel_delays", 0))
        
        for day in range(days_into_mission + 1, int(total_days) + 1):
            result = process_single_mission(mission_raw, day=day, username=user.username, company_name=user.company_name)
            if "status" in result and result["status"] == 1:
                profit = result.get("profit", 0)
                if profit > 0 and user.current_loan > 0:
                    net_profit = max(0, profit - user.current_loan)
                    db.users.update_one(
                        {"_id": ObjectId(user.id)},
                        {"$inc": {"bank": Int64(net_profit)}, "$set": {"current_loan": Int64(0)}}
                    )
                    logging.info(f"User {user.username}: Mission {mission_id} completed, profit ${profit:,}, repaid loan ${user.current_loan:,}, net to bank ${net_profit:,}")
                elif profit > 0:
                    db.users.update_one(
                        {"_id": ObjectId(user.id)},
                        {"$inc": {"bank": Int64(profit)}}
                    )
                    logging.info(f"User {user.username}: Mission {mission_id} completed, added profit ${profit:,} to bank")
                results[mission_id] = result
                break
            mission_raw = db.missions.find_one({"_id": ObjectId(mission_id)})
            results[mission_id] = result
    
    return JSONResponse(content=results, status_code=200)

@app.get("/leaderboard", response_class=HTMLResponse)
async def get_leaderboard(request: Request, user: User = Depends(get_current_user)):
    USE_CASES = ["fuel", "lifesupport", "energystorage", "construction", "electronics", "coolants", 
                 "industrial", "medical", "propulsion", "shielding", "agriculture", "mining"]
    element_uses = {elem["name"]: elem.get("uses", []) for elem in db.elements.find()}
    
    pipeline = [
        {"$match": {}},
        {
            "$lookup": {
                "from": "missions",
                "let": {"userId": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$user_id", "$$userId"]}}}
                ],
                "as": "missions"
            }
        },
        {"$project": {"user_id": "$_id", "company": "$company_name", "missions": 1}}
    ]
    all_users = list(users_collection.aggregate(pipeline))
    logging.info(f"Loaded {len(all_users)} users for leaderboard")

    leaderboard_data = []
    for entry in all_users:
        total_elements = {}
        total_profit = 0
        use_case_mass = {use: 0 for use in USE_CASES}
        missions = entry.get("missions", [])
        logging.info(f"User {entry['company']}: Processing {len(missions)} missions")
        
        for mission in missions:
            profit = mission.get("profit", 0)
            total_profit += profit if isinstance(profit, (int, float)) else 0
            elements = mission.get("elements", [])
            for elem in elements:
                name = elem.get("name", "")
                mass_kg = elem.get("mass_kg", 0)
                if isinstance(mass_kg, (int, float)):
                    total_elements[name] = total_elements.get(name, 0) + mass_kg
                    uses = element_uses.get(name, [])
                    for use in uses:
                        if use in USE_CASES:
                            use_case_mass[use] += mass_kg
        
        total_mass = sum(total_elements.values())
        leaderboard_data.append({
            "user_id": str(entry["user_id"]),
            "company": entry["company"],
            "total_profit": total_profit,
            "total_elements": total_elements,
            "use_case_mass": use_case_mass,
            "score": total_profit + total_mass * 1000
        })
        logging.info(f"User {entry['company']}: Total Profit: {total_profit}, Use Case Mass: {use_case_mass}")

    leaderboard_data.sort(key=lambda x: x["total_profit"], reverse=True)
    logging.info(f"Leaderboard data after sorting: {len(leaderboard_data)} entries")

    for i, entry in enumerate(leaderboard_data, 1):
        entry["rank"] = i

    logging.info(f"User ID: {user.id}, Companies: {[e['company'] for e in leaderboard_data]}")
    user_entry = next((e for e in leaderboard_data if e["user_id"] == user.id), None)
    user_rank = user_entry["rank"] if user_entry else len(leaderboard_data) + 1
    logging.info(f"User: {user.company_name}, Entry: {user_entry}, Rank: {user_rank}")

    top_10 = leaderboard_data[:10]
    logging.info(f"Top 10 entries: {[e['company'] for e in top_10]}")

    if user_entry and user_entry not in top_10:
        top_10.append(user_entry)

    if top_10:
        fig = go.Figure()
        for entry in top_10:
            use_cases = list(entry["use_case_mass"].keys())
            masses = list(entry["use_case_mass"].values())
            fig.add_trace(
                go.Bar(
                    x=use_cases,
                    y=masses,
                    name=entry["company"],
                    text=[f"{m:,} kg" for m in masses],
                    textposition="auto"
                )
            )
        fig.update_layout(
            barmode='group',
            title_text="Total Mass by Use Case",
            xaxis_title="Use Case",
            yaxis_title="Total Mass (kg)",
            template="plotly_dark",
            height=600
        )
        graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        graph_html = "<p>No data available</p>"

    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
        "leaderboard": top_10,
        "user_rank": user_rank,
        "user_company": user.company_name,
        "graph_html": graph_html
    })