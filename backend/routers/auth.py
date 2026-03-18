from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.auth import LoginRequest, TokenResponse, AdminCreate
from ..services.auth_service import authenticate_admin, create_access_token, hash_password
from ..models.admin import AdminUser
from ..middleware.auth_guard import require_admin, require_superadmin
from datetime import timedelta
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    admin = authenticate_admin(req.username, req.password, db)
    if not admin:
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    token = create_access_token(
        {"sub": str(admin.id)},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        admin_name=admin.full_name or admin.username,
        is_superadmin=admin.is_superadmin
    )


@router.get("/me")
def get_me(admin: AdminUser = Depends(require_admin)):
    return {
        "id": admin.id,
        "username": admin.username,
        "full_name": admin.full_name,
        "is_superadmin": admin.is_superadmin
    }


@router.post("/admins", dependencies=[Depends(require_superadmin)])
def create_admin(req: AdminCreate, db: Session = Depends(get_db)):
    existing = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้นี้มีอยู่แล้ว")
    admin = AdminUser(
        username=req.username,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        is_superadmin=req.is_superadmin
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return {"id": admin.id, "username": admin.username, "message": "สร้างบัญชีสำเร็จ"}


@router.put("/admins/password")
def change_password(
    old_password: str,
    new_password: str,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    from ..services.auth_service import verify_password
    if not verify_password(old_password, admin.hashed_password):
        raise HTTPException(status_code=400, detail="รหัสผ่านเดิมไม่ถูกต้อง")
    admin.hashed_password = hash_password(new_password)
    db.commit()
    return {"message": "เปลี่ยนรหัสผ่านสำเร็จ"}
