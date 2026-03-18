from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.device import RegisteredDevice
from ..schemas.device import (
    DeviceResponse, DeviceUpdate, DeviceRegisterRequest,
    DeviceActivateRequest, DeviceActivateResponse, DeviceTokenValidateResponse
)
from ..services.device_service import register_device, validate_device_by_token
from ..services.auth_service import authenticate_admin
from ..middleware.auth_guard import require_admin

router = APIRouter(prefix="/api", tags=["devices"])


# === Admin endpoints ===

@router.get("/admin/devices", response_model=List[DeviceResponse])
def list_devices(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(RegisteredDevice).order_by(RegisteredDevice.registered_at.desc()).all()


@router.post("/admin/devices", response_model=DeviceResponse)
def create_device(req: DeviceRegisterRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    try:
        return register_device(req.device_name, req.fingerprint, req.location, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/admin/devices/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    req: DeviceUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    device = db.query(RegisteredDevice).filter(RegisteredDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="ไม่พบอุปกรณ์")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/admin/devices/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    device = db.query(RegisteredDevice).filter(RegisteredDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="ไม่พบอุปกรณ์")
    db.delete(device)
    db.commit()
    return {"message": f"ลบอุปกรณ์ {device.device_name} แล้ว"}


@router.post("/admin/devices/get-fingerprint-hash")
def get_fingerprint_hash(fingerprint: str, _=Depends(require_admin)):
    from ..services.device_service import compute_fingerprint_hash
    return {"hash": compute_fingerprint_hash(fingerprint)}


@router.post("/admin/devices/{device_id}/regenerate-token", response_model=DeviceResponse)
def regenerate_token(device_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """สร้าง device token ใหม่ (ใช้เมื่อต้องการ re-activate อุปกรณ์)"""
    from ..services.device_service import activate_device_for_browser
    device = activate_device_for_browser(device_id, db)
    if not device:
        raise HTTPException(status_code=404, detail="ไม่พบอุปกรณ์")
    return device


# === Public endpoints (ใช้จากหน้า check-in) ===

@router.post("/devices/activate", response_model=DeviceActivateResponse)
def activate_device(req: DeviceActivateRequest, db: Session = Depends(get_db)):
    """
    Activate อุปกรณ์จากหน้า check-in
    ต้องใส่ username/password ของ admin เพื่อยืนยันตัวตน
    สามารถเลือก device_id ที่มีอยู่ หรือสร้างใหม่โดยใส่ device_name
    """
    # ตรวจสอบสิทธิ์ admin
    admin = authenticate_admin(req.username, req.password, db)
    if not admin:
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    from ..services.device_service import activate_device_for_browser, create_and_activate_device

    if req.device_id:
        # เลือกอุปกรณ์ที่มีอยู่แล้ว
        device = activate_device_for_browser(req.device_id, db)
        if not device:
            raise HTTPException(status_code=404, detail="ไม่พบอุปกรณ์ หรืออุปกรณ์ถูกปิดใช้งาน")
    elif req.device_name:
        # สร้างอุปกรณ์ใหม่
        device = create_and_activate_device(
            req.device_name,
            req.location or "",
            db
        )
    else:
        raise HTTPException(status_code=400, detail="กรุณาเลือกอุปกรณ์หรือใส่ชื่ออุปกรณ์ใหม่")

    return DeviceActivateResponse(
        device_token=device.device_token,
        device_name=device.device_name,
        device_id=device.id,
        message=f"Activate อุปกรณ์ '{device.device_name}' สำเร็จ"
    )


@router.get("/devices/validate-token", response_model=DeviceTokenValidateResponse)
def validate_token(token: str, db: Session = Depends(get_db)):
    """ตรวจสอบว่า device token ยังใช้ได้อยู่หรือไม่"""
    device = validate_device_by_token(token, db)
    if device:
        return DeviceTokenValidateResponse(
            valid=True,
            device_name=device.device_name,
            device_id=device.id
        )
    return DeviceTokenValidateResponse(valid=False, device_name=None, device_id=None)


@router.get("/devices/list-for-activate")
def list_devices_for_activate(username: str, password: str, db: Session = Depends(get_db)):
    """ดึงรายชื่ออุปกรณ์สำหรับเลือก activate (ต้องใส่ admin credentials)"""
    admin = authenticate_admin(username, password, db)
    if not admin:
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    devices = db.query(RegisteredDevice).filter(
        RegisteredDevice.is_active == True
    ).order_by(RegisteredDevice.device_name).all()

    return [
        {"id": d.id, "device_name": d.device_name, "location": d.location}
        for d in devices
    ]
