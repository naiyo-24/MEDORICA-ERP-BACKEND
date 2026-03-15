from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.monthly_target.mr_monthly_target_models import MRMonthlyTarget
from models.onboarding.mr_onbooarding_models import MedicalRepresentative

router = APIRouter(prefix="/monthly-target/mr", tags=["MR Monthly Target"])

class MRMonthlyTargetResponseSchema(BaseModel):
    id: int
    mr_id: str
    month: int
    year: int
    opening_target_rupees: float
    deducted_target_rupees: float
    remaining_target_rupees: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

def _validate_month_year(month: int, year: int) -> None:
    if month < 1 or month > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="month must be between 1 and 12")
    if year < 2000 or year > 3000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="year must be between 2000 and 3000")

@router.post("/post-or-update", response_model=MRMonthlyTargetResponseSchema, status_code=status.HTTP_201_CREATED)
def create_or_update_monthly_target(
    mr_id: str = Form(...),
    month: int = Form(...),
    year: int = Form(...),
    opening_target_rupees: Optional[float] = Form(None),
    db: Session = Depends(get_db),
):
    _validate_month_year(month, year)
    mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
    if not mr_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")
    if opening_target_rupees is None:
        opening_target_rupees = mr_record.monthly_target_rupees or 0.0
    record = (
        db.query(MRMonthlyTarget)
        .filter(
            MRMonthlyTarget.mr_id == mr_id,
            MRMonthlyTarget.month == month,
            MRMonthlyTarget.year == year,
        )
        .first()
    )
    if record:
        record.opening_target_rupees = opening_target_rupees
        record.remaining_target_rupees = opening_target_rupees - (record.deducted_target_rupees or 0.0)
    else:
        record = MRMonthlyTarget(
            mr_id=mr_id,
            month=month,
            year=year,
            opening_target_rupees=opening_target_rupees,
            deducted_target_rupees=0.0,
            remaining_target_rupees=opening_target_rupees,
        )
        db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/get-all", response_model=list[MRMonthlyTargetResponseSchema])
def get_all_mr_monthly_targets(db: Session = Depends(get_db)):
    return db.query(MRMonthlyTarget).all()

@router.get("/get-by-mr/{mr_id}", response_model=list[MRMonthlyTargetResponseSchema])
def get_monthly_targets_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
    mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
    if not mr_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")
    return (
        db.query(MRMonthlyTarget)
        .filter(MRMonthlyTarget.mr_id == mr_id)
        .order_by(MRMonthlyTarget.year.desc(), MRMonthlyTarget.month.desc())
        .all()
    )

@router.get("/get-by/{mr_id}/{year}/{month}", response_model=MRMonthlyTargetResponseSchema)
def get_monthly_target_by_mr_year_month(mr_id: str, year: int, month: int, db: Session = Depends(get_db)):
    _validate_month_year(month, year)
    record = (
        db.query(MRMonthlyTarget)
        .filter(
            MRMonthlyTarget.mr_id == mr_id,
            MRMonthlyTarget.year == year,
            MRMonthlyTarget.month == month,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly target not found")
    return record
