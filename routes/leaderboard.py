import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config import MongoDBConfig
from auth.auth import get_current_user
from models.models import User
import plotly.graph_objects as go

router = APIRouter()
templates = Jinja2Templates(directory="templates")
db = MongoDBConfig.get_database()

@router.get("/leaderboard", response_class=HTMLResponse)
async def get_leaderboard(request: Request, user: User = Depends(get_current_user)):
    if isinstance(user, RedirectResponse):
        return user
    USE_CASES = ["fuel", "lifesupport", "energystorage", "construction", "electronics", "coolants", "industrial", "medical", "propulsion", "shielding", "agriculture", "mining"]
    element_uses = {elem["name"]: elem.get("uses", []) for elem in db.elements.find()}
    
    pipeline = [{"$match": {}}, {"$lookup": {"from": "missions", "let": {"userId": {"$toString": "$_id"}}, "pipeline": [{"$match": {"$expr": {"$eq": ["$user_id", "$$userId"]}}}], "as": "missions"}}, {"$project": {"user_id": "$_id", "company": "$company_name", "username": "$username", "bank": "$bank", "missions": 1}}]
    all_users = list(db.users.aggregate(pipeline))
    logging.info(f"Loaded {len(all_users)} users for leaderboard")

    leaderboard_data = []
    for entry in all_users:
        total_elements = {}
        total_profit = 0
        use_case_mass = {use: 0 for use in USE_CASES}
        missions = entry.get("missions", [])
        logging.info(f"User {entry['username']} @ {entry['company']}: Processing {len(missions)} missions")
        
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
            "username": entry["username"],
            "bank": entry["bank"],
            "total_profit": total_profit,
            "total_elements": total_elements,
            "use_case_mass": use_case_mass,
            "score": total_profit + total_mass * 1000
        })
        logging.info(f"User {entry['username']} @ {entry['company']}: Total Profit: {total_profit}, Use Case Mass: {use_case_mass}")

    leaderboard_data.sort(key=lambda x: x["total_profit"], reverse=True)
    logging.info(f"Leaderboard data after sorting: {len(leaderboard_data)} entries")

    for i, entry in enumerate(leaderboard_data, 1):
        entry["rank"] = i

    user_entry = next((e for e in leaderboard_data if e["user_id"] == user.id), None)
    user_rank = user_entry["rank"] if user_entry else len(leaderboard_data) + 1
    top_10 = leaderboard_data[:10]
    if user_entry and user_entry not in top_10:
        top_10.append(user_entry)

    if top_10:
        fig = go.Figure()
        for entry in top_10:
            use_cases = list(entry["use_case_mass"].keys())
            masses = list(entry["use_case_mass"].values())
            fig.add_trace(go.Bar(x=use_cases, y=masses, name=f"{entry['username']} @ {entry['company']}", text=[f"{m:,} kg" for m in masses], textposition="auto"))
        fig.update_layout(barmode='group', title_text="Total Mass by Use Case", xaxis_title="Use Case", yaxis_title="Total Mass (kg)", template="plotly_dark", height=600)
        graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        graph_html = "<p>No data available</p>"

    user_display = f"{user.username} @ {user.company_name} - ${user.bank:,}"
    logging.info(f"User {user_display}: Loaded leaderboard, Rank: {user_rank}")
    return templates.TemplateResponse("leaderboard.html", {"request": request, "leaderboard": top_10, "user_rank": user_rank, "user_display": user_display, "user": user, "graph_html": graph_html})