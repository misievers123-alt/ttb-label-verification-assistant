# TTB Label Verification Assistant

Author: Michael E. Sievers

## Submission Links

- GitHub Repository: TO BE PROVIDED AT SUBMISSION
- Deployed Application URL: TO BE PROVIDED AT SUBMISSION

## Project Summary

This prototype demonstrates how AI-assisted OCR and automated field verification can reduce repetitive manual review work performed by TTB label compliance agents.

The system extracts text from alcohol beverage labels, compares the extracted information against application data, validates required government warning language, and produces confidence scores to assist reviewers.

The solution is intentionally designed as a decision-support tool rather than an autonomous approval system. Human reviewers remain responsible for final compliance determinations.

Key design goals included:

- Fast response times.
- Simple and accessible user experience.
- Local processing without external AI dependencies.
- Human-in-the-loop review.
- Support for future batch-processing workflows.
- Transparent scoring and explainable results.

This prototype uses AI/OCR as a decision-support tool, not an autonomous approval system.

## Mission Fit

The core mission is operational label verification for TTB compliance review. In the assessment framing, "a lot of what we do is just matching." This prototype is built around that mission:

- OCR extraction from uploaded label images.
- A transparent matching engine for expected application fields.
- Confidence scoring from 0-100.
- Hard-check validation for the required Government Warning.
- Human review routing for uncertain or low-confidence cases.
- Batch processing for multiple label images.
- Fast response time, with a prototype goal of under 5 seconds per image when local OCR and image quality allow it.

The AI-assisted workflow is intentionally simple:

```text
Image
  -> OCR
  -> Field Extraction
  -> Confidence Scoring
  -> Human Review
```

It is not a chatbot and does not use generative AI to make autonomous approval decisions.

## Stakeholder Alignment

The prototype reflects the assessment stakeholders:

- **Sarah - business requirements:** focuses the app on repetitive matching work, exception routing, and faster review throughput.
- **Marcus - technical constraints:** keeps the solution standalone, simple to deploy, free of COLA integration, and free of paid/cloud AI APIs.
- **Dave - edge cases and operational reality:** uses fuzzy matching so values like `STONE'S THROW` and `Stone's Throw` are treated as likely matches instead of false failures.
- **Jenny - compliance requirements and future ideas:** treats the Government Warning as a hard compliance check, preserves human review, and documents future enhancements without overbuilding the prototype.

## Features

- Upload one or more alcohol label images.
- Enter expected application values for Brand Name, Class/Type, Alcohol Content / ABV, and Net Contents.
- Run local OCR with `pytesseract`.
- Display extracted OCR text for reviewer validation.
- Compare OCR text against expected application fields.
- Validate required Government Warning text as Found, Partial Match, or Missing.
- Show field-level scores from 0-100.
- Show an overall weighted score.
- Route each label to Pass, Needs Review, or Fail.
- Flag poor image quality or no readable OCR text for human review.
- Summarize batch results with total processed, passed, needs review, failed, and average processing time.
- Download field-level results as CSV.

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install the free Tesseract OCR engine if it is not already available:

- Windows: install Tesseract from a trusted distribution such as UB Mannheim, then add the install folder to `PATH`.
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

## How To Run

```bash
streamlit run app.py
```

Then open the local Streamlit URL, upload label image files, enter the expected application fields, and select **Run Verification**.

## Source Repository Contents

Expected repository files:

- `app.py`: Streamlit application, OCR pipeline, matching engine, scoring logic, batch processing, and CSV export.
- `requirements.txt`: Python package dependencies.
- `packages.txt`: System dependency used by Streamlit Community Cloud to install the free Tesseract OCR engine.
- `.streamlit/config.toml`: Streamlit runtime configuration.
- `.gitignore`: Keeps local caches, temporary files, and output archives out of the source repository.
- `README.md`: Setup, run, scoring, assumptions, limitations, security, and human review documentation.
- `SUBMISSION_CHECKLIST.md`: Short deliverables checklist for the assessment submission.
- `FORM_SUBMISSION_SUMMARY.md`: Form-field reference with URL placeholders and a short project description.

## Deployment

Recommended no-cost deployment path:

1. Create a GitHub repository.
2. Push these project files to the repository.
3. Go to [Streamlit Community Cloud](https://streamlit.io/cloud).
4. Select **New app**.
5. Choose the GitHub repository and branch.
6. Set the main file path to `app.py`.
7. Deploy.

Streamlit Cloud reads `requirements.txt` for Python packages and `packages.txt` for system packages. The included `packages.txt` installs `tesseract-ocr`, which is required by `pytesseract`.

After deployment, use the Streamlit app URL as the **Deployed Application URL** deliverable.

Example Git commands after creating an empty GitHub repository:

```bash
git init
git add .
git commit -m "Initial TTB label verification assistant"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git branch -M main
git push -u origin main
```

Then deploy that repository through Streamlit Community Cloud.

## Scoring Methodology

Each label field receives a score from 0-100:

- 100 = exact or normalized match.
- 80-99 = likely match with minor formatting or OCR differences.
- 60-79 = needs human review.
- 0-59 = likely mismatch.

The overall score is weighted by compliance importance:

| Field | Weight | Matching Approach |
| --- | ---: | --- |
| Government Warning | 35% | Normalized hard-check comparison |
| Alcohol Content / ABV | 25% | Normalized numeric comparison |
| Brand Name | 20% | Fuzzy text match |
| Net Contents | 10% | Normalized volume comparison |
| Class/Type | 10% | Fuzzy text match |

The scoring system is designed to prioritize agent attention, not replace agent judgment. Exact legal requirements such as the government warning are treated as hard checks, while fields such as brand name allow fuzzy matching to account for punctuation, capitalization, and OCR variation.

The app prevents high overall scores from masking a low-confidence field match. If Brand Name, Class/Type, Alcohol Content / ABV, or Net Contents scores below 60, the overall status is routed to **Needs Review** even when the weighted score is high.

This prototype is a decision-support tool requiring human review for low-confidence OCR results.

Example fuzzy match:

| Application Value | Label/OCR Value | Score | Status |
| --- | --- | ---: | --- |
| `STONE'S THROW` | `Stone's Throw` | High confidence, approximately 98-100 depending on OCR output | Match |

This is deliberate. The app should not fail a label only because of capitalization, punctuation, or minor OCR variation.

## Status Rules

- **Pass**: overall score is 90-100, the Government Warning is present with high confidence, and OCR text is sufficient.
- **Needs Review**: overall score is 70-89, the Government Warning is partial, or OCR text appears too short for reliable automated screening.
- **Fail**: overall score is below 70 or the required Government Warning is missing with low confidence.

Government Warning is a hard compliance check. If the required warning is missing or only partially detected, the label is routed to Needs Review or Fail regardless of the weighted score.

## Assumptions

- A reviewer enters application data for the label or label set being evaluated.
- Batch mode uses the same application data for all uploaded images.
- OCR quality depends on resolution, lighting, contrast, orientation, label curvature, and font style.
- Brand and Class/Type may appear anywhere in the OCR text, so those fields use fuzzy matching.
- ABV is checked by extracting percentage-like values from OCR text.
- Net contents supports common units such as ml, L, oz, fl oz, pint, quart, and gallon.
- Government Warning validation normalizes casing, punctuation, spacing, and line breaks before matching.

## Limitations

- This prototype does not integrate with COLA systems or submit decisions to TTB.
- It is standalone by design and requires no COLA system integration.
- It does not verify type size, contrast, artwork layout, mandatory placement, formula details, or every regulatory rule.
- It checks Government Warning wording from OCR text, but does not verify bold formatting, font size, or exact placement; those visual compliance checks remain in scope for human review.
- OCR can misread stylized fonts, curved bottles, reflective materials, low-resolution images, or rotated text.
- Fuzzy matching can produce false positives if unrelated text resembles an expected field.
- Processing speed depends on local CPU, Tesseract installation, image size, and number of uploaded files.
- This is a screening and triage prototype, not a legal compliance determination engine.

## Security And Privacy Notes

- The app runs locally and does not require external paid APIs.
- The app avoids paid or cloud AI APIs.
- Uploaded images are processed in memory during the Streamlit session.
- The prototype does not intentionally persist uploaded labels, OCR text, or application data.
- Reviewers should still follow agency data handling rules for sensitive or non-public application materials.
- Production deployment would need authentication, access controls, audit logging, retention rules, and secure infrastructure review.

## Human-In-The-Loop Review

The assistant is designed to reduce repetitive manual verification and help agents focus on exceptions. A human reviewer should inspect every Needs Review or Fail result, compare the OCR text against the original label image, and make the final compliance judgment.

Even Pass results should be spot-checked when source images are low quality, OCR text is sparse, or label formatting is unusual.

## Trade-Offs

- `pytesseract` keeps the prototype free and standalone, but OCR accuracy is lower than some commercial OCR services.
- Fuzzy matching improves operational usefulness for common formatting differences, but it can occasionally score unrelated text too highly.
- Strict Government Warning handling reduces compliance risk, but partial OCR reads may route otherwise acceptable labels to human review.
- Batch upload improves reviewer throughput, but the prototype assumes the same application fields apply to all uploaded images in that batch.
- The UI is intentionally simple for non-technical agents, so advanced tuning controls are left out of the first prototype.

## Future Enhancements

- Add reviewer notes and disposition tracking.
- Add side-by-side OCR highlighting over the label image.
- Add field-specific extraction zones for front, back, and side labels.
- Add confidence calibration using historical reviewed labels.
- Add queue management for high-volume review operations.
- Add integration hooks for approved internal systems after security review.
- Add automated test fixtures with sample label images and expected outcomes.
- Add barcode/UPC scan support so reviewers can optionally capture product identifiers from label or package images and compare them against application or distribution metadata when available.
- Explore barcode/UPC scanning where present on alcohol packaging. Not all labels include scannable product identifiers, so this would be an optional enrichment feature rather than a required validation step.
