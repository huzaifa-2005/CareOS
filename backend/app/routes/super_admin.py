from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.db import supabase
from app.services.admin_auth_service import authenticate_admin, create_admin_token
from app.dependencies import get_current_admin

router = APIRouter()


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class ClinicCreateRequest(BaseModel):
    name: str
    timezone: str
    whatsapp_number: str


class ClinicStatusUpdate(BaseModel):
    is_active: bool


class StaffCreateRequest(BaseModel):
    full_name: str
    email: str
    role: str
    password: str


@router.post("/api/admin/login")
async def admin_login(payload: AdminLoginRequest):
    if not authenticate_admin(payload.email, payload.password):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    token = create_admin_token()
    return {"token": token}


@router.get("/api/admin/clinics")
async def list_clinics(admin=Depends(get_current_admin)):
    result = supabase.table("clinics").select("*").execute()
    return {"clinics": result.data}


@router.post("/api/admin/clinics")
async def create_clinic(payload: ClinicCreateRequest, admin=Depends(get_current_admin)):
    result = supabase.table("clinics").insert({
        "name": payload.name,
        "timezone": payload.timezone,
        "whatsapp_number": payload.whatsapp_number,
        "is_active": True,
    }).execute()
    return {"success": True, "clinic": result.data[0]}


@router.patch("/api/admin/clinics/{clinic_id}")
async def update_clinic_status(clinic_id: str, payload: ClinicStatusUpdate, admin=Depends(get_current_admin)):
    supabase.table("clinics").update({"is_active": payload.is_active}).eq("id", clinic_id).execute()
    return {"success": True}


@router.get("/api/admin/clinics/{clinic_id}/stats")
async def clinic_stats(clinic_id: str, admin=Depends(get_current_admin)):
    conversations = supabase.table("conversations").select("intent_route").eq("clinic_id", clinic_id).execute()
    appointments = supabase.table("appointments").select("id, status").eq("clinic_id", clinic_id).execute()

    rule_based_count = sum(1 for c in conversations.data if c["intent_route"] == "rule_based")
    rag_llm_count = sum(1 for c in conversations.data if c["intent_route"] == "rag_llm")
    total_appointments = len(appointments.data)
    booked_count = sum(1 for a in appointments.data if a["status"] == "booked")

    return {
        "total_conversations": len(conversations.data),
        "rule_based_count": rule_based_count,
        "rag_llm_count": rag_llm_count,
        "total_appointments": total_appointments,
        "booked_count": booked_count,
    }


@router.get("/api/admin/clinics/{clinic_id}/staff")
async def list_staff(clinic_id: str, admin=Depends(get_current_admin)):
    result = supabase.table("clinic_staff").select("id, full_name, email, role, created_at").eq("clinic_id", clinic_id).execute()
    return {"staff": result.data}


@router.post("/api/admin/clinics/{clinic_id}/staff")
async def create_staff(clinic_id: str, payload: StaffCreateRequest, admin=Depends(get_current_admin)):
    from app.services.staff_auth_service import hash_password
    supabase.table("clinic_staff").insert({
        "clinic_id": clinic_id,
        "full_name": payload.full_name,
        "email": payload.email,
        "role": payload.role,
        "password_hash": hash_password(payload.password),
    }).execute()
    return {"success": True}

@router.get("/api/admin/clinics/{clinic_id}/feedback")
async def admin_list_feedback(clinic_id: str, admin=Depends(get_current_admin)):
    result = supabase.table("feedback").select("*").eq("clinic_id", clinic_id) \
        .order("created_at", desc=True).execute()
    return {"feedback": result.data}