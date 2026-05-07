# Serverless Document Processing Pipeline

A polished, production-ready pipeline that turns document uploads into searchable metadata using Cloud Run, Pub/Sub, BigQuery, and a modern frontend.

**Live demo**: https://doc-frontend-5502500586.us-central1.run.app

## Why this matters

This project showcases a fully automated, serverless pipeline for document intelligence:

- Upload a document to Cloud Storage
- Trigger a Pub/Sub event
- Process the document with Gemini metadata extraction or a fallback processor
- Persist structured results to BigQuery
- Visualize and filter documents in a responsive web UI

## What’s included

- `app/` — FastAPI backend with Cloud Pub/Sub push handling and BigQuery ingestion
- `frontend/` — Vite + React SPA served by nginx with `/api` proxying to the backend
- `Dockerfile` — Backend container configuration for Cloud Run
- `deploy.ps1` — Cloud-ready deployment script for backend, frontend, Pub/Sub, and BigQuery
- `requirements.txt` — Python runtime dependencies
- `sample.txt` — Sample document for pipeline validation

## Highlights

- **Cloud Run backend** with automated deployment support
- **Gemini integration** for document classification, language detection, summarization, and tagging
- **BigQuery storage** for analytics-ready document metadata
- **Frontend dashboard** with tag filtering and live document results
- **Resilient fallback mode** when Gemini is unavailable

## Quick start

1. Install backend dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Deploy backend to Cloud Run:
   ```powershell
   cd d:\vibecw
   gcloud run deploy doc-processor-service --source . --region=us-central1 --allow-unauthenticated --set-env-vars="PROJECT_ID=vibecw,DATASET_ID=doc_processing_db,TABLE_ID=documents"
   ```

3. Deploy frontend to Cloud Run:
   ```powershell
   cd d:\vibecw\frontend
   gcloud run deploy doc-frontend --source . --region=us-central1 --allow-unauthenticated
   ```

4. Trigger the pipeline:
   ```powershell
   gcloud storage cp d:\vibecw\sample.txt gs://<your-bucket-name>/
   ```

5. Verify health:
   ```powershell
   Invoke-WebRequest -Uri https://doc-processor-service-5502500586.us-central1.run.app/health -Method GET
   ```

6. View document output:
   ```powershell
   Invoke-WebRequest -Uri https://doc-processor-service-5502500586.us-central1.run.app/documents -Method GET -UseBasicParsing
   ```

## Notes for reviewers

- Backend configuration is driven by `PROJECT_ID`, `DATASET_ID`, and `TABLE_ID`
- Frontend proxy is configured in `frontend/nginx.conf`
- The project is designed for fast iteration and easy redeployment
