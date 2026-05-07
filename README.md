# 🚀 Serverless Document Intelligence Pipeline

> A production-ready, event-driven document processing platform built with Google Cloud, Gemini AI, and modern serverless architecture.

🌐 **Live Demo:**
[Serverless Document Intelligence Pipeline](https://doc-frontend-5502500586.us-central1.run.app?utm_source=chatgpt.com)

---

## ✨ Overview

This project demonstrates a scalable, cloud-native pipeline that automatically transforms uploaded documents into structured, searchable metadata.

Built using **Cloud Run, Pub/Sub, BigQuery, FastAPI, React, and Gemini AI**, the system processes documents in real time and exposes analytics-ready insights through a clean frontend dashboard.

The architecture is fully serverless, highly modular, and designed for production deployment workflows.

---

# 🏗️ Architecture

```text
User Upload
     │
     ▼
Google Cloud Storage
     │
     ▼
Pub/Sub Event Trigger
     │
     ▼
Cloud Run (FastAPI Backend)
     │
     ├── Gemini Metadata Extraction
     │
     ├── Fallback Processing Logic
     │
     ▼
BigQuery Storage
     │
     ▼
React Dashboard UI
```

---

# 🔥 Key Features

### ⚡ Event-Driven Processing

Automatically triggers document workflows whenever a file is uploaded to Cloud Storage.

### 🧠 Gemini AI Integration

Extracts:

* Document summaries
* Language detection
* Classification
* Smart tags and metadata

### ☁️ Fully Serverless Deployment

Powered entirely by managed Google Cloud services:

* Cloud Run
* Pub/Sub
* BigQuery
* Cloud Storage

### 📊 Analytics-Ready Storage

Structured metadata is persisted in BigQuery for querying, reporting, and visualization.

### 🎨 Modern Frontend Dashboard

Responsive React interface with:

* Live document listing
* Tag-based filtering
* Metadata visualization

### 🛡️ Fault-Tolerant Design

Includes fallback processing when Gemini APIs are unavailable.

---

# 🛠️ Tech Stack

| Category       | Technologies            |
| -------------- | ----------------------- |
| Backend        | FastAPI, Python         |
| Frontend       | React, Vite, nginx      |
| Cloud Platform | Google Cloud Platform   |
| AI Layer       | Gemini API              |
| Messaging      | Pub/Sub                 |
| Storage        | BigQuery, Cloud Storage |
| Deployment     | Docker, Cloud Run       |

---

# 📂 Project Structure

```bash
├── app/                  # FastAPI backend + Pub/Sub handlers
├── frontend/             # React + Vite frontend application
├── Dockerfile            # Backend container configuration
├── deploy.ps1            # Automated deployment script
├── requirements.txt      # Python dependencies
├── sample.txt            # Sample document for testing
└── README.md
```

---

# 🚀 Getting Started

## 1️⃣ Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

---

## 2️⃣ Deploy Backend

```powershell
cd d:\project_folder

gcloud run deploy doc-processor-service `
  --source . `
  --region=us-central1 `
  --allow-unauthenticated `
  --set-env-vars="PROJECT_ID=project_folder,DATASET_ID=doc_processing_db,TABLE_ID=documents"
```

---

## 3️⃣ Deploy Frontend

```powershell
cd d:\project_folder\frontend

gcloud run deploy doc-frontend `
  --source . `
  --region=us-central1 `
  --allow-unauthenticated
```

---

## 4️⃣ Upload a Document

```powershell
gcloud storage cp d:\project_folder\sample.txt gs://<your-bucket-name>/
```

---

## 5️⃣ Verify Backend Health

```powershell
Invoke-WebRequest `
  -Uri https://doc-processor-service-5502500586.us-central1.run.app/health `
  -Method GET
```

---

## 6️⃣ View Processed Documents

```powershell
Invoke-WebRequest `
  -Uri https://doc-processor-service-5502500586.us-central1.run.app/documents `
  -Method GET `
  -UseBasicParsing
```

---

# 📸 Product Highlights

### 🔎 Smart Metadata Extraction

Automatically generates structured insights from raw documents.

### 📈 Cloud-Native Scalability

Handles asynchronous workloads using event-driven architecture.

### ⚙️ Production-Oriented Design

Includes:

* Containerized deployment
* Cloud-native scaling
* Automated infrastructure flow
* Decoupled services

---

# 💡 Why This Project Stands Out

This project demonstrates practical experience with:

* Modern cloud architecture
* AI-powered backend systems
* Event-driven pipelines
* Full-stack deployment workflows
* Serverless engineering patterns
* Production-ready API development

It reflects real-world engineering practices used in scalable SaaS and AI infrastructure platforms.

---

# 🔮 Future Improvements

* OCR support for PDFs and scanned documents
* Authentication and user-specific dashboards
* Real-time pipeline monitoring
* Vector embeddings + semantic search
* Multi-document batch processing

---

# 👩‍💻 Author

**Shreya Jha**
Information Science & Engineering Student
Open Source Contributor • Cloud & AI Enthusiast

---

# ⭐ Live Application

👉 Explore the deployed project here:

[Open Live Demo](https://doc-frontend-5502500586.us-central1.run.app?utm_source=chatgpt.com)
