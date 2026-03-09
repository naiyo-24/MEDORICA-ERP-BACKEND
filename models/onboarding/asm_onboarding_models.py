from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, Integer, String, Text, func

from db import Base


# Store onboarding and compensation details for area sales managers.
class AreaSalesManager(Base):
	__tablename__ = "area_sales_manager"

	id = Column(Integer, primary_key=True, index=True)
	asm_id = Column(String(32), unique=True, nullable=False, index=True)
	full_name = Column(String(255), nullable=False)
	phone_no = Column(String(20), unique=True, nullable=False, index=True)
	alt_phone_no = Column(String(20), nullable=True)
	email = Column(String(255), nullable=True)
	address = Column(Text, nullable=True)
	joining_date = Column(Date, nullable=True)
	password = Column(Text, nullable=False)
	profile_photo = Column(Text, nullable=True)
	bank_name = Column(String(255), nullable=True)
	bank_account_no = Column(String(100), nullable=True)
	ifsc_code = Column(String(50), nullable=True)
	branch_name = Column(String(255), nullable=True)
	headquarter_assigned = Column(String(255), nullable=True)
	territories_of_work = Column(JSON, nullable=True)
	monthly_target_rupees = Column(Float, nullable=True)
	basic_salary_rupees = Column(Float, nullable=True)
	daily_allowances_rupees = Column(Float, nullable=True)
	hra_rupees = Column(Float, nullable=True)
	phone_allowances_rupees = Column(Float, nullable=True)
	children_allowances_rupees = Column(Float, nullable=True)
	special_allowances_rupees = Column(Float, nullable=True)
	medical_allowances_rupees = Column(Float, nullable=True)
	esic_rupees = Column(Float, nullable=True)
	total_monthly_compensation_rupees = Column(Float, nullable=True)
	active = Column(Boolean, nullable=False, default=True, server_default="true")
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
