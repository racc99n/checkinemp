from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
from ..utils.timezone import now_th


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    employee_code = Column(String, unique=True, nullable=False)
    department = Column(String, default="")
    position = Column(String, default="")
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=True)
    telegram_chat_id = Column(String, nullable=True)
    face_encoding_path = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_th)
    updated_at = Column(DateTime, default=now_th, onupdate=now_th)

    shift = relationship("Shift")
    attendance_records = relationship("AttendanceRecord", back_populates="employee")
