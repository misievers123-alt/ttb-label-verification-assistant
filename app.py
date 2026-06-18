"""TTB Label Verification Assistant.

Author: Michael E. Sievers
"""

import csv
import io
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import streamlit as st
from PIL import Image, ImageOps

try:
    import pytesseract
except ImportError:  # pragma: no cover - handled in the UI
    pytesseract = None

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - fallback keeps the app usable
    fuzz = None
    from difflib import SequenceMatcher


GOVERNMENT_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should "
    "not drink alcoholic beverages during pregnancy because of the risk of "
    "birth defects. (2) Consumption of alcoholic beverages impairs your "
    "ability to drive a car or operate machinery, and may cause health problems."
)

FIELD_WEIGHTS = {
    "Government Warning": 0.35,
    "Alcohol Content / ABV": 0.25,
    "Brand Name": 0.20,
    "Net Contents": 0.10,
    "Class/Type": 0.10,
}

PASS_THRESHOLD = 90
REVIEW_THRESHOLD = 70
WARNING_FAIL_THRESHOLD = 60
WARNING_PARTIAL_THRESHOLD = 80
OCR_MIN_TEXT_LENGTH = 30


@dataclass
class FieldResult:
    expected: str
    observed: str
    detected: str
    score: int
    method: str
    status: str
    notes: str


@dataclass
class LabelReview:
    filename: str
    ocr_text: str
    results: Dict[str, FieldResult]
    overall_score: int
    status: str
    processing_seconds: float
    ocr_quality_note: str
    ocr_confidence: float | None


def normalize_text(value: str) -> str:
    value = value or ""
    value = value.upper()
    value = value.replace("&", " AND ")
    value = re.sub(r"[^A-Z0-9.% ]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_warning(value: str) -> str:
    value = normalize_text(value)
    value = value.replace("GOVERNMENT WARNING", "GOVERNMENT WARNING ")
    return re.sub(r"\s+", " ", value).strip()


def fuzzy_score(expected: str, observed: str) -> int:
    expected_norm = normalize_text(expected)
    observed_norm = normalize_text(observed)
    if not expected_norm or not observed_norm:
        return 0
    if expected_norm in observed_norm:
        return 100
    if fuzz:
        return int(
            max(
                fuzz.partial_ratio(expected_norm, observed_norm),
                fuzz.token_set_ratio(expected_norm, observed_norm),
            )
        )
    return int(SequenceMatcher(None, expected_norm, observed_norm).ratio() * 100)


def best_fuzzy_match(expected: str, ocr_text: str) -> Tuple[str, int]:
    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
    candidates = lines + ([" ".join(lines)] if lines else [])
    if not candidates:
        return "", 0

    best_text = ""
    best_score = 0
    for candidate in candidates:
        score = fuzzy_score(expected, candidate)
        if score > best_score:
            best_text = candidate
            best_score = score
    return best_text, best_score


def extract_abv_candidates(text: str) -> str:
    patterns = [
        r"\b\d{1,2}(?:\.\d+)?\s*%\s*(?:ALC\.?|ALCOHOL)?\s*(?:BY\s+VOL(?:UME)?\.?|ABV)?",
        r"\bABV\s*\d{1,2}(?:\.\d+)?\s*%",
        r"\bALC\.?\s*\d{1,2}(?:\.\d+)?\s*%\s*BY\s+VOL\.?",
        r"\bALCOHOL\s+\d{1,2}(?:\.\d+)?\s*%\s*BY\s+VOL(?:UME)?\.?",
    ]
    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return " ".join(dict.fromkeys(match.strip() for match in matches))


def extract_net_contents_candidates(text: str) -> str:
    pattern = (
        r"\b\d+(?:\.\d+)?\s*(?:ML|L|LITER|LITERS|OZ|FL\s*OZ|PINT|PINTS|"
        r"QUART|QUARTS|GALLON|GALLONS)\b"
    )
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    return " ".join(dict.fromkeys(match.strip() for match in matches))


def numeric_value(value: str) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", value or "")
    return float(match.group()) if match else None


def normalized_abv_score(expected: str, observed: str) -> int:
    expected_value = numeric_value(expected)
    observed_values = [float(v) for v in re.findall(r"\d{1,2}(?:\.\d+)?", observed or "")]
    if expected_value is None or not observed_values:
        return 0
    closest_delta = min(abs(expected_value - candidate) for candidate in observed_values)
    if closest_delta <= 0.05:
        return 100
    if closest_delta <= 0.2:
        return 95
    if closest_delta <= 0.5:
        return 75
    if closest_delta <= 1.0:
        return 55
    return 0


def normalize_volume(value: str) -> Tuple[float | None, str]:
    value_norm = normalize_text(value)
    number = numeric_value(value_norm)
    if number is None:
        return None, ""
    if re.search(r"\bML\b", value_norm):
        return number, "ML"
    if re.search(r"\bL(?:ITER|ITERS)?\b", value_norm):
        return number * 1000, "ML"
    if re.search(r"\b(?:FL OZ|OZ)\b", value_norm):
        return number, "OZ"
    if re.search(r"\bPINTS?\b", value_norm):
        return number * 16, "OZ"
    if re.search(r"\bQUARTS?\b", value_norm):
        return number * 32, "OZ"
    if re.search(r"\bGALLONS?\b", value_norm):
        return number * 128, "OZ"
    return number, ""


def normalized_net_contents_score(expected: str, observed: str) -> int:
    expected_amount, expected_unit = normalize_volume(expected)
    if expected_amount is None:
        return 0

    candidates = re.findall(
        r"\d+(?:\.\d+)?\s*(?:ML|L|LITER|LITERS|OZ|FL\s*OZ|PINT|PINTS|QUART|QUARTS|GALLON|GALLONS)",
        observed or "",
        flags=re.IGNORECASE,
    )
    for candidate in candidates:
        observed_amount, observed_unit = normalize_volume(candidate)
        if observed_amount is None:
            continue
        if expected_unit and observed_unit and expected_unit != observed_unit:
            continue
        tolerance = max(expected_amount * 0.01, 0.1)
        if abs(expected_amount - observed_amount) <= tolerance:
            return 100
    return 0


def warning_score(ocr_text: str) -> int:
    expected = normalize_warning(GOVERNMENT_WARNING)
    observed = normalize_warning(ocr_text)
    if expected in observed:
        return 100
    if not observed:
        return 0
    if fuzz:
        return min(int(fuzz.partial_ratio(expected, observed)), 99)
    return min(int(SequenceMatcher(None, expected, observed).ratio() * 100), 99)


def warning_detected_text(ocr_text: str, score: int) -> str:
    if score == 100:
        return "Full required Government Warning text detected in OCR output."
    if score >= WARNING_PARTIAL_THRESHOLD:
        return "Partial warning-like text detected; human review required."
    return ""


def ocr_quality_note(ocr_text: str) -> str:
    normalized = normalize_text(ocr_text)
    if not normalized:
        return "No readable OCR text was extracted. Route to human review."
    if len(normalized) < OCR_MIN_TEXT_LENGTH:
        return "OCR text is very short. Image quality, orientation, or contrast may be poor."
    return ""


def field_status(score: int) -> str:
    if score >= 90:
        return "Match"
    if score >= 60:
        return "Needs Review"
    return "Mismatch"


def warning_status(score: int) -> str:
    if score == 100:
        return "Found"
    if score >= WARNING_PARTIAL_THRESHOLD:
        return "Partial Match"
    return "Missing"


def warning_notes(score: int) -> str:
    status = warning_status(score)
    if status == "Found":
        return "Required warning text appears to be present after normalization."
    if status == "Partial Match":
        return "Warning resembles required text but needs human confirmation."
    return "Required warning text was not found with sufficient confidence."


def run_ocr(image: Image.Image) -> Tuple[str, float | None]:
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed. Install requirements.txt and try again.")

    prepared = ImageOps.exif_transpose(image).convert("L")
    prepared = ImageOps.autocontrast(prepared)
    ocr_text = pytesseract.image_to_string(prepared)

    confidence_values = []
    try:
        data = pytesseract.image_to_data(prepared, output_type=pytesseract.Output.DICT)
        for raw_conf in data.get("conf", []):
            try:
                conf = float(raw_conf)
            except (TypeError, ValueError):
                continue
            if conf >= 0:
                confidence_values.append(conf)
    except Exception:
        confidence_values = []

    avg_confidence = (
        sum(confidence_values) / len(confidence_values) if confidence_values else None
    )
    return ocr_text, avg_confidence


def score_fields(expected_fields: Dict[str, str], ocr_text: str) -> Dict[str, FieldResult]:
    brand_detected, brand_score = best_fuzzy_match(expected_fields["Brand Name"], ocr_text)
    class_detected, class_score = best_fuzzy_match(expected_fields["Class/Type"], ocr_text)
    abv_detected = extract_abv_candidates(ocr_text)
    net_detected = extract_net_contents_candidates(ocr_text)
    warning_match_score = warning_score(ocr_text)
    warning_detected = warning_detected_text(ocr_text, warning_match_score)

    results = {
        "Brand Name": FieldResult(
            expected_fields["Brand Name"],
            brand_detected,
            brand_detected,
            brand_score,
            "Fuzzy text match",
            "",
            "Best OCR text match; allows punctuation, capitalization, and OCR variation.",
        ),
        "Class/Type": FieldResult(
            expected_fields["Class/Type"],
            class_detected,
            class_detected,
            class_score,
            "Fuzzy text match",
            "",
            "Best OCR text match because class/type may appear in several label positions.",
        ),
        "Alcohol Content / ABV": FieldResult(
            expected_fields["Alcohol Content / ABV"],
            abv_detected,
            abv_detected,
            normalized_abv_score(expected_fields["Alcohol Content / ABV"], abv_detected),
            "Normalized numeric comparison",
            "",
            "Compares percentage values extracted directly from OCR text.",
        ),
        "Net Contents": FieldResult(
            expected_fields["Net Contents"],
            net_detected,
            net_detected,
            normalized_net_contents_score(expected_fields["Net Contents"], net_detected),
            "Normalized volume comparison",
            "",
            "Compares volume values extracted directly from OCR text.",
        ),
        "Government Warning": FieldResult(
            GOVERNMENT_WARNING,
            warning_detected,
            warning_detected,
            warning_match_score,
            "Normalized hard-check comparison",
            warning_status(warning_match_score),
            warning_notes(warning_match_score),
        ),
    }

    for field, result in results.items():
        if field != "Government Warning":
            result.status = field_status(result.score)
    return results


def weighted_score(results: Dict[str, FieldResult]) -> int:
    return round(sum(results[field].score * weight for field, weight in FIELD_WEIGHTS.items()))


def status_for_review(score: int, results: Dict[str, FieldResult], ocr_text: str) -> str:
    warning = results["Government Warning"]
    if warning.status == "Missing":
        return "Fail"
    if warning.status == "Partial Match":
        return "Needs Review"
    key_fields = ["Brand Name", "Class/Type", "Alcohol Content / ABV", "Net Contents"]
    if any(results[field].score < 60 for field in key_fields):
        return "Needs Review"
    if len(normalize_text(ocr_text)) < OCR_MIN_TEXT_LENGTH:
        return "Needs Review"
    if score >= PASS_THRESHOLD:
        return "Pass"
    if score >= REVIEW_THRESHOLD:
        return "Needs Review"
    return "Fail"


def review_label(uploaded_file, expected_fields: Dict[str, str]) -> LabelReview:
    start = time.perf_counter()
    image = Image.open(uploaded_file)
    ocr_text, ocr_confidence = run_ocr(image)
    results = score_fields(expected_fields, ocr_text)
    overall = weighted_score(results)
    status = status_for_review(overall, results, ocr_text)
    elapsed = time.perf_counter() - start
    return LabelReview(
        uploaded_file.name,
        ocr_text,
        results,
        overall,
        status,
        elapsed,
        ocr_quality_note(ocr_text),
        ocr_confidence,
    )


def comparison_rows(review: LabelReview) -> List[Dict[str, str | int]]:
    return [
        {
            "Field": field,
            "Application Value": result.expected,
            "Detected OCR Value": result.detected[:500] if result.detected else "Not detected",
            "Score": result.score,
            "Status": result.status,
            "Notes": result.notes,
        }
        for field, result in review.results.items()
    ]


def build_csv(reviews: List[LabelReview]) -> str:
    output = io.StringIO()
    fieldnames = [
        "Filename",
        "Overall Score",
        "Overall Status",
        "Processing Seconds",
        "OCR Quality Note",
        "OCR Confidence",
        "Field",
        "Application Value",
        "Detected OCR Value",
        "Field Score",
        "Field Status",
        "Notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for review in reviews:
        for row in comparison_rows(review):
            writer.writerow(
                {
                    "Filename": review.filename,
                    "Overall Score": review.overall_score,
                    "Overall Status": review.status,
                    "Processing Seconds": f"{review.processing_seconds:.2f}",
                    "OCR Quality Note": review.ocr_quality_note,
                    "OCR Confidence": (
                        f"{review.ocr_confidence:.1f}"
                        if review.ocr_confidence is not None
                        else "Unavailable"
                    ),
                    "Field": row["Field"],
                    "Application Value": row["Application Value"],
                    "Detected OCR Value": row["Detected OCR Value"],
                    "Field Score": row["Score"],
                    "Field Status": row["Status"],
                    "Notes": row["Notes"],
                }
            )
    return output.getvalue()


def render_score_bar(label: str, score: int) -> None:
    st.metric(label, f"{score}/100")
    st.progress(score / 100)


st.set_page_config(
    page_title="TTB Label Verification Assistant",
    layout="wide",
)

st.title("TTB Label Verification Assistant")
st.caption("Standalone OCR and matching tool for alcohol label verification by TTB compliance agents.")

st.info("Workflow: Label image -> OCR text extraction -> field matching -> confidence scoring -> human review routing.")
st.caption(
    "Known limitation: this prototype does not verify font size, bold formatting, placement, "
    "or full regulatory compliance."
)

with st.sidebar:
    st.header("Application Data")
    brand_name = st.text_input("Brand Name")
    class_type = st.text_input("Class/Type")
    abv = st.text_input("Alcohol Content / ABV", placeholder="Example: 13.5%")
    net_contents = st.text_input("Net Contents", placeholder="Example: 750 ml")
    st.caption("Standalone prototype. No COLA integration. No paid or cloud AI APIs.")
    run_review = st.button("Run Verification", type="primary", use_container_width=True)

uploaded_files = st.file_uploader(
    "Upload alcohol label image(s)",
    type=["png", "jpg", "jpeg", "webp", "tif", "tiff"],
    accept_multiple_files=True,
)

if uploaded_files:
    preview_cols = st.columns(min(len(uploaded_files), 3))
    for index, uploaded_file in enumerate(uploaded_files[:3]):
        with preview_cols[index % len(preview_cols)]:
            st.image(Image.open(uploaded_file), caption=uploaded_file.name, use_container_width=True)
            uploaded_file.seek(0)
else:
    st.info("Upload one or more label images and enter the expected application fields to begin.")

expected = {
    "Brand Name": brand_name,
    "Class/Type": class_type,
    "Alcohol Content / ABV": abv,
    "Net Contents": net_contents,
}

missing_fields = [name for name, value in expected.items() if not value.strip()]

if run_review:
    if not uploaded_files:
        st.error("Please upload at least one label image before running verification.")
    elif missing_fields:
        st.error(f"Please complete these fields: {', '.join(missing_fields)}.")
    else:
        reviews: List[LabelReview] = []
        progress = st.progress(0)

        with st.spinner("Running OCR, matching fields, and routing review status..."):
            try:
                for index, uploaded_file in enumerate(uploaded_files, start=1):
                    uploaded_file.seek(0)
                    reviews.append(review_label(uploaded_file, expected))
                    progress.progress(index / len(uploaded_files))
            except Exception as exc:
                st.error(
                    "OCR could not run. Confirm that Tesseract OCR is installed and available "
                    f"on PATH. Details: {exc}"
                )
                st.stop()

        passed = sum(1 for review in reviews if review.status == "Pass")
        needs_review = sum(1 for review in reviews if review.status == "Needs Review")
        failed = sum(1 for review in reviews if review.status == "Fail")
        avg_seconds = sum(review.processing_seconds for review in reviews) / len(reviews)

        st.subheader("Results Dashboard")
        summary_cols = st.columns(5)
        summary_cols[0].metric("Total Processed", len(reviews))
        summary_cols[1].metric("Passed", passed)
        summary_cols[2].metric("Needs Review", needs_review)
        summary_cols[3].metric("Failed", failed)
        summary_cols[4].metric("Avg Processing Time", f"{avg_seconds:.2f}s")

        st.download_button(
            "Download CSV Results",
            data=build_csv(reviews),
            file_name="ttb_label_verification_results.csv",
            mime="text/csv",
        )

        for review_index, review in enumerate(reviews):
            status_type = {
                "Pass": "success",
                "Needs Review": "warning",
                "Fail": "error",
            }[review.status]

            st.divider()
            st.subheader(review.filename)
            getattr(st, status_type)(f"Status: {review.status}")

            overall_col, warning_col, confidence_col, time_col = st.columns([1, 1, 1, 1])
            with overall_col:
                render_score_bar("Overall Weighted Score", review.overall_score)
            with warning_col:
                warning = review.results["Government Warning"]
                st.metric("Government Warning", warning.status)
                st.progress(warning.score / 100)
            with confidence_col:
                st.metric(
                    "OCR Confidence",
                    (
                        f"{review.ocr_confidence:.1f}/100"
                        if review.ocr_confidence is not None
                        else "Unavailable"
                    ),
                )
            with time_col:
                st.metric("Processing Time", f"{review.processing_seconds:.2f}s")

            if review.ocr_quality_note:
                st.warning(review.ocr_quality_note)

            score_cols = st.columns(4)
            for col, field in zip(
                score_cols,
                ["Brand Name", "Class/Type", "Alcohol Content / ABV", "Net Contents"],
            ):
                with col:
                    render_score_bar(field, review.results[field].score)

            st.subheader("Detected Fields")
            st.dataframe(
                [
                    {
                        "Field": field,
                        "Expected": review.results[field].expected,
                        "Detected From OCR": (
                            review.results[field].detected
                            if review.results[field].detected
                            else "Not detected"
                        ),
                        "Score": review.results[field].score,
                        "Status": review.results[field].status,
                    }
                    for field in [
                        "Brand Name",
                        "Class/Type",
                        "Alcohol Content / ABV",
                        "Net Contents",
                        "Government Warning",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

            st.dataframe(
                comparison_rows(review),
                use_container_width=True,
                hide_index=True,
            )

            with st.expander("OCR text"):
                st.text_area(
                    "Extracted text",
                    review.ocr_text,
                    height=240,
                    key=f"ocr-{review_index}-{review.filename}",
                )

        with st.expander("Required Government Warning text"):
            st.write(GOVERNMENT_WARNING)
