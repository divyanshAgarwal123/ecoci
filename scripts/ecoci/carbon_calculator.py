from __future__ import annotations

import os
import hashlib
from typing import Any, Dict, List, Optional

# Optional Google Cloud integration
try:
    from .gcp_integration import (
        is_gcp_enabled,
        save_to_bigquery,
        get_carbon_intensity_for_region,
    )
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    
    def is_gcp_enabled():
        return False
    
    def save_to_bigquery(metrics):
        return False
    
    def get_carbon_intensity_for_region(region):
        return None


def estimate_emissions(
    pipeline_jobs: List[Dict[str, Any]],
    runner_cpu_cores: int,
    kwh_per_core_hour: float,
    carbon_intensity_kg_per_kwh: float,
    runner_region: Optional[str] = None,
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
    pipeline_id: Optional[int] = None,
    gitlab_ci_content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calculate carbon emissions for pipeline jobs.
    
    Args:
        pipeline_jobs: List of job dictionaries with duration info
        runner_cpu_cores: Number of CPU cores per runner
        kwh_per_core_hour: Energy consumption per core-hour
        carbon_intensity_kg_per_kwh: Grid carbon intensity
        runner_region: Optional runner region for GCP carbon intensity lookup
        project_id: Optional GitLab project ID for BigQuery tracking
        project_name: Optional project name for BigQuery tracking
        pipeline_id: Optional pipeline ID for BigQuery tracking
        gitlab_ci_content: Optional .gitlab-ci.yml content for tracking changes
        
    Returns:
        Dictionary with emissions data and per-job breakdown
    """
    by_job = []
    total_kwh = 0.0
    total_co2 = 0.0

    # Use Google Cloud Carbon Footprint API for region-specific intensity if available
    if GCP_AVAILABLE and is_gcp_enabled() and runner_region:
        gcp_intensity = get_carbon_intensity_for_region(runner_region)
        if gcp_intensity:
            carbon_intensity_kg_per_kwh = gcp_intensity
            print(f"☁️ Using Google Cloud carbon intensity for region {runner_region}")

    kwh_per_core_second = kwh_per_core_hour / 3600.0

    for job in pipeline_jobs:
        duration = float(job.get("duration") or 0)
        job_kwh = duration * runner_cpu_cores * kwh_per_core_second
        job_co2 = job_kwh * carbon_intensity_kg_per_kwh
        total_kwh += job_kwh
        total_co2 += job_co2
        by_job.append(
            {
                "job_id": job.get("id"),
                "name": job.get("name"),
                "duration_seconds": duration,
                "kwh": round(job_kwh, 4),
                "co2_kg": round(job_co2, 4),
            }
        )

    # Calculate total duration
    total_duration_seconds = sum(float(job.get("duration") or 0) for job in pipeline_jobs)

    # Create hash of gitlab-ci.yml for tracking changes
    gitlab_ci_hash = ""
    if gitlab_ci_content:
        gitlab_ci_hash = hashlib.md5(gitlab_ci_content.encode()).hexdigest()

    result = {
        "total_kwh": round(total_kwh, 4),
        "total_co2_kg": round(total_co2, 4),
        "by_job": by_job,
        "assumptions": {
            "runner_cpu_cores": runner_cpu_cores,
            "kwh_per_core_hour": kwh_per_core_hour,
            "carbon_intensity_kg_per_kwh": carbon_intensity_kg_per_kwh,
        },
    }

    # Optional: Save to BigQuery if Google Cloud is configured
    if GCP_AVAILABLE and is_gcp_enabled() and project_id and pipeline_id:
        bigquery_metrics = {
            "pipeline_id": pipeline_id,
            "project_id": project_id,
            "project_name": project_name or f"project-{project_id}",
            "total_duration_seconds": int(total_duration_seconds),
            "total_energy_wh": round(total_kwh * 1000, 2),  # Convert to Wh
            "total_co2_grams": round(total_co2 * 1000, 2),  # Convert to grams
            "optimizations_applied": [],  # Will be populated by optimizer
            "savings_percent": 0.0,  # Will be calculated after optimization
            "runner_region": runner_region or "unknown",
            "gitlab_ci_yml_hash": gitlab_ci_hash,
        }
        
        saved = save_to_bigquery(bigquery_metrics)
        result["saved_to_bigquery"] = saved
        if saved:
            print("✅ Carbon metrics saved to Google BigQuery for historical tracking")

    return result
