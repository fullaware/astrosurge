from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routes.auth import router as auth_router
from routes.missions import router as missions_router
from routes.ships import router as ships_router
from routes.leaderboard import router as leaderboard_router

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routers
app.include_router(auth_router)
app.include_router(missions_router)
app.include_router(ships_router)
app.include_router(leaderboard_router)