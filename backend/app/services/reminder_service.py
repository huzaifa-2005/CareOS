import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from app.services.db import supabase

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD")


def send_email_reminder(patient_email: str, treatment_type: str, scheduled_at: str):
    try:
        msg = MIMEText(f"Reminder: You have a {treatment_type} appointment in 2 hours, at {scheduled_at}.")
        msg["Subject"] = "Appointment Reminder - CareOS"
        msg["From"] = SENDER_EMAIL
        msg["To"] = patient_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, patient_email, msg.as_string())
    except Exception as e:
        print(f"Failed to send email reminder: {e}")


def send_whatsapp_reminder(phone_number: str, treatment_type: str, scheduled_at: str):
    """
    ⚠️ Backend wiring only — intentionally NOT connected to Twilio's send call.
    This function is ready to plug in later; currently just logs instead of sending.
    """
    print(f"[WhatsApp reminder - NOT SENT, wiring only] Would notify {phone_number}: "
          f"{treatment_type} appointment at {scheduled_at}")
    # Uncomment when ready to actually send:
    # from twilio.rest import Client
    # client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    # client.messages.create(
    #     from_=os.getenv("TWILIO_WHATSAPP_NUMBER"),
    #     to=f"whatsapp:{phone_number}",
    #     body=f"Reminder: {treatment_type} appointment at {scheduled_at}"
    # )


def check_and_send_reminders():
    print("⏰ Reminder check running...")
    now = datetime.now(timezone.utc)
    window_start = now + timedelta(hours=2)
    window_end = now + timedelta(hours=2, minutes=5)

    result = supabase.table("appointments").select("*") \
        .eq("status", "booked") \
        .gte("scheduled_at", window_start.isoformat()) \
        .lt("scheduled_at", window_end.isoformat()) \
        .execute()

    for appt in result.data:
        patient = supabase.table("patients").select("email").eq("id", appt["patient_id"]).execute()
        if patient.data and patient.data[0].get("email"):
            send_email_reminder(patient.data[0]["email"], appt["treatment_type"], appt["scheduled_at"])

        contacts = supabase.table("contact_identifiers").select("identifier_value, channel") \
            .eq("patient_id", appt["patient_id"]).eq("channel", "whatsapp").execute()
        for c in contacts.data:
            send_whatsapp_reminder(c["identifier_value"], appt["treatment_type"], appt["scheduled_at"])


            