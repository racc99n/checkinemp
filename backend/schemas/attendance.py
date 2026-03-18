from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    employee_code: str
    department: str
    device_name: Optional[str]
    check_in_at: Optional[datetime]
    check_out_at: Optional[datetime]
    status: str
    notes: str
    work_date: str
    face_confidence: Optional[float]

    class Config:
        from_attributes = True


class AttendanceUpdate(BaseModel):
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CheckInRequest(BaseModel):
    image_b64: str
    fingerprint: Optional[str] = None  # เก็บไว้ backward compatible แต่ไม่ใช้สำหรับ auth แล้ว


class CheckInResponse(BaseModel):
    success: bool
    action: str  # "check_in" or "check_out"
    employee_name: str
    employee_code: str
    timestamp: datetime
    status: str
    message: str
