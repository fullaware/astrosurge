from fastapi import FastAPI, Depends, HTTPException, Request, status, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
import os
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from config import MongoDBConfig
from amos.mine_asteroid import mine_asteroid
import logging

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")  # Serve static files

# MongoDB Setup using MongoDBConfig
db = MongoDBConfig.get_database()
users_collection = db["users"]
login_attempts_collection = db["login_attempts"]

# JWT Setup
SECRET_KEY = os.environ.get("JWT_SECRET", "SUPERSECRETKEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=5)

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User Models
class User(BaseModel):
    id: str = Field(alias="_id")
    username: str
    email: str
    hashed_password: str
    company_name: str = "Unnamed Company"

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    company_name: Optional[str] = "Unnamed Company"

class UserUpdate(BaseModel):
    company_name: Optional[str]

class Token(BaseModel):
    access_token: str
    token_type: str

# Token Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
    user_dict = {
        "_id": str(user["_id"]),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "hashed_password": user.get("hashed_password", user.get("password_hash", "")),
        "company_name": user.get("company_name", "Unnamed Company")
    }
    return User(**user_dict)

# Login Attempt Tracking
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

# Endpoints
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request, show_register: bool = False, error: str = None):
    return templates.TemplateResponse("index.html", {"request": request, "show_register": show_register, "error": error})

@app.post("/register", response_class=RedirectResponse)
async def register(
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    company_name: str = Form(default="Unnamed Company")
):
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_dict = {
        "_id": ObjectId(),
        "username": username,
        "email": email,
        "hashed_password": pwd_context.hash(password),
        "company_name": company_name
    }
    users_collection.insert_one(user_dict)
    access_token = create_access_token(data={"sub": str(user_dict["_id"])})
    response = RedirectResponse(url="/dashboard/6612a3b8f9e8d4c7b9a1f2e3", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.post("/login", response_class=RedirectResponse)
async def login(response: Response, request: Request, username: str = Form(...), password: str = Form(...)):
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
    response = RedirectResponse(url="/dashboard/6612a3b8f9e8d4c7b9a1f2e3", status_code=status.HTTP_303_SEE_OTHER)
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
    users_collection.update_one({"_id": ObjectId(user.id)}, {"$set": update_dict})
    updated_user = users_collection.find_one({"_id": ObjectId(user.id)})
    updated_user_dict = {
        "_id": str(updated_user["_id"]),
        "username": updated_user.get("username", ""),
        "email": updated_user.get("email", ""),
        "hashed_password": updated_user.get("hashed_password", updated_user.get("password_hash", "")),
        "company_name": updated_user.get("company_name", "Unnamed Company")
    }
    return User(**updated_user_dict)

@app.get("/dashboard/{mission_id}", response_class=HTMLResponse)
async def get_dashboard(request: Request, mission_id: str, user: User = Depends(get_current_user)):
    mission_data = mine_asteroid(
        mission_id,
        username=user.username,
        company_name=user.company_name,
        ship_name=None
    )
    if "error" in mission_data:
        raise HTTPException(status_code=500, detail=mission_data["error"])
    if not mission_data.get("ship_name"):
        ship = db.ships.find_one({"user_id": mission_data["user_id"], "active": True})
        mission_data["ship_name"] = ship["name"] if ship else "Unknown Ship"
    return templates.TemplateResponse("dashboard.html", {"request": request, "mission": mission_data})

@app.get("/leaderboard", response_class=HTMLResponse)
async def get_leaderboard(request: Request, user: User = Depends(get_current_user)):
    pipeline = [
        {"$group": {"_id": "$company", "total_profit": {"$sum": "$profit"}}},
        {"$sort": {"total_profit": -1}},
        {"$limit": 10}
    ]
    leaderboard = list(db.missions.aggregate(pipeline))
    leaderboard = [{"company": entry["_id"], "total_profit": entry["total_profit"]} for entry in leaderboard]
    return templates.TemplateResponse("leaderboard.html", {"request": request, "leaderboard": leaderboard})