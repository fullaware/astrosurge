"""
main.py

This module serves as the entry point for managing asteroid mining missions. The primary objectives are:

1. **Find an Asteroid**:
   - Locate an asteroid using its name or distance from Earth.
   - Assess its value and plan a mission to mine its resources.

2. **Plan a Mission**:
   - Create a mission to mine the asteroid, assigning a ship and calculating costs.
   - Define the planned duration and investment required for the mission.

3. **Execute the Mission**:
   - Simulate the mission day by day using `execute_mining_mission`.
   - Follow the mission plan:
     a. Travel to the asteroid by incrementing or decrementing `ship.location` until it matches the asteroid's distance.
     b. Mine the asteroid by removing `mass_kg` from its elements and depositing them into the ship's cargo.
     c. Travel back to Earth by updating `ship.location` until it reaches `0` (Earth).
     d. Deposit the mined resources into the mission's `mined_elements` list.

4. **Sell Resources**:
   - Once the ship returns to Earth, sell the mined elements and update the user's/company's `bank` field with the proceeds.

5. **Track Mission Progress**:
   - Maintain the state of the mission by updating the `mission` document and `ship` variables daily.
   - Track the `actual_duration` of the mission and calculate additional costs incurred each day.

6. **Mission Completion**:
   - A mission is marked as "Mission Success" if the ship completes the trip and deposits its cargo on Earth.
   - A mission is marked as "Mission Failure" if the ship's `hull` reaches `0` before returning to Earth.

This module ensures that the mining process is realistic and adheres to the planned objectives, allowing for iterative execution of missions while maintaining accurate state tracking.
"""

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from bson import ObjectId
import random
from typing import Optional, List
import hashlib
import hmac
import base64

# Import existing user management function
from amos.manage_users import get_or_create_and_auth_user

# For database access to asteroids
from config.mongodb_config import MongoDBConfig
from models.models import AsteroidModel

# Secret key for signing cookies
SECRET_KEY = "CHANGE_THIS_TO_A_SECURE_SECRET_KEY"

# Initialize FastAPI app
app = FastAPI(
    title="Asteroid Mining Simulator API",
    description="An API for managing asteroid mining missions, ships, and simulations.",
    version="1.0.0",
)

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mongo collections
asteroids_collection = MongoDBConfig.get_collection("asteroids")

# Simple cookie signing/verification functions
def sign_value(value: str) -> str:
    message = value.encode()
    signature = hmac.new(SECRET_KEY.encode(), message, digestmod=hashlib.sha256).digest()
    signature_b64 = base64.b64encode(signature).decode()
    return f"{value}:{signature_b64}"

def verify_signed_value(signed_value: str) -> Optional[str]:
    if not signed_value or ":" not in signed_value:
        return None
    value, signature = signed_value.rsplit(":", 1)
    expected_signed_value = sign_value(value)
    if hmac.compare_digest(expected_signed_value, signed_value):
        return value
    return None

# Authentication dependency
async def get_current_user(user_cookie: Optional[str] = Cookie(None)):
    if not user_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = verify_signed_value(user_cookie)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    return {"user_id": user_id}

# ---------------------
# ROUTES
# ---------------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    user = get_or_create_and_auth_user(username, password)
    if user:
        user_id_str = str(user["_id"])
        signed_user_id = sign_value(user_id_str)
        response = RedirectResponse(url="/distance", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="user", value=signed_user_id, httponly=True)
        return response
    return templates.TemplateResponse("registration.html", {"request": request, "error": "Registration failed"})

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = get_or_create_and_auth_user(username, password)
    if user:
        user_id_str = str(user["_id"])
        signed_user_id = sign_value(user_id_str)
        response = RedirectResponse(url="/distance", status_code=status.HTTP_302_FOUND)
        
        # Fix: Add explicit cookie parameters for better browser compatibility
        response.set_cookie(
            key="user", 
            value=signed_user_id, 
            httponly=True,
            samesite="lax",  # Important - allows cookies on redirects 
            max_age=3600,    # 1 hour expiration
        )
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/distance", response_class=HTMLResponse)
async def distance_form(request: Request, current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("distance.html", {"request": request})

@app.post("/distance", response_class=HTMLResponse)
async def distance_submit(request: Request, distance_days: int = Form(...), current_user: dict = Depends(get_current_user)):
    response = RedirectResponse(url=f"/asteroids/{distance_days}", status_code=status.HTTP_302_FOUND)
    return response

@app.get("/asteroids/{distance_days}", response_class=HTMLResponse)
async def show_asteroids(request: Request, distance_days: int, current_user: dict = Depends(get_current_user)):
    # This MongoDB query still uses "moid_days" as the field name
    matching_asteroids = list(asteroids_collection.find({"moid_days": distance_days}))
    valid_asteroids = [AsteroidModel(**a).dict() for a in matching_asteroids]
    # Take up to 3 random asteroids
    random_asteroids = random.sample(valid_asteroids, k=min(len(valid_asteroids), 3))

    return templates.TemplateResponse(
        "asteroids.html", 
        {
            "request": request, 
            "distance_days": distance_days, 
            "asteroids": random_asteroids
        }
    )

# ---------------------
# API ENDPOINTS
# ---------------------
@app.get("/api/asteroids/")
async def get_asteroids(distance_days: Optional[int] = None):
    if distance_days:
        matching_asteroids = list(asteroids_collection.find({"moid_days": distance_days}))
    else:
        # Get all asteroids, limited to 100 to avoid excessive data transfer
        matching_asteroids = list(asteroids_collection.find().limit(100))
    
    # Convert ObjectId to strings for JSON serialization
    for asteroid in matching_asteroids:
        asteroid["_id"] = str(asteroid["_id"])
    
    return {"asteroids": matching_asteroids}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)