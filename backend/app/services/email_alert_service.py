import os
import smtplib
from email.mime.text import MIMEText
from app.services.db import supabase

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD")

def send_urgent_alert(clinic_id: str, patient_name: str, treatment_type: str):
    staff = supabase.table("clinic_staff").select("email").eq("clinic_id", clinic_id).execute()

    if not staff.data:
        return

    for row in staff.data:
        recipient = row.get("email")
        if not recipient:
            continue
        try:
            msg = MIMEText(f"Patient: {patient_name}\nReason: {treatment_type}\n\nPlease check WhatsApp / dashboard for full conversation.")
            msg["Subject"] = "🚨 URGENT Patient Alert - CareOS"
            msg["From"] = SENDER_EMAIL
            msg["To"] = recipient

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
        except Exception as e:
            print(f"Failed to send urgent email alert: {e}")