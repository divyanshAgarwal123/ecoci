#!/bin/bash
# Deploy EcoCI to Google Cloud Run

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
SERVICE_NAME="ecoci-webhook"
REGION="${GCP_REGION:-us-central1}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying EcoCI to Google Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"

# Build container image
echo "📦 Building container image..."
gcloud builds submit --tag "${IMAGE_NAME}" --project="${PROJECT_ID}"

# Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE_NAME}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --set-env-vars="GITLAB_TOKEN=${GITLAB_TOKEN}" \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}" \
  --set-env-vars="BIGQUERY_DATASET=ecoci_metrics" \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=10 \
  --project="${PROJECT_ID}"

# Get service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

echo ""
echo "✅ Deployment complete!"
echo "📍 Webhook URL: ${SERVICE_URL}/webhook"
echo ""
echo "Next steps:"
echo "1. Go to your GitLab project → Settings → Webhooks"
echo "2. Add webhook URL: ${SERVICE_URL}/webhook"
echo "3. Select 'Pipeline events' trigger"
echo "4. Add secret token if desired"
echo ""
echo "Test health check:"
echo "curl ${SERVICE_URL}/health"
