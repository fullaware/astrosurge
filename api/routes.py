from fastapi import FastAPI
from api.asteroid_routes import asteroid_router
from api.ship_routes import ship_router
from api.mission_routes import mission_router
from api.simulation_routes import simulation_router
from api.user_routes import user_router  # New user routes
from api.element_routes import element_router  # New element routes

def register_routes(app: FastAPI):
    """
    Register all API routes with the FastAPI app.
    """
    app.include_router(asteroid_router, prefix="/asteroids", tags=["Asteroids"])
    app.include_router(ship_router, prefix="/ships", tags=["Ships"])
    app.include_router(mission_router, prefix="/missions", tags=["Missions"])
    app.include_router(simulation_router, prefix="/simulation", tags=["Simulation"])
    app.include_router(user_router, prefix="/users", tags=["Users"])  # New route
    app.include_router(element_router, prefix="/elements", tags=["Elements"])  # New route