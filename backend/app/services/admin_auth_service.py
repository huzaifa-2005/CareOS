import os
from app.services.staff_auth_service import create_token

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def authenticate_admin(email: str, password: str) -> bool:
    return email == ADMIN_EMAIL and password == ADMIN_PASSWORD


def create_admin_token() -> str:
    return create_token(staff_id="super_admin", clinic_id="none", role="super_admin")