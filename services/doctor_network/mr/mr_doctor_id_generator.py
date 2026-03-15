import re


# Generate doctor ID in the pattern: {mr_id}-DOC-{doctor_phone_no_digits}.
def generate_mr_doctor_id(mr_id: str, doctor_phone_no: str) -> str:
	if mr_id is None or mr_id.strip() == "":
		raise ValueError("MR ID is required")

	if doctor_phone_no is None or doctor_phone_no.strip() == "":
		raise ValueError("Doctor phone number is required")

	phone_digits = re.sub(r"\D", "", doctor_phone_no)
	if phone_digits == "":
		raise ValueError("Doctor phone number must contain digits")

	return f"{mr_id}-DOC-{phone_digits}"
