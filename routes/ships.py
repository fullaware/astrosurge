import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from config import MongoDBConfig
from amos.manage_mission import create_new_ship, get_elements_mined, get_daily_value
from utils.auth import get_current_user, validate_alphanumeric
from models.models import User
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
        logging.info(f"User {user.username}: Created new ship {ship_name} for mission planning")
    except ValueError as e:
        return RedirectResponse(url=f"/?travel_days={travel_days}&error={str(e)}", status_code=status.HTTP_303_SEE_OTHER)
    
    return RedirectResponse(url=f"/?travel_days={travel_days}&asteroid_full_name={asteroid_full_name}", status_code=status.HTTP_303_SEE_OTHER)

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
        logging.info(f"User {user.username}: Ship {ship_id} element {element} y_values: {y_values[:5]}...")  # Log first 5
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