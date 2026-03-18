from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.admin import AdminUser
from ..services.auth_service import decode_token
from typing import Optional


async def require_admin(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> AdminUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบ")

    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token ไม่ถูกต้องหรือหมดอายุ")

    admin_id = payload.get("sub")
    admin = db.query(AdminUser).filter(
        AdminUser.id == int(admin_id),
        AdminUser.is_active == True
    ).first()
    if not admin:
        raise HTTPException(status_code=401, detail="ไม่พบบัญชีผู้ใช้")
    return admin


async def require_superadmin(admin: AdminUser = Depends(require_admin)) -> AdminUser:
    if not admin.is_superadmin:
        raise HTTPException(status_code=403, detail="ต้องการสิทธิ์ superadmin")
    return admin
