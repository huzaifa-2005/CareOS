from app.services.db import supabase

def save_conversation(clinic_id: str, patient_id: str, message_text: str,
                       direction: str, intent_route: str = None, channel: str = "whatsapp"):
    supabase.table("conversations").insert({
        "clinic_id": clinic_id,
        "patient_id": patient_id,
        "channel": channel,
        "message_direction": direction,
        "message_text": message_text,
        "intent_route": intent_route,
    }).execute()