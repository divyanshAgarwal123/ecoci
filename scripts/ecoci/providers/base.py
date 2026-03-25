from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class CIProvider(ABC):
    """Abstract interface for CI providers."""

    @abstractmethod
    def list_workflow_files(self, repo: str, ref: str) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_workflow_content(self, repo: str, workflow_path: str, ref: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def analyze_workflow(
        self,
        workflow_yaml: str,
        run_jobs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def optimize_workflow(self, workflow_yaml: str) -> Tuple[str, List[str]]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
