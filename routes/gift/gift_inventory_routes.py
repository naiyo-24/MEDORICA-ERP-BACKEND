from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.gift.gift_inventory_models import GiftInventory

router = APIRouter(prefix="/gift-inventory", tags=["Gift Inventory"])


class GiftInventoryResponseSchema(BaseModel):
	gift_id: int
	product_name: str
	description: Optional[str] = None
	quantity_in_stock: int
	price_in_rupees: float
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Create a new Gift Inventory record. Accepts form data for all fields. Returns the created Gift Inventory details if successful, otherwise appropriate error messages.
@router.post("/post", response_model=GiftInventoryResponseSchema, status_code=status.HTTP_201_CREATED)
def create_gift_inventory(
	product_name: str = Form(...),
	price_in_rupees: float = Form(...),
	quantity_in_stock: int = Form(0),
	description: Optional[str] = Form(None),
	db: Session = Depends(get_db),
):
	new_gift = GiftInventory(
		product_name=product_name,
		description=description,
		quantity_in_stock=quantity_in_stock,
		price_in_rupees=price_in_rupees,
	)

	db.add(new_gift)
	db.commit()
	db.refresh(new_gift)
	return new_gift


# Fetch a Gift Inventory record by its Gift ID. Returns the Gift Inventory details if found, otherwise a 404 error.
@router.get("/get-by/{gift_id}", response_model=GiftInventoryResponseSchema)
def get_gift_inventory_by_id(gift_id: int, db: Session = Depends(get_db)):
	record = db.query(GiftInventory).filter(GiftInventory.gift_id == gift_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift inventory item not found")
	return record


# Fetch all Gift Inventory records. Returns a list of Gift Inventory details.
@router.get("/get-all", response_model=list[GiftInventoryResponseSchema])
def get_all_gift_inventory(db: Session = Depends(get_db)):
	return db.query(GiftInventory).all()


# Update an existing Gift Inventory record by its Gift ID. Accepts form data for all fields. Returns the updated Gift Inventory details if successful, otherwise appropriate error messages.
@router.put("/update-by/{gift_id}", response_model=GiftInventoryResponseSchema)
def update_gift_inventory_by_id(
	gift_id: int,
	product_name: Optional[str] = Form(None),
	description: Optional[str] = Form(None),
	quantity_in_stock: Optional[int] = Form(None),
	price_in_rupees: Optional[float] = Form(None),
	db: Session = Depends(get_db),
):
	record = db.query(GiftInventory).filter(GiftInventory.gift_id == gift_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift inventory item not found")

	if product_name is not None:
		record.product_name = product_name
	if description is not None:
		record.description = description
	if quantity_in_stock is not None:
		record.quantity_in_stock = quantity_in_stock
	if price_in_rupees is not None:
		record.price_in_rupees = price_in_rupees

	db.commit()
	db.refresh(record)
	return record


# Delete a Gift Inventory record by its Gift ID. Returns a success message on successful deletion.
@router.delete("/delete-by/{gift_id}", status_code=status.HTTP_200_OK)
def delete_gift_inventory_by_id(gift_id: int, db: Session = Depends(get_db)):
	record = db.query(GiftInventory).filter(GiftInventory.gift_id == gift_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift inventory item not found")

	db.delete(record)
	db.commit()
	return {"message": f"Gift inventory item with id {gift_id} deleted successfully"}
