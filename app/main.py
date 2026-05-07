import base64
import json
import os
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .processor import process_document
from .bigquery import stream_to_bigquery, query_documents

app = FastAPI(title="Doc Processor API")

# Allow the frontend (Cloud Run / localhost:5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pub/Sub models ───────────────────────────────────────────────────────────

class PubSubMessage(BaseModel):
    data: str
    messageId: str
    publishTime: str
    attributes: dict = None

class PubSubRequest(BaseModel):
    message: PubSubMessage
    subscription: str


# ── Pub/Sub push endpoint ────────────────────────────────────────────────────

@app.post("/")
async def receive_pubsub(request: Request):
    """Receive push messages from Cloud Pub/Sub."""
    try:
        body = await request.json()
        envelope = PubSubRequest(**body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Pub/Sub envelope: {exc}")

    if not envelope.message.data:
        raise HTTPException(status_code=400, detail="Empty data field in Pub/Sub message.")

    try:
        decoded = base64.b64decode(envelope.message.data).decode("utf-8")
        event_data = json.loads(decoded)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot decode message data: {exc}")

    bucket   = event_data.get("bucket")
    filename = event_data.get("name")

    if not bucket or not filename:
        # Not a storage event we care about — acknowledge silently
        print(f"Ignoring non-storage event: {event_data}")
        return {"status": "ignored"}

    print(f"Handling upload: gs://{bucket}/{filename}")

    # ── Process ──────────────────────────────────────────────────────────────
    try:
        metadata = process_document(bucket, filename)
    except Exception as exc:
        print(f"ERROR during OCR processing: {exc}")
        # Return 500 → Pub/Sub retries → eventually routes to DLQ
        raise HTTPException(status_code=500, detail=f"Processing error: {exc}")

    # ── Store ─────────────────────────────────────────────────────────────────
    try:
        stream_to_bigquery(metadata)
    except EnvironmentError as exc:
        # BigQuery not configured — log and acknowledge so we don't spam retries
        print(f"BigQuery not configured (acknowledging message): {exc}")
        return {"status": "bq_skipped", "reason": str(exc)}
    except Exception as exc:
        print(f"ERROR streaming to BigQuery: {exc}")
        raise HTTPException(status_code=500, detail=f"BigQuery error: {exc}")

    return {"status": "success", "filename": filename}


# ── Frontend data endpoints ───────────────────────────────────────────────────

@app.get("/documents")
def get_documents(tag: str = Query(default=None, description="Filter by tag substring")):
    """
    Return a list of processed documents from BigQuery.
    Falls back to mock data if BigQuery is not available.
    """
    docs = query_documents(tag_filter=tag)
    # processing_date is always an ISO string from query_documents()
    return {"documents": docs, "count": len(docs)}


@app.get("/tags")
def get_tags():
    """Return a deduplicated list of all tags present in the dataset."""
    docs = query_documents()
    tag_set = set()
    for doc in docs:
        for t in (doc.get("tags") or "").split(","):
            t = t.strip()
            if t:
                tag_set.add(t)
    return {"tags": sorted(tag_set)}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "doc-processor-api"}
