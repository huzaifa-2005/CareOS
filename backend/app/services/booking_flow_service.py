from app.services.booking_session_service import get_session, start_session, update_session, end_session
from app.services.calendar_service import get_available_slots, create_calendar_event
from app.services.db import supabase
from app.services.calendar_service import update_calendar_event
from app.services.email_alert_service import send_urgent_alert

BOOKING_TRIGGERS = ["book appointment", "book", "appointment", "want to book"]

RESCHEDULE_TRIGGERS = ["reschedule", "change appointment", "change my appointment"]

URGENT_KEYWORDS = ["emergency", "urgent", "severe", "bleeding", "can't breathe", "chest pain", "fainted", "accident"]
CANCEL_TRIGGERS = ["cancel appointment", "cancel my appointment", "cancel"]
WAITLIST_TRIGGERS = ["waitlist", "notify me", "earlier slot", "earliest slot"]

def is_cancel_trigger(message: str) -> bool:
    return any(t in message.lower().strip() for t in CANCEL_TRIGGERS)

def is_waitlist_trigger(message: str) -> bool:
    return any(t in message.lower().strip() for t in WAITLIST_TRIGGERS)


def handle_cancel_flow(clinic_id: str, patient_id: str) -> str:
    existing = supabase.table("appointments") \
        .select("id, scheduled_at, google_event_id") \
        .eq("patient_id", patient_id).eq("status", "booked").execute()

    if not existing.data:
        return "You don't have any active appointments to cancel."

    appointment = existing.data[0]
    supabase.table("appointments").update({"status": "cancelled"}) \
        .eq("id", appointment["id"]).execute()

    return f"Your appointment on {appointment['scheduled_at']} has been cancelled. Let us know if you'd like to book a new one."


def handle_waitlist_flow(clinic_id: str, patient_id: str, message: str) -> str:
    session = get_session(patient_id)
    msg = message.strip()

    if not session or session.get("flow_type") != "waitlist":
        start_session(clinic_id, patient_id, "waitlist", "ask_doctor")
        update_session(patient_id, "ask_doctor", {})
        return "Which doctor would you like to be notified about? (enter doctor's name)"

    step = session["current_step"]
    data = session["collected_data"]

    if step == "ask_doctor":
        data["doctor_name"] = msg
        update_session(patient_id, "ask_date", data)
        return "What's your preferred date range? (e.g. 'next week', '2026-08-01 to 2026-08-05')"

    elif step == "ask_date":
        data["preferred_date"] = msg
        supabase.table("waitlist_requests").insert({
            "clinic_id": clinic_id,
            "patient_id": patient_id,
            "doctor_name": data["doctor_name"],
            "preferred_date": data["preferred_date"],
        }).execute()
        end_session(patient_id)
        return f"Got it! We'll email you if an earlier slot with Dr {data['doctor_name']} opens up around {data['preferred_date']}."

    end_session(patient_id)
    return "Something went wrong, let's start over."
def detect_urgency(message: str) -> str:
    msg = message.lower()
    if any(word in msg for word in URGENT_KEYWORDS):
        return "urgent"
    return "normal"

def is_reschedule_trigger(message: str) -> bool:
    msg = message.lower().strip()
    return any(trigger in msg for trigger in RESCHEDULE_TRIGGERS)

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
        data["urgency_level"] = detect_urgency(msg)
        update_session(patient_id, "ask_date", data)
        return "What date would you like to come in? (format: YYYY-MM-DD)"

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
            "urgency_level": data.get("urgency_level", "normal"),
            "scheduled_at": f"{data['date']}T{data['time']}:00",
            "status": "booked",
            "google_event_id": event_id
        }).execute()
        if data.get("urgency_level") == "urgent":
            send_urgent_alert(clinic_id, patient_name, data["treatment_type"])

        end_session(patient_id)
        return f"✅ Your appointment is booked for {data['date']} at {data['time']}. See you then!"

    end_session(patient_id)
    return "Something went wrong, let's start over. Type 'book appointment' to try again."



def handle_reschedule_flow(clinic_id: str, patient_id: str, message: str) -> str:
    session = get_session(patient_id)
    msg = message.strip()

    if not session:
        existing = supabase.table("appointments") \
            .select("id, scheduled_at, google_event_id") \
            .eq("patient_id", patient_id) \
            .eq("status", "booked") \
            .execute()

        if not existing.data:
            return "You don't have any active appointments to reschedule."

        appointment = existing.data[0]  # simplest: assume most recent booked appointment
        start_session(clinic_id, patient_id, "reschedule", "ask_new_date")
        update_session(patient_id, "ask_new_date", {"appointment_id": appointment["id"], "google_event_id": appointment["google_event_id"]})
        return f"Your current appointment is on {appointment['scheduled_at']}. What new date would you like? (YYYY-MM-DD)"

    step = session["current_step"]
    data = session["collected_data"]

    if step == "ask_new_date":
        data["new_date"] = msg
        slots = get_available_slots(msg)
        if not slots:
            return "No slots available that day. Please try another date (YYYY-MM-DD)."
        data["available_slots"] = slots
        update_session(patient_id, "ask_new_time", data)
        slots_text = ", ".join(slots[:8])
        return f"Available slots: {slots_text}\nWhich time would you like?"

    elif step == "ask_new_time":
        if msg not in data.get("available_slots", []):
            return "That slot isn't available. Please pick one from the list."
        data["new_time"] = msg
        update_session(patient_id, "confirm_reschedule", data)
        return f"Confirm reschedule to {data['new_date']} at {data['new_time']}? (yes/no)"

    elif step == "confirm_reschedule":
        if msg.lower() not in ["yes", "y", "haan", "ji"]:
            end_session(patient_id)
            return "Reschedule cancelled."

        update_calendar_event(data["google_event_id"], data["new_date"], data["new_time"])

        supabase.table("appointments").update({
            "scheduled_at": f"{data['date']}T{data['time']}:00",
            "status": "rescheduled"
        }).eq("id", data["appointment_id"]).execute()

        end_session(patient_id)
        return f"✅ Rescheduled to {data['new_date']} at {data['new_time']}."

    end_session(patient_id)
    return "Something went wrong, let's start over."