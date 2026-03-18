from pydantic import BaseModel
from typing import Optional


class ShiftCreate(BaseModel):
    name: str
    start_time: str          # "HH:MM"
    end_time: str            # "HH:MM"
    late_threshold_minutes: int = 15


class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    late_threshold_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class ShiftResponse(BaseModel):
    id: int
    name: str
    start_time: str
    end_time: str
    late_threshold_minutes: int
    is_active: bool

    class Config:
        from_attributes = True
