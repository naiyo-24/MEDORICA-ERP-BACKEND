from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.chemist_shop.mr_chemist_shop_network_models import MRChemistShopNetwork
from models.onboarding.mr_onbooarding_models import MedicalRepresentative
from services.chemist_shop.mr.mr_chemist_shop_id_generator import generate_mr_chemist_shop_id
from services.chemist_shop.mr.mr_chemist_shop_photo_upload import (
	delete_mr_chemist_shop_assets,
	save_mr_chemist_shop_bank_passbook_photo,
	save_mr_chemist_shop_photo,
)

router = APIRouter(prefix="/chemist-shop/mr", tags=["MR Chemist Shop Network"])


class MRChemistShopNetworkResponseSchema(BaseModel):
	id: int
	shop_id: str
	mr_id: str
	shop_name: str
	address: Optional[str] = None
	phone_no: str
	email: Optional[str] = None
	description: Optional[str] = None
	photo: Optional[str] = None
	bank_passbook_photo: Optional[str] = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Create a chemist shop record for an MR.
@router.post("/post", response_model=MRChemistShopNetworkResponseSchema, status_code=status.HTTP_201_CREATED)
def create_mr_chemist_shop(
	mr_id: str = Form(...),
	shop_name: str = Form(...),
	phone_no: str = Form(...),
	address: Optional[str] = Form(None),
	email: Optional[str] = Form(None),
	description: Optional[str] = Form(None),
	photo: Optional[UploadFile] = File(None),
	bank_passbook_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")

	existing_shop_for_mr = (
		db.query(MRChemistShopNetwork)
		.filter(MRChemistShopNetwork.mr_id == mr_id, MRChemistShopNetwork.phone_no == phone_no)
		.first()
	)
	if existing_shop_for_mr:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Chemist shop with this phone number already exists for this MR",
		)

	try:
		generated_shop_id = generate_mr_chemist_shop_id(phone_no)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	new_shop = MRChemistShopNetwork(
		shop_id=generated_shop_id,
		mr_id=mr_id,
		shop_name=shop_name,
		address=address,
		phone_no=phone_no,
		email=email,
		description=description,
	)

	if photo is not None:
		try:
			new_shop.photo = save_mr_chemist_shop_photo(photo, generated_shop_id, shop_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shop photo") from exc

	if bank_passbook_photo is not None:
		try:
			new_shop.bank_passbook_photo = save_mr_chemist_shop_bank_passbook_photo(
				bank_passbook_photo, generated_shop_id, shop_name
			)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bank passbook photo") from exc

	db.add(new_shop)
	db.commit()
	db.refresh(new_shop)
	return new_shop


# Fetch all chemist shops in the MR chemist shop network.
@router.get("/get-all", response_model=list[MRChemistShopNetworkResponseSchema])
def get_all_mr_chemist_shops(db: Session = Depends(get_db)):
	return db.query(MRChemistShopNetwork).all()


# Fetch all chemist shops linked to a specific MR ID.
@router.get("/get-by-mr/{mr_id}", response_model=list[MRChemistShopNetworkResponseSchema])
def get_chemist_shops_by_mr_id(mr_id: str, db: Session = Depends(get_db)):
	mr_record = db.query(MedicalRepresentative).filter(MedicalRepresentative.mr_id == mr_id).first()
	if not mr_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found")
	return db.query(MRChemistShopNetwork).filter(MRChemistShopNetwork.mr_id == mr_id).all()


# Fetch a specific chemist shop by MR ID and shop ID.
@router.get("/get-by/{mr_id}/{shop_id}", response_model=MRChemistShopNetworkResponseSchema)
def get_chemist_shop_by_mr_and_shop_id(mr_id: str, shop_id: str, db: Session = Depends(get_db)):
	record = (
		db.query(MRChemistShopNetwork)
		.filter(MRChemistShopNetwork.mr_id == mr_id, MRChemistShopNetwork.shop_id == shop_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")
	return record


# Fetch a specific chemist shop by shop ID only.
@router.get("/get-by-shop/{shop_id}", response_model=MRChemistShopNetworkResponseSchema)
def get_chemist_shop_by_shop_id(shop_id: str, db: Session = Depends(get_db)):
	record = db.query(MRChemistShopNetwork).filter(MRChemistShopNetwork.shop_id == shop_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")
	return record


# Update a chemist shop by MR ID and shop ID.
@router.put("/update-by/{mr_id}/{shop_id}", response_model=MRChemistShopNetworkResponseSchema)
def update_chemist_shop_by_mr_and_shop_id(
	mr_id: str,
	shop_id: str,
	shop_name: Optional[str] = Form(None),
	phone_no: Optional[str] = Form(None),
	address: Optional[str] = Form(None),
	email: Optional[str] = Form(None),
	description: Optional[str] = Form(None),
	photo: Optional[UploadFile] = File(None),
	bank_passbook_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = (
		db.query(MRChemistShopNetwork)
		.filter(MRChemistShopNetwork.mr_id == mr_id, MRChemistShopNetwork.shop_id == shop_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")

	if phone_no is not None:
		existing_for_phone = (
			db.query(MRChemistShopNetwork)
			.filter(
				MRChemistShopNetwork.mr_id == mr_id,
				MRChemistShopNetwork.phone_no == phone_no,
				MRChemistShopNetwork.id != record.id,
			)
			.first()
		)
		if existing_for_phone:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Chemist shop with this phone number already exists for this MR",
			)

		try:
			new_shop_id = generate_mr_chemist_shop_id(phone_no)
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

		if new_shop_id != record.shop_id:
			existing_shop_id = (
				db.query(MRChemistShopNetwork)
				.filter(MRChemistShopNetwork.shop_id == new_shop_id, MRChemistShopNetwork.id != record.id)
				.first()
			)
			if existing_shop_id:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop ID already in use")
			record.shop_id = new_shop_id

		record.phone_no = phone_no

	if shop_name is not None:
		record.shop_name = shop_name
	if address is not None:
		record.address = address
	if email is not None:
		record.email = email
	if description is not None:
		record.description = description

	if photo is not None:
		photo_shop_name = shop_name if shop_name is not None else record.shop_name
		try:
			record.photo = save_mr_chemist_shop_photo(photo, record.shop_id, photo_shop_name)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shop photo") from exc

	if bank_passbook_photo is not None:
		passbook_shop_name = shop_name if shop_name is not None else record.shop_name
		try:
			record.bank_passbook_photo = save_mr_chemist_shop_bank_passbook_photo(
				bank_passbook_photo, record.shop_id, passbook_shop_name
			)
		except Exception as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bank passbook photo") from exc

	db.commit()
	db.refresh(record)
	return record


# Update a chemist shop by shop ID only.
@router.put("/update-by-shop/{shop_id}", response_model=MRChemistShopNetworkResponseSchema)
def update_chemist_shop_by_shop_id(
	shop_id: str,
	shop_name: Optional[str] = Form(None),
	phone_no: Optional[str] = Form(None),
	address: Optional[str] = Form(None),
	email: Optional[str] = Form(None),
	description: Optional[str] = Form(None),
	photo: Optional[UploadFile] = File(None),
	bank_passbook_photo: Optional[UploadFile] = File(None),
	db: Session = Depends(get_db),
):
	record = db.query(MRChemistShopNetwork).filter(MRChemistShopNetwork.shop_id == shop_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")

	return update_chemist_shop_by_mr_and_shop_id(
		mr_id=record.mr_id,
		shop_id=record.shop_id,
		shop_name=shop_name,
		phone_no=phone_no,
		address=address,
		email=email,
		description=description,
		photo=photo,
		bank_passbook_photo=bank_passbook_photo,
		db=db,
	)


# Delete a chemist shop by MR ID and shop ID, and remove associated assets.
@router.delete("/delete-by/{mr_id}/{shop_id}", status_code=status.HTTP_200_OK)
def delete_chemist_shop_by_mr_and_shop_id(mr_id: str, shop_id: str, db: Session = Depends(get_db)):
	record = (
		db.query(MRChemistShopNetwork)
		.filter(MRChemistShopNetwork.mr_id == mr_id, MRChemistShopNetwork.shop_id == shop_id)
		.first()
	)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")

	try:
		delete_mr_chemist_shop_assets(record.shop_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete chemist shop assets",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Chemist shop with id {shop_id} deleted successfully"}


# Delete a chemist shop by shop ID only, and remove associated assets.
@router.delete("/delete-by-shop/{shop_id}", status_code=status.HTTP_200_OK)
def delete_chemist_shop_by_shop_id(shop_id: str, db: Session = Depends(get_db)):
	record = db.query(MRChemistShopNetwork).filter(MRChemistShopNetwork.shop_id == shop_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found")

	try:
		delete_mr_chemist_shop_assets(record.shop_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete chemist shop assets",
		) from exc

	db.delete(record)
	db.commit()
	return {"message": f"Chemist shop with id {shop_id} deleted successfully"}
