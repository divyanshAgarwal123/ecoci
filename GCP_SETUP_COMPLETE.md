# ✅ Google Cloud Setup Complete!

## What Was Done

1. ✅ **Project Created:** `ecoci-carbon-tracking`
2. ✅ **BigQuery Enabled:** Free tier (1 TB queries/month)
3. ✅ **Dataset Created:** `ecoci_metrics`
4. ✅ **Table Created:** `pipeline_runs` with full schema
5. ✅ **Service Account Created:** `ecoci-bot@ecoci-carbon-tracking.iam.gserviceaccount.com`
6. ✅ **Permissions Granted:** BigQuery Data Editor role
7. ✅ **Key Generated:** `ecoci-service-account.json`

---

## 📋 Next Step: Add to GitLab CI/CD Variables

Go to your GitLab project:
**https://gitlab.com/gitlab-ai-hackathon/participants/34560917/-/settings/ci_cd**

Click **"Variables" → "Expand" → "Add variable"**

### Variable 1: GCP_PROJECT_ID
- **Key:** `GCP_PROJECT_ID`
- **Value:** `ecoci-carbon-tracking`
- **Type:** Variable
- **Protected:** ✓ Yes
- **Masked:** ✗ No
- **Expand variable reference:** ✗ No

### Variable 2: BIGQUERY_DATASET
- **Key:** `BIGQUERY_DATASET`
- **Value:** `ecoci_metrics`
- **Type:** Variable
- **Protected:** ✓ Yes
- **Masked:** ✗ No
- **Expand variable reference:** ✗ No

### Variable 3: GCP_SERVICE_ACCOUNT_KEY
- **Key:** `GCP_SERVICE_ACCOUNT_KEY`
- **Value:** Copy the ENTIRE JSON below (including curly braces)
- **Type:** Variable (NOT File)
- **Protected:** ✓ Yes
- **Masked:** ✗ No
- **Expand variable reference:** ✗ No

**Copy this JSON:**
```json
{
  "type": "service_account",
  "project_id": "ecoci-carbon-tracking",
  "private_key_id": "<YOUR_PRIVATE_KEY_ID>",
  "private_key": "-----BEGIN PRIVATE KEY-----\n<YOUR_PRIVATE_KEY_HERE>\n-----END PRIVATE KEY-----\n",
  "client_email": "ecoci-bot@ecoci-carbon-tracking.iam.gserviceaccount.com",
  "client_id": "<YOUR_CLIENT_ID>",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/ecoci-bot%40ecoci-carbon-tracking.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

> ⚠️ **IMPORTANT:** Replace the placeholder values above with your actual service account key.
> Generate one via: `gcloud iam service-accounts keys create key.json --iam-account=ecoci-bot@ecoci-carbon-tracking.iam.gserviceaccount.com`

---

## 🧪 Test the Integration

After adding the variables, test with Python:

```bash
cd /Volumes/MacTech/gitlab_new/34560917

# Set environment variables (temporary test)
export GCP_PROJECT_ID="ecoci-carbon-tracking"
export BIGQUERY_DATASET="ecoci_metrics"
export GCP_SERVICE_ACCOUNT_KEY='<paste the JSON here>'

# Test the integration
python3 -c "
from scripts.ecoci.gcp_integration import is_gcp_enabled, save_to_bigquery
print('GCP Enabled:', is_gcp_enabled())

# Test saving a metric
test_metric = {
    'pipeline_id': 99999,
    'project_id': 79403566,
    'project_name': 'test-project',
    'total_duration_seconds': 600,
    'total_energy_wh': 200,
    'total_co2_grams': 95,
    'optimizations_applied': ['cache', 'parallel'],
    'savings_percent': 50,
    'runner_region': 'us-central1',
    'gitlab_ci_yml_hash': 'abc123'
}

result = save_to_bigquery(test_metric)
print('Saved to BigQuery:', result)
"
```

---

## 📊 View Your Data

**BigQuery Console:**
https://console.cloud.google.com/bigquery?project=ecoci-carbon-tracking&page=table&d=ecoci_metrics&t=pipeline_runs

**Query your data:**
```bash
bq query --use_legacy_sql=false '
SELECT 
  project_name,
  total_co2_grams,
  savings_percent,
  run_timestamp
FROM `ecoci-carbon-tracking.ecoci_metrics.pipeline_runs`
ORDER BY run_timestamp DESC
LIMIT 10'
```

---

## ⚠️ Important Notes

1. **BigQuery Free Tier:** 1 TB queries/month, 10 GB storage (plenty for EcoCI)
2. **Cloud Run requires billing:** We skipped Cloud Run deployment since billing isn't enabled
3. **Service account key:** Keep `ecoci-service-account.json` secure (already in .gitignore)
4. **Automatic saving:** Once GitLab variables are set, every pipeline analysis will auto-save to BigQuery

---

## 🎯 What Happens Now

When your EcoCI agent runs:

1. Fetches pipeline data from GitLab
2. Calculates carbon emissions
3. **Automatically saves metrics to BigQuery** ✨
4. Uses **region-specific carbon intensity** from Google Cloud
5. Creates optimized merge request
6. You can query trends in BigQuery!

---

## 🚀 Next: Enable Billing for Cloud Run (Optional)

If you want webhook automation:

1. Go to: https://console.cloud.google.com/billing
2. Reactivate "My Billing Account" or create new one
3. Then run: `./scripts/deploy_cloud_run.sh`

**Cost:** ~$1/month for typical usage (1000 pipeline analyses)

---

*Setup completed on: 2026-02-17*
*Local key file: `/Volumes/MacTech/gitlab_new/34560917/ecoci-service-account.json`*
