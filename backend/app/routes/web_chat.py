from fastapi import APIRouter
from pydantic import BaseModel

from app.services.patient_service import get_or_create_web_patient
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

# TEMP: same hardcoded clinic_id pattern used in whatsapp.py — replace with real
# multi-tenant lookup once that's built.
CLINIC_ID = "d98e07aa-6de1-426c-8c13-6a60ddea931b"


class SessionRequest(BaseModel):
    session_id: str


class MessageRequest(BaseModel):
    session_id: str
    message: str


@router.post("/api/web-chat/session")
async def create_session(payload: SessionRequest):
    patient_id = get_or_create_web_patient(CLINIC_ID, payload.session_id)
    return {"patient_id": patient_id, "clinic_id": CLINIC_ID}


@router.post("/api/web-chat/message")
async def send_message(payload: MessageRequest):
    patient_id = get_or_create_web_patient(CLINIC_ID, payload.session_id)
    body = payload.message

    active_session = get_session(patient_id)

    if active_session:
        if active_session["flow_type"] == "booking":
            reply_text = handle_booking_flow(CLINIC_ID, patient_id, body)
        else:
            reply_text = handle_reschedule_flow(CLINIC_ID, patient_id, body)
        intent_route = None
    elif is_reschedule_trigger(body):
        reply_text = handle_reschedule_flow(CLINIC_ID, patient_id, body)
        intent_route = None
    elif is_booking_trigger(body):
        reply_text = handle_booking_flow(CLINIC_ID, patient_id, body)
        intent_route = None
    else:
        intent_route, reply_text = classify_and_respond(body, CLINIC_ID)

    save_conversation(CLINIC_ID, patient_id, body, "inbound", intent_route, channel="web")
    save_conversation(CLINIC_ID, patient_id, reply_text, "outbound", None, channel="web")

    return {"reply": reply_text}


@router.get("/api/web-chat/history/{session_id}")
async def get_history(session_id: str):
    patient_id = get_or_create_web_patient(CLINIC_ID, session_id)

    result = supabase.table("conversations") \
        .select("message_text, message_direction, created_at") \
        .eq("patient_id", patient_id) \
        .order("created_at") \
        .execute()

    return {"messages": result.data}