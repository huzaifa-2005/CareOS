from app.services.db import supabase
from app.services.staff_auth_service import hash_password, verify_password, create_token


def signup_patient(clinic_id: str, username: str, email: str, password: str):
    existing_username = supabase.table("patients").select("id").eq("username", username).execute()
    if existing_username.data:
        return {"error": "Username already taken"}

    existing_email = supabase.table("patients").select("id").eq("email", email).execute()
    if existing_email.data:
        return {"error": "Email already registered"}

    new_patient = supabase.table("patients").insert({
        "clinic_id": clinic_id,
        "full_name": username,
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
    }).execute()
    patient_id = new_patient.data[0]["id"]

    supabase.table("contact_identifiers").insert({
        "patient_id": patient_id,
        "channel": "web",
        "identifier_value": username,
    }).execute()

    return {"patient_id": patient_id}


def login_patient(username: str, password: str):
    result = supabase.table("patients").select("*").eq("username", username).execute()
    if not result.data:
        return None
    patient = result.data[0]
    if not patient.get("password_hash") or not verify_password(password, patient["password_hash"]):
        return None
    return patient