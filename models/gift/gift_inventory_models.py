from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from db import Base


# Store gift inventory details.
class GiftInventory(Base):
	__tablename__ = "gift_inventory"

	gift_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	product_name = Column(String(1055), nullable=False)
	description = Column(Text, nullable=True)
	quantity_in_stock = Column(Integer, nullable=False, default=0)
	price_in_rupees = Column(Float, nullable=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
