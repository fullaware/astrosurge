from fastapi import FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from amos.mine_asteroid import mine_asteroid

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.post("/missions/{mission_id}/start")
async def start_mission(mission_id: str):
    try:
        result = mine_asteroid(mission_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/{mission_id}", response_class=HTMLResponse)
async def mission_dashboard(request: Request, mission_id: str):
    try:
        mission_data = mine_asteroid(mission_id)
        if "error" in mission_data:
            raise HTTPException(status_code=400, detail=mission_data["error"])
        return templates.TemplateResponse("dashboard.html", {"request": request, "mission": mission_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))