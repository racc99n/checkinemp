from sqlalchemy import Column, Integer, String, Boolean, DateTime
from ..database import Base
from ..utils.timezone import now_th


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    is_superadmin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_th)
    last_login_at = Column(DateTime, nullable=True)
