from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.whatsapp import router as whatsapp_router
from app.routes.web_chat import router as web_chat_router
from app.routes.receptionist_dashboard import router as receptionist_router
from app.routes.super_admin import router as super_admin_router
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.reminder_service import check_and_send_reminders

app = FastAPI()

scheduler = BackgroundScheduler()
scheduler.add_job(
    check_and_send_reminders,
    "interval",
    minutes=5,
    misfire_grace_time=300,  # allow up to 5 min late
    coalesce=True,           # if multiple missed, just run once
    max_instances=1
)
scheduler.start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://care-os-web-chat.vercel.app",
        "https://care-os-receptionist-dashboard.vercel.app",
        "https://care-os-super-admin.vercel.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
        "http://localhost:5502",
        "http://127.0.0.1:5502",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(whatsapp_router)
app.include_router(web_chat_router)
app.include_router(receptionist_router)
app.include_router(super_admin_router)