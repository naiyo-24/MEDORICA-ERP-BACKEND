from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.monthly_target.asm_monthly_target_models import ASMMonthlyTarget
from models.onboarding.asm_onboarding_models import AreaSalesManager

router = APIRouter(prefix="/monthly-target/asm", tags=["ASM Monthly Target"])


class ASMMonthlyTargetResponseSchema(BaseModel):
	id: int
	asm_id: str
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


@router.post("/post-or-update", response_model=ASMMonthlyTargetResponseSchema, status_code=status.HTTP_201_CREATED)
def create_or_update_monthly_target(
	asm_id: str = Form(...),
	month: int = Form(...),
	year: int = Form(...),
	opening_target_rupees: Optional[float] = Form(None),
	db: Session = Depends(get_db),
):
	_validate_month_year(month, year)

	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")

	if opening_target_rupees is None:
		opening_target_rupees = asm_record.monthly_target_rupees or 0.0

	record = (
		db.query(ASMMonthlyTarget)
		.filter(
			ASMMonthlyTarget.asm_id == asm_id,
			ASMMonthlyTarget.month == month,
			ASMMonthlyTarget.year == year,
		)
		.first()
	)

	if record:
		record.opening_target_rupees = opening_target_rupees
		record.remaining_target_rupees = opening_target_rupees - (record.deducted_target_rupees or 0.0)
	else:
		record = ASMMonthlyTarget(
			asm_id=asm_id,
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


@router.get("/get-all", response_model=list[ASMMonthlyTargetResponseSchema])
def get_all_asm_monthly_targets(db: Session = Depends(get_db)):
	return db.query(ASMMonthlyTarget).all()


@router.get("/get-by-asm/{asm_id}", response_model=list[ASMMonthlyTargetResponseSchema])
def get_monthly_targets_by_asm_id(asm_id: str, db: Session = Depends(get_db)):
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")

	return (
		db.query(ASMMonthlyTarget)
		.filter(ASMMonthlyTarget.asm_id == asm_id)
		.order_by(ASMMonthlyTarget.year.desc(), ASMMonthlyTarget.month.desc())
		.all()
	)


@router.get("/get-by/{asm_id}/{year}/{month}", response_model=ASMMonthlyTargetResponseSchema)
def get_monthly_target_by_asm_year_month(asm_id: str, year: int, month: int, db: Session = Depends(get_db)):
	_validate_month_year(month, year)

	record = (
		db.query(ASMMonthlyTarget)
		.filter(
			ASMMonthlyTarget.asm_id == asm_id,
			ASMMonthlyTarget.year == year,
			ASMMonthlyTarget.month == month,
		)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly target not found")

	return record
