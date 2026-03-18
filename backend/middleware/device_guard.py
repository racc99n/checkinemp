from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.device import RegisteredDevice
from ..services import device_service
from ..services import telegram_service
from ..utils.timezone import now_th
from typing import Optional


async def require_registered_device(
    x_device_token: Optional[str] = Header(None),
    x_device_fingerprint: Optional[str] = Header(None),
    x_device_fingerprint_hash: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> RegisteredDevice:
    device = None

    # วิธีหลัก: ตรวจสอบจาก device token (เสถียรกว่า fingerprint)
    if x_device_token:
        device = device_service.validate_device_by_token(x_device_token, db)

    # Fallback: ถ้าไม่มี token ให้ลอง fingerprint hash
    if not device and x_device_fingerprint_hash:
        device = device_service.validate_device(x_device_fingerprint_hash, db)

    # Fallback: ถ้าส่ง raw fingerprint มาให้ลอง hash แล้วตรวจ
    if not device and x_device_fingerprint:
        recalculated_hash = device_service.compute_fingerprint_hash(x_device_fingerprint)
        device = device_service.validate_device(recalculated_hash, db)

    if not device:
        if not x_device_token and not x_device_fingerprint and not x_device_fingerprint_hash:
            raise HTTPException(
                status_code=403,
                detail="ไม่พบข้อมูลอุปกรณ์ กรุณา activate อุปกรณ์ก่อนใช้งาน"
            )
        telegram_service.notify_blocked_device(
            x_device_token or x_device_fingerprint_hash or "unknown",
            now_th()
        )
        raise HTTPException(
            status_code=403,
            detail="อุปกรณ์นี้ยังไม่ได้รับการลงทะเบียน กรุณา activate อุปกรณ์หรือติดต่อผู้ดูแลระบบ"
        )

    device_service.update_last_seen(device, db)
    return device
