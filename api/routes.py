from fastapi import FastAPI
from api.asteroid_routes import asteroid_router
from api.ship_routes import ship_router
from api.mission_routes import mission_router
from api.simulation_routes import simulation_router

def register_routes(app: FastAPI):
    """
    Register all API routes with the FastAPI app.
    """
    app.include_router(asteroid_router, prefix="/asteroids", tags=["Asteroids"])
    app.include_router(ship_router, prefix="/ships", tags=["Ships"])
    app.include_router(mission_router, prefix="/missions", tags=["Missions"])
    app.include_router(simulation_router, prefix="/simulation", tags=["Simulation"])