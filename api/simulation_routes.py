from fastapi import APIRouter, HTTPException
from amos import execute_mining_mission, get_missions  # Updated import
from bson import ObjectId

simulation_router = APIRouter()

@simulation_router.post("/{mission_id}/start")
def start_simulation(mission_id: str):
    """
    Start a mining simulation for a specific mission.
    """
    try:
        mission = get_missions(ObjectId(mission_id))
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Start the simulation
        execute_mining_mission(mission_id=ObjectId(mission_id))
        return {"message": "Simulation started successfully", "mission_id": mission_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@simulation_router.get("/{mission_id}/progress")
def get_simulation_progress(mission_id: str):
    """
    Retrieve the progress of a mining simulation.
    """
    try:
        mission = get_missions(ObjectId(mission_id))
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Return mission progress
        return {"mission_id": mission_id, "progress": mission[0].dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@simulation_router.post("/{mission_id}/stop")
def stop_simulation(mission_id: str):
    """
    Stop a mining simulation for a specific mission.
    """
    try:
        # Logic to stop the simulation (e.g., update mission status)
        return {"message": "Simulation stopped successfully", "mission_id": mission_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))