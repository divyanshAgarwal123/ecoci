"""Google Cloud Platform integration for EcoCI carbon tracking."""

from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional
from datetime import datetime


def is_gcp_enabled() -> bool:
    """Check if Google Cloud integration is configured."""
    return bool(os.getenv("GCP_PROJECT_ID") and os.getenv("GCP_SERVICE_ACCOUNT_KEY"))


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
        from google.oauth2 import service_account
        
        # Load service account credentials
        creds_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
        if not creds_json:
            return False
            
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(creds_json)
        )
        
        client = bigquery.Client(
            credentials=credentials,
            project=os.getenv("GCP_PROJECT_ID")
        )
        
        # Prepare row for insertion
        table_id = f"{os.getenv('GCP_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET', 'ecoci_metrics')}.pipeline_runs"
        
        rows_to_insert = [{
            "pipeline_id": metrics.get("pipeline_id"),
            "project_id": metrics.get("project_id"),
            "project_name": metrics.get("project_name"),
            "run_timestamp": datetime.utcnow().isoformat(),
            "total_duration_seconds": metrics.get("total_duration_seconds"),
            "total_energy_wh": metrics.get("total_energy_wh"),
            "total_co2_grams": metrics.get("total_co2_grams"),
            "optimizations_applied": metrics.get("optimizations_applied", []),
            "savings_percent": metrics.get("savings_percent", 0),
            "runner_region": metrics.get("runner_region", "unknown"),
            "gitlab_ci_yml_hash": metrics.get("gitlab_ci_yml_hash", "")
        }]
        
        errors = client.insert_rows_json(table_id, rows_to_insert)
        
        if not errors:
            print(f"✅ Saved to BigQuery: {metrics.get('total_co2_grams')}g CO₂")
            return True
        else:
            print(f"⚠️ BigQuery insert errors: {errors}")
            return False
            
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
        from google.oauth2 import service_account
        
        creds_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
        if not creds_json:
            return False
            
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(creds_json)
        )
        
        client = bigquery.Client(
            credentials=credentials,
            project=os.getenv("GCP_PROJECT_ID")
        )
        
        dataset_id = os.getenv('BIGQUERY_DATASET', 'ecoci_metrics')
        dataset_ref = f"{os.getenv('GCP_PROJECT_ID')}.{dataset_id}"
        
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
        from google.oauth2 import service_account
        
        creds_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
        if not creds_json:
            return None
            
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(creds_json)
        )
        
        client = bigquery.Client(
            credentials=credentials,
            project=os.getenv("GCP_PROJECT_ID")
        )
        
        table_ref = f"{os.getenv('GCP_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET', 'ecoci_metrics')}.pipeline_runs"
        
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
