from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.shift import Shift
from ..schemas.shift import ShiftCreate, ShiftUpdate, ShiftResponse
from ..middleware.auth_guard import require_admin

router = APIRouter(prefix="/api/admin/shifts", tags=["shifts"])


@router.get("", response_model=List[ShiftResponse])
def list_shifts(
    active_only: bool = False,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    q = db.query(Shift)
    if active_only:
        q = q.filter(Shift.is_active == True)
    return q.order_by(Shift.id).all()


@router.post("", response_model=ShiftResponse)
def create_shift(
    req: ShiftCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    existing = db.query(Shift).filter(Shift.name == req.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"กะ '{req.name}' มีอยู่แล้ว")
    shift = Shift(**req.model_dump())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.get("/{shift_id}", response_model=ShiftResponse)
def get_shift(shift_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="ไม่พบกะงาน")
    return shift


@router.put("/{shift_id}", response_model=ShiftResponse)
def update_shift(
    shift_id: int,
    req: ShiftUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="ไม่พบกะงาน")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(shift, field, value)
    db.commit()
    db.refresh(shift)
    return shift


@router.delete("/{shift_id}")
def delete_shift(shift_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="ไม่พบกะงาน")
    shift.is_active = False
    db.commit()
    return {"message": f"ปิดใช้งานกะ '{shift.name}' แล้ว"}


# --- Public endpoint (ไม่ต้อง auth) สำหรับ frontend dropdown ---
@router.get("/public/list", response_model=List[ShiftResponse])
def list_shifts_public(db: Session = Depends(get_db)):
    return db.query(Shift).filter(Shift.is_active == True).order_by(Shift.id).all()
