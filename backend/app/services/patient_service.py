from app.services.db import supabase

def get_or_create_patient(clinic_id: str, phone_number: str, patient_name: str) -> str:
    existing = supabase.table("contact_identifiers") \
        .select("patient_id") \
        .eq("channel", "whatsapp") \
        .eq("identifier_value", phone_number) \
        .execute()

    if existing.data:
        return existing.data[0]["patient_id"]

    new_patient = supabase.table("patients") \
        .insert({"clinic_id": clinic_id, "full_name": patient_name}) \
        .execute()
    patient_id = new_patient.data[0]["id"]

    supabase.table("contact_identifiers").insert({
        "patient_id": patient_id,
        "channel": "whatsapp",
        "identifier_value": phone_number
    }).execute()

    return patient_id