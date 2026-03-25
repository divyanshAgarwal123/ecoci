from __future__ import annotations

import os
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

    def optimize_workflow(self, workflow_yaml: str) -> Tuple[str, List[str]]:
        optimized, changes, _warnings = optimize_ci_yaml(workflow_yaml)
        return optimized, changes

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
