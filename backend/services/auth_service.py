from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from ..models.admin import AdminUser
from ..config import settings
from ..utils.timezone import now_th


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = now_th() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def authenticate_admin(username: str, password: str, db: Session) -> Optional[AdminUser]:
    admin = db.query(AdminUser).filter(
        AdminUser.username == username,
        AdminUser.is_active == True
    ).first()
    if not admin or not verify_password(password, admin.hashed_password):
        return None
    admin.last_login_at = now_th()
    db.commit()
    return admin


def create_default_admin(db: Session):
    existing = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    if not existing:
        admin = AdminUser(
            username="admin",
            hashed_password=hash_password("admin1234"),
            full_name="ผู้ดูแลระบบ",
            is_superadmin=True
        )
        db.add(admin)
        db.commit()
        print("[OK] Created default admin: username=admin, password=admin1234 (please change!)")
