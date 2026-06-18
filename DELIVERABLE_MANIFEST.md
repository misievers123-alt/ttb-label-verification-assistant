# Deliverable Manifest

This archive contains the complete source and documentation package for the TTB Label Verification Assistant prototype.

## Included Files

- `app.py` - Streamlit application with OCR extraction, field comparison, scoring, batch upload, CSV export, and human-review routing.
- `README.md` - Project summary, mission fit, setup/run instructions, scoring methodology, assumptions, limitations, security/privacy notes, human-in-the-loop explanation, stakeholder alignment, trade-offs, and deployment instructions.
- `requirements.txt` - Python dependencies.
- `packages.txt` - Streamlit Cloud system package dependency for Tesseract OCR.
- `.streamlit/config.toml` - Streamlit configuration.
- `.gitignore` - Repository hygiene file.
- `SUBMISSION_CHECKLIST.md` - Checklist for source repository and deployed URL deliverables.
- `DEPLOYMENT_NOTES.md` - Practical deployment steps for GitHub and Streamlit Community Cloud.
- `FORM_SUBMISSION_SUMMARY.md` - Form-field reference with safe placeholders for repository and deployed application URLs.

## Assessment Alignment

The prototype is designed around the assessment mission:

```text
Image -> OCR -> Field Extraction -> Confidence Scoring -> Human Review
```

It is a standalone AI/OCR decision-support tool for alcohol label verification by TTB compliance agents. It is not a chatbot, does not integrate with COLA, does not require paid/cloud AI APIs, and does not make autonomous approval decisions.

## Verification Notes

The source code has been syntax-checked with:

```bash
py -3.11 -m py_compile app.py
```

The source code has been syntax-checked. Final deployment testing should be completed after the GitHub repository is connected to Streamlit Community Cloud.
