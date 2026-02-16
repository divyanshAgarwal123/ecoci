# Quick Start: Enable Google Cloud Integration

## 🚀 Enable BigQuery Tracking (5 minutes)

### 1. Install Google Cloud SDK

```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login
```

### 2. Set up GCP Project

```bash
# Create or select project
export GCP_PROJECT_ID="ecoci-carbon-tracking"
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable run.googleapis.com
```

### 3. Create BigQuery Dataset & Table

```bash
# Run the setup script
chmod +x scripts/setup_bigquery.sh
./scripts/setup_bigquery.sh
```

### 4. Configure GitLab CI/CD Variables

Go to your GitLab project → Settings → CI/CD → Variables and add:

```
GCP_PROJECT_ID = ecoci-carbon-tracking
BIGQUERY_DATASET = ecoci_metrics
GCP_SERVICE_ACCOUNT_KEY = { "type": "service_account", ... }
```

To get the service account key:

```bash
# Create service account
gcloud iam service-accounts create ecoci-bot \
  --display-name="EcoCI Bot"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:ecoci-bot@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# Download credentials
gcloud iam service-accounts keys create service-account.json \
  --iam-account=ecoci-bot@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# Copy the JSON content to GitLab variable
cat service-account.json
```

### 5. Test the Integration

Run your pipeline - carbon metrics will automatically save to BigQuery!

```bash
# Query recent runs
bq query --use_legacy_sql=false '
SELECT 
  project_name,
  run_timestamp,
  total_co2_grams,
  savings_percent
FROM `ecoci-carbon-tracking.ecoci_metrics.pipeline_runs`
ORDER BY run_timestamp DESC
LIMIT 10'
```

---

## ☁️ Deploy to Cloud Run (10 minutes)

### 1. Build and Deploy

```bash
# Set environment variables
export GCP_PROJECT_ID="ecoci-carbon-tracking"
export GITLAB_TOKEN="glpat-your-token"
export ECOCI_TRIGGER_TOKEN="your-trigger-token"

# Deploy
chmod +x scripts/deploy_cloud_run.sh
./scripts/deploy_cloud_run.sh
```

### 2. Configure GitLab Webhook

The deployment script will output a webhook URL like:
```
https://ecoci-webhook-xxx-uc.a.run.app/webhook
```

Go to your GitLab project → Settings → Webhooks:
- URL: `https://ecoci-webhook-xxx-uc.a.run.app/webhook`
- Trigger: ✓ Pipeline events
- Click "Add webhook"

### 3. Test It

Trigger a pipeline in your project - EcoCI will automatically analyze it!

```bash
# Check Cloud Run logs
gcloud run logs read ecoci-webhook --project=$GCP_PROJECT_ID --limit=20
```

---

## 📊 View Carbon Trends

### Option 1: BigQuery Console

Visit: https://console.cloud.google.com/bigquery?project=ecoci-carbon-tracking

Run queries like:
```sql
-- Daily carbon emissions
SELECT 
  DATE(run_timestamp) as date,
  COUNT(*) as runs,
  AVG(total_co2_grams) as avg_co2_per_run,
  SUM(total_co2_grams) / 1000 as total_co2_kg
FROM `ecoci-carbon-tracking.ecoci_metrics.pipeline_runs`
GROUP BY date
ORDER BY date DESC;

-- Top carbon-intensive projects
SELECT 
  project_name,
  COUNT(*) as pipeline_runs,
  AVG(total_co2_grams) as avg_co2,
  SUM(total_co2_grams) / 1000 as total_co2_kg
FROM `ecoci-carbon-tracking.ecoci_metrics.pipeline_runs`
GROUP BY project_name
ORDER BY total_co2_kg DESC;
```

### Option 2: CLI

```bash
# Total carbon saved this month
bq query --use_legacy_sql=false '
SELECT 
  SUM(total_co2_grams * savings_percent / 100) / 1000 as co2_saved_kg
FROM `ecoci-carbon-tracking.ecoci_metrics.pipeline_runs`
WHERE run_timestamp >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)'
```

---

## 🎯 What You Get

With Google Cloud enabled:

✅ **Historical tracking** — All pipeline carbon metrics saved to BigQuery  
✅ **Region-specific accuracy** — Uses GCP Carbon Footprint data (0.25-0.8 kg/kWh)  
✅ **Automated workflows** — Cloud Run webhook triggers optimization on every pipeline  
✅ **Powerful analytics** — SQL queries for trends, top emitters, ROI calculations  
✅ **Cost-effective** — ~$1/month for typical usage (50 projects, 100 pipelines/day)  

---

## 🔍 Verify Integration

Check if Google Cloud is working:

```bash
# Test BigQuery connection
python -c "
from scripts.ecoci.gcp_integration import is_gcp_enabled, setup_bigquery_table
print('GCP Enabled:', is_gcp_enabled())
if is_gcp_enabled():
    setup_bigquery_table()
"

# Test Cloud Run deployment
curl https://your-service.run.app/health
```

---

## 💡 Tips

1. **Start with BigQuery** — Easy to set up, provides immediate value
2. **Add Cloud Run later** — For full automation (webhook-triggered)
3. **Monitor costs** — Use GCP billing alerts (set at $5/month)
4. **Query optimization** — BigQuery charges per TB scanned, so use date filters

---

## 🆘 Troubleshooting

**"Permission denied" errors:**
```bash
# Grant your user BigQuery permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="user:your-email@gmail.com" \
  --role="roles/bigquery.admin"
```

**"Table not found" errors:**
```bash
# Recreate the table
./scripts/setup_bigquery.sh
```

**Cloud Run won't start:**
```bash
# Check logs
gcloud run logs read ecoci-webhook --limit=50
```

---

*For detailed technical information, see [CLOUD_INTEGRATION.md](CLOUD_INTEGRATION.md)*
