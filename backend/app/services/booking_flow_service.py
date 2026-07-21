from app.services.booking_session_service import get_session, start_session, update_session, end_session
from app.services.calendar_service import get_available_slots, create_calendar_event
from app.services.db import supabase

BOOKING_TRIGGERS = ["book appointment", "book", "appointment", "want to book"]

def is_booking_trigger(message: str) -> bool:
    msg = message.lower().strip()
    return any(trigger in msg for trigger in BOOKING_TRIGGERS)

def handle_booking_flow(clinic_id: str, patient_id: str, message: str) -> str:
    session = get_session(patient_id)
    msg = message.strip()

    if not session:
        start_session(clinic_id, patient_id, "booking", "ask_treatment")
        return "Sure! What type of treatment or consultation do you need? (e.g., general checkup, dental, skin)"

    step = session["current_step"]
    data = session["collected_data"]

    if step == "ask_treatment":
        data["treatment_type"] = msg
        update_session(patient_id, "ask_date", data)
        return "Great. What date would you like to come in? (format: YYYY-MM-DD)"

    elif step == "ask_date":
        data["date"] = msg
        slots = get_available_slots(msg)
        if not slots:
            return "No slots available that day. Please try another date (YYYY-MM-DD)."
        data["available_slots"] = slots
        update_session(patient_id, "ask_time", data)
        slots_text = ", ".join(slots[:8])
        return f"Available slots: {slots_text}\nWhich time would you like?"

    elif step == "ask_time":
        if msg not in data.get("available_slots", []):
            return "That slot isn't available. Please pick one from the list I sent."
        data["time"] = msg
        update_session(patient_id, "confirm", data)
        return f"Confirm booking for {data['date']} at {data['time']} for {data['treatment_type']}? (yes/no)"

    elif step == "confirm":
        if msg.lower() not in ["yes", "y", "haan", "ji"]:
            end_session(patient_id)
            return "Booking cancelled. Let me know if you'd like to try again."

        patient_row = supabase.table("patients").select("full_name").eq("id", patient_id).execute()
        patient_name = patient_row.data[0]["full_name"] or "Patient"

        event_id = create_calendar_event(data["date"], data["time"], patient_name)

        supabase.table("appointments").insert({
            "clinic_id": clinic_id,
            "patient_id": patient_id,
            "treatment_type": data["treatment_type"],
            "urgency_level": "normal",
            "scheduled_at": f"{data['date']}T{data['time']}:00",
            "status": "booked",
            "google_event_id": event_id
        }).execute()

        end_session(patient_id)
        return f"✅ Your appointment is booked for {data['date']} at {data['time']}. See you then!"

    end_session(patient_id)
    return "Something went wrong, let's start over. Type 'book appointment' to try again."