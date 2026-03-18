from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime
from typing import Optional, List
import csv
import io
from ..database import get_db
from ..models.attendance import AttendanceRecord
from ..models.employee import Employee
from ..utils.timezone import now_th
from ..models.device import RegisteredDevice
from ..schemas.attendance import AttendanceResponse, AttendanceUpdate
from ..middleware.auth_guard import require_admin

router = APIRouter(prefix="/api/admin/attendance", tags=["attendance"])


def _record_to_response(r: AttendanceRecord) -> dict:
    return {
        "id": r.id,
        "employee_id": r.employee_id,
        "employee_name": r.employee.full_name if r.employee else "",
        "employee_code": r.employee.employee_code if r.employee else "",
        "department": r.employee.department if r.employee else "",
        "device_name": r.device.device_name if r.device else "ไม่ทราบ",
        "check_in_at": r.check_in_at,
        "check_out_at": r.check_out_at,
        "status": r.status,
        "notes": r.notes,
        "work_date": r.work_date,
        "face_confidence": r.face_confidence,
    }


@router.get("")
def list_attendance(
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    employee_id: Optional[int] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    q = db.query(AttendanceRecord).options(
        joinedload(AttendanceRecord.employee),
        joinedload(AttendanceRecord.device)
    )
    if date_from:
        q = q.filter(AttendanceRecord.work_date >= date_from)
    if date_to:
        q = q.filter(AttendanceRecord.work_date <= date_to)
    if employee_id:
        q = q.filter(AttendanceRecord.employee_id == employee_id)
    if department:
        q = q.join(Employee).filter(Employee.department == department)
    if status:
        q = q.filter(AttendanceRecord.status == status)

    total = q.count()
    records = q.order_by(AttendanceRecord.work_date.desc(), AttendanceRecord.check_in_at.desc()) \
               .offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "records": [_record_to_response(r) for r in records]
    }


@router.get("/summary")
def get_summary(
    month: Optional[str] = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    if not month:
        month = now_th().strftime("%Y-%m")

    q = db.query(AttendanceRecord).filter(
        AttendanceRecord.work_date.startswith(month)
    )
    records = q.all()
    total = len(records)
    present = sum(1 for r in records if r.status == "present")
    late = sum(1 for r in records if r.status == "late")
    today_str = now_th().date().isoformat()
    today_count = sum(1 for r in records if r.work_date == today_str)

    return {
        "month": month,
        "total_records": total,
        "present": present,
        "late": late,
        "today_count": today_count
    }


@router.get("/export/csv")
def export_csv(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    q = db.query(AttendanceRecord).options(
        joinedload(AttendanceRecord.employee),
        joinedload(AttendanceRecord.device)
    )
    if date_from:
        q = q.filter(AttendanceRecord.work_date >= date_from)
    if date_to:
        q = q.filter(AttendanceRecord.work_date <= date_to)
    if department:
        q = q.join(Employee).filter(Employee.department == department)

    records = q.order_by(AttendanceRecord.work_date, AttendanceRecord.check_in_at).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "วันที่", "รหัสพนักงาน", "ชื่อ-สกุล", "แผนก",
        "เวลาเข้างาน", "เวลาออกงาน", "สถานะ", "อุปกรณ์", "หมายเหตุ"
    ])
    for r in records:
        emp = r.employee
        writer.writerow([
            r.work_date,
            emp.employee_code if emp else "",
            emp.full_name if emp else "",
            emp.department if emp else "",
            r.check_in_at.strftime("%H:%M:%S") if r.check_in_at else "",
            r.check_out_at.strftime("%H:%M:%S") if r.check_out_at else "",
            r.status,
            r.device.device_name if r.device else "",
            r.notes
        ])

    output.seek(0)
    filename = f"attendance_{date_from or 'all'}_{date_to or 'all'}.csv"
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.patch("/{record_id}")
def update_record(
    record_id: int,
    req: AttendanceUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="ไม่พบบันทึก")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(record, field, value)
    db.commit()
    return {"message": "อัปเดตสำเร็จ"}
