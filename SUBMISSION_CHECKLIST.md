# Submission Checklist

Author: Michael E. Sievers

## Submission Links

- GitHub Repository: TO BE PROVIDED AT SUBMISSION
- Deployed Application URL: TO BE PROVIDED AT SUBMISSION

## Deliverable 1: Source Code Repository

Create a GitHub repository and include these files:

- `app.py`
- `requirements.txt`
- `packages.txt`
- `.streamlit/config.toml`
- `.gitignore`
- `README.md`
- `SUBMISSION_CHECKLIST.md`

The README includes setup instructions, run instructions, approach, tools used, assumptions, limitations, security/privacy notes, and human-in-the-loop review guidance.

## Deliverable 2: Deployed Application URL

Recommended deployment:

1. Push the repository to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app from the GitHub repository.
4. Set main file path to `app.py`.
5. Deploy.
6. Copy the Streamlit app URL into the submission form.

## Notes For Submission

The prototype is an AI/OCR decision-support tool for alcohol label verification by TTB compliance reviewers. The core workflow is:

```text
Image -> OCR -> Field Extraction -> Confidence Scoring -> Human Review
```

It focuses on matching, not chatbot interaction. It uses fuzzy matching for Brand Name and Class/Type, strict validation for the Government Warning, field-level scores, weighted overall scores, Pass / Needs Review / Fail routing, batch processing, and CSV export.

It is standalone, does not integrate with COLA, does not use paid external AI APIs, and does not intentionally store uploaded label data.

## Stakeholder Mapping

- Sarah: business need for matching and exception routing.
- Marcus: technical constraints, standalone design, no paid/cloud AI APIs.
- Dave: edge cases such as punctuation and capitalization differences.
- Jenny: compliance requirements, hard Government Warning check, and human review.
