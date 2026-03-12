from sqlalchemy import Column, DateTime, Integer, String, Text, func

from db import Base


# Store notification details for ASM or MR audiences.
class Notification(Base):
	__tablename__ = "notifications"

	id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	title = Column(String(255), nullable=False)
	sub_title = Column(Text, nullable=True)
	audience = Column(String(10), nullable=False, index=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
