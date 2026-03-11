from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func

from db import Base


# Store doctor network details managed by an ASM.
class ASMDoctorNetwork(Base):
	__tablename__ = "asm_doctor_network"
	__table_args__ = (
		UniqueConstraint("asm_id", "doctor_phone_no", name="uq_asm_doctor_phone"),
	)

	id = Column(Integer, primary_key=True, index=True)
	doctor_id = Column(String(64), unique=True, nullable=False, index=True)
	asm_id = Column(String(32), ForeignKey("area_sales_manager.asm_id"), nullable=False, index=True)
	doctor_name = Column(String(255), nullable=False)
	doctor_birthday = Column(Date, nullable=True)
	doctor_specialization = Column(String(255), nullable=True)
	doctor_qualification = Column(String(255), nullable=True)
	doctor_experience = Column(String(255), nullable=True)
	doctor_description = Column(Text, nullable=True)
	doctor_photo = Column(Text, nullable=True)
	doctor_chambers = Column(JSON, nullable=True)
	doctor_phone_no = Column(String(20), nullable=False, index=True)
	doctor_email = Column(String(255), nullable=True)
	doctor_address = Column(Text, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
