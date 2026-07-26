from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.patient_auth_service import signup_patient, login_patient
from app.services.staff_auth_service import create_token
from app.dependencies import get_current_patient
from app.services.booking_session_service import get_session
from app.services.booking_flow_service import (
    handle_booking_flow,
    handle_reschedule_flow,
    is_booking_trigger,
    is_reschedule_trigger,
)
from app.services.intent_classifier import classify_and_respond
from app.services.conversation_service import save_conversation
from app.services.db import supabase

router = APIRouter()


CLINIC_ID = "d98e07aa-6de1-426c-8c13-6a60ddea931b"

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/api/patient/signup")
async def patient_signup(payload: SignupRequest):
    if payload.password != payload.confirm_password:
        return {"error": "Passwords do not match"}

    result = signup_patient(CLINIC_ID, payload.username, payload.email, payload.password)
    if "error" in result:
        return result

    token = create_token(staff_id=result["patient_id"], clinic_id=CLINIC_ID, role="patient")
    return {"token": token, "patient_id": result["patient_id"]}


@router.post("/api/patient/login")
async def patient_login(payload: LoginRequest):
    patient = login_patient(payload.username, payload.password)
    if not patient:
        return {"error": "Invalid username or password"}

    token = create_token(staff_id=patient["id"], clinic_id=patient["clinic_id"], role="patient")
    return {"token": token, "patient_id": patient["id"]}



class SessionRequest(BaseModel):
    session_id: str


class MessageRequest(BaseModel):
    message: str


@router.post("/api/web-chat/message")
async def send_message(payload: MessageRequest, patient=Depends(get_current_patient)):
    patient_id = patient["staff_id"]  # this holds the patient_id from the JWT
    clinic_id = patient["clinic_id"]
    body = payload.message

    active_session = get_session(patient_id)

    if active_session:
        if active_session["flow_type"] == "booking":
            reply_text = handle_booking_flow(clinic_id, patient_id, body)
        else:
            reply_text = handle_reschedule_flow(clinic_id, patient_id, body)
        intent_route = None
    elif is_reschedule_trigger(body):
        reply_text = handle_reschedule_flow(clinic_id, patient_id, body)
        intent_route = None
    elif is_booking_trigger(body):
        reply_text = handle_booking_flow(clinic_id, patient_id, body)
        intent_route = None
    else:
        intent_route, reply_text = classify_and_respond(body, clinic_id)

    save_conversation(clinic_id, patient_id, body, "inbound", intent_route, channel="web")
    save_conversation(clinic_id, patient_id, reply_text, "outbound", None, channel="web")

    return {"reply": reply_text}

@router.get("/api/web-chat/history")
async def get_history(patient=Depends(get_current_patient)):
    patient_id = patient["staff_id"]

    result = supabase.table("conversations") \
        .select("message_text, message_direction, created_at") \
        .eq("patient_id", patient_id) \
        .order("created_at") \
        .execute()

    return {"messages": result.data}