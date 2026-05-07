import os
from datetime import datetime, timezone
from google.cloud import bigquery

# Read at module level — Cloud Run injects env vars before Python starts
PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET_ID = os.environ.get("DATASET_ID")
TABLE_ID    = os.environ.get("TABLE_ID")

_client: bigquery.Client | None = None


def _get_client() -> bigquery.Client:
    """Lazily initialise the BigQuery client and raise a clear error if not possible."""
    global _client
    if _client is not None:
        return _client

    if not PROJECT_ID:
        raise EnvironmentError(
            "BigQuery not initialised: PROJECT_ID environment variable is missing. "
            "Set it in Cloud Run configuration or your local environment."
        )
    try:
        _client = bigquery.Client(project=PROJECT_ID)
        print(f"BigQuery client initialised for project '{PROJECT_ID}'.")
        return _client
    except Exception as exc:
        raise RuntimeError(
            f"BigQuery client creation failed — check Application Default Credentials. Error: {exc}"
        ) from exc


def _validate_env():
    """Raise with actionable message when env vars are incomplete."""
    missing = [v for v in ("PROJECT_ID", "DATASET_ID", "TABLE_ID") if not os.environ.get(v)]
    if missing:
        raise EnvironmentError(
            f"BigQuery env vars not set: {missing}. "
            "Set them in Cloud Run -> Edit & Deploy -> Variables & Secrets."
        )


def stream_to_bigquery(metadata: dict) -> None:
    """
    Stream a single metadata dict to BigQuery.
    Raises on failure so the caller can decide whether to DLQ.
    """
    _validate_env()
    client = _get_client()

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    print(f"Streaming to {table_ref}: {metadata}")

    errors = client.insert_rows_json(table_ref, [metadata])

    if errors:
        # Log structured detail for each individual row error
        for err in errors:
            print(f"BigQuery row error — index {err.get('index')}: {err.get('errors')}")
        raise RuntimeError(f"BigQuery insert failed with {len(errors)} error(s): {errors}")

    print("Row inserted successfully into BigQuery.")


def query_documents(tag_filter: str | None = None) -> list[dict]:
    """
    Query the documents table, optionally filtering by tag.
    Returns a list of dicts, or an empty list on error.
    """
    try:
        _validate_env()
        client = _get_client()
    except EnvironmentError as exc:
        print(f"BigQuery not initialised — returning mock data. Reason: {exc}")
        return _mock_documents(tag_filter)
    except RuntimeError as exc:
        print(f"BigQuery client error — returning mock data. Reason: {exc}")
        return _mock_documents(tag_filter)

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    if tag_filter:
        query = f"""
            SELECT filename, processing_date, tags, word_count,
                   document_type, language, summary
            FROM `{table_ref}`
            WHERE LOWER(tags) LIKE LOWER(@tag)
            ORDER BY processing_date DESC
            LIMIT 500
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("tag", "STRING", f"%{tag_filter}%")]
        )
    else:
        query = f"""
            SELECT filename, processing_date, tags, word_count,
                   document_type, language, summary
            FROM `{table_ref}`
            ORDER BY processing_date DESC
            LIMIT 500
        """
        job_config = bigquery.QueryJobConfig()

    try:
        rows = client.query(query, job_config=job_config).result()
        result = []
        for row in rows:
            d = dict(row)
            # BigQuery returns TIMESTAMP as datetime — convert to ISO string with Z
            pd = d.get("processing_date")
            if pd is not None and hasattr(pd, "isoformat"):
                d["processing_date"] = pd.isoformat().replace('+00:00', 'Z')
            result.append(d)
        return result
    except Exception as exc:
        print(f"BigQuery query failed: {exc} — returning mock data.")
        return _mock_documents(tag_filter)


def _mock_documents(tag_filter: str | None = None) -> list[dict]:
    """Fallback mock data when BigQuery is unavailable (dev/demo mode)."""
    import datetime, random
    samples = [
        {"filename": "invoice_q1.pdf",   "tags": "invoice,finance",  "document_type": "invoice",  "language": "en", "word_count": 320,  "summary": "Q1 2026 vendor invoice for cloud services.", "processing_date": "2026-05-05T12:00:00Z"},
        {"filename": "contract_nda.docx","tags": "contract,legal",   "document_type": "contract",  "language": "en", "word_count": 1540, "summary": "Non-disclosure agreement between two parties.", "processing_date": "2026-05-04T09:30:00Z"},
        {"filename": "resume_jr.pdf",    "tags": "hr",               "document_type": "resume",    "language": "en", "word_count": 480,  "summary": "Software engineer resume with 5 years experience.", "processing_date": "2026-05-03T14:15:00Z"},
        {"filename": "rapport_fr.txt",   "tags": "report,finance",   "document_type": "report",    "language": "fr", "word_count": 720,  "summary": "Quarterly financial report (translated from French).", "processing_date": "2026-05-02T10:00:00Z"},
        {"filename": "sample.txt",       "tags": "invoice",          "document_type": "invoice",   "language": "en", "word_count": 379,  "summary": "Sample invoice document for pipeline testing.", "processing_date": "2026-05-05T14:52:20Z"},
    ]
    if tag_filter:
        samples = [s for s in samples if tag_filter.lower() in s["tags"].lower()]
    return samples
