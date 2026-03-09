from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, func

from db import Base


# Store doctors mapped to a medical representative.
class MRDoctorNetwork(Base):
	__tablename__ = "mr_doctor_network"

	id = Column(Integer, primary_key=True, index=True)
	mr_id = Column(String(32), nullable=False, index=True)
	doctor_id = Column(String(32), unique=True, nullable=False, index=True)
	doctor_name = Column(String(255), nullable=False)
	phone_no = Column(String(20), unique=True, nullable=False, index=True)
	email = Column(String(255), nullable=True)
	description = Column(Text, nullable=True)
	address = Column(Text, nullable=True)
	qualification = Column(String(255), nullable=True)
	specialization = Column(String(255), nullable=True)
	experience = Column(String(100), nullable=True)
	chambers = Column(JSON, nullable=True)
	profile_photo = Column(Text, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
