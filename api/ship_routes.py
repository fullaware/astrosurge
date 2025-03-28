from fastapi import APIRouter, HTTPException
from amos import (
    create_ship,
    get_ships_by_user_id,
    get_ship,
    update_ship_attributes,
    list_cargo,
    empty_cargo,
    repair_ship,
)
from bson import ObjectId

ship_router = APIRouter()

@ship_router.post("/")
def create_new_ship(user_id: str, name: str):
    """
    Create a new ship for a user.
    """
    try:
        ship = create_ship(name=name, user_id=ObjectId(user_id))
        return {"message": "Ship created successfully", "ship": ship}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.get("/")
def list_user_ships(user_id: str):
    """
    List all ships for a specific user.
    """
    try:
        ships = get_ships_by_user_id(ObjectId(user_id))
        if not ships:
            raise HTTPException(status_code=404, detail="No ships found for this user.")
        return {"ships": ships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.get("/{ship_id}")
def get_ship_details(ship_id: str):
    """
    Retrieve details of a specific ship by its ID.
    """
    try:
        ship = get_ship(ObjectId(ship_id))
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found.")
        return {"ship": ship}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.put("/{ship_id}")
def update_ship(ship_id: str, updates: dict):
    """
    Update attributes of a specific ship.
    """
    try:
        updated_ship = update_ship_attributes(ObjectId(ship_id), updates)
        if not updated_ship:
            raise HTTPException(status_code=404, detail="Ship not found or no changes made.")
        return {"message": "Ship updated successfully", "ship": updated_ship}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.get("/{ship_id}/cargo")
def list_ship_cargo(ship_id: str):
    """
    List the cargo of a specific ship.
    """
    try:
        cargo = list_cargo(ObjectId(ship_id))
        return {"cargo": cargo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.delete("/{ship_id}/cargo")
def clear_ship_cargo(ship_id: str):
    """
    Empty the cargo of a specific ship.
    """
    try:
        empty_cargo(ObjectId(ship_id))
        return {"message": "Cargo cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.post("/{ship_id}/repair")
def repair_ship_endpoint(ship_id: str):
    """
    Repair a specific ship.
    """
    try:
        repaired_ship = repair_ship(ObjectId(ship_id))
        if not repaired_ship:
            raise HTTPException(status_code=404, detail="Ship not found or cannot be repaired.")
        return {"message": "Ship repaired successfully", "ship": repaired_ship}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))