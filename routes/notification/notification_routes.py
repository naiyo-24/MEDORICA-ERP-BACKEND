from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.notification.notification_models import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponseSchema(BaseModel):
	id: int
	title: str
	sub_title: Optional[str] = None
	audience: Literal["asm", "mr"]
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Create a new notification for ASM or MR audience.
@router.post("/post", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
def create_notification(
	title: str = Form(...),
	sub_title: Optional[str] = Form(None),
	audience: Literal["asm", "mr"] = Form(...),
	db: Session = Depends(get_db),
):
	new_notification = Notification(
		title=title,
		sub_title=sub_title,
		audience=audience,
	)

	db.add(new_notification)
	db.commit()
	db.refresh(new_notification)
	return new_notification


# Fetch a notification by its ID.
@router.get("/get-by/{notification_id}", response_model=NotificationResponseSchema)
def get_notification_by_id(notification_id: int, db: Session = Depends(get_db)):
	record = db.query(Notification).filter(Notification.id == notification_id).first()
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
	return record


# Fetch all notifications.
@router.get("/get-all", response_model=list[NotificationResponseSchema])
def get_all_notifications(db: Session = Depends(get_db)):
	return db.query(Notification).all()
