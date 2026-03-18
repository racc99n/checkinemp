from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DeviceCreate(BaseModel):
    device_name: str
    fingerprint_hash: str = ""
    location: str = ""


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceResponse(BaseModel):
    id: int
    device_name: str
    fingerprint_hash: Optional[str] = ""
    device_token: str
    location: str
    is_active: bool
    registered_at: datetime
    last_seen_at: Optional[datetime]

    class Config:
        from_attributes = True


class DeviceRegisterRequest(BaseModel):
    device_name: str
    fingerprint: str = ""  # optional now, backward compatible
    location: str = ""


class DeviceActivateRequest(BaseModel):
    """Request สำหรับ activate อุปกรณ์จากหน้า check-in"""
    username: str
    password: str
    device_id: Optional[int] = None       # เลือกอุปกรณ์ที่มีอยู่
    device_name: Optional[str] = None      # หรือสร้างใหม่
    location: Optional[str] = None


class DeviceActivateResponse(BaseModel):
    device_token: str
    device_name: str
    device_id: int
    message: str


class DeviceTokenValidateResponse(BaseModel):
    valid: bool
    device_name: Optional[str]
    device_id: Optional[int]
