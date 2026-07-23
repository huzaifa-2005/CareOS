from fastapi import Header, HTTPException
from app.services.staff_auth_service import decode_token


def get_current_staff(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.replace("Bearer ", "")
    try:
        payload = decode_token(token)
        return payload  # contains staff_id, clinic_id, role
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")