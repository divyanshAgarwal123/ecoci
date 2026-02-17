"""Google Cloud Platform integration for EcoCI carbon tracking."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# Path to config and service account key (relative to this file)
_THIS_DIR = Path(__file__).resolve().parent
_GCP_CONFIG_PATH = _THIS_DIR / "gcp_config.json"
_PROJECT_ROOT = _THIS_DIR.parent.parent
_SERVICE_ACCOUNT_KEY_PATH = _PROJECT_ROOT / "ecoci-service-account.json"


def _load_gcp_config() -> Dict[str, str]:
    """Load GCP config from gcp_config.json or environment variables."""
    config = {}
    
    # Try loading from config file first
    if _GCP_CONFIG_PATH.exists():
        with open(_GCP_CONFIG_PATH) as f:
            config = json.load(f)
    
    # Environment variables override config file
    return {
        "project_id": os.getenv("GCP_PROJECT_ID", config.get("gcp_project_id", "")),
        "dataset": os.getenv("BIGQUERY_DATASET", config.get("bigquery_dataset", "ecoci_metrics")),
        "table": config.get("bigquery_table", "pipeline_runs"),
    }


def _get_credentials():
    """
    Load Google Cloud credentials from:
    1. GCP_SERVICE_ACCOUNT_KEY env var (JSON string) — for CI/CD
    2. ecoci-service-account.json file — for local development
    3. Application Default Credentials (ADC) — for Cloud Run
    """
    try:
        from google.oauth2 import service_account
        
        # Option 1: Environment variable (CI/CD)
        creds_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
        if creds_json:
            return service_account.Credentials.from_service_account_info(
                json.loads(creds_json)
            )
        
        # Option 2: Local key file
        if _SERVICE_ACCOUNT_KEY_PATH.exists():
            return service_account.Credentials.from_service_account_file(
                str(_SERVICE_ACCOUNT_KEY_PATH)
            )
        
        # Option 3: Application Default Credentials (Cloud Run / gcloud auth)
        import google.auth
        credentials, _ = google.auth.default()
        return credentials
        
    except Exception:
        return None


def is_gcp_enabled() -> bool:
    """Check if Google Cloud integration is configured."""
    config = _load_gcp_config()
    if not config.get("project_id"):
        return False
    
    # Check if we can get credentials
    return _get_credentials() is not None


def save_to_bigquery(metrics: Dict[str, Any]) -> bool:
    """
    Save carbon metrics to BigQuery for historical tracking.
    
    Args:
        metrics: Dictionary containing pipeline carbon metrics
        
    Returns:
        True if successful, False otherwise
    """
    if not is_gcp_enabled():
        return False
    
    try:
        from google.cloud import bigquery
        
        config = _load_gcp_config()
        credentials = _get_credentials()
        if not credentials:
            return False
        
        client = bigquery.Client(
            credentials=credentials,
            project=config["project_id"]
        )
        
        # Prepare row for insertion
        table_id = f"{config['project_id']}.{config['dataset']}.{config['table']}"
        
        timestamp = datetime.utcnow().isoformat()
        
        row = {
            "pipeline_id": metrics.get("pipeline_id", 0),
            "project_id": metrics.get("project_id", 0),
            "project_name": metrics.get("project_name", ""),
            "run_timestamp": timestamp,
            "total_duration_seconds": metrics.get("total_duration_seconds", 0),
            "total_energy_wh": metrics.get("total_energy_wh", 0),
            "total_co2_grams": metrics.get("total_co2_grams", 0),
            "savings_percent": metrics.get("savings_percent", 0),
            "runner_region": metrics.get("runner_region", "unknown"),
            "gitlab_ci_yml_hash": metrics.get("gitlab_ci_yml_hash", ""),
        }
        
        # Use load_table_from_json (free tier compatible, no streaming/DML)
        table_ref = client.get_table(table_id)
        errors = client.load_table_from_json(
            [row], table_ref
        ).result()
        
        print(f"✅ Saved to BigQuery: {row['total_co2_grams']}g CO₂")
        return True
            
    except Exception as e:
        print(f"⚠️ BigQuery integration failed: {e}")
        return False


def get_carbon_intensity_for_region(region: str) -> Optional[float]:
    """
    Get region-specific carbon intensity using Google Cloud Carbon Footprint API.
    
    Args:
        region: GCP region (e.g., 'us-central1', 'europe-west1')
        
    Returns:
        Carbon intensity in kg CO₂ per kWh, or None if unavailable
    """
    if not is_gcp_enabled():
        return None
        
    try:
        # Map common GitLab runner regions to GCP regions
        region_mapping = {
            "us-east": "us-east1",
            "us-west": "us-west1",
            "eu-west": "europe-west1",
            "asia-southeast": "asia-southeast1",
        }
        
        gcp_region = region_mapping.get(region, region)
        
        # Google Cloud Carbon Intensity data (approximate, kg CO₂e per kWh)
        # Source: https://cloud.google.com/sustainability/region-carbon
        carbon_intensity_by_region = {
            "us-central1": 0.394,  # Iowa
            "us-east1": 0.315,     # South Carolina
            "us-west1": 0.252,     # Oregon
            "us-west2": 0.252,     # Los Angeles
            "europe-west1": 0.196, # Belgium
            "europe-west2": 0.257, # London
            "europe-west3": 0.348, # Frankfurt
            "asia-southeast1": 0.493, # Singapore
            "asia-northeast1": 0.506, # Tokyo
            "australia-southeast1": 0.810, # Sydney
        }
        
        intensity = carbon_intensity_by_region.get(gcp_region, 0.475)  # Default to global average
        print(f"📍 Using carbon intensity for {gcp_region}: {intensity} kg CO₂/kWh")
        return intensity
        
    except Exception as e:
        print(f"⚠️ Failed to get region-specific carbon intensity: {e}")
        return None


def setup_bigquery_table() -> bool:
    """
    Create BigQuery table for carbon metrics if it doesn't exist.
    
    Returns:
        True if successful or table already exists, False otherwise
    """
    if not is_gcp_enabled():
        return False
        
    try:
        from google.cloud import bigquery
        
        config = _load_gcp_config()
        credentials = _get_credentials()
        if not credentials:
            return False
        
        client = bigquery.Client(
            credentials=credentials,
            project=config["project_id"]
        )
        
        dataset_id = config["dataset"]
        dataset_ref = f"{config['project_id']}.{dataset_id}"
        
        # Create dataset if it doesn't exist
        try:
            client.get_dataset(dataset_ref)
        except:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            client.create_dataset(dataset)
            print(f"✅ Created BigQuery dataset: {dataset_id}")
        
        # Define table schema
        schema = [
            bigquery.SchemaField("pipeline_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("project_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("project_name", "STRING"),
            bigquery.SchemaField("run_timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("total_duration_seconds", "INTEGER"),
            bigquery.SchemaField("total_energy_wh", "FLOAT"),
            bigquery.SchemaField("total_co2_grams", "FLOAT"),
            bigquery.SchemaField("optimizations_applied", "STRING", mode="REPEATED"),
            bigquery.SchemaField("savings_percent", "FLOAT"),
            bigquery.SchemaField("runner_region", "STRING"),
            bigquery.SchemaField("gitlab_ci_yml_hash", "STRING"),
        ]
        
        table_ref = f"{dataset_ref}.pipeline_runs"
        
        try:
            client.get_table(table_ref)
            print(f"✅ BigQuery table already exists: {table_ref}")
        except:
            table = bigquery.Table(table_ref, schema=schema)
            client.create_table(table)
            print(f"✅ Created BigQuery table: {table_ref}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ BigQuery setup failed: {e}")
        return False


def query_carbon_trends(days: int = 30) -> Optional[Dict[str, Any]]:
    """
    Query carbon metrics trends from BigQuery.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Dictionary with trend data, or None if unavailable
    """
    if not is_gcp_enabled():
        return None
        
    try:
        from google.cloud import bigquery
        
        config = _load_gcp_config()
        credentials = _get_credentials()
        if not credentials:
            return None
        
        client = bigquery.Client(
            credentials=credentials,
            project=config["project_id"]
        )
        
        table_ref = f"{config['project_id']}.{config['dataset']}.{config['table']}"
        
        query = f"""
        SELECT 
            DATE(run_timestamp) as date,
            COUNT(*) as pipeline_runs,
            AVG(total_co2_grams) as avg_co2_per_run,
            SUM(total_co2_grams) / 1000 as total_co2_kg,
            AVG(savings_percent) as avg_savings_percent
        FROM `{table_ref}`
        WHERE run_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY date
        ORDER BY date DESC
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        trends = []
        for row in results:
            trends.append({
                "date": str(row.date),
                "pipeline_runs": row.pipeline_runs,
                "avg_co2_per_run": round(row.avg_co2_per_run, 2),
                "total_co2_kg": round(row.total_co2_kg, 2),
                "avg_savings_percent": round(row.avg_savings_percent, 1)
            })
        
        return {
            "period_days": days,
            "trends": trends
        }
        
    except Exception as e:
        print(f"⚠️ Failed to query carbon trends: {e}")
        return None
