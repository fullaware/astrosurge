from fastapi import APIRouter, HTTPException
from amos import (
    get_missions,
    plan_mission,
    fund_mission,
    update_mission,
    MissionStatus,
)
from bson import ObjectId

mission_router = APIRouter()

@mission_router.get("/", response_model=dict)
def list_missions(user_id: str):
    """
    Retrieve all missions for a specific user.

    - **user_id**: The ID of the user whose missions are being retrieved.
    - **Returns**: A dictionary containing a list of the user's missions.
    """
    try:
        missions = get_missions(ObjectId(user_id))
        if not missions:
            raise HTTPException(status_code=404, detail="No missions found for this user.")
        return {"missions": [mission.dict() for mission in missions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mission_router.post("/", response_model=dict)
def create_mission(user_id: str, asteroid_name: str, ship_id: str, mining_days: int):
    """
    Create a new mission for a user.

    - **user_id**: The ID of the user creating the mission.
    - **asteroid_name**: The name of the asteroid to mine.
    - **ship_id**: The ID of the ship to use for the mission.
    - **mining_days**: The number of days allocated for mining.
    - **Returns**: A dictionary containing a success message and the created mission details.
    """
    try:
        mission = plan_mission(
            user_id=ObjectId(user_id),
            asteroid_name=asteroid_name,
            ship_id=ObjectId(ship_id),
            mining_days=mining_days,
        )
        return {"message": "Mission created successfully", "mission": mission.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mission_router.post("/{mission_id}/fund", response_model=dict)
def fund_mission_endpoint(mission_id: str):
    """
    Fund a mission.

    - **mission_id**: The ID of the mission to fund.
    - **Returns**: A dictionary containing a success message and the funded mission details.
    """
    try:
        funded_mission = fund_mission(ObjectId(mission_id))
        if not funded_mission:
            raise HTTPException(status_code=404, detail="Mission not found or already funded.")
        return {"message": "Mission funded successfully", "mission": funded_mission.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mission_router.put("/{mission_id}", response_model=dict)
def update_mission_endpoint(mission_id: str, updates: dict):
    """
    Update an existing mission.

    - **mission_id**: The ID of the mission to update.
    - **updates**: A dictionary of fields to update.
    - **Returns**: A dictionary containing a success message.
    """
    try:
        success = update_mission(ObjectId(mission_id), updates)
        if not success:
            raise HTTPException(status_code=404, detail="Mission not found or no changes made.")
        return {"message": "Mission updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@mission_router.get("/{mission_id}", response_model=dict)
def get_mission_details(mission_id: str):
    """
    Retrieve details of a specific mission.

    - **mission_id**: The ID of the mission to retrieve.
    - **Returns**: A dictionary containing the mission details.
    """
    try:
        missions = get_missions(filter={"_id": ObjectId(mission_id)})
        if not missions:
            raise HTTPException(status_code=404, detail="Mission not found.")
        return {"mission": missions[0].dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))