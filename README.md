# Claim Routing Agent (FNOL Processing)

## Overview
This project implements a rule-based claim routing agent that processes FNOL (First Notice of Loss) documents in PDF format and determines the appropriate claim handling route.

## Approach
- Attempts text extraction using pdfplumber
- Falls back to OCR using pytesseract when PDF text extraction fails
- Extracts key claim-related fields using pattern matching
- Identifies missing mandatory fields
- Applies predefined business rules to route the claim
- Outputs structured JSON with routing decision and reasoning

## Mandatory Fields
The following fields are required for automated routing:
- Policy Number
- Date of Loss
- Claim Type
- Estimated Damage

If any of these fields are missing, the claim is routed to Manual Review.

## Routing Rules
- Missing mandatory fields → Manual Review
- Injury-related claims → Specialist Queue
- Fraud-related keywords → Investigation Flag
- Estimated damage below 25,000 → Fast-track
- Otherwise → Standard Processing

## OCR Limitations
ACORD forms contain complex layouts and multi-column formatting. Due to OCR uncertainty, ambiguous values are filtered and such cases are intentionally routed for human review to avoid incorrect automation.

## How to Run
```bash
pip install -r requirements.txt
python3 main.py
