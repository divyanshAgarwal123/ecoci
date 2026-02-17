#!/usr/bin/env python3
"""Insert sample data into BigQuery for demo purposes."""

import sys
sys.path.insert(0, "/Volumes/MacTech/gitlab_new/34560917")

from scripts.ecoci.gcp_integration import save_to_bigquery

samples = [
    {
        "pipeline_id": 10001,
        "project_id": 79403566,
        "project_name": "rails-app",
        "total_duration_seconds": 2850,
        "total_energy_wh": 1075,
        "total_co2_grams": 511,
        "savings_percent": 0,
        "runner_region": "us-central1",
        "gitlab_ci_yml_hash": "before",
    },
    {
        "pipeline_id": 10002,
        "project_id": 79403566,
        "project_name": "rails-app",
        "total_duration_seconds": 1140,
        "total_energy_wh": 392,
        "total_co2_grams": 186,
        "savings_percent": 64,
        "runner_region": "us-central1",
        "gitlab_ci_yml_hash": "after",
    },
    {
        "pipeline_id": 10003,
        "project_id": 12345678,
        "project_name": "node-api",
        "total_duration_seconds": 1800,
        "total_energy_wh": 680,
        "total_co2_grams": 323,
        "savings_percent": 0,
        "runner_region": "europe-west1",
        "gitlab_ci_yml_hash": "before",
    },
    {
        "pipeline_id": 10004,
        "project_id": 12345678,
        "project_name": "node-api",
        "total_duration_seconds": 540,
        "total_energy_wh": 204,
        "total_co2_grams": 40,
        "savings_percent": 70,
        "runner_region": "europe-west1",
        "gitlab_ci_yml_hash": "after",
    },
    {
        "pipeline_id": 10005,
        "project_id": 87654321,
        "project_name": "python-ml",
        "total_duration_seconds": 3600,
        "total_energy_wh": 1500,
        "total_co2_grams": 713,
        "savings_percent": 0,
        "runner_region": "us-west1",
        "gitlab_ci_yml_hash": "before",
    },
    {
        "pipeline_id": 10006,
        "project_id": 87654321,
        "project_name": "python-ml",
        "total_duration_seconds": 1200,
        "total_energy_wh": 500,
        "total_co2_grams": 126,
        "savings_percent": 67,
        "runner_region": "us-west1",
        "gitlab_ci_yml_hash": "after",
    },
]

print("Inserting sample data into BigQuery...")
for s in samples:
    result = save_to_bigquery(s)
    status = "OK" if result else "FAIL"
    print(f"  {s['project_name']} (pipeline {s['pipeline_id']}): {status}")

print("\nDone! Query with:")
print("bq query --use_legacy_sql=false 'SELECT * FROM ecoci-carbon-tracking.ecoci_metrics.pipeline_runs'")
