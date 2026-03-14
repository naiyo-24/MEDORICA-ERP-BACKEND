from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, func

from db import Base


# Store order details created by an ASM with optional links to distributor, chemist shop and doctor.
class ASMOrder(Base):
	__tablename__ = "asm_order"

	id = Column(Integer, primary_key=True, index=True)
	order_id = Column(String(128), unique=True, nullable=False, index=True)
	asm_id = Column(String(32), ForeignKey("area_sales_manager.asm_id"), nullable=False, index=True)
	distributor_id = Column(String(32), ForeignKey("distributor.dist_id"), nullable=True, index=True)
	chemist_shop_id = Column(String(64), ForeignKey("asm_chemist_shop_network.shop_id"), nullable=True, index=True)
	doctor_id = Column(String(64), ForeignKey("asm_doctor_network.doctor_id"), nullable=True, index=True)
	products_with_price = Column(JSON, nullable=False)
	total_amount_rupees = Column(Float, nullable=False)
	status = Column(String(20), nullable=False, default="pending", server_default="pending")
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
