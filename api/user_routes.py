from fastapi import APIRouter, HTTPException
from amos import get_or_create_and_auth_user, update_users  # Updated import

user_router = APIRouter()

@user_router.post("/login")
def login_user(username: str, password: str):
    """
    Authenticate or create a user.
    """
    user = get_or_create_and_auth_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user": user}

@user_router.put("/{user_id}")
def update_user(user_id: str, updates: dict):
    """
    Update user details.
    """
    updated_user = update_users(user_id, updates)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": updated_user}