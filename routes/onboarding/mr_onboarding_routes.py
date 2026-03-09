import json
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.onboarding.mr_onbooarding_models import MedicalRepresentative
from services.onboarding.mr.mr_id_generator import generate_mr_id
from services.onboarding.mr.mr_profile_photo_upload import delete_mr_profile_assets, save_mr_profile_photo

router = APIRouter(prefix="/onboarding/mr", tags=["MR Onboarding"])


class MRResponseSchema(BaseModel):
	id: int
	mr_id: str
	full_name: str
	phone_no: str
	alt_phone_no: Optional[str] = None
	email: Optional[str] = None
	address: Optional[str] = None
	joining_date: Optional[date] = None
	password: str
	profile_photo: Optional[str] = None
	bank_name: Optional[str] = None
	bank_account_no: Optional[str] = None
	ifsc_code: Optional[str] = None
	branch_name: Optional[str] = None
	headquarter_assigned: Optional[str] = None
	territories_of_work: Optional[Any] = None
	monthly_target_rupees: Optional[float] = None
	basic_salary_rupees: Optional[float] = None
	daily_allowances_rupees: Optional[float] = None
	hra_rupees: Optional[float] = None
	phone_allowances_rupees: Optional[float] = None
	children_allowances_rupees: Optional[float] = None
	esic_rupees: Optional[float] = None
	total_monthly_compensation_rupees: Optional[float] = None
	active: bool
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


class MRLoginSchema(BaseModel):
	phone_no: str
	password: str

# Helper function to parse territories_of_work into a Python object. Accepts valid JSON or comma-separated strings. Returns None if input is empty.
def _parse_territories_json(territories_of_work: Optional[str]) -> Optional[Any]:
	if territories_of_work is None or territories_of_work.strip() == "":
		return None
	try:
		return json.loads(territories_of_work)
	except json.JSONDecodeError:
		# If not valid JSON, treat as comma-separated string and convert to array
		territories_list = [t.strip() for t in territories_of_work.split(",") if t.strip()]
		return territories_list if territories_list else None

# Create a new MR record. Accepts form data for all fields, including an optional profile photo upload. Returns the created MR details if successful, otherwise appropriate error messages.
@router.post("/post", response_model=MRResponseSchema, status_code=status.HTTP_201_CREATED)
def create_mr(
	full_name: str = Form(...),
	phone_no: str = Form(...),
	password: str = Form(...),
	alt_phone_no: Optional[str] = Form(None),
	email: Optional[str] = Form(None),
	address: Optional[str] = Form(None),
	joining_date: Optional[date] = Form(None),
	bank_name: Optional[str] = Form(None),
	bank_account_no: Optional[str] = Form(None),
	ifsc_code: Optional[str] = Form(None),
	branch_name: Optional[str] = Form(None),
	headquarter_assigned: Optional[str] = Form(None),
	territories_of_work: Optional[str] = Form(None),
	monthly_target_rupees: Optional[float] = Form(None),
	basic_salary_rupees: Optional[float] = Form(None),
	daily_allowances_rupees: Optional[float] = Form(None),
	hra_rupees: Optional[float] = Form(None),
	phone_allowances_rupees: Optional[float] = Form(None),
	children_allowances_rupees: Optional[float] = Form(None),
	esic_rupees: Optional[float] = Form(None),
	total_monthly_compensation_rupees: Optional[float] = Form(None),
	active: bool = Form(True),
	profile_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	try:
		mr_id = generate_mr_id(phone_no)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	existing_mr = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if existing_mr:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MR already exists")

	new_mr = MedicalRepresentative(
		mr_id=mr_id,
		full_name=full_name,
		phone_no=phone_no,
		alt_phone_no=alt_phone_no,
		email=email,
		address=address,
		joining_date=joining_date,
		password=password,
		bank_name=bank_name,
		bank_account_no=bank_account_no,
		ifsc_code=ifsc_code,
		branch_name=branch_name,
		headquarter_assigned=headquarter_assigned,
		territories_of_work=_parse_territories_json(territories_of_work),
		monthly_target_rupees=monthly_target_rupees,
		basic_salary_rupees=basic_salary_rupees,
		daily_allowances_rupees=daily_allowances_rupees,
		hra_rupees=hra_rupees,
		phone_allowances_rupees=phone_allowances_rupees,
		children_allowances_rupees=children_allowances_rupees,
		esic_rupees=esic_rupees,
		total_monthly_compensation_rupees=total_monthly_compensation_rupees,
		active=active,
	)

	if profile_photo is not None:
		try:
			new_mr.profile_photo = save_mr_profile_photo(profile_photo, mr_id, full_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid profile photo") from exc

	db.add(new_mr)
	db.commit()
	db.refresh(new_mr)
	return new_mr

# Update an existing MR record by its MR ID. Accepts form data for all fields, including an optional profile photo upload. Returns the updated MR details if successful, otherwise appropriate error messages.
@router.put("/update-by/{mr_id}", response_model=MRResponseSchema)
def update_mr_by_id(
	mr_id: str,
	full_name: Optional[str] = Form(None),
	phone_no: Optional[str] = Form(None),
	password: Optional[str] = Form(None),
	alt_phone_no: Optional[str] = Form(None),
	email: Optional[str] = Form(None),
	address: Optional[str] = Form(None),
	joining_date: Optional[date] = Form(None),
	bank_name: Optional[str] = Form(None),
	bank_account_no: Optional[str] = Form(None),
	ifsc_code: Optional[str] = Form(None),
	branch_name: Optional[str] = Form(None),
	headquarter_assigned: Optional[str] = Form(None),
	territories_of_work: Optional[str] = Form(None),
	monthly_target_rupees: Optional[float] = Form(None),
	basic_salary_rupees: Optional[float] = Form(None),
	daily_allowances_rupees: Optional[float] = Form(None),
	hra_rupees: Optional[float] = Form(None),
	phone_allowances_rupees: Optional[float] = Form(None),
	children_allowances_rupees: Optional[float] = Form(None),
	esic_rupees: Optional[float] = Form(None),
	total_monthly_compensation_rupees: Optional[float] = Form(None),
	active: Optional[bool] = Form(None),
	profile_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")

	if phone_no is not None:
		try:
			new_mr_id = generate_mr_id(phone_no)
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

		if new_mr_id != record.mr_id:
			existing_with_new_id = (
				db.query(MedicalRepresentative)
				.filter(MedicalRepresentative.mr_id == new_mr_id, MedicalRepresentative.id != record.id)
				.first()
			)
			if existing_with_new_id:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already in use")
			record.mr_id = new_mr_id
		record.phone_no = phone_no

	if full_name is not None:
		record.full_name = full_name
	if password is not None:
		record.password = password
	if alt_phone_no is not None:
		record.alt_phone_no = alt_phone_no
	if email is not None:
		record.email = email
	if address is not None:
		record.address = address
	if joining_date is not None:
		record.joining_date = joining_date
	if bank_name is not None:
		record.bank_name = bank_name
	if bank_account_no is not None:
		record.bank_account_no = bank_account_no
	if ifsc_code is not None:
		record.ifsc_code = ifsc_code
	if branch_name is not None:
		record.branch_name = branch_name
	if headquarter_assigned is not None:
		record.headquarter_assigned = headquarter_assigned
	if territories_of_work is not None:
		record.territories_of_work = _parse_territories_json(territories_of_work)
	if monthly_target_rupees is not None:
		record.monthly_target_rupees = monthly_target_rupees
	if basic_salary_rupees is not None:
		record.basic_salary_rupees = basic_salary_rupees
	if daily_allowances_rupees is not None:
		record.daily_allowances_rupees = daily_allowances_rupees
	if hra_rupees is not None:
		record.hra_rupees = hra_rupees
	if phone_allowances_rupees is not None:
		record.phone_allowances_rupees = phone_allowances_rupees
	if children_allowances_rupees is not None:
		record.children_allowances_rupees = children_allowances_rupees
	if esic_rupees is not None:
		record.esic_rupees = esic_rupees
	if total_monthly_compensation_rupees is not None:
		record.total_monthly_compensation_rupees = total_monthly_compensation_rupees
	if active is not None:
		record.active = active

	if profile_photo is not None:
		final_full_name = full_name if full_name is not None else record.full_name
		try:
			record.profile_photo = save_mr_profile_photo(profile_photo, record.mr_id, final_full_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid profile photo") from exc

	db.commit()
	db.refresh(record)
	return record

# Fetch an MR record by its MR ID. Returns the MR details if found, otherwise a 404 error.
@router.get("/get-by/{mr_id}", response_model=MRResponseSchema)
def get_mr_by_id(mr_id: str, db: Session = Depends(get_db)):
	record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")
	return record

# Fetch all MR records. Returns a list of MR details.
@router.get("/get-all", response_model=list[MRResponseSchema])
def get_all_mr(db: Session = Depends(get_db)):
	return db.query(MedicalRepresentative).all()

# Delete an MR record by its MR ID. Returns a success message on successful deletion.
@router.delete("/delete-by/{mr_id}", status_code=status.HTTP_200_OK)
def delete_mr_by_id(mr_id: str, db: Session = Depends(get_db)):
	record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")

	try:
		delete_mr_profile_assets(record.mr_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete MR profile photo assets",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"MR with id {mr_id} deleted successfully"}

# Login endpoint for MR using phone number and password. Returns basic MR details on successful login.
@router.post("/login", status_code=status.HTTP_200_OK)
def mr_login(payload: MRLoginSchema, db: Session = Depends(get_db)):
	record = (
		db.query(MedicalRepresentative)
		.filter(MedicalRepresentative.phone_no == payload.phone_no)
		.first()
	)

	if not record or record.password != payload.password:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone number or password")

	return {
		"message": "Login successful",
		"mr_id": record.mr_id,
		"full_name": record.full_name,
		"phone_no": record.phone_no,
	}
