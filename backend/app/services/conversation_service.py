from app.services.db import supabase

def save_conversation(clinic_id: str, patient_id: str, message_text: str,
                       direction: str, intent_route: str = None):
    supabase.table("conversations").insert({
        "clinic_id": clinic_id,
        "patient_id": patient_id,
        "channel": "whatsapp",
        "message_direction": direction,       # 'inbound' or 'outbound'
        "message_text": message_text,
        "intent_route": intent_route,          # "None" for outbound rows
    }).execute()