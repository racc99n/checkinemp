from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmployeeCreate(BaseModel):
    full_name: str
    employee_code: str
    department: str = ""
    position: str = ""
    shift_id: Optional[int] = None
    telegram_chat_id: Optional[str] = None


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    shift_id: Optional[int] = None
    telegram_chat_id: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    id: int
    full_name: str
    employee_code: str
    department: str
    position: str
    shift_id: Optional[int]
    shift_name: Optional[str] = None
    telegram_chat_id: Optional[str]
    face_encoding_path: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollFaceRequest(BaseModel):
    images_b64: list[str]  # 3-5 base64 encoded images
