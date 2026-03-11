import re


# Generate doctor ID in the pattern: {asm_id}-DOC-{doctor_phone_no_digits}.
def generate_asm_doctor_id(asm_id: str, doctor_phone_no: str) -> str:
	if asm_id is None or asm_id.strip() == "":
		raise ValueError("ASM ID is required")

	if doctor_phone_no is None or doctor_phone_no.strip() == "":
		raise ValueError("Doctor phone number is required")

	phone_digits = re.sub(r"\D", "", doctor_phone_no)
	if phone_digits == "":
		raise ValueError("Doctor phone number must contain digits")

	return f"{asm_id}-DOC-{phone_digits}"
