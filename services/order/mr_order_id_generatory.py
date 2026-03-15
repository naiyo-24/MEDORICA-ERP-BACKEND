import re
from datetime import datetime, timezone
from uuid import uuid4

# Generate order ID in the pattern: {mr_id}-ORD-{UTC timestamp}-{random suffix}.
def generate_mr_order_id(mr_id: str) -> str:
    if mr_id is None or mr_id.strip() == "":
        raise ValueError("MR ID is required")

    normalized_mr_id = re.sub(r"[^A-Za-z0-9_-]", "", mr_id.strip())
    if normalized_mr_id == "":
        raise ValueError("MR ID must contain valid characters")

    utc_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_suffix = uuid4().hex[:6].upper()
    return f"{normalized_mr_id}-ORD-{utc_timestamp}-{random_suffix}"
