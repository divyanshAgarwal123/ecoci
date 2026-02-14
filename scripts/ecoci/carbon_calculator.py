from __future__ import annotations

from typing import Any, Dict, List


def estimate_emissions(
    pipeline_jobs: List[Dict[str, Any]],
    runner_cpu_cores: int,
    kwh_per_core_hour: float,
    carbon_intensity_kg_per_kwh: float,
) -> Dict[str, Any]:
    by_job = []
    total_kwh = 0.0
    total_co2 = 0.0

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

    return {
        "total_kwh": round(total_kwh, 4),
        "total_co2_kg": round(total_co2, 4),
        "by_job": by_job,
        "assumptions": {
            "runner_cpu_cores": runner_cpu_cores,
            "kwh_per_core_hour": kwh_per_core_hour,
            "carbon_intensity_kg_per_kwh": carbon_intensity_kg_per_kwh,
        },
    }
