from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from app.services.rule_based import handle_rule_based

router = APIRouter()

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    from_number = form_data.get("From")      # e.g. "whatsapp:+923001234567"
    body = form_data.get("Body")             # message text
    profile_name = form_data.get("ProfileName")  # sender's WhatsApp display name

    # TODO: pass from_number, body into your intent classifier / rule-based flow here

    rule_response = handle_rule_based(body)

    if rule_response:
        reply_text = rule_response
    else:
        # No rule matched — this is where the intent classifier /
        # RAG-LLM pipeline will plug in (next subtasks)
        reply_text = "Let me connect you to more detailed help..."  # temporary placeholder

    twiml = MessagingResponse()
    twiml.message(reply_text)

    return Response(content=str(twiml), media_type="application/xml")