import os
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.services.db import supabase

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(staff_id: str, clinic_id: str, role: str) -> str:
    payload = {
        "staff_id": staff_id,
        "clinic_id": clinic_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def authenticate_staff(email: str, password: str):
    result = supabase.table("clinic_staff").select("*").eq("email", email).execute()
    if not result.data:
        return None

    staff = result.data[0]
    if not staff.get("password_hash"):
        return None
    if not verify_password(password, staff["password_hash"]):
        return None

    return staff