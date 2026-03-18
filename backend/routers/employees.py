from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models.employee import Employee
from ..schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EnrollFaceRequest
from ..services.face_service import get_face_service
from ..middleware.auth_guard import require_admin, require_superadmin
from typing import List, Optional

router = APIRouter(prefix="/api/admin/employees", tags=["employees"])


def _emp_to_response(emp: Employee) -> dict:
    d = {
        "id": emp.id,
        "full_name": emp.full_name,
        "employee_code": emp.employee_code,
        "department": emp.department,
        "position": emp.position,
        "shift_id": emp.shift_id,
        "shift_name": emp.shift.name if emp.shift else None,
        "telegram_chat_id": emp.telegram_chat_id,
        "face_encoding_path": emp.face_encoding_path,
        "is_active": emp.is_active,
        "created_at": emp.created_at,
    }
    return d


@router.get("")
def list_employees(
    department: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    q = db.query(Employee).options(joinedload(Employee.shift))
    if active_only:
        q = q.filter(Employee.is_active == True)
    if department:
        q = q.filter(Employee.department == department)
    emps = q.order_by(Employee.employee_code).all()
    return [_emp_to_response(e) for e in emps]


@router.post("", response_model=EmployeeResponse)
def create_employee(req: EmployeeCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    existing = db.query(Employee).filter(Employee.employee_code == req.employee_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"รหัสพนักงาน {req.employee_code} มีอยู่แล้ว")
    emp = Employee(**req.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.get("/{emp_id}")
def get_employee(emp_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    emp = db.query(Employee).options(joinedload(Employee.shift)).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="ไม่พบพนักงาน")
    return _emp_to_response(emp)


@router.put("/{emp_id}", response_model=EmployeeResponse)
def update_employee(
    emp_id: int,
    req: EmployeeUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="ไม่พบพนักงาน")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(emp, field, value)
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="ไม่พบพนักงาน")
    emp.is_active = False
    db.commit()
    return {"message": f"ปิดใช้งานพนักงาน {emp.full_name} แล้ว"}


@router.post("/{emp_id}/enroll")
def enroll_face(
    emp_id: int,
    req: EnrollFaceRequest,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    emp = db.query(Employee).filter(Employee.id == emp_id, Employee.is_active == True).first()
    if not emp:
        raise HTTPException(status_code=404, detail="ไม่พบพนักงาน")
    if len(req.images_b64) < 3:
        raise HTTPException(status_code=400, detail="ต้องการรูปภาพอย่างน้อย 3 รูป")

    try:
        face_svc = get_face_service()
        path = face_svc.enroll(emp_id, req.images_b64)
        emp.face_encoding_path = path
        db.commit()
        return {"message": f"บันทึกข้อมูลใบหน้าของ {emp.full_name} สำเร็จ", "encoding_path": path}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{emp_id}/face")
def remove_face(emp_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="ไม่พบพนักงาน")
    get_face_service().remove(emp_id)
    emp.face_encoding_path = None
    db.commit()
    return {"message": "ลบข้อมูลใบหน้าแล้ว"}
