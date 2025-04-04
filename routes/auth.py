import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from datetime import datetime, UTC  # Added for created_at
from config import MongoDBConfig
from utils.auth import create_access_token, get_current_user, get_optional_user, record_login_attempt, check_login_attempts, validate_alphanumeric, pwd_context
from models.models import User, UserCreate, UserUpdate, PyInt64  # Added PyInt64

router = APIRouter()
templates = Jinja2Templates(directory="templates")
db = MongoDBConfig.get_database()
users_collection = db["users"]
login_attempts_collection = db["login_attempts"]

@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request, show_register: bool = False, error: str = None, travel_days: int = None, current_user: User = Depends(get_optional_user)):
    from utils.helpers import get_random_asteroids
    missions = list(db.missions.find({"user_id": current_user.id})) if current_user else []
    asteroids = get_random_asteroids(travel_days) if travel_days and current_user else []
    available_ships = list(db.ships.find({"user_id": current_user.id, "location": 0.0, "active": True})) if current_user else []
    has_ships = len(available_ships) > 0
    logging.info(f"User {current_user.username if current_user else 'Anonymous'}: Loaded {len(missions)} missions, {len(asteroids)} asteroids, {len(available_ships)} available ships")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "show_register": show_register,
        "error": error,
        "user": current_user,
        "missions": missions,
        "asteroids": asteroids,
        "available_ships": available_ships,
        "travel_days": travel_days,
        "has_ships": has_ships
    })

@router.post("/register", response_class=RedirectResponse)
async def register(response: Response, username: str = Form(...), email: str = Form(...), password: str = Form(...), company_name: str = Form(default="Unnamed Company")):
    validate_alphanumeric(username, "Username")
    validate_alphanumeric(company_name, "Company Name")
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_dict = UserCreate(username=username, email=email, password=password, company_name=company_name).dict()
    user_dict["_id"] = ObjectId()
    user_dict["hashed_password"] = pwd_context.hash(password)
    user_dict["bank"] = PyInt64(0)
    user_dict["loan_count"] = 0
    user_dict["current_loan"] = PyInt64(0)
    user_dict["max_overrun_days"] = 10
    user_dict["created_at"] = datetime.now(UTC)
    users_collection.insert_one(user_dict)
    access_token = create_access_token(data={"sub": str(user_dict["_id"])})
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.post("/login", response_class=RedirectResponse)
async def login(response: Response, request: Request, username: str = Form(...), password: str = Form(...)):
    validate_alphanumeric(username, "Username")
    attempt_count, lockout_until = check_login_attempts(username)
    if lockout_until:
        remaining_time = (lockout_until - datetime.now(UTC)).total_seconds() // 60
        error_msg = f"Too many failed attempts. Locked out until {lockout_until.strftime('%H:%M:%S UTC')} (~{int(remaining_time)} minutes)"
        logging.warning(f"User {username} login locked out until {lockout_until}")
        return RedirectResponse(url=f"/?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)

    user = users_collection.find_one({"username": username})
    if not user or not pwd_context.verify(password, user.get("hashed_password", user.get("password_hash"))):
        record_login_attempt(username, success=False)
        attempt_count += 1
        error_msg = f"Invalid credentials. {5 - attempt_count} attempts remaining" if attempt_count < 5 else f"Too many failed attempts. Locked out for 5 minutes"
        logging.info(f"User {username} login failed: {'no such user' if not user else 'wrong password'}, {5 - attempt_count if attempt_count < 5 else 0} attempts left")
        return RedirectResponse(url=f"/?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)
    
    record_login_attempt(username, success=True)
    access_token = create_access_token(data={"sub": str(user["_id"])})
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    logging.info(f"User {username} logged in successfully")
    return response

@router.get("/logout", response_class=RedirectResponse)
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/users/me/details", response_class=HTMLResponse)
async def get_user_details(request: Request, user: User = Depends(get_current_user)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("user_details.html", {"request": request, "user": user})

@router.patch("/users/me", response_model=User)
async def update_user(
    company_name: str = Form(None),
    email: str = Form(None),
    max_overrun_days: int = Form(None),
    user: User = Depends(get_current_user)
):
    if isinstance(user, RedirectResponse):
        return user
    update_dict = {}
    if company_name is not None:
        validate_alphanumeric(company_name, "Company Name")
        update_dict["company_name"] = company_name
    if email is not None:
        update_dict["email"] = email
    if max_overrun_days is not None:
        if max_overrun_days < 0:
            raise HTTPException(status_code=400, detail="Max overrun days must be non-negative")
        update_dict["max_overrun_days"] = max_overrun_days
    if not update_dict:
        return user
    users_collection.update_one({"_id": ObjectId(user.id)}, {"$set": update_dict})
    if "company_name" in update_dict:
        db.missions.update_many({"user_id": user.id}, {"$set": {"company": update_dict["company_name"]}})
        logging.info(f"User {user.username}: Updated company name to {update_dict['company_name']} for all missions")
    updated_user = users_collection.find_one({"_id": ObjectId(user.id)})
    return User(**{**updated_user, "_id": str(updated_user["_id"])})