import os
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

def get_calendar_service():
    credentials_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=credentials)

def get_available_slots(date: str, duration_minutes: int = 30) -> list[str]:
    """
    date format: 'YYYY-MM-DD'
    Returns list of available start times as strings, e.g. ['10:00', '10:30', ...]
    Clinic hours hardcoded 10 AM - 8 PM for now.
    """
    service = get_calendar_service()
    day_start = datetime.fromisoformat(f"{date}T10:00:00")
    day_end = datetime.fromisoformat(f"{date}T20:00:00")

    body = {
        "timeMin": day_start.isoformat() + "Z",
        "timeMax": day_end.isoformat() + "Z",
        "items": [{"id": CALENDAR_ID}],
    }
    freebusy = service.freebusy().query(body=body).execute()
    busy_slots = freebusy["calendars"][CALENDAR_ID]["busy"]

    all_slots = []
    current = day_start
    while current + timedelta(minutes=duration_minutes) <= day_end:
        slot_end = current + timedelta(minutes=duration_minutes)
        is_busy = any(
            current < datetime.fromisoformat(b["end"].replace("Z", "")) and
            slot_end > datetime.fromisoformat(b["start"].replace("Z", ""))
            for b in busy_slots
        )
        if not is_busy:
            all_slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=duration_minutes)

    return all_slots

def create_calendar_event(date: str, time: str, patient_name: str, duration_minutes: int = 30) -> str:
    service = get_calendar_service()
    start_dt = datetime.fromisoformat(f"{date}T{time}:00")
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event = {
        "summary": f"Appointment - {patient_name}",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Karachi"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Karachi"},
    }
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return created_event["id"]  # save this in your `appointments` table for future rescheduling

def update_calendar_event(event_id: str, new_date: str, new_time: str, duration_minutes: int = 30):
    service = get_calendar_service()
    start_dt = datetime.fromisoformat(f"{new_date}T{new_time}:00")
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event = service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
    event["start"] = {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Karachi"}
    event["end"] = {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Karachi"}
    service.events().update(calendarId=CALENDAR_ID, eventId=event_id, body=event).execute()