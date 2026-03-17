# SQLAlchemy model for ASM Gift Application
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from db import Base

class ASMGiftApplication(Base):
    __tablename__ = "asm_gift_applications"

    request_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    asm_id = Column(String(32), ForeignKey("area_sales_manager.asm_id"), nullable=False, index=True)
    doctor_id = Column(String(64), ForeignKey("asm_doctor_network.doctor_id"), nullable=False, index=True)
    gift_id = Column(Integer, ForeignKey("gift_inventory.gift_id"), nullable=False, index=True)
    occassion = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    gift_date = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="pending")  # pending, approved, shipped, delivered
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
