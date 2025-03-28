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

@ship_router.post("/", response_model=dict)
def create_new_ship(user_id: str, name: str):
    """
    Create a new ship for a user.

    - **user_id**: The ID of the user creating the ship.
    - **name**: The name of the new ship.
    - **Returns**: A dictionary containing a success message and the created ship details.
    """
    try:
        ship = create_ship(name=name, user_id=ObjectId(user_id))
        return {"message": "Ship created successfully", "ship": ship}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.get("/", response_model=dict)
def list_user_ships(user_id: str):
    """
    List all ships for a specific user.

    - **user_id**: The ID of the user whose ships are being retrieved.
    - **Returns**: A dictionary containing a list of the user's ships.
    """
    try:
        ships = get_ships_by_user_id(ObjectId(user_id))
        if not ships:
            raise HTTPException(status_code=404, detail="No ships found for this user.")
        return {"ships": ships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.get("/{ship_id}", response_model=dict)
def get_ship_details(ship_id: str):
    """
    Retrieve details of a specific ship by its ID.

    - **ship_id**: The ID of the ship to retrieve.
    - **Returns**: A dictionary containing the ship details.
    """
    try:
        ship = get_ship(ObjectId(ship_id))
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found.")
        return {"ship": ship}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.put("/{ship_id}", response_model=dict)
def update_ship(ship_id: str, updates: dict):
    """
    Update attributes of a specific ship.

    - **ship_id**: The ID of the ship to update.
    - **updates**: A dictionary of fields to update.
    - **Returns**: A dictionary containing a success message and the updated ship details.
    """
    try:
        updated_ship = update_ship_attributes(ObjectId(ship_id), updates)
        if not updated_ship:
            raise HTTPException(status_code=404, detail="Ship not found or no changes made.")
        return {"message": "Ship updated successfully", "ship": updated_ship}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.get("/{ship_id}/cargo", response_model=dict)
def list_ship_cargo(ship_id: str):
    """
    List the cargo of a specific ship.

    - **ship_id**: The ID of the ship whose cargo is being retrieved.
    - **Returns**: A dictionary containing the ship's cargo.
    """
    try:
        cargo = list_cargo(ObjectId(ship_id))
        return {"cargo": cargo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.delete("/{ship_id}/cargo", response_model=dict)
def clear_ship_cargo(ship_id: str):
    """
    Empty the cargo of a specific ship.

    - **ship_id**: The ID of the ship whose cargo is being cleared.
    - **Returns**: A dictionary containing a success message.
    """
    try:
        empty_cargo(ObjectId(ship_id))
        return {"message": "Cargo cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ship_router.post("/{ship_id}/repair", response_model=dict)
def repair_ship_endpoint(ship_id: str):
    """
    Repair a specific ship.

    - **ship_id**: The ID of the ship to repair.
    - **Returns**: A dictionary containing a success message and the repaired ship details.
    """
    try:
        repaired_ship = repair_ship(ObjectId(ship_id))
        if not repaired_ship:
            raise HTTPException(status_code=404, detail="Ship not found or cannot be repaired.")
        return {"message": "Ship repaired successfully", "ship": repaired_ship}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))