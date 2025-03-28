from fastapi import APIRouter, HTTPException
from amos import get_or_create_and_auth_user, update_users, get_user_id_by_user_name
from bson import ObjectId

user_router = APIRouter()

@user_router.post("/login", response_model=dict)
def login_user(username: str, password: str):
    """
    Authenticate or create a user.

    - **username**: The username of the user.
    - **password**: The password of the user.
    - **Returns**: A dictionary containing a success message and the user ID.
    """
    try:
        user = get_or_create_and_auth_user(username, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"message": "User authenticated successfully", "user_id": str(user["_id"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.put("/{user_id}", response_model=dict)
def update_user(user_id: str, updates: dict):
    """
    Update user details.

    - **user_id**: The ID of the user to update.
    - **updates**: A dictionary of fields to update.
    - **Returns**: A dictionary containing a success message and the updated user details.
    """
    try:
        updated_user = update_users(ObjectId(user_id), updates)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User updated successfully", "user": updated_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.get("/{username}", response_model=dict)
def get_user_id(username: str):
    """
    Retrieve the user ID by username.

    - **username**: The username of the user.
    - **Returns**: A dictionary containing the username and user ID.
    """
    try:
        user_id = get_user_id_by_user_name(username)
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        return {"username": username, "user_id": str(user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))