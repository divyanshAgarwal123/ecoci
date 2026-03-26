from __future__ import annotations

import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from ..ci_analyzer import analyze_ci_config
from ..config import load_config
from ..gitlab_client import GitLabClient
from ..optimizer import optimize_ci_yaml
from .base import CIProvider


class GitLabProvider(CIProvider):
    """Backward-compatible provider wrapper around existing GitLab client + analyzers."""

    def __init__(self):
        self.client = GitLabClient(load_config())
        self.token = self.client.config.token

    @staticmethod
    def infer_project_from_git() -> Optional[str]:
        """Infer GitLab namespace/project from git remote origin URL."""
        try:
            out = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        except Exception:
            return None

        # https://gitlab.com/group/subgroup/repo.git OR git@gitlab.com:group/repo.git
        m = re.search(r"gitlab\.com[:/](?P<path>.+?)(?:\.git)?$", out)
        if not m:
            return None
        path = m.group("path").strip("/")
        return path or None

    def get_default_branch(self, repo: str) -> str:
        return self.client.get_default_branch(repo)

    def list_workflow_files(self, repo: str, ref: str) -> List[str]:
        # GitLab CI has canonical root file; this keeps CIProvider compatibility.
        return [".gitlab-ci.yml"]

    def get_workflow_content(self, repo: str, workflow_path: str, ref: str) -> str:
        return self.client.get_repository_file(repo, workflow_path, ref)

    def analyze_workflow(
        self,
        workflow_yaml: str,
        run_jobs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        analysis = analyze_ci_config(workflow_yaml)
        return {
            "issues": analysis.get("issues", []),
            "recommendations": analysis.get("recommendations", []),
            "job_count": len(analysis.get("impacted_jobs", [])),
            "observed_total_duration_seconds": round(
                sum(float(j.get("duration") or 0) for j in (run_jobs or [])), 2
            ),
            "dag_summary": analysis.get("dag_summary", {}),
        }

    def get_run_jobs(self, repo: str, run_id: int) -> List[Dict[str, Any]]:
        """Fetch GitLab pipeline jobs for a given pipeline ID."""
        return self.client.list_pipeline_jobs(repo, str(run_id))

    def compute_run_metrics(
        self,
        jobs: List[Dict[str, Any]],
        carbon_intensity_kg_per_kwh: Optional[float] = None,
        runner_cpu_cores: Optional[int] = None,
        kwh_per_core_hour: Optional[float] = None,
        runner_cost_per_minute_usd: float = 0.008,
    ) -> Dict[str, Any]:
        """Compute speed/cost/carbon metrics from GitLab pipeline job durations."""
        carbon_intensity = carbon_intensity_kg_per_kwh or self.client.config.carbon_intensity_kg_per_kwh
        cpu_cores = runner_cpu_cores or self.client.config.runner_cpu_cores
        core_kwh_hour = kwh_per_core_hour or self.client.config.kwh_per_core_hour

        total_duration = 0.0
        total_kwh = 0.0
        total_cost = 0.0
        kwh_per_core_second = core_kwh_hour / 3600.0
        by_job: List[Dict[str, Any]] = []

        for j in jobs:
            sec = float(j.get("duration") or 0.0)
            total_duration += sec
            kwh = sec * cpu_cores * kwh_per_core_second
            cost = (sec / 60.0) * runner_cost_per_minute_usd
            total_kwh += kwh
            total_cost += cost
            by_job.append(
                {
                    "id": j.get("id"),
                    "name": j.get("name"),
                    "status": j.get("status"),
                    "duration_seconds": round(sec, 2),
                    "kwh": round(kwh, 4),
                    "co2_kg": round(kwh * carbon_intensity, 4),
                    "cost_usd": round(cost, 4),
                }
            )

        return {
            "total_duration_seconds": round(total_duration, 2),
            "total_kwh": round(total_kwh, 4),
            "total_co2_kg": round(total_kwh * carbon_intensity, 4),
            "total_cost_usd": round(total_cost, 4),
            "by_job": by_job,
            "assumptions": {
                "runner_cpu_cores": cpu_cores,
                "kwh_per_core_hour": core_kwh_hour,
                "carbon_intensity_kg_per_kwh": carbon_intensity,
                "runner_cost_per_minute_usd": runner_cost_per_minute_usd,
                "source": "GitLab pipeline job durations",
            },
        }

    def optimize_workflow(self, workflow_yaml: str) -> Tuple[str, List[str]]:
        optimized, changes, _warnings = optimize_ci_yaml(workflow_yaml)
        return optimized, changes

    def optimize_workflow_with_metadata(self, workflow_yaml: str, workflow_path: str = ".gitlab-ci.yml") -> Dict[str, Any]:
        optimized, changes = self.optimize_workflow(workflow_yaml)
        fixes = [
            {
                "title": c,
                "confidence": 0.9,
                "risk": "low",
                "auto_apply": True,
                "rollback": f"Revert {workflow_path} to previous revision",
            }
            for c in changes
        ]
        return {
            "optimized_workflow": optimized,
            "changes": changes,
            "fixes": fixes,
            "diff": "",
        }

    @staticmethod
    def estimate_kpi_impact(changes: List[str], baseline_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        speed_gain_pct = min(len(changes) * 4.0, 24.0)
        cost_gain_pct = min(len(changes) * 3.5, 20.0)
        co2_gain_pct = min(len(changes) * 3.5, 20.0)
        return {
            "assumptions": "Heuristic estimate based on optimization count",
            "estimated_improvements": {
                "duration_percent": round(speed_gain_pct, 1),
                "cost_percent": round(cost_gain_pct, 1),
                "co2_percent": round(co2_gain_pct, 1),
            },
        }

    def create_optimization_pr(
        self,
        repo: str,
        workflow_path: str,
        optimized_content: str,
        base_branch: str,
        branch: str,
        title: str,
        body: str,
        commit_message: str,
    ) -> Dict[str, Any]:
        self.client.ensure_branch(repo, branch, base_branch)
        commit = self.client.create_commit(
            project_id=repo,
            branch=branch,
            commit_message=commit_message,
            actions=[
                {
                    "action": "update",
                    "file_path": workflow_path,
                    "content": optimized_content,
                }
            ],
        )
        mr = self.client.create_merge_request(
            project_id=repo,
            source_branch=branch,
            target_branch=base_branch,
            title=title,
            description=body,
        )
        return {
            "commit": commit,
            "pull_request": mr,
        }
