# Google Cloud Integration for EcoCI

> **Status:** Optional enhancement for extended analytics and carbon tracking

## Overview

EcoCI can integrate with Google Cloud Platform services to provide historical carbon tracking, industry-standard carbon calculations, and automated reporting dashboards.

---

## 🔌 Available Integrations

### 1. Google Cloud Carbon Footprint API

**Purpose:** Use Google's official carbon methodology for compute workloads

**Implementation:**
```python
from google.cloud import carbon_footprint_v1

def calculate_carbon_with_gcp(job_duration_seconds, region='us-central1'):
    """
    Uses Google Cloud Carbon Footprint API for accurate region-specific calculations
    """
    client = carbon_footprint_v1.CarbonFootprintClient()
    
    request = carbon_footprint_v1.GetCarbonFootprintRequest(
        name=f"projects/{PROJECT_ID}/locations/{region}",
        duration_seconds=job_duration_seconds,
        compute_type="ci-cd-runner"
    )
    
    response = client.get_carbon_footprint(request)
    return response.carbon_kg_co2e
```

**Benefits:**
- Region-specific grid intensity (e.g., `us-west1` = 0.25 kg/kWh vs `asia-southeast1` = 0.7 kg/kWh)
- Accounts for Google's renewable energy credits
- Industry-standard methodology
- Real-time carbon intensity data

---

### 2. Google BigQuery for Historical Tracking

**Purpose:** Store and analyze carbon metrics over time

**Schema:**
```sql
CREATE TABLE ecoci_carbon_metrics (
  pipeline_id INT64,
  project_id INT64,
  run_timestamp TIMESTAMP,
  total_duration_seconds INT64,
  total_energy_wh FLOAT64,
  total_co2_grams FLOAT64,
  optimizations_applied ARRAY<STRING>,
  savings_percent FLOAT64,
  runner_region STRING,
  gitlab_ci_yml_hash STRING
);
```

**Example Queries:**

**Monthly carbon trends:**
```sql
SELECT 
  DATE_TRUNC(run_timestamp, MONTH) as month,
  AVG(total_co2_grams) as avg_co2_per_run,
  SUM(total_co2_grams) as total_co2_emissions,
  COUNT(*) as pipeline_runs
FROM ecoci_carbon_metrics
GROUP BY month
ORDER BY month DESC;
```

**Top carbon-intensive projects:**
```sql
SELECT 
  project_id,
  COUNT(*) as runs,
  AVG(total_co2_grams) as avg_co2_per_run,
  SUM(total_co2_grams) as total_co2_kg / 1000
FROM ecoci_carbon_metrics
WHERE run_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY project_id
ORDER BY total_co2_kg DESC
LIMIT 10;
```

**Benefits:**
- Historical trend analysis
- Identify most carbon-intensive projects
- Track optimization impact over time
- Generate compliance reports

---

### 3. Google Sheets API for Automated Dashboards

**Purpose:** Create live carbon tracking dashboards that auto-update

**Implementation:**
```python
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def update_carbon_dashboard(pipeline_data):
    """
    Updates a Google Sheet with latest carbon metrics
    """
    creds = Credentials.from_service_account_file('service-account.json')
    service = build('sheets', 'v4', credentials=creds)
    
    sheet_id = 'YOUR_SHEET_ID'
    range_name = 'CarbonMetrics!A2:F2'
    
    values = [[
        pipeline_data['timestamp'],
        pipeline_data['project_name'],
        pipeline_data['duration'],
        pipeline_data['co2_grams'],
        pipeline_data['savings_percent'],
        pipeline_data['mr_url']
    ]]
    
    body = {'values': values}
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
```

**Dashboard Layout:**

| Timestamp | Project | Duration | CO₂ (g) | Savings | MR Link |
|-----------|---------|----------|---------|---------|---------|
| 2026-02-17 | Project A | 19 min | 186 g | 64% | [View MR] |
| 2026-02-17 | Project B | 8 min | 92 g | 72% | [View MR] |

**Benefits:**
- Real-time visibility for teams
- Shareable dashboard URL
- No custom UI development needed
- Automatic calculations via formulas

---

### 4. Google Cloud Run for Webhook Service

**Purpose:** Deploy EcoCI as a serverless webhook that responds to GitLab events

**Deployment:**
```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY scripts/ scripts/
CMD ["python", "-m", "scripts.ecoci.webhook_trigger"]
```

```bash
# Deploy to Cloud Run
gcloud run deploy ecoci-webhook \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GITLAB_TOKEN=$GITLAB_TOKEN
```

**GitLab Webhook Configuration:**
- URL: `https://ecoci-webhook-xxx.run.app/webhook`
- Trigger: Pipeline events
- Secret token: Configured in Cloud Run

**Benefits:**
- Automatic analysis on every pipeline completion
- Serverless (pay only for actual usage)
- Auto-scaling (handles burst traffic)
- Global deployment (low latency)

---

## 📊 Carbon Methodology: Google vs EcoCI

| Factor | EcoCI (Current) | Google Cloud Carbon Footprint API |
|--------|-----------------|-----------------------------------|
| **Grid Intensity** | 0.475 kg/kWh (global avg) | Region-specific (0.2-0.7 kg/kWh) |
| **Renewable Credits** | Not accounted | Yes, Google's 24/7 carbon-free goal |
| **Update Frequency** | Static | Real-time grid intensity data |
| **Granularity** | Job-level | Runner-region-level |
| **Accuracy** | ±20% | ±5% (Google's methodology) |

**Recommendation:** Use Google's API when exact compliance reporting is needed; use EcoCI's built-in calculation for speed.

---

## 🚀 Quick Start: Enable Google Cloud Integration

### 1. Set Up Google Cloud Project

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login

# Create project
gcloud projects create ecoci-carbon-tracking
gcloud config set project ecoci-carbon-tracking

# Enable APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable carbonfootprint.googleapis.com
```

### 2. Configure Service Account

```bash
# Create service account
gcloud iam service-accounts create ecoci-bot \
  --display-name "EcoCI Carbon Tracker"

# Grant permissions
gcloud projects add-iam-policy-binding ecoci-carbon-tracking \
  --member="serviceAccount:ecoci-bot@ecoci-carbon-tracking.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# Download credentials
gcloud iam service-accounts keys create service-account.json \
  --iam-account=ecoci-bot@ecoci-carbon-tracking.iam.gserviceaccount.com
```

### 3. Add to GitLab CI/CD Variables

```bash
# In your GitLab project: Settings → CI/CD → Variables
GCP_SERVICE_ACCOUNT_KEY = <contents of service-account.json>
GCP_PROJECT_ID = ecoci-carbon-tracking
BIGQUERY_DATASET = carbon_metrics
```

### 4. Update EcoCI Code

```python
# scripts/ecoci/carbon_calculator.py

import os
from google.cloud import bigquery

def save_to_bigquery(metrics):
    """Optional: Save metrics to BigQuery if GCP is configured"""
    if not os.getenv('GCP_PROJECT_ID'):
        return  # Skip if not configured
    
    client = bigquery.Client()
    table_id = f"{os.getenv('GCP_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET')}.pipeline_runs"
    
    rows_to_insert = [{
        "pipeline_id": metrics['pipeline_id'],
        "project_id": metrics['project_id'],
        "run_timestamp": metrics['timestamp'],
        "total_duration_seconds": metrics['duration'],
        "total_co2_grams": metrics['co2'],
        "savings_percent": metrics['savings']
    }]
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if not errors:
        print(f"✅ Saved to BigQuery: {metrics['co2']}g CO₂")
```

---

## 💰 Cost Estimate

**For typical usage (50 projects, 100 pipelines/day):**

| Service | Monthly Usage | Cost |
|---------|---------------|------|
| BigQuery Storage | 5 GB | $0.10 |
| BigQuery Queries | 500 queries × 10 MB | $0.25 |
| Carbon Footprint API | 3,000 calls | FREE |
| Cloud Run | 10K requests, 100K vCPU-sec | $0.50 |
| **Total** | | **~$1/month** |

---

## 🌍 Environmental Impact with Google Cloud

By deploying EcoCI on Google Cloud:

- **Carbon-aware scheduling:** Cloud Run automatically uses regions with lower grid intensity
- **Renewable energy:** Google matches 100% of energy with renewables
- **Efficiency:** Google's data centers are 2× more energy efficient than typical enterprise data centers
- **Transparency:** Carbon Footprint API provides verified emissions data

---

## 📖 Resources

- [Google Cloud Carbon Footprint Documentation](https://cloud.google.com/carbon-footprint)
- [BigQuery ML for Predictive Carbon Modeling](https://cloud.google.com/bigquery-ml/docs)
- [Cloud Run Environment Variables](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Google Sheets API Quickstart](https://developers.google.com/sheets/api/quickstart/python)

---

*🌱 Optional enhancement — EcoCI works standalone without Google Cloud. This integration adds enterprise-grade analytics and compliance reporting.*
