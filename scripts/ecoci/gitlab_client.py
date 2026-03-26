from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from .config import EcoCIConfig


@dataclass
class GitLabClient:
    config: EcoCIConfig

    @staticmethod
    def _project_ref(project_id: str) -> str:
        return requests.utils.quote(str(project_id), safe="")

    def _headers(self) -> Dict[str, str]:
        return {
            "PRIVATE-TOKEN": self.config.token,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.config.base_url.rstrip('/')}/api/v4{path}"
        response = requests.request(method, url, headers=self._headers(), params=params, json=json_body, timeout=30)
        response.raise_for_status()
        if response.text:
            return response.json()
        return None

    def get_project(self, project_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/projects/{self._project_ref(project_id)}")

    def get_pipeline(self, project_id: str, pipeline_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/projects/{self._project_ref(project_id)}/pipelines/{pipeline_id}")

    def list_pipeline_jobs(self, project_id: str, pipeline_id: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/projects/{self._project_ref(project_id)}/pipelines/{pipeline_id}/jobs")

    def get_job(self, project_id: str, job_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/projects/{self._project_ref(project_id)}/jobs/{job_id}")

    def get_repository_file(self, project_id: str, file_path: str, ref: str) -> str:
        encoded_path = requests.utils.quote(file_path, safe="")
        payload = self._request("GET", f"/projects/{self._project_ref(project_id)}/repository/files/{encoded_path}", params={"ref": ref})
        content = base64.b64decode(payload["content"]).decode("utf-8")
        return content

    def create_commit(self, project_id: str, branch: str, commit_message: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        body = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": actions,
        }
        return self._request("POST", f"/projects/{self._project_ref(project_id)}/repository/commits", json_body=body)

    def create_merge_request(
        self,
        project_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        remove_source_branch: bool = True,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
            "remove_source_branch": remove_source_branch,
        }
        if labels:
            body["labels"] = ",".join(labels)
        return self._request("POST", f"/projects/{self._project_ref(project_id)}/merge_requests", json_body=body)

    def create_merge_request_note(self, project_id: str, mr_iid: str, body: str) -> Dict[str, Any]:
        payload = {"body": body}
        return self._request("POST", f"/projects/{self._project_ref(project_id)}/merge_requests/{mr_iid}/notes", json_body=payload)

    def create_branch(self, project_id: str, branch: str, ref: str) -> Dict[str, Any]:
        return self._request("POST", f"/projects/{self._project_ref(project_id)}/repository/branches", params={"branch": branch, "ref": ref})

    def get_default_branch(self, project_id: str) -> str:
        project = self.get_project(project_id)
        return project.get("default_branch", "main")

    def ensure_branch(self, project_id: str, branch: str, ref: str) -> None:
        try:
            self.create_branch(project_id, branch, ref)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 400:
                return
            raise
