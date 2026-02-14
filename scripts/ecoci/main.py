from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .carbon_calculator import estimate_emissions
from .ci_analyzer import analyze_ci_config
from .config import load_config
from .gitlab_client import GitLabClient
from .mr_creator import create_merge_request
from .optimizer import optimize_ci_yaml


def run(project_id: str, pipeline_id: str, ref: str) -> Dict[str, Any]:
    config = load_config()
    client = GitLabClient(config)

    ci_yaml = client.get_repository_file(project_id, ".gitlab-ci.yml", ref)
    analysis = analyze_ci_config(ci_yaml)

    jobs = client.list_pipeline_jobs(project_id, pipeline_id)
    carbon = estimate_emissions(
        jobs,
        runner_cpu_cores=config.runner_cpu_cores,
        kwh_per_core_hour=config.kwh_per_core_hour,
        carbon_intensity_kg_per_kwh=config.carbon_intensity_kg_per_kwh,
    )

    optimized_yaml, changes, warnings = optimize_ci_yaml(ci_yaml)

    summary = {
        "headline": "Automated CI/CD improvements from EcoCI",
        "changes": changes,
        "dag_summary": analysis.get("dag_summary", {}),
        "metrics": {
            "time_saved": "TBD",
            "cost_saved": "TBD",
            "co2_saved": f"{carbon['total_co2_kg']} kg CO2 per pipeline",
        },
        "carbon_dashboard": _render_carbon_dashboard(carbon),
    }

    mr = create_merge_request(
        client=client,
        project_id=project_id,
        ref=ref,
        optimized_ci_yaml=optimized_yaml,
        summary=summary,
        pipeline_id=pipeline_id,
    )

    return {
        "analysis": analysis,
        "carbon": carbon,
        "changes": changes,
        "warnings": warnings,
        "merge_request": mr,
    }


def _render_carbon_dashboard(carbon: Dict[str, Any]) -> str:
    rows = [
        "| Job | Duration (s) | kWh | CO2 (kg) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for job in carbon["by_job"]:
        rows.append(
            f"| {job.get('name')} | {job.get('duration_seconds')} | {job.get('kwh')} | {job.get('co2_kg')} |"
        )
    return "\n".join(
        [
            "## EcoCI Carbon Dashboard",
            "Estimated emissions for this pipeline:",
            "",
            *rows,
            "",
            f"**Total**: {carbon['total_co2_kg']} kg CO2 ({carbon['total_kwh']} kWh)",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="EcoCI pipeline optimizer")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--pipeline-id", required=True)
    parser.add_argument("--ref", required=True)
    args = parser.parse_args()

    result = run(args.project_id, args.pipeline_id, args.ref)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
