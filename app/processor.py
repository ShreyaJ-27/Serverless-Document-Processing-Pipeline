import os
import io
import re
import random
import datetime
from datetime import timezone
from google.cloud import storage

# ── Gemini client (graceful fallback if SDK missing or key absent) ──────────
try:
    import google.generativeai as genai
    _GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    if _GEMINI_KEY:
        genai.configure(api_key=_GEMINI_KEY, transport='rest')
        _GEMINI_AVAILABLE = True
    else:
        _GEMINI_AVAILABLE = False
        print("WARNING: GEMINI_API_KEY not set — falling back to simulated OCR.")
except ImportError:
    _GEMINI_AVAILABLE = False
    print("WARNING: google-generativeai not installed — falling back to simulated OCR.")

_GCS_CLIENT = None

def _get_gcs_client():
    global _GCS_CLIENT
    if _GCS_CLIENT is None:
        _GCS_CLIENT = storage.Client()
    return _GCS_CLIENT


def _download_blob(bucket: str, filename: str) -> str:
    """Download a GCS object and return its text content (UTF-8)."""
    client = _get_gcs_client()
    blob = client.bucket(bucket).blob(filename)
    content = blob.download_as_bytes()
    # Try to decode as text; fall back to latin-1 to avoid errors
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="replace")


def _gemini_process(text: str, filename: str) -> dict:
    """Use Gemini to classify, detect language, translate, and summarise."""
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    prompt = f"""
You are a document intelligence assistant. Analyse the following document content and return a JSON object (and ONLY a JSON object, no markdown fences) with these exact keys:

- "document_type": one of [invoice, contract, resume, receipt, report, memo, letter, other]
- "language": ISO 639-1 code of the ORIGINAL language (e.g. "en", "fr", "es")
- "english_text": the full text translated to English (if already English, return as-is)
- "summary": a 1-2 sentence summary in English
- "tags": a comma-separated list of 1-3 relevant keyword tags from [invoice, receipt, contract, report, memo, confidential, hr, finance, legal, technical, medical]
- "word_count": integer word count of the ORIGINAL text

Document filename: {filename}

Document content:
\"\"\"
{text[:8000]}
\"\"\"
"""
    response = model.generate_content(prompt)
    raw = response.text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()
    import json
    return json.loads(raw)


def _simulated_process(filename: str) -> dict:
    """Fallback mock OCR when Gemini is unavailable."""
    tags_pool = ["invoice", "receipt", "contract", "report", "memo", "confidential", "hr", "finance", "legal"]
    tags = random.sample(tags_pool, k=random.randint(1, 3))
    return {
        "document_type": random.choice(["invoice", "contract", "resume", "receipt", "report", "memo"]),
        "language": "en",
        "english_text": "(simulated — Gemini not configured)",
        "summary": f"Simulated processing of {filename}.",
        "tags": ",".join(tags),
        "word_count": random.randint(100, 5000),
    }


def process_document(bucket: str, filename: str) -> dict:
    """
    Main entry point called by main.py.
    Downloads the file, runs Gemini (or fallback), and returns a metadata dict
    ready for BigQuery insertion.
    """
    print(f"Processing gs://{bucket}/{filename}")

    gemini_result = None

    if _GEMINI_AVAILABLE:
        try:
            text = _download_blob(bucket, filename)
            gemini_result = _gemini_process(text, filename)
        except Exception as exc:
            print(f"Gemini processing failed: {exc} — using simulated fallback.")

    if gemini_result is None:
        gemini_result = _simulated_process(filename)

    metadata = {
        "filename": filename,
        "processing_date": datetime.datetime.now(timezone.utc).isoformat(),
        "tags": gemini_result.get("tags", ""),
        "word_count": int(gemini_result.get("word_count", 0)),
        "document_type": gemini_result.get("document_type", "other"),
        "language": gemini_result.get("language", "en"),
        "summary": gemini_result.get("summary", ""),
    }

    print(f"Metadata extracted: {metadata}")
    return metadata
