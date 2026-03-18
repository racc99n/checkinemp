import hashlib
import json
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from ..utils.timezone import now_th
from ..models.device import RegisteredDevice


def compute_fingerprint_hash(fingerprint_data: str) -> str:
    try:
        data = json.loads(fingerprint_data)
        # Remove volatile fields
        volatile = {"timestamp", "battery", "connection"}
        stable = {k: v for k, v in sorted(data.items()) if k not in volatile}
        canonical = json.dumps(stable, sort_keys=True, ensure_ascii=True)
    except (json.JSONDecodeError, AttributeError):
        canonical = str(fingerprint_data).strip()
    return hashlib.sha256(canonical.encode()).hexdigest()


def validate_device_by_token(device_token: str, db: Session) -> Optional[RegisteredDevice]:
    """ตรวจสอบอุปกรณ์จาก device_token (วิธีหลัก)"""
    return db.query(RegisteredDevice).filter(
        RegisteredDevice.device_token == device_token,
        RegisteredDevice.is_active == True
    ).first()


def validate_device(fingerprint_hash: str, db: Session) -> Optional[RegisteredDevice]:
    """ตรวจสอบอุปกรณ์จาก fingerprint_hash (fallback)"""
    return db.query(RegisteredDevice).filter(
        RegisteredDevice.fingerprint_hash == fingerprint_hash,
        RegisteredDevice.is_active == True
    ).first()


def update_last_seen(device: RegisteredDevice, db: Session):
    device.last_seen_at = now_th()
    db.commit()


def generate_device_token() -> str:
    """สร้าง device token ใหม่ (UUID v4)"""
    return str(uuid.uuid4())


def register_device(device_name: str, fingerprint: str, location: str, db: Session) -> RegisteredDevice:
    fp_stripped = fingerprint.strip()
    # ถ้าเป็น 64-char hex แล้ว (frontend pre-computed SHA256) ให้ใช้ตรงๆ ไม่ต้อง hash ซ้ำ
    if len(fp_stripped) == 64 and all(c in '0123456789abcdef' for c in fp_stripped.lower()):
        fingerprint_hash = fp_stripped.lower()
    else:
        fingerprint_hash = compute_fingerprint_hash(fingerprint)

    device = RegisteredDevice(
        device_name=device_name,
        fingerprint_hash=fingerprint_hash,
        location=location,
        device_token=generate_device_token()
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def activate_device_for_browser(device_id: int, db: Session) -> Optional[RegisteredDevice]:
    """สร้าง device token ใหม่สำหรับอุปกรณ์ที่เลือก (ใช้เมื่อ activate จากหน้า check-in)"""
    device = db.query(RegisteredDevice).filter(
        RegisteredDevice.id == device_id,
        RegisteredDevice.is_active == True
    ).first()
    if not device:
        return None
    device.device_token = generate_device_token()
    device.last_seen_at = now_th()
    db.commit()
    db.refresh(device)
    return device


def create_and_activate_device(device_name: str, location: str, db: Session) -> RegisteredDevice:
    """สร้างอุปกรณ์ใหม่และ activate ทันที (ใช้จากหน้า check-in)"""
    device = RegisteredDevice(
        device_name=device_name,
        fingerprint_hash="",
        location=location,
        device_token=generate_device_token()
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device
