from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse

router = APIRouter()

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    from_number = form_data.get("From")      # e.g. "whatsapp:+923001234567"
    body = form_data.get("Body")             # message text
    profile_name = form_data.get("ProfileName")  # sender's WhatsApp display name

    # TODO: pass from_number, body into your intent classifier / rule-based flow here

    reply_text = f"Received: {body}"  # placeholder until routing logic exists

    twiml = MessagingResponse()
    twiml.message(reply_text)

    return Response(content=str(twiml), media_type="application/xml")