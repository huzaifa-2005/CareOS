from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.db import supabase
from app.services.staff_auth_service import authenticate_staff, create_token
from app.dependencies import get_current_staff

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class AppointmentStatusUpdate(BaseModel):
    status: str


class DoctorCreateRequest(BaseModel):
    full_name: str
    specialty: str
    consultation_fee: float


@router.post("/api/receptionist/login")
async def login(payload: LoginRequest):
    staff = authenticate_staff(payload.email, payload.password)
    if not staff:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(staff["id"], staff["clinic_id"], staff["role"])
    return {"token": token, "full_name": staff["full_name"], "role": staff["role"]}


@router.get("/api/receptionist/appointments")
async def list_appointments(status: Optional[str] = None, staff=Depends(get_current_staff)):
    query = supabase.table("appointments").select("*").eq("clinic_id", staff["clinic_id"])
    if status:
        query = query.eq("status", status)
    result = query.order("scheduled_at").execute()
    return {"appointments": result.data}


@router.patch("/api/receptionist/appointments/{appointment_id}")
async def update_appointment_status(appointment_id: str, payload: AppointmentStatusUpdate, staff=Depends(get_current_staff)):
    supabase.table("appointments").update({"status": payload.status}) \
        .eq("id", appointment_id).eq("clinic_id", staff["clinic_id"]).execute()
    return {"success": True}


@router.get("/api/receptionist/patients")
async def list_patients(search: Optional[str] = None, staff=Depends(get_current_staff)):
    query = supabase.table("patients").select("*").eq("clinic_id", staff["clinic_id"])
    if search:
        query = query.ilike("full_name", f"%{search}%")
    result = query.execute()
    return {"patients": result.data}


@router.get("/api/receptionist/patients/{patient_id}/conversations")
async def get_patient_conversations(patient_id: str, staff=Depends(get_current_staff)):
    result = supabase.table("conversations").select("*") \
        .eq("patient_id", patient_id).eq("clinic_id", staff["clinic_id"]) \
        .order("created_at").execute()
    return {"conversations": result.data}


@router.get("/api/receptionist/faqs")
async def list_faqs(staff=Depends(get_current_staff)):
    result = supabase.table("faqs").select("*").eq("clinic_id", staff["clinic_id"]).execute()
    return {"faqs": result.data}


@router.get("/api/receptionist/doctors")
async def list_doctors(staff=Depends(get_current_staff)):
    result = supabase.table("doctors").select("*").eq("clinic_id", staff["clinic_id"]).execute()
    return {"doctors": result.data}


@router.post("/api/receptionist/doctors")
async def create_doctor(payload: DoctorCreateRequest, staff=Depends(get_current_staff)):
    supabase.table("doctors").insert({
        "clinic_id": staff["clinic_id"],
        "full_name": payload.full_name,
        "specialty": payload.specialty,
        "consultation_fee": payload.consultation_fee,
        "is_active": True,
    }).execute()
    return {"success": True}


@router.get("/api/receptionist/urgent-flags")
async def urgent_appointments(staff=Depends(get_current_staff)):
    result = supabase.table("appointments").select("*") \
        .eq("clinic_id", staff["clinic_id"]).eq("urgency_level", "urgent") \
        .order("scheduled_at").execute()
    return {"appointments": result.data}