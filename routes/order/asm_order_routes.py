import json
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.chemist_shop.asm_chemist_shop_network_models import ASMChemistShopNetwork
from models.distributor.distributor_models import Distributor
from models.doctor_network.asm_doctor_network_models import ASMDoctorNetwork
from models.monthly_target.asm_monthly_target_models import ASMMonthlyTarget
from models.onboarding.asm_onboarding_models import AreaSalesManager
from models.order.asm_order_models import ASMOrder
from services.order.asm_order_id_generator import generate_asm_order_id

router = APIRouter(prefix="/order/asm", tags=["ASM Orders"])

ALLOWED_ORDER_STATUSES = {"pending", "approved", "shipped", "delivered"}


class ASMOrderResponseSchema(BaseModel):
	id: int
	order_id: str
	asm_id: str
	distributor_id: Optional[str] = None
	chemist_shop_id: Optional[str] = None
	doctor_id: Optional[str] = None
	products_with_price: Any
	total_amount_rupees: float
	status: str
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


def _parse_products_with_price_json(products_with_price: str) -> Any:
	if products_with_price is None or products_with_price.strip() == "":
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="products_with_price is required")

	try:
		parsed = json.loads(products_with_price)
	except json.JSONDecodeError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="products_with_price must be valid JSON",
		) from exc

	if parsed is None:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="products_with_price cannot be null",
		)

	if not isinstance(parsed, (list, dict)):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="products_with_price must be a JSON array or object",
		)

	return parsed


def _normalize_order_status(status_value: str) -> str:
	if status_value is None or status_value.strip() == "":
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status is required")

	normalized = status_value.strip().lower()
	if normalized not in ALLOWED_ORDER_STATUSES:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="status must be one of: pending, approved, shipped, delivered",
		)
	return normalized


def _validate_optional_links(
	db: Session,
	asm_id: str,
	distributor_id: Optional[str],
	chemist_shop_id: Optional[str],
	doctor_id: Optional[str],
):
	if distributor_id is not None:
		distributor = db.query(Distributor).filter(Distributor.dist_id == distributor_id).first()
		if not distributor:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distributor not found")

	if chemist_shop_id is not None:
		shop = (
			db.query(ASMChemistShopNetwork)
			.filter(
				ASMChemistShopNetwork.shop_id == chemist_shop_id,
				ASMChemistShopNetwork.asm_id == asm_id,
			)
			.first()
		)
		if not shop:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chemist shop not found for this ASM")

	if doctor_id is not None:
		doctor = (
			db.query(ASMDoctorNetwork)
			.filter(
				ASMDoctorNetwork.doctor_id == doctor_id,
				ASMDoctorNetwork.asm_id == asm_id,
			)
			.first()
		)
		if not doctor:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found for this ASM")


def _deduct_monthly_target_on_approval(
	db: Session,
	asm_record: AreaSalesManager,
	order_amount_rupees: float,
):
	today = date.today()
	month = today.month
	year = today.year

	monthly_target_record = (
		db.query(ASMMonthlyTarget)
		.filter(
			ASMMonthlyTarget.asm_id == asm_record.asm_id,
			ASMMonthlyTarget.month == month,
			ASMMonthlyTarget.year == year,
		)
		.with_for_update()
		.first()
	)

	if monthly_target_record is None:
		opening_target = asm_record.monthly_target_rupees or 0.0
		monthly_target_record = ASMMonthlyTarget(
			asm_id=asm_record.asm_id,
			month=month,
			year=year,
			opening_target_rupees=opening_target,
			deducted_target_rupees=0.0,
			remaining_target_rupees=opening_target,
		)
		db.add(monthly_target_record)
		db.flush()

	remaining_before = monthly_target_record.remaining_target_rupees or 0.0
	if remaining_before < order_amount_rupees:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Insufficient monthly target remaining for approval",
		)

	monthly_target_record.deducted_target_rupees = (monthly_target_record.deducted_target_rupees or 0.0) + order_amount_rupees
	monthly_target_record.remaining_target_rupees = remaining_before - order_amount_rupees


# Create a new order for an ASM by ASM ID.
@router.post("/post-by/{asm_id}", response_model=ASMOrderResponseSchema, status_code=status.HTTP_201_CREATED)
def create_asm_order(
	asm_id: str,
	distributor_id: Optional[str] = Form(None),
	chemist_shop_id: Optional[str] = Form(None),
	doctor_id: Optional[str] = Form(None),
	products_with_price: str = Form(...),
	total_amount_rupees: float = Form(...),
	status_value: str = Form("pending", alias="status"),
	db: Session = Depends(get_db),
):
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")

	_validate_optional_links(db, asm_id, distributor_id, chemist_shop_id, doctor_id)

	try:
		generated_order_id = generate_asm_order_id(asm_id)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	new_order = ASMOrder(
		order_id=generated_order_id,
		asm_id=asm_id,
		distributor_id=distributor_id,
		chemist_shop_id=chemist_shop_id,
		doctor_id=doctor_id,
		products_with_price=_parse_products_with_price_json(products_with_price),
		total_amount_rupees=total_amount_rupees,
		status=_normalize_order_status(status_value),
	)

	db.add(new_order)
	db.commit()
	db.refresh(new_order)
	return new_order


# Fetch all ASM orders.
@router.get("/get-all", response_model=list[ASMOrderResponseSchema])
def get_all_asm_orders(db: Session = Depends(get_db)):
	return db.query(ASMOrder).all()


# Fetch all orders for a specific ASM.
@router.get("/get-by-asm/{asm_id}", response_model=list[ASMOrderResponseSchema])
def get_orders_by_asm_id(asm_id: str, db: Session = Depends(get_db)):
	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")
	return db.query(ASMOrder).filter(ASMOrder.asm_id == asm_id).all()


# Fetch one order by ASM ID and order ID.
@router.get("/get-by/{asm_id}/{order_id}", response_model=ASMOrderResponseSchema)
def get_order_by_asm_and_order_id(asm_id: str, order_id: str, db: Session = Depends(get_db)):
	record = db.query(ASMOrder).filter(ASMOrder.order_id == order_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

	if record.asm_id != asm_id:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found for this ASM")

	return record


# Update an order by order ID.
@router.put("/update-by/{order_id}", response_model=ASMOrderResponseSchema)
def update_order_by_order_id(
	order_id: str,
	distributor_id: Optional[str] = Form(None),
	chemist_shop_id: Optional[str] = Form(None),
	doctor_id: Optional[str] = Form(None),
	products_with_price: Optional[str] = Form(None),
	total_amount_rupees: Optional[float] = Form(None),
	status_value: Optional[str] = Form(None, alias="status"),
	db: Session = Depends(get_db),
):
	record = db.query(ASMOrder).filter(ASMOrder.order_id == order_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

	asm_record = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == record.asm_id).first()
	if not asm_record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM not found")

	# On update, None means "leave unchanged" for optional link fields.
	next_distributor_id = distributor_id if distributor_id is not None else record.distributor_id
	next_chemist_shop_id = chemist_shop_id if chemist_shop_id is not None else record.chemist_shop_id
	next_doctor_id = doctor_id if doctor_id is not None else record.doctor_id
	_validate_optional_links(db, record.asm_id, next_distributor_id, next_chemist_shop_id, next_doctor_id)

	if distributor_id is not None:
		record.distributor_id = distributor_id
	if chemist_shop_id is not None:
		record.chemist_shop_id = chemist_shop_id
	if doctor_id is not None:
		record.doctor_id = doctor_id
	if products_with_price is not None:
		record.products_with_price = _parse_products_with_price_json(products_with_price)
	if total_amount_rupees is not None:
		if record.status == "approved" and total_amount_rupees != record.total_amount_rupees:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Cannot change total amount after order is approved",
			)
		record.total_amount_rupees = total_amount_rupees
	if status_value is not None:
		next_status = _normalize_order_status(status_value)
		if record.status == "approved" and next_status != "approved":
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Cannot change status after order is approved",
			)

		next_total_amount = total_amount_rupees if total_amount_rupees is not None else record.total_amount_rupees
		if record.status != "approved" and next_status == "approved":
			_deduct_monthly_target_on_approval(db, asm_record, next_total_amount)

		record.status = next_status

	db.commit()
	db.refresh(record)
	return record


# Delete an order by order ID.
@router.delete("/delete-by/{order_id}", status_code=status.HTTP_200_OK)
def delete_order_by_order_id(order_id: str, db: Session = Depends(get_db)):
	record = db.query(ASMOrder).filter(ASMOrder.order_id == order_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

	db.delete(record)
	db.commit()
	return {"message": f"Order with id {order_id} deleted successfully"}
