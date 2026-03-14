import re
from datetime import datetime, timezone
from uuid import uuid4


# Generate order ID in the pattern: {asm_id}-ORD-{UTC timestamp}-{random suffix}.
def generate_asm_order_id(asm_id: str) -> str:
	if asm_id is None or asm_id.strip() == "":
		raise ValueError("ASM ID is required")

	# Keep only letters, numbers, dashes and underscores for a stable identifier segment.
	normalized_asm_id = re.sub(r"[^A-Za-z0-9_-]", "", asm_id.strip())
	if normalized_asm_id == "":
		raise ValueError("ASM ID must contain valid characters")

	utc_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
	random_suffix = uuid4().hex[:6].upper()
	return f"{normalized_asm_id}-ORD-{utc_timestamp}-{random_suffix}"
