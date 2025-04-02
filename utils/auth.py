import re
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Request, status
from typing import Optional
from bson import ObjectId
from config import MongoDBConfig
from models.models import User, PyInt64

SECRET_KEY = "SUPERSECRETKEY"  # Ideally from os.environ.get("JWT_SECRET", "SUPERSECRETKEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=5)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
VALIDATION_PATTERN = re.compile(r'^[a-zA-Z0-9]{1,30}$')

db = MongoDBConfig.get_database()
users_collection = db["users"]
login_attempts_collection = db["login_attempts"]

def validate_alphanumeric(value: str, field_name: str):
    if not VALIDATION_PATTERN.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be alphanumeric (A-Z, a-z, 0-9) and up to 30 characters long"
        )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request, required: bool = True):
    token = request.cookies.get("access_token")
    if not token:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            if required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
    except jwt.PyJWTError:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    user_dict = {
        "_id": str(user["_id"]),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "hashed_password": user.get("hashed_password", user.get("password_hash", "")),
        "company_name": user.get("company_name", "Unnamed Company"),
        "bank": PyInt64(user.get("bank", 0)),
        "loan_count": user.get("loan_count", 0),
        "current_loan": PyInt64(user.get("current_loan", 0))
    }
    return User(**user_dict)

async def get_optional_user(request: Request):
    return await get_current_user(request, required=False)

def record_login_attempt(username: str, success: bool):
    now = datetime.utcnow()
    attempt = {"username": username, "timestamp": now, "success": success}
    login_attempts_collection.insert_one(attempt)
    login_attempts_collection.delete_many({"timestamp": {"$lt": now - LOCKOUT_DURATION}})

def check_login_attempts(username: str) -> tuple[int, Optional[datetime]]:
    now = datetime.utcnow()
    recent_attempts = login_attempts_collection.find({
        "username": username,
        "timestamp": {"$gte": now - LOCKOUT_DURATION},
        "success": False
    })
    failed_attempts = list(recent_attempts)
    count = len(failed_attempts)
    if count >= MAX_LOGIN_ATTEMPTS:
        earliest_attempt = min(attempt["timestamp"] for attempt in failed_attempts)
        unlock_time = earliest_attempt + LOCKOUT_DURATION
        if now < unlock_time:
            return count, unlock_time
    return count, None