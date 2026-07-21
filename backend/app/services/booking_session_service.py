from app.services.db import supabase

def get_session(patient_id: str):
    result = supabase.table("booking_sessions").select("*").eq("patient_id", patient_id).execute()
    return result.data[0] if result.data else None

def start_session(clinic_id: str, patient_id: str, flow_type: str, first_step: str):
    supabase.table("booking_sessions").insert({
        "clinic_id": clinic_id,
        "patient_id": patient_id,
        "flow_type": flow_type,
        "current_step": first_step,
        "collected_data": {}
    }).execute()

def update_session(patient_id: str, step: str, data: dict):
    supabase.table("booking_sessions").update({
        "current_step": step,
        "collected_data": data,
        "updated_at": "now()"
    }).eq("patient_id", patient_id).execute()

def end_session(patient_id: str):
    supabase.table("booking_sessions").delete().eq("patient_id", patient_id).execute()