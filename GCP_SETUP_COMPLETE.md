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
  "private_key_id": "REDACTED_KEY_ID",
  "private_key": "-----BEGIN PRIVATE KEY-----\nREDACTED\nREDACTED+h/ZSTCE9VHWsaQw+\n42ui4LcO87UZF3WkmVU5dL6GyCtzR9tRz6MfSLVKlp6Wpx8d9ZpS291EOifMCs58\nD4rr2jATYFppRSc8hO33Ny3KAqQ8hLEkesISlq2nw0TXfrR/5EIBqVWPJuA7g4tu\n5KR5s7cO9q6Y9T40QHzkyVyF7Km+7Jpehaob2MOKmxTGa1iGA7Gy5TU5osDcEIPJ\na3KeCSpSyYn929Tdh/C7puxCmqcDbkr+Pb0nJS2qpFKlbxV3+BSSBRYMkKOYjEZe\nRe1bPWClAgMBAAECggEAREDACTED\nTHe5O9bqDo4boWdWuzPeRHpheULIdlpUf/Bhv0BWvu2D2/7Eobltd6OFMzpA90Ww\nVlPFZUOBJ4xTB6tzRLz5GzRDIYTbqV/yVct4bQQYIec79cYS2kqeyXmZPFfY2abA\nPHYJW/yHX+Gxgh9nxraey4rV0C+zwhKQQ6A5/I+ea6CWwVXAyaewfE0wSGu0hUU0\nm5DSYgNsnhy0EvrM3m2Th3YAuJhY16l/3cN0HvrWcNh/+I8GiTPKuzpOujFj3gk3\nx09XrGlFzL11nH/36RWedk+QKkZ3BxRYrEHbZSDbAQKBgQDO3SW+XKeAj8LRCxom\nNsNitVpqSJwOWL1Petig0Y1qgnHHEGX8r+1ITY70frZ1Hcs4EiVdUs0A+47EVs6n\nEsfmeXJfZDy58inOAmReGj5RJQU3fGxhOzMGxmkqeI2LUfXi2wC+6cNsx6mkWZZA\nhQcN1utBMH6tKiOEHnpSPgIDpQKBgQDHdlL3ykWdmGEhfsYlLwCfZ3QgB1UyV0EK\ndeLJrbqhdY4Qsvh5mn54h90ln0MVlPbMRMMD+URYUy6nhV+9ww12DvWKv9np/jR6\nc+hCFWPNSZgf1OB21wR3IRxqRN05YsBJzrKcgKrYAcEbKK+GQbRzSwdEnhzMMurv\nx1l8FGtZAQKBgCPkVQcpdlqlFu1EWt4khFQdGTn1rTYECZy/uNR2Z24CghFC9B8a\nuzXfVx1u2uOJLthktZzyn+U6wHOqiCKO7KY9ji2k67Brpvs6iQWW0hcsMDKHYRqh\nteHIDTk0P4Lbzqj0zLVTQ/gc0H9Wl+5L5oRtNNZTvrb258CltR2N6rWNAoGAXPX4\nlSPgbiKmokXDc3EEiUZeCM9iFaQ02/s1R2mAod935rCCvaoTZ3lqyC4Bxf03SNyD\nR0bVY5ThGZI/nOFbVLqEFbZ0iWnAa5G5nZL6gKLcE3nTY4+ytRLpe128/RHZLIz5\nEZemCCZJKa88nwXgZBuDt6c5JLJWbIosWnfp0AECgYEAREDACTED\nt6bAL4fh2cNOB+mxPP/EXgQK6hl5rp+Ou/iRf3tU5g2R1dz9ce1nvAMngPA3voWq\n8GN4IUTlqTCuxrwscfF+vRUj2jrvuiyQ1YVyJahxpqjHbWusppY5hBNHDh/1Bu1R\nwyqUgr33q5AESwletdfh5R4=\n-----END PRIVATE KEY-----\n",
  "client_email": "ecoci-bot@ecoci-carbon-tracking.iam.gserviceaccount.com",
  "client_id": "REDACTED_CLIENT_ID",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/ecoci-bot%40ecoci-carbon-tracking.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

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
