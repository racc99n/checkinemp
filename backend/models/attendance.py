from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("registered_devices.id"), nullable=True)
    check_in_at = Column(DateTime, nullable=True)
    check_out_at = Column(DateTime, nullable=True)
    check_in_photo_path = Column(String, nullable=True)
    check_out_photo_path = Column(String, nullable=True)
    face_confidence = Column(Float, nullable=True)
    status = Column(String, default="present")  # present, late, absent
    notes = Column(String, default="")
    work_date = Column(String, nullable=False)  # YYYY-MM-DD

    employee = relationship("Employee", back_populates="attendance_records")
    device = relationship("RegisteredDevice")
