# Form Submission Summary

Use this as a quick reference when completing the Treasury Take Home Test form.

## Applicant Fields

- First Name: MIKE
- Last Name: SIEVERS
- Email: TO BE PROVIDED BY APPLICANT
- Phone Number: TO BE PROVIDED BY APPLICANT

## Required Deliverable Fields

- Source Code Repository: TO BE PROVIDED AT SUBMISSION
- Deployed Application URL: TO BE PROVIDED AT SUBMISSION

Do not invent URLs. Add the actual GitHub repository URL after the repository is created, and add the actual deployed application URL after the Streamlit app is deployed.

## Suggested Short Description

TTB Label Verification Assistant is a standalone Streamlit prototype for alcohol label verification by TTB compliance agents. It uses local OCR, fuzzy matching for Brand Name and Class/Type, strict Government Warning validation, field-level scoring, weighted overall scoring, Pass / Needs Review / Fail routing, batch upload, CSV export, and human-in-the-loop review. It does not integrate with COLA and does not use paid/cloud AI APIs.

## Optional Notes If Asked

The repository includes a generated sample label at `sample_data/old_tom_dist.png`. Future enhancements documented in the README include barcode/UPC scanning where present and normalized input masking for application fields to reduce preventable formatting-based mismatches.
