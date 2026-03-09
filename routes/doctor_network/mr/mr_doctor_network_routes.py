import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.doctor_network.mr.mr_doctor_network_models import MRDoctorNetwork
from models.onboarding.mr_onbooarding_models import MedicalRepresentative
from services.doctor_network.mr.mr_doctor_network_id_generator import generate_doctor_id
from services.doctor_network.mr.mr_doctor_photo_upload import (
	delete_doctor_profile_assets,
	save_doctor_profile_photo,
)

router = APIRouter(prefix="/doctor-network/mr", tags=["MR Doctor Network"])


class MRDoctorResponseSchema(BaseModel):
	id: int
	mr_id: str
	doctor_id: str
	doctor_name: str
	phone_no: str
	email: Optional[str] = None
	description: Optional[str] = None
	address: Optional[str] = None
	qualification: Optional[str] = None
	specialization: Optional[str] = None
	experience: Optional[str] = None
	chambers: Optional[Any] = None
	profile_photo: Optional[str] = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True

# Utility function to parse JSON fields from form data, treating empty or missing values as None.
def _parse_json_or_none(raw_value: Optional[str], field_name: str) -> Optional[Any]:
	if raw_value is None or raw_value.strip() == "":
		return None
	try:
		return json.loads(raw_value)
	except json.JSONDecodeError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"{field_name} must be valid JSON",
		) from exc


# Create a doctor record under an MR's network, with optional profile photo upload.
@router.post("/post-by-mr/{mr_id}", response_model=MRDoctorResponseSchema, status_code=status.HTTP_201_CREATED)
def create_doctor_by_mr_id(
	mr_id: str,
	doctor_name: str = Form(...),
	phone_no: str = Form(...),
	email: Optional[str] = Form(None),
	description: Optional[str] = Form(None),
	address: Optional[str] = Form(None),
	qualification: Optional[str] = Form(None),
	specialization: Optional[str] = Form(None),
	experience: Optional[str] = Form(None),
	chambers: Optional[str] = Form(None),
	profile_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")

	try:
		doctor_id = generate_doctor_id(phone_no)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	existing_doctor = db.query(MRDoctorNetwork).filter(MRDoctorNetwork.doctor_id == doctor_id).first()
	if existing_doctor:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor already exists")

	new_record = MRDoctorNetwork(
		mr_id=mr_id,
		doctor_id=doctor_id,
		doctor_name=doctor_name,
		phone_no=phone_no,
		email=email,
		description=description,
		address=address,
		qualification=qualification,
		specialization=specialization,
		experience=experience,
		chambers=_parse_json_or_none(chambers, "chambers"),
	)

	if profile_photo is not None:
		try:
			new_record.profile_photo = save_doctor_profile_photo(profile_photo, mr_id, doctor_id, doctor_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid profile photo") from exc

	db.add(new_record)
	db.commit()
	db.refresh(new_record)
	return new_record

# Get all doctors across all MR networks, or filter by doctor_id or mr_id. Also supports fetching a specific doctor under a specific MR.
@router.get("/get-all", response_model=list[MRDoctorResponseSchema])
def get_all_doctors(db: Session = Depends(get_db)):
	return db.query(MRDoctorNetwork).all()

# Get doctor details by doctor_id, regardless of MR association. Useful for direct lookups when doctor_id is known. Returns 404 if not found.
@router.get("/get-by-doctor/{doctor_id}", response_model=MRDoctorResponseSchema)
def get_doctor_by_doctor_id(doctor_id: str, db: Session = Depends(get_db)):
	record = db.query(MRDoctorNetwork).filter(MRDoctorNetwork.doctor_id == doctor_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
	return record

# Get all doctors associated with a specific MR by mr_id. Returns an empty list if no doctors are found for the given MR.
@router.get("/get-all-by-mr/{mr_id}", response_model=list[MRDoctorResponseSchema])
def get_all_doctors_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
	return db.query(MRDoctorNetwork).filter(MRDoctorNetwork.mr_id == mr_id).all()

# Get doctor details by both mr_id and doctor_id, ensuring the doctor belongs to the specified MR. Returns 404 if not found or if doctor does not belong to the MR.
@router.get("/get-by-mr/{mr_id}/doctor/{doctor_id}", response_model=MRDoctorResponseSchema)
def get_doctor_by_mr_id_and_doctor_id(mr_id: str, doctor_id: str, db: Session = Depends(get_db)):
	record = (
		db.query(MRDoctorNetwork)
		.filter(MRDoctorNetwork.mr_id == mr_id, MRDoctorNetwork.doctor_id == doctor_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
	return record

# Update doctor details by doctor_id. Allows updating any field, including phone_no which triggers doctor_id regeneration and asset reorganization. Returns 404 if doctor not found, or 400 for invalid inputs or conflicts.
@router.put("/update-by/{doctor_id}", response_model=MRDoctorResponseSchema)
def update_doctor_by_doctor_id(
	doctor_id: str,
	doctor_name: Optional[str] = Form(None),
	phone_no: Optional[str] = Form(None),
	email: Optional[str] = Form(None),
	description: Optional[str] = Form(None),
	address: Optional[str] = Form(None),
	qualification: Optional[str] = Form(None),
	specialization: Optional[str] = Form(None),
	experience: Optional[str] = Form(None),
	chambers: Optional[str] = Form(None),
	profile_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = db.query(MRDoctorNetwork).filter(MRDoctorNetwork.doctor_id == doctor_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

	if phone_no is not None:
		try:
			new_doctor_id = generate_doctor_id(phone_no)
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

		if new_doctor_id != record.doctor_id:
			existing_with_new_id = (
				db.query(MRDoctorNetwork)
				.filter(MRDoctorNetwork.doctor_id == new_doctor_id, MRDoctorNetwork.id != record.id)
				.first()
			)
			if existing_with_new_id:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already in use")
			old_doctor_id = record.doctor_id
			record.doctor_id = new_doctor_id
			# Keep profile assets aligned to the new doctor_id directory.
			delete_doctor_profile_assets(record.mr_id, old_doctor_id)
		record.phone_no = phone_no

	if doctor_name is not None:
		record.doctor_name = doctor_name
	if email is not None:
		record.email = email
	if description is not None:
		record.description = description
	if address is not None:
		record.address = address
	if qualification is not None:
		record.qualification = qualification
	if specialization is not None:
		record.specialization = specialization
	if experience is not None:
		record.experience = experience
	if chambers is not None:
		record.chambers = _parse_json_or_none(chambers, "chambers")

	if profile_photo is not None:
		final_name = doctor_name if doctor_name is not None else record.doctor_name
		try:
			record.profile_photo = save_doctor_profile_photo(profile_photo, record.mr_id, record.doctor_id, final_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid profile photo") from exc

	db.commit()
	db.refresh(record)
	return record

# Delete a doctor record by doctor_id, along with associated profile photo assets. Returns 404 if doctor not found, or 500 if asset deletion fails. Successful deletion returns a confirmation message.
@router.delete("/delete-by/{doctor_id}", status_code=status.HTTP_200_OK)
def delete_doctor_by_doctor_id(doctor_id: str, db: Session = Depends(get_db)):
	record = db.query(MRDoctorNetwork).filter(MRDoctorNetwork.doctor_id == doctor_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

	try:
		delete_doctor_profile_assets(record.mr_id, record.doctor_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete doctor profile photo assets",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Doctor with id {doctor_id} deleted successfully"}
