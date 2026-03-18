from sqlalchemy import Column, Integer, String, Boolean, DateTime
from ..database import Base
from ..utils.timezone import now_th
import uuid


class RegisteredDevice(Base):
    __tablename__ = "registered_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_name = Column(String, nullable=False)
    fingerprint_hash = Column(String, nullable=True)  # เก็บไว้อ้างอิงเท่านั้น (ไม่ใช่สำหรับ auth)
    device_token = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    location = Column(String, default="")
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=now_th)
    last_seen_at = Column(DateTime, nullable=True)
