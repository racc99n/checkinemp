from sqlalchemy import Column, Integer, String, Boolean
from ..database import Base
from ..utils.timezone import now_th


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)          # เช่น "กะเช้า", "กะดึก"
    start_time = Column(String, nullable=False)                  # "09:00"
    end_time = Column(String, nullable=False)                    # "18:00"
    late_threshold_minutes = Column(Integer, default=15)         # นาทีที่ถือว่าสาย
    is_active = Column(Boolean, default=True)
