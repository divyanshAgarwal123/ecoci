from __future__ import annotations

import base64
import os
import re
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml

from .base import CIProvider


class GitHubProvider(CIProvider):
    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        self.token = token or os.getenv("GITHUB_TOKEN", "").strip()
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        resp = requests.request(method, url, headers=self._headers(), params=params, json=json_body, timeout=30)
        if resp.status_code >= 400:
            raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text[:300]}")
        if not resp.text:
            return None
        return resp.json()

    @staticmethod
    def infer_repo_from_git() -> Optional[str]:
        """Infer owner/repo from git remote origin URL in current directory."""
        try:
            out = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        except Exception:
            return None

        # https://github.com/owner/repo.git
        m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", out)
        if not m:
            return None
        return f"{m.group('owner')}/{m.group('repo')}"

    def get_default_branch(self, repo: str) -> str:
        payload = self._request("GET", f"/repos/{repo}")
        return payload.get("default_branch", "main")

    def list_workflow_files(self, repo: str, ref: str = "main") -> List[str]:
        tree = self._request("GET", f"/repos/{repo}/git/trees/{ref}", params={"recursive": "1"})
        files = []
        for item in tree.get("tree", []):
            path = item.get("path", "")
            if item.get("type") == "blob" and path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
                files.append(path)
        return sorted(files)

    def get_workflow_content(self, repo: str, workflow_path: str, ref: str = "main") -> str:
        payload = self._request("GET", f"/repos/{repo}/contents/{workflow_path}", params={"ref": ref})
        content_b64 = payload.get("content", "")
        if not content_b64:
            return ""
        return base64.b64decode(content_b64).decode("utf-8")

    def list_workflow_runs(self, repo: str, branch: Optional[str] = None, per_page: int = 10) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"per_page": per_page}
        if branch:
            params["branch"] = branch
        data = self._request("GET", f"/repos/{repo}/actions/runs", params=params)
        return data.get("workflow_runs", [])

    def get_run_jobs(self, repo: str, run_id: int) -> List[Dict[str, Any]]:
        data = self._request("GET", f"/repos/{repo}/actions/runs/{run_id}/jobs", params={"per_page": 100})
        return data.get("jobs", [])

    def get_job_logs(self, repo: str, job_id: int) -> str:
        """Fetch plain-text logs for a GitHub Actions job."""
        url = f"{self.base_url}/repos/{repo}/actions/jobs/{job_id}/logs"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        if resp.status_code >= 400:
            raise RuntimeError(f"GitHub logs API error {resp.status_code}: {resp.text[:200]}")
        return resp.text

    @staticmethod
    def _duration_seconds(job: Dict[str, Any]) -> float:
        # Newer APIs can include run_duration_ms.
        ms = job.get("run_duration_ms")
        if ms:
            return round(float(ms) / 1000.0, 2)

        started = job.get("started_at")
        completed = job.get("completed_at")
        if not started or not completed:
            return 0.0

        try:
            s = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
            c = datetime.fromisoformat(str(completed).replace("Z", "+00:00"))
            return round(max((c - s).total_seconds(), 0.0), 2)
        except Exception:
            return 0.0

    def compute_run_metrics(
        self,
        jobs: List[Dict[str, Any]],
        carbon_intensity_kg_per_kwh: float = 0.475,
        runner_cpu_cores: int = 2,
        kwh_per_core_hour: float = 0.5,
        runner_cost_per_minute_usd: float = 0.008,
    ) -> Dict[str, Any]:
        """Compute speed/cost/carbon metrics from real run job durations."""
        by_job: List[Dict[str, Any]] = []
        total_duration = 0.0
        total_kwh = 0.0
        total_cost = 0.0

        kwh_per_core_second = kwh_per_core_hour / 3600.0
        for j in jobs:
            sec = self._duration_seconds(j)
            total_duration += sec
            kwh = sec * runner_cpu_cores * kwh_per_core_second
            cost = (sec / 60.0) * runner_cost_per_minute_usd
            total_kwh += kwh
            total_cost += cost
            by_job.append(
                {
                    "id": j.get("id"),
                    "name": j.get("name"),
                    "status": j.get("conclusion") or j.get("status"),
                    "duration_seconds": round(sec, 2),
                    "kwh": round(kwh, 4),
                    "co2_kg": round(kwh * carbon_intensity_kg_per_kwh, 4),
                    "cost_usd": round(cost, 4),
                }
            )

        return {
            "total_duration_seconds": round(total_duration, 2),
            "total_kwh": round(total_kwh, 4),
            "total_co2_kg": round(total_kwh * carbon_intensity_kg_per_kwh, 4),
            "total_cost_usd": round(total_cost, 4),
            "by_job": by_job,
            "assumptions": {
                "runner_cpu_cores": runner_cpu_cores,
                "kwh_per_core_hour": kwh_per_core_hour,
                "carbon_intensity_kg_per_kwh": carbon_intensity_kg_per_kwh,
                "runner_cost_per_minute_usd": runner_cost_per_minute_usd,
            },
        }

    @staticmethod
    def build_dashboard_markdown(repo: str, workflow_path: str, run_id: Optional[int], metrics: Dict[str, Any]) -> str:
        lines = [
            "## 🌱 EcoCI Run Dashboard",
            "",
            f"- Repo: `{repo}`",
            f"- Workflow: `{workflow_path}`",
        ]
        if run_id:
            lines.append(f"- Run ID: `{run_id}`")
        lines.extend(
            [
                "",
                "| Metric | Value |",
                "| --- | ---: |",
                f"| Total duration | {metrics.get('total_duration_seconds', 0)} s |",
                f"| Estimated cost | ${metrics.get('total_cost_usd', 0)} |",
                f"| Energy | {metrics.get('total_kwh', 0)} kWh |",
                f"| CO2 | {metrics.get('total_co2_kg', 0)} kg |",
                "",
                "_Generated by EcoCI CLI (GitHub provider)._",
            ]
        )
        return "\n".join(lines)

    def create_pr_comment(self, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        return self._request(
            "POST",
            f"/repos/{repo}/issues/{pr_number}/comments",
            json_body={"body": body},
        )

    def analyze_workflow(
        self,
        workflow_yaml: str,
        run_jobs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        data = yaml.safe_load(workflow_yaml) or {}
        jobs = data.get("jobs", {}) if isinstance(data, dict) else {}
        issues: List[str] = []
        recommendations: List[str] = []

        if "concurrency" not in data:
            issues.append("Missing workflow-level concurrency control")
            recommendations.append("Add concurrency group to auto-cancel superseded runs")

        top_on = data.get("on", {})
        has_path_filters = False
        if isinstance(top_on, dict):
            for evt in ("push", "pull_request"):
                evt_cfg = top_on.get(evt)
                if isinstance(evt_cfg, dict) and ("paths" in evt_cfg or "paths-ignore" in evt_cfg):
                    has_path_filters = True
        if not has_path_filters:
            recommendations.append("Add paths/paths-ignore filters to skip workflow on docs-only changes")

        total_duration_seconds = 0.0
        if run_jobs:
            for j in run_jobs:
                sec = float(j.get("run_duration_ms") or 0) / 1000.0
                if sec <= 0 and j.get("started_at") and j.get("completed_at"):
                    # Best effort fallback skipped for brevity
                    pass
                total_duration_seconds += sec

        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue

            if "timeout-minutes" not in job:
                recommendations.append(f"Job '{job_name}' missing timeout-minutes")

            runs_on = job.get("runs-on")
            if isinstance(runs_on, str) and runs_on.endswith("-latest"):
                recommendations.append(f"Job '{job_name}' uses floating runner label '{runs_on}'")

            steps = job.get("steps", []) if isinstance(job.get("steps"), list) else []
            has_cache = False
            for step in steps:
                if not isinstance(step, dict):
                    continue
                uses = str(step.get("uses", ""))
                if uses.startswith("actions/cache@"):
                    has_cache = True
                if uses.startswith("actions/setup-node@") and isinstance(step.get("with"), dict):
                    if step["with"].get("cache"):
                        has_cache = True
                if uses.startswith("actions/setup-python@") and isinstance(step.get("with"), dict):
                    if step["with"].get("cache"):
                        has_cache = True
                if uses.endswith("@main") or uses.endswith("@master"):
                    issues.append(f"Job '{job_name}' uses floating action ref '{uses}'")

            if not has_cache:
                recommendations.append(f"Job '{job_name}' has no dependency caching")

        return {
            "issues": sorted(set(issues)),
            "recommendations": sorted(set(recommendations)),
            "job_count": len(jobs),
            "observed_total_duration_seconds": round(total_duration_seconds, 1),
        }

    def optimize_workflow(self, workflow_yaml: str) -> Tuple[str, List[str]]:
        data = yaml.safe_load(workflow_yaml) or {}
        changes: List[str] = []

        if "concurrency" not in data:
            data["concurrency"] = {
                "group": "${{ github.workflow }}-${{ github.ref }}",
                "cancel-in-progress": True,
            }
            changes.append("Added workflow concurrency with cancel-in-progress")

        jobs = data.get("jobs", {}) if isinstance(data, dict) else {}
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue

            if "timeout-minutes" not in job:
                job["timeout-minutes"] = 20
                changes.append(f"Added timeout-minutes to job '{job_name}'")

            steps = job.get("steps")
            if not isinstance(steps, list):
                continue

            for step in steps:
                if not isinstance(step, dict):
                    continue
                uses = str(step.get("uses", ""))
                with_cfg = step.get("with")

                if uses.startswith("actions/setup-node@"):
                    if not isinstance(with_cfg, dict):
                        with_cfg = {}
                        step["with"] = with_cfg
                    if not with_cfg.get("cache"):
                        with_cfg["cache"] = "npm"
                        changes.append(f"Enabled npm cache in '{job_name}'")

                if uses.startswith("actions/setup-python@"):
                    if not isinstance(with_cfg, dict):
                        with_cfg = {}
                        step["with"] = with_cfg
                    if not with_cfg.get("cache"):
                        with_cfg["cache"] = "pip"
                        changes.append(f"Enabled pip cache in '{job_name}'")

        optimized = yaml.safe_dump(data, sort_keys=False)
        return optimized, changes

    def _get_ref_sha(self, repo: str, branch: str) -> str:
        payload = self._request("GET", f"/repos/{repo}/git/ref/heads/{branch}")
        return payload["object"]["sha"]

    def _ensure_branch(self, repo: str, branch: str, base_branch: str) -> None:
        try:
            self._request("GET", f"/repos/{repo}/git/ref/heads/{branch}")
            return
        except Exception:
            base_sha = self._get_ref_sha(repo, base_branch)
            self._request(
                "POST",
                f"/repos/{repo}/git/refs",
                json_body={"ref": f"refs/heads/{branch}", "sha": base_sha},
            )

    def _upsert_file(self, repo: str, path: str, branch: str, content_text: str, message: str) -> Dict[str, Any]:
        existing_sha = None
        try:
            existing = self._request("GET", f"/repos/{repo}/contents/{path}", params={"ref": branch})
            existing_sha = existing.get("sha")
        except Exception:
            existing_sha = None

        body: Dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content_text.encode("utf-8")).decode("utf-8"),
            "branch": branch,
        }
        if existing_sha:
            body["sha"] = existing_sha

        return self._request("PUT", f"/repos/{repo}/contents/{path}", json_body=body)

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
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN is required to create commits/PRs")

        self._ensure_branch(repo, branch, base_branch)
        commit_res = self._upsert_file(repo, workflow_path, branch, optimized_content, commit_message)
        pr = self._request(
            "POST",
            f"/repos/{repo}/pulls",
            json_body={
                "title": title,
                "head": branch,
                "base": base_branch,
                "body": body,
            },
        )
        return {
            "commit": commit_res,
            "pull_request": pr,
        }
