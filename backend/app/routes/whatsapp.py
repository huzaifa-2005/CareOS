from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from app.services.patient_service import get_or_create_patient
from app.services.conversation_service import save_conversation
from app.services.intent_classifier import classify_and_respond
from app.services.booking_session_service import get_session
from app.services.booking_flow_service import handle_booking_flow, is_booking_trigger

router = APIRouter()

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    from_number = form_data.get("From")      # e.g. "whatsapp:+923001234567"
    body = form_data.get("Body")             # message text
    patient_name = form_data.get("ProfileName")  # sender's WhatsApp display name

    # pass from_number, body into your intent classifier / rule-based flow here

    

    # if rule_response:
    #     reply_text = rule_response
    # else:
        # No rule matched — this is where the intent classifier /
        # RAG-LLM pipeline will plug in (next subtasks) 
        # reply_text = "Let me connect you to more detailed help..."  ( temporary placeholder )
    
    
    
    # TEMP: hardcode a real clinic_id from your `clinics` table for now —
    # multi-clinic routing (matching Twilio number -> clinic) isn't built yet.
   
    clinic_id = "d98e07aa-6de1-426c-8c13-6a60ddea931b"

    patient_id = get_or_create_patient(clinic_id, from_number, patient_name)

    

    active_session = get_session(patient_id)

    if active_session or is_booking_trigger(body):
        reply_text = handle_booking_flow(clinic_id, patient_id, body)
        intent_route = None  # not rule-based or rag_llm — it's structured flow
    else:
        intent_route, reply_text = classify_and_respond(body, clinic_id)

    save_conversation(clinic_id, patient_id, body, "inbound", intent_route)
    save_conversation(clinic_id, patient_id, reply_text, "outbound", None)

    
    twiml = MessagingResponse()
    twiml.message(reply_text)

    return Response(content=str(twiml), media_type="application/xml")