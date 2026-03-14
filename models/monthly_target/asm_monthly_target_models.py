from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func

from db import Base


# Store monthly target tracking for an ASM for a given month-year period.
class ASMMonthlyTarget(Base):
	__tablename__ = "asm_monthly_target"
	__table_args__ = (
		UniqueConstraint("asm_id", "month", "year", name="uq_asm_month_year_target"),
	)

	id = Column(Integer, primary_key=True, index=True)
	asm_id = Column(String(32), ForeignKey("area_sales_manager.asm_id"), nullable=False, index=True)
	month = Column(Integer, nullable=False, index=True)
	year = Column(Integer, nullable=False, index=True)
	opening_target_rupees = Column(Float, nullable=False, default=0.0, server_default="0")
	deducted_target_rupees = Column(Float, nullable=False, default=0.0, server_default="0")
	remaining_target_rupees = Column(Float, nullable=False, default=0.0, server_default="0")
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
