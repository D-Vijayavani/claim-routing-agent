import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import re
import json
# Mandatory fields required for automated claim routing
MANDATORY_FIELDS = [
    "policyNumber",
    "dateOfLoss",
    "claimType",
    "estimatedDamage"
]
def clean_value(value):
    if not value:
        return None

    LABEL_WORDS = [
        "CONTACT",
        "DESCRIPTION",
        "ACORD",
        "LOSS",
        "NOTICE",
        "POLICY",
        "NUMBER"
    ]

    for word in LABEL_WORDS:
        if word in value.upper():
            return None

    return value
# -------------------------------
# STEP 1: Read PDF with fallback OCR
# -------------------------------
# NOTE:
# Due to OCR limitations on multi-column ACORD forms,
# some fields may not be extracted reliably.
# Such cases are intentionally routed to Manual Review.

def read_pdf(path):
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"⚠️ PDF parsing failed: {e}")

    # If text is empty or clearly placeholder, use OCR
    if not text.strip() or "DESCRIPTION OF ACCIDENT (ACORD" in text:
        print("ℹ️ Using OCR fallback")
        images = convert_from_path(path)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"

    return text

# -------------------------------
# STEP 2: Field Extraction (same as before)
# -------------------------------
def extract_policy_number(text):
    match = re.search(r"POLICY NUMBER[:\s]*([A-Z0-9-]+)", text, re.IGNORECASE)
    return match.group(1) if match else None

def extract_policyholder_name(text):
    match = re.search(r"NAME OF INSURED.*?:\s*(.*)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extract_date_of_loss(text):
    match = re.search(r"DATE OF LOSS[:\s]*([0-9/]+)", text, re.IGNORECASE)
    return match.group(1) if match else None

def extract_location(text):
    match = re.search(r"LOCATION OF LOSS.*?:\s*(.*)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extract_description(text):
    match = re.search(r"DESCRIPTION OF ACCIDENT[:\s]*(.*)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extract_estimated_damage(text):
    match = re.search(r"ESTIMATE AMOUNT[:\s]*\$?([0-9,]+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return None

def extract_claim_type(text):
    text = text.lower()
    if "injury" in text:
        return "injury"
    if "vehicle" in text or "collision" in text:
        return "vehicle"
    return None


def route_claim(fields, missing_fields):
    description = (fields.get("description") or "").lower()
    damage = fields.get("estimatedDamage")
    claim_type = fields.get("claimType")

    # 1. Missing mandatory fields → manual review
    if missing_fields:
        return "Manual Review", "Mandatory fields are missing"

    # 2. Fraud keywords → investigation
    if any(word in description for word in ["fraud", "staged", "inconsistent"]):
        return "Investigation Flag", "Suspicious keywords detected"

    # 3. Injury claims → specialist
    if claim_type == "injury":
        return "Specialist Queue", "Injury-related claim requires human assessment"

    # 4. Low damage → fast track
    if damage is not None and damage < 25000:
        return "Fast-track", "Estimated damage below 25,000"

    return "Standard Processing", "Default routing applied"

# -------------------------------
# STEP 4: MAIN EXECUTION
# -------------------------------
def main():
    pdf_path = "ACORD-Automobile-Loss-Notice.pdf"

    fnol_text = read_pdf("/Users/vijayavanidonthi/Documents/claim-agent/ACORD-Automobile-Loss-Notice.pdf")

   

    extracted_fields = {
    "policyNumber": clean_value(extract_policy_number(fnol_text)),
    "policyHolderName": clean_value(extract_policyholder_name(fnol_text)),
    "dateOfLoss": extract_date_of_loss(fnol_text),
    "location": clean_value(extract_location(fnol_text)),
    "description": clean_value(extract_description(fnol_text)),
    "estimatedDamage": extract_estimated_damage(fnol_text),
    "claimType": extract_claim_