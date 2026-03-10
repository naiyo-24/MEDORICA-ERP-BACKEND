from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, func

from db import Base


# Store team details, leadership assignment, and member mapping.
class Team(Base):
	__tablename__ = "team"

	id = Column(Integer, primary_key=True, index=True)
	team_id = Column(Integer, unique=True, nullable=True, index=True)
	team_name = Column(String(255), nullable=False)
	team_description = Column(Text, nullable=True)
	whatsapp_group_link = Column(Text, nullable=True)
	team_leader_asm_id = Column(String(32), nullable=False, index=True)
	team_members_mr_ids = Column(JSON, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)