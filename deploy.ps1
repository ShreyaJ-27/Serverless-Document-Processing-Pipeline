# Deployment script for Serverless Document Pipeline

$PROJECT_ID = gcloud config get-value project
if (-not $PROJECT_ID) {
    Write-Host "Please set your default project using: gcloud config set project [YOUR_PROJECT_ID]"
    exit
}

# Configuration
$REGION = "us-central1"
$BUCKET_NAME = "$PROJECT_ID-doc-upload-$(Get-Random -Maximum 9999)"
$TOPIC_NAME = "doc-upload-topic"
$SERVICE_NAME = "doc-processor-service"
$DATASET_ID = "doc_processing_db"
$TABLE_ID = "documents"

Write-Host "Deploying Pipeline to Project: $PROJECT_ID"

Write-Host "`n1. Enabling necessary Google Cloud APIs..."
gcloud services enable run.googleapis.com pubsub.googleapis.com storage.googleapis.com bigquery.googleapis.com artifactregistry.googleapis.com

Write-Host "`n2. Creating Cloud Storage bucket..."
# Check if bucket exists, if not create it
gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION

Write-Host "`n3. Creating BigQuery Dataset and Table..."
# Create dataset
bq mk --location=$REGION --dataset $PROJECT_ID`:$DATASET_ID
# Create table with schema
$SCHEMA = "filename:STRING,processing_date:TIMESTAMP,tags:STRING,word_count:INTEGER"
bq mk --table $PROJECT_ID`:$DATASET_ID.$TABLE_ID $SCHEMA

Write-Host "`n4. Building and deploying to Cloud Run..."
# Assuming we run this from the directory containing Dockerfile
gcloud run deploy $SERVICE_NAME `
    --source . `
    --region=$REGION `
    --allow-unauthenticated `
    --set-env-vars="PROJECT_ID=$PROJECT_ID,DATASET_ID=$DATASET_ID,TABLE_ID=$TABLE_ID"

# Get the URL of the deployed service
$SERVICE_URL = (gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)")
Write-Host "Service deployed at: $SERVICE_URL"

Write-Host "`n5. Creating Pub/Sub topic and Subscription..."
gcloud pubsub topics create $TOPIC_NAME

# Create Pub/Sub push subscription to the Cloud Run service
# Create a service account to represent the Pub/Sub subscription identity
$PUBSUB_SA = "pubsub-invoker-sa"
gcloud iam service-accounts create $PUBSUB_SA --display-name "Pub/Sub Invoker Service Account"
$PUBSUB_SA_EMAIL = "$PUBSUB_SA@$PROJECT_ID.iam.gserviceaccount.com"

# Give the SA permission to invoke Cloud Run
gcloud run services add-iam-policy-binding $SERVICE_NAME `
    --region=$REGION `
    --member="serviceAccount:$PUBSUB_SA_EMAIL" `
    --role="roles/run.invoker"

gcloud pubsub subscriptions create ${TOPIC_NAME}-sub `
    --topic=$TOPIC_NAME `
    --push-endpoint="$SERVICE_URL/" `
    --push-auth-service-account=$PUBSUB_SA_EMAIL

Write-Host "`n6. Configuring Cloud Storage to publish to Pub/Sub..."
# Give GCS service account permission to publish to Pub/Sub
$GCS_SA = (gcloud storage service-agent --project=$PROJECT_ID)
gcloud pubsub topics add-iam-policy-binding $TOPIC_NAME `
    --member="serviceAccount:$GCS_SA" `
    --role="roles/pubsub.publisher"

gcloud storage buckets notifications create gs://$BUCKET_NAME `
    --topic=$TOPIC_NAME `
    --event-types=OBJECT_FINALIZE

Write-Host "`n=== Deployment Complete ==="
Write-Host "To test the pipeline, upload a file to the bucket:"
Write-Host "gcloud storage cp sample.txt gs://$BUCKET_NAME/"
