"""
webui.py
A minimal FastAPI interface with dark theme placeholders.
"""
import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from pymongo import MongoClient
from dotenv import load_dotenv
from generate_logo import generate_logo

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client["beryl_mvp"]
app = FastAPI(title="Space Mining UI")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    generate_logo(0)  # Generate the initial logo
    return templates.TemplateResponse("index.html", {"request": request, "title": "Space Mining MVP"})

@app.get("/missions", response_class=HTMLResponse)
def get_missions(request: Request):
    missions = list(db.missions.find())
    return templates.TemplateResponse("missions.html", {"request": request, "missions": missions})

@app.post("/launch", response_class=HTMLResponse)
def launch_mission(request: Request, asteroid_name: str = Form(...), days_to_mine: int = Form(...)):
    new_mission = {
        "asteroid_name": asteroid_name,
        "days_to_mine": days_to_mine,
        "status": "Launched"
    }
    db.missions.insert_one(new_mission)
    msg = f"Mission to {asteroid_name} launched for {days_to_mine} days!"
    return templates.TemplateResponse("index.html", {"request": request, "message": msg})

@app.get("/static/logo.png", response_class=FileResponse)
def get_logo():
    return FileResponse("static/logo.png")
