from fastapi import APIRouter, HTTPException
from amos import execute_mining_mission, get_missions
from bson import ObjectId

simulation_router = APIRouter()

@simulation_router.post("/{mission_id}/start", response_model=dict)
def start_simulation(mission_id: str):
    """
    Start a mining simulation for a specific mission.

    - **mission_id**: The ID of the mission to start.
    - **Returns**: A dictionary containing a success message and the mission ID.
    """
    try:
        mission = get_missions(ObjectId(mission_id))
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        execute_mining_mission(mission_id=ObjectId(mission_id))
        return {"message": "Simulation started successfully", "mission_id": mission_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@simulation_router.get("/{mission_id}/progress", response_model=dict)
def get_simulation_progress(mission_id: str):
    """
    Retrieve the progress of a mining simulation.

    - **mission_id**: The ID of the mission.
    - **Returns**: A dictionary containing the mission ID and its progress.
    """
    try:
        mission = get_missions(ObjectId(mission_id))
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        return {"mission_id": mission_id, "progress": mission[0].dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@simulation_router.post("/{mission_id}/stop", response_model=dict)
def stop_simulation(mission_id: str):
    """
    Stop a mining simulation for a specific mission.

    - **mission_id**: The ID of the mission to stop.
    - **Returns**: A dictionary containing a success message and the mission ID.
    """
    try:
        return {"message": "Simulation stopped successfully", "mission_id": mission_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))