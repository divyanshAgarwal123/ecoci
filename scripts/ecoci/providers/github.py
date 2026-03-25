from __future__ import annotations

import base64
import difflib
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

    @staticmethod
    def _infer_runner_cores(job: Dict[str, Any], default_cores: int) -> int:
        """Best-effort runner core inference from labels/name metadata."""
        labels = job.get("labels") or []
        label_text = " ".join([str(x).lower() for x in labels])
        name_text = str(job.get("runner_name", "")).lower()
        combined = f"{label_text} {name_text}"

        for token, cores in (("16-core", 16), ("8-core", 8), ("4-core", 4), ("2-core", 2)):
            if token in combined:
                return cores

        if "large" in combined or "xlarge" in combined:
            return max(default_cores, 8)
        if "ubuntu" in combined or "windows" in combined or "macos" in combined:
            return default_cores
        return default_cores

    @staticmethod
    def _os_energy_multiplier(job: Dict[str, Any]) -> float:
        labels = job.get("labels") or []
        label_text = " ".join([str(x).lower() for x in labels])
        if "windows" in label_text:
            return 1.1
        if "macos" in label_text:
            return 1.2
        return 1.0

    def compute_run_metrics(
        self,
        jobs: List[Dict[str, Any]],
        carbon_intensity_kg_per_kwh: float = 0.475,
        runner_cpu_cores: int = 2,
        kwh_per_core_hour: float = 0.5,
        runner_cost_per_minute_usd: float = 0.008,
    ) -> Dict[str, Any]:
        """Compute speed/cost/carbon metrics from run job durations with runner-aware estimates."""
        by_job: List[Dict[str, Any]] = []
        total_duration = 0.0
        total_kwh = 0.0
        total_cost = 0.0
        total_weighted_cores = 0.0

        kwh_per_core_second = kwh_per_core_hour / 3600.0
        for j in jobs:
            sec = self._duration_seconds(j)
            total_duration += sec

            inferred_cores = self._infer_runner_cores(j, runner_cpu_cores)
            energy_multiplier = self._os_energy_multiplier(j)

            kwh = sec * inferred_cores * kwh_per_core_second * energy_multiplier
            cost = (sec / 60.0) * runner_cost_per_minute_usd
            total_kwh += kwh
            total_cost += cost
            total_weighted_cores += inferred_cores
            by_job.append(
                {
                    "id": j.get("id"),
                    "name": j.get("name"),
                    "status": j.get("conclusion") or j.get("status"),
                    "duration_seconds": round(sec, 2),
                    "estimated_runner_cores": inferred_cores,
                    "energy_multiplier": energy_multiplier,
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
                "default_runner_cpu_cores": runner_cpu_cores,
                "average_estimated_runner_cores": round(total_weighted_cores / len(jobs), 2) if jobs else runner_cpu_cores,
                "kwh_per_core_hour": kwh_per_core_hour,
                "carbon_intensity_kg_per_kwh": carbon_intensity_kg_per_kwh,
                "runner_cost_per_minute_usd": runner_cost_per_minute_usd,
                "estimation_model": "duration_seconds * inferred_cores * os_multiplier",
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
        findings: List[Dict[str, Any]] = []

        def add_finding(fid: str, severity: str, message: str, fix: str, confidence: float) -> None:
            findings.append(
                {
                    "id": fid,
                    "severity": severity,
                    "message": message,
                    "fix": fix,
                    "confidence": confidence,
                    "auto_apply": confidence >= 0.9,
                }
            )

        def parse_permissions(perms: Any) -> Dict[str, str]:
            if isinstance(perms, str):
                return {"*": perms}
            if isinstance(perms, dict):
                return {str(k): str(v) for k, v in perms.items()}
            return {}

        if "concurrency" not in data:
            issues.append("Missing workflow-level concurrency control")
            recommendations.append("Add concurrency group to auto-cancel superseded runs")
            add_finding(
                "missing_concurrency",
                "medium",
                "Workflow missing concurrency control; superseded runs may waste CI minutes",
                "Add workflow-level concurrency with cancel-in-progress",
                0.98,
            )

        if "permissions" not in data:
            issues.append("Missing explicit workflow permissions")
            recommendations.append("Set least-privilege workflow permissions at top level")
            add_finding(
                "missing_permissions",
                "medium",
                "Workflow does not define explicit permissions; defaults may be broader than needed",
                "Add top-level permissions: contents: read (expand only when needed)",
                0.93,
            )
        else:
            perms = parse_permissions(data.get("permissions"))
            if perms.get("*", "").lower() == "write-all":
                issues.append("Workflow uses write-all permissions")
                add_finding(
                    "workflow_write_all_permissions",
                    "critical",
                    "Workflow permissions are set to write-all",
                    "Use explicit least-privilege permissions (prefer contents: read)",
                    0.95,
                )

            broad_write_scopes = [k for k, v in perms.items() if k != "*" and str(v).lower() == "write"]
            if broad_write_scopes:
                recommendations.append("Review write permissions and keep only required scopes")
                add_finding(
                    "broad_write_permissions",
                    "high",
                    f"Workflow requests write scopes: {', '.join(sorted(broad_write_scopes))}",
                    "Reduce write scopes to minimum required for workflow operations",
                    0.88,
                )

        top_on = data.get("on", {})
        has_path_filters = False
        if isinstance(top_on, dict):
            for evt in ("push", "pull_request"):
                evt_cfg = top_on.get(evt)
                if isinstance(evt_cfg, dict) and ("paths" in evt_cfg or "paths-ignore" in evt_cfg):
                    has_path_filters = True
            if "pull_request_target" in top_on:
                issues.append("Workflow triggers on pull_request_target")
                add_finding(
                    "pull_request_target_event",
                    "high",
                    "Workflow uses pull_request_target; validate untrusted code handling",
                    "Avoid privileged steps for forked PRs and restrict token permissions",
                    0.82,
                )
        if not has_path_filters:
            recommendations.append("Add paths/paths-ignore filters to skip workflow on docs-only changes")
            add_finding(
                "missing_paths_filters",
                "low",
                "Workflow runs on all changes including docs-only updates",
                "Add paths-ignore for docs and markdown-only changes",
                0.9,
            )

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
                add_finding(
                    "missing_timeout",
                    "medium",
                    f"Job '{job_name}' has no timeout-minutes",
                    "Set timeout-minutes to prevent stalled jobs consuming CI minutes",
                    0.97,
                )

            runs_on = job.get("runs-on")
            if isinstance(runs_on, str) and runs_on.endswith("-latest"):
                recommendations.append(f"Job '{job_name}' uses floating runner label '{runs_on}'")
                add_finding(
                    "floating_runner_label",
                    "low",
                    f"Job '{job_name}' uses floating runner image '{runs_on}'",
                    "Pin to a tested runner image where reproducibility is critical",
                    0.8,
                )

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
                    add_finding(
                        "floating_action_ref",
                        "high",
                        f"Job '{job_name}' uses floating action reference '{uses}'",
                        "Pin actions to immutable commit SHA or stable major version",
                        0.85,
                    )
                elif uses.startswith("actions/") and re.search(r"@v\d+$", uses):
                    recommendations.append(f"Job '{job_name}' action '{uses}' is major-version pinned only")
                    add_finding(
                        "action_major_pin_only",
                        "low",
                        f"Job '{job_name}' uses major tag '{uses}' instead of immutable SHA",
                        "Prefer commit SHA pinning for high-assurance supply-chain security",
                        0.72,
                    )

                if uses.startswith("actions/checkout@"):
                    with_cfg = step.get("with") if isinstance(step.get("with"), dict) else {}
                    if with_cfg.get("persist-credentials", True):
                        recommendations.append(
                            f"Job '{job_name}' checkout step keeps credentials persisted by default"
                        )
                        add_finding(
                            "checkout_persist_credentials",
                            "medium",
                            f"Job '{job_name}' uses actions/checkout with persist-credentials enabled",
                            "Set persist-credentials: false unless push/publish is required",
                            0.78,
                        )

                run_cmd = str(step.get("run", ""))
                if re.search(r"curl\s+[^\n]*\|\s*(bash|sh|zsh)", run_cmd, re.IGNORECASE):
                    issues.append(f"Job '{job_name}' has curl|shell execution pattern")
                    add_finding(
                        "curl_pipe_shell",
                        "critical",
                        f"Job '{job_name}' executes remote script via curl|shell",
                        "Download script, verify checksum/signature, then execute",
                        0.7,
                    )
                if re.search(r"echo\s+\$\{\{\s*secrets\.[^}]+\}\}", run_cmd, re.IGNORECASE):
                    issues.append(f"Job '{job_name}' may print secrets to logs")
                    add_finding(
                        "secrets_echo",
                        "high",
                        f"Job '{job_name}' appears to echo secret values in shell commands",
                        "Avoid printing secret values and mask derived tokens",
                        0.76,
                    )

                env_cfg = step.get("env") if isinstance(step.get("env"), dict) else {}
                for env_key, env_val in env_cfg.items():
                    sval = str(env_val)
                    if re.search(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z\-_]{20,})", sval):
                        issues.append(f"Job '{job_name}' step env '{env_key}' appears to contain hardcoded credential")
                        add_finding(
                            "hardcoded_secret",
                            "critical",
                            f"Job '{job_name}' step env '{env_key}' may contain hardcoded secret material",
                            "Move secret to GitHub Actions secrets and reference via ${{ secrets.* }}",
                            0.9,
                        )
                if re.search(r"wget\s+[^\n]*\|\s*(bash|sh|zsh)", run_cmd, re.IGNORECASE):
                    issues.append(f"Job '{job_name}' has wget|shell execution pattern")
                    add_finding(
                        "wget_pipe_shell",
                        "critical",
                        f"Job '{job_name}' executes remote script via wget|shell",
                        "Download script, verify checksum/signature, then execute",
                        0.7,
                    )

            if not has_cache:
                recommendations.append(f"Job '{job_name}' has no dependency caching")
                add_finding(
                    "missing_cache",
                    "medium",
                    f"Job '{job_name}' has no dependency caching",
                    "Enable setup-* cache and/or actions/cache",
                    0.95,
                )

        severity_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        ranked_findings: List[Dict[str, Any]] = []
        for f in findings:
            sev = str(f.get("severity", "low")).lower()
            conf = float(f.get("confidence", 0.0))
            score = severity_weight.get(sev, 1) * 100 + int(conf * 100)
            f_with_score = dict(f)
            f_with_score["priority_score"] = score
            ranked_findings.append(f_with_score)

        ranked_findings.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

        ranked_recommendations: List[Dict[str, Any]] = []
        seen_fixes = set()
        for f in ranked_findings:
            fix = str(f.get("fix", "")).strip()
            if not fix or fix in seen_fixes:
                continue
            seen_fixes.add(fix)
            ranked_recommendations.append(
                {
                    "fix": fix,
                    "severity": f.get("severity", "low"),
                    "confidence": f.get("confidence", 0.0),
                    "priority_score": f.get("priority_score", 0),
                }
            )

        critical_count = sum(1 for f in ranked_findings if str(f.get("severity", "")).lower() == "critical")
        high_count = sum(1 for f in ranked_findings if str(f.get("severity", "")).lower() == "high")
        quality_gate = {
            "pass": critical_count == 0,
            "critical_count": critical_count,
            "high_count": high_count,
            "status": "fail" if critical_count > 0 else ("warn" if high_count > 0 else "pass"),
        }

        return {
            "issues": sorted(set(issues)),
            "recommendations": sorted(set(recommendations)),
            "job_count": len(jobs),
            "observed_total_duration_seconds": round(total_duration_seconds, 1),
            "findings": findings,
            "prioritized_findings": ranked_findings,
            "prioritized_recommendations": ranked_recommendations,
            "quality_gate": quality_gate,
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

    def optimize_workflow_with_metadata(self, workflow_yaml: str) -> Dict[str, Any]:
        """Return optimized workflow with confidence-scored fixes and diff preview."""
        optimized, changes = self.optimize_workflow(workflow_yaml)

        fixes: List[Dict[str, Any]] = []
        for c in changes:
            confidence = 0.9
            risk = "low"
            if "concurrency" in c.lower():
                confidence = 0.98
            elif "timeout-minutes" in c.lower():
                confidence = 0.97
            elif "cache" in c.lower():
                confidence = 0.93
            elif "workflow" in c.lower():
                confidence = 0.9

            fixes.append(
                {
                    "title": c,
                    "confidence": round(confidence, 2),
                    "risk": risk,
                    "auto_apply": confidence >= 0.9,
                    "rollback": "Revert .github/workflows file to previous revision",
                }
            )

        diff_text = self.build_unified_diff(workflow_yaml, optimized)
        return {
            "optimized_workflow": optimized,
            "changes": changes,
            "fixes": fixes,
            "diff": diff_text,
        }

    @staticmethod
    def build_unified_diff(before_text: str, after_text: str, before_name: str = "before.yml", after_name: str = "after.yml") -> str:
        diff = difflib.unified_diff(
            before_text.splitlines(keepends=True),
            after_text.splitlines(keepends=True),
            fromfile=before_name,
            tofile=after_name,
        )
        return "".join(diff)

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
