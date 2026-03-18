from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from ..database import get_db
from ..utils.timezone import now_th
from ..models.attendance import AttendanceRecord
from ..models.employee import Employee
from ..models.shift import Shift
from ..models.device import RegisteredDevice
from ..schemas.attendance import CheckInRequest, CheckInResponse
from ..services.face_service import get_face_service
from ..services import telegram_service
from ..middleware.device_guard import require_registered_device
from ..config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["checkin"])


def _is_late(check_in_time: datetime, employee: Employee, db: Session) -> bool:
    """ตรวจสอบว่าเข้างานสายหรือไม่ โดยดูจากกะของพนักงาน"""
    shift = None
    if employee.shift_id:
        shift = db.query(Shift).filter(Shift.id == employee.shift_id, Shift.is_active == True).first()

    if shift:
        shift_h, shift_m = map(int, shift.start_time.split(":"))
        threshold_minutes = shift.late_threshold_minutes
    else:
        # Fallback: ใช้ค่าจาก config (กรณียังไม่กำหนดกะ)
        shift_h, shift_m = map(int, settings.SHIFT_START_TIME.split(":"))
        threshold_minutes = settings.LATE_THRESHOLD_MINUTES

    total_minutes = shift_m + threshold_minutes
    extra_hours = total_minutes // 60
    final_minutes = total_minutes % 60

    threshold = check_in_time.replace(
        hour=shift_h + extra_hours, minute=final_minutes,
        second=0, microsecond=0
    )
    return check_in_time > threshold


@router.post("/checkin", response_model=CheckInResponse)
def checkin(
    req: CheckInRequest,
    device: RegisteredDevice = Depends(require_registered_device),
    db: Session = Depends(get_db)
):
    face_svc = get_face_service()
    employee_id, confidence = face_svc.identify(req.image_b64)

    if not employee_id:
        telegram_service.notify_unknown_face(
            device_name=device.device_name,
            timestamp=now_th(),
            photo_b64=req.image_b64
        )
        raise HTTPException(
            status_code=404,
            detail="ไม่พบใบหน้าในระบบ กรุณาติดต่อผู้ดูแลระบบ"
        )

    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.is_active == True
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลพนักงาน")

    now = now_th()
    today = now.date().isoformat()

    open_record = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee_id,
        AttendanceRecord.work_date == today,
        AttendanceRecord.check_out_at == None
    ).first()

    if open_record:
        # Check-out
        open_record.check_out_at = now
        open_record.check_out_photo_path = req.image_b64[:200]
        db.commit()

        telegram_service.notify_check_out(
            employee_name=employee.full_name,
            employee_code=employee.employee_code,
            device_name=device.device_name,
            check_in_at=open_record.check_in_at,
            check_out_at=now,
            employee_chat_id=employee.telegram_chat_id
        )
        return CheckInResponse(
            success=True,
            action="check_out",
            employee_name=employee.full_name,
            employee_code=employee.employee_code,
            timestamp=now,
            status=open_record.status,
            message=f"บันทึกการออกงานสำเร็จ ✅"
        )
    else:
        # Check-in
        late = _is_late(now, employee, db)
        status = "late" if late else "present"

        # Check if already checked in + out today (second visit = additional check-in)
        existing_today = db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.work_date == today
        ).count()

        notes = ""
        if existing_today > 0:
            notes = f"การบันทึกครั้งที่ {existing_today + 1} ของวันนี้"
        if late:
            notes += " | เข้างานสาย"

        record = AttendanceRecord(
            employee_id=employee_id,
            device_id=device.id,
            check_in_at=now,
            face_confidence=confidence,
            status=status,
            notes=notes.strip(" |"),
            work_date=today,
            check_in_photo_path=req.image_b64[:200]
        )
        db.add(record)
        db.commit()

        telegram_service.notify_check_in(
            employee_name=employee.full_name,
            employee_code=employee.employee_code,
            device_name=device.device_name,
            timestamp=now,
            status=status,
            employee_chat_id=employee.telegram_chat_id,
            confidence=confidence
        )

        msg = "บันทึกการเข้างานสำเร็จ ✅"
        if late:
            msg += " (สาย)"

        return CheckInResponse(
            success=True,
            action="check_in",
            employee_name=employee.full_name,
            employee_code=employee.employee_code,
            timestamp=now,
            status=status,
            message=msg
        )


@router.get("/health")
def health():
    return {"status": "ok", "timestamp": now_th().isoformat()}
