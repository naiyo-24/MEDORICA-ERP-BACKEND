# FastAPI routes for ASM Gift Applications
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.gift.asm_gift_application_models import ASMGiftApplication
from models.onboarding.asm_onboarding_models import AreaSalesManager
from models.doctor_network.asm_doctor_network_models import ASMDoctorNetwork
from models.gift.gift_inventory_models import GiftInventory

router = APIRouter(prefix="/gift-application/asm", tags=["ASM Gift Application"])

class ASMGiftApplicationResponseSchema(BaseModel):
    request_id: int
    asm_id: str
    doctor_id: str
    gift_id: int
    occassion: Optional[str] = None
    message: Optional[str] = None
    gift_date: Optional[date] = None
    remarks: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    # Extra fields for display
    asm_name: Optional[str] = None
    doctor_name: Optional[str] = None
    asm_phone_no: Optional[str] = None
    doctor_phone_no: Optional[str] = None
    gift_name: Optional[str] = None

    class Config:
        from_attributes = True

# Helper to enrich application with related info
def enrich_application(app: ASMGiftApplication, db: Session):
    asm = db.query(AreaSalesManager).filter(AreaSalesManager.asm_id == app.asm_id).first()
    doctor = db.query(ASMDoctorNetwork).filter(ASMDoctorNetwork.doctor_id == app.doctor_id).first()
    gift = db.query(GiftInventory).filter(GiftInventory.gift_id == app.gift_id).first()
    return {
        **app.__dict__,
        "asm_name": asm.full_name if asm else None,
        "doctor_name": doctor.doctor_name if doctor else None,
        "asm_phone_no": asm.phone_no if asm else None,
        "doctor_phone_no": doctor.doctor_phone_no if doctor else None,
        "gift_name": gift.product_name if gift else None,
    }

# Create a new ASM Gift Application
@router.post("/post", response_model=ASMGiftApplicationResponseSchema, status_code=status.HTTP_201_CREATED)
def create_asm_gift_application(
    asm_id: str = Form(...),
    doctor_id: str = Form(...),
    gift_id: int = Form(...),
    occassion: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    gift_date: Optional[date] = Form(None),
    remarks: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    new_app = ASMGiftApplication(
        asm_id=asm_id,
        doctor_id=doctor_id,
        gift_id=gift_id,
        occassion=occassion,
        message=message,
        gift_date=gift_date,
        remarks=remarks,
        status="pending",
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return enrich_application(new_app, db)

# Get all ASM Gift Applications
@router.get("/get-all", response_model=List[ASMGiftApplicationResponseSchema])
def get_all_asm_gift_applications(db: Session = Depends(get_db)):
    apps = db.query(ASMGiftApplication).all()
    return [enrich_application(app, db) for app in apps]

# Get ASM Gift Applications by ASM ID
@router.get("/get-by-asm/{asm_id}", response_model=List[ASMGiftApplicationResponseSchema])
def get_asm_gift_applications_by_asm_id(asm_id: str, db: Session = Depends(get_db)):
    apps = db.query(ASMGiftApplication).filter(ASMGiftApplication.asm_id == asm_id).all()
    return [enrich_application(app, db) for app in apps]

# Update ASM Gift Application by ASM ID and Request ID
@router.put("/update-by/{asm_id}/{request_id}", response_model=ASMGiftApplicationResponseSchema)
def update_asm_gift_application(
    asm_id: str,
    request_id: int,
    doctor_id: Optional[str] = Form(None),
    occassion: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    gift_date: Optional[date] = Form(None),
    remarks: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    app = db.query(ASMGiftApplication).filter(ASMGiftApplication.asm_id == asm_id, ASMGiftApplication.request_id == request_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM Gift Application not found")
    if doctor_id is not None:
        app.doctor_id = doctor_id
    if occassion is not None:
        app.occassion = occassion
    if message is not None:
        app.message = message
    if gift_date is not None:
        app.gift_date = gift_date
    if remarks is not None:
        app.remarks = remarks
    if status is not None:
        app.status = status
    db.commit()
    db.refresh(app)
    return enrich_application(app, db)

# Delete ASM Gift Application by Request ID
@router.delete("/delete-by/{request_id}", status_code=status.HTTP_200_OK)
def delete_asm_gift_application(request_id: int, db: Session = Depends(get_db)):
    app = db.query(ASMGiftApplication).filter(ASMGiftApplication.request_id == request_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASM Gift Application not found")
    db.delete(app)
    db.commit()
    return {"message": f"ASM Gift Application with id {request_id} deleted successfully"}
