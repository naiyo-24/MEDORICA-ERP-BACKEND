import json
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.doctor_network.mr_doctor_network_models import MRDoctorNetwork
from models.onboarding.mr_onbooarding_models import MedicalRepresentative
from services.doctor_network.mr.mr_doctor_id_generator import generate_mr_doctor_id
from services.doctor_network.mr.mr_doctor_photo_upload import delete_mr_doctor_assets, save_mr_doctor_photo

router = APIRouter(prefix="/doctor-network/mr", tags=["MR Doctor Network"])


class MRDoctorNetworkResponseSchema(BaseModel):
	id: int
	doctor_id: str
	mr_id: str
	doctor_name: str
	doctor_birthday: Optional[date] = None
	doctor_specialization: Optional[str] = None
	doctor_qualification: Optional[str] = None
	doctor_experience: Optional[str] = None
	doctor_description: Optional[str] = None
	doctor_photo: Optional[str] = None
	doctor_chambers: Optional[Any] = None
	doctor_phone_no: str
	doctor_email: Optional[str] = None
	doctor_address: Optional[str] = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Parse doctor chambers from JSON string input.
def _parse_doctor_chambers_json(doctor_chambers: Optional[str]) -> Optional[Any]:
	if doctor_chambers is None or doctor_chambers.strip() == "":
		return None
	try:
		parsed = json.loads(doctor_chambers)
	except json.JSONDecodeError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_chambers must be valid JSON") from exc

	if parsed is None:
		return None

	if not isinstance(parsed, list):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_chambers must be a JSON array")

	for chamber in parsed:
		if not isinstance(chamber, dict):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Each doctor chamber must be a JSON object",
			)

	return parsed


# Create a doctor record for an MR.
@router.post("/post", response_model=MRDoctorNetworkResponseSchema, status_code=status.HTTP_201_CREATED)
def create_mr_doctor(
	mr_id: str = Form(...),
	doctor_name: str = Form(...),
	doctor_phone_no: str = Form(...),
	doctor_birthday: Optional[date] = Form(None),
	doctor_specialization: Optional[str] = Form(None),
	doctor_qualification: Optional[str] = Form(None),
	doctor_experience: Optional[str] = Form(None),
	doctor_description: Optional[str] = Form(None),
	doctor_chambers: Optional[str] = Form(None),
	doctor_email: Optional[str] = Form(None),
	doctor_address: Optional[str] = Form(None),
	doctor_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")

	existing_doctor_for_mr = (
		db.query(MRDoctorNetwork)
		.filter(MRDoctorNetwork.mr_id == mr_id, MRDoctorNetwork.doctor_phone_no == doctor_phone_no)
		.first()
	)
	if existing_doctor_for_mr:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Doctor already exists for this MR",
		)

	try:
		generated_doctor_id = generate_mr_doctor_id(mr_id, doctor_phone_no)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	existing_doctor_id = db.query(MRDoctorNetwork).filter(MRDoctorNetwork.doctor_id == generated_doctor_id).first()
	if existing_doctor_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor ID already exists")

	new_doctor = MRDoctorNetwork(
		doctor_id=generated_doctor_id,
		mr_id=mr_id,
		doctor_name=doctor_name,
		doctor_birthday=doctor_birthday,
		doctor_specialization=doctor_specialization,
		doctor_qualification=doctor_qualification,
		doctor_experience=doctor_experience,
		doctor_description=doctor_description,
		doctor_chambers=_parse_doctor_chambers_json(doctor_chambers),
		doctor_phone_no=doctor_phone_no,
		doctor_email=doctor_email,
		doctor_address=doctor_address,
	)

	if doctor_photo is not None:
		try:
			new_doctor.doctor_photo = save_mr_doctor_photo(doctor_photo, generated_doctor_id, doctor_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid doctor photo") from exc

	db.add(new_doctor)
	db.commit()
	db.refresh(new_doctor)
	return new_doctor


# Fetch all doctors in MR doctor network.
@router.get("/get-all", response_model=list[MRDoctorNetworkResponseSchema])
def get_all_mr_doctors(db: Session = Depends(get_db)):
	return db.query(MRDoctorNetwork).all()


# Fetch all doctors linked to a specific MR ID.
@router.get("/get-by-mr/{mr_id}", response_model=list[MRDoctorNetworkResponseSchema])
def get_doctors_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
	mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")
	return db.query(MRDoctorNetwork).filter(MRDoctorNetwork.mr_id == mr_id).all()


# Fetch a specific doctor by MR ID and doctor ID.
@router.get("/get-by/{mr_id}/{doctor_id}", response_model=MRDoctorNetworkResponseSchema)
def get_doctor_by_mr_and_doctor_id(mr_id: str, doctor_id: str, db: Session = Depends(get_db)):
	record = (
		db.query(MRDoctorNetwork)
		.filter(MRDoctorNetwork.mr_id == mr_id, MRDoctorNetwork.doctor_id == doctor_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
	return record


# Update a doctor by MR ID and doctor ID.
@router.put("/update-by/{mr_id}/{doctor_id}", response_model=MRDoctorNetworkResponseSchema)
def update_doctor_by_mr_and_doctor_id(
	mr_id: str,
	doctor_id: str,
	doctor_name: Optional[str] = Form(None),
	doctor_phone_no: Optional[str] = Form(None),
	doctor_birthday: Optional[date] = Form(None),
	doctor_specialization: Optional[str] = Form(None),
	doctor_qualification: Optional[str] = Form(None),
	doctor_experience: Optional[str] = Form(None),
	doctor_description: Optional[str] = Form(None),
	doctor_chambers: Optional[str] = Form(None),
	doctor_email: Optional[str] = Form(None),
	doctor_address: Optional[str] = Form(None),
	doctor_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = (
		db.query(MRDoctorNetwork)
		.filter(MRDoctorNetwork.mr_id == mr_id, MRDoctorNetwork.doctor_id == doctor_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

	if doctor_phone_no is not None:
		existing_for_phone = (
			db.query(MRDoctorNetwork)
			.filter(
				MRDoctorNetwork.mr_id == mr_id,
				MRDoctorNetwork.doctor_phone_no == doctor_phone_no,
				MRDoctorNetwork.id != record.id,
			)
			.first()
		)
		if existing_for_phone:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor already exists for this MR")

		try:
			new_doctor_id = generate_mr_doctor_id(mr_id, doctor_phone_no)
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

		if new_doctor_id != record.doctor_id:
			existing_doctor_id = (
				db.query(MRDoctorNetwork)
				.filter(MRDoctorNetwork.doctor_id == new_doctor_id, MRDoctorNetwork.id != record.id)
				.first()
			)
			if existing_doctor_id:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor ID already in use")
			record.doctor_id = new_doctor_id

		record.doctor_phone_no = doctor_phone_no

	if doctor_name is not None:
		record.doctor_name = doctor_name
	if doctor_birthday is not None:
		record.doctor_birthday = doctor_birthday
	if doctor_specialization is not None:
		record.doctor_specialization = doctor_specialization
	if doctor_qualification is not None:
		record.doctor_qualification = doctor_qualification
	if doctor_experience is not None:
		record.doctor_experience = doctor_experience
	if doctor_description is not None:
		record.doctor_description = doctor_description
	if doctor_chambers is not None:
		record.doctor_chambers = _parse_doctor_chambers_json(doctor_chambers)
	if doctor_email is not None:
		record.doctor_email = doctor_email
	if doctor_address is not None:
		record.doctor_address = doctor_address

	if doctor_photo is not None:
		photo_doctor_name = doctor_name if doctor_name is not None else record.doctor_name
		try:
			record.doctor_photo = save_mr_doctor_photo(doctor_photo, record.doctor_id, photo_doctor_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid doctor photo") from exc

	db.commit()
	db.refresh(record)
	return record


# Update a doctor by doctor ID only.
@router.put("/update-by-doctor/{doctor_id}", response_model=MRDoctorNetworkResponseSchema)
def update_doctor_by_doctor_id(
	doctor_id: str,
	doctor_name: Optional[str] = Form(None),
	doctor_phone_no: Optional[str] = Form(None),
	doctor_birthday: Optional[date] = Form(None),
	doctor_specialization: Optional[str] = Form(None),
	doctor_qualification: Optional[str] = Form(None),
	doctor_experience: Optional[str] = Form(None),
	doctor_description: Optional[str] = Form(None),
	doctor_chambers: Optional[str] = Form(None),
	doctor_email: Optional[str] = Form(None),
	doctor_address: Optional[str] = Form(None),
	doctor_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = db.query(MRDoctorNetwork).filter(MRDoctorNetwork.doctor_id == doctor_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

	return update_doctor_by_mr_and_doctor_id(
		mr_id=record.mr_id,
		doctor_id=record.doctor_id,
		doctor_name=doctor_name,
		doctor_phone_no=doctor_phone_no,
		doctor_birthday=doctor_birthday,
		doctor_specialization=doctor_specialization,
		doctor_qualification=doctor_qualification,
		doctor_experience=doctor_experience,
		doctor_description=doctor_description,
		doctor_chambers=doctor_chambers,
		doctor_email=doctor_email,
		doctor_address=doctor_address,
		doctor_photo=doctor_photo,
		db=db,
	)


# Delete a doctor by doctor ID and remove associated photo assets.
@router.delete("/delete-by/{doctor_id}", status_code=status.HTTP_200_OK)
def delete_doctor_by_doctor_id(doctor_id: str, db: Session = Depends(get_db)):
	record = db.query(MRDoctorNetwork).filter(MRDoctorNetwork.doctor_id == doctor_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

	try:
		delete_mr_doctor_assets(record.doctor_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete doctor photo assets",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Doctor with id {doctor_id} deleted successfully"}
