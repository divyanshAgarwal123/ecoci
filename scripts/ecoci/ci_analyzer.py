from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Dict, List, Set, Tuple

import yaml


DEFAULT_CODE_PATTERNS = [
    "**/*.py", "**/*.js", "**/*.ts", "**/*.go",
    "**/*.java", "**/*.rb", "**/*.php", "**/*.yml",
]

# ── Runner-tier heuristics ────────────────────────────────────
# Tags that hint at heavyweight shared runners
HEAVY_TAGS: Set[str] = {"docker", "linux", "shared", "gitlab-org"}
# Tags that hint at lighter / spot runners
LIGHT_TAGS: Set[str] = {"small", "spot", "medium", "saas-linux-small-amd64"}
# Jobs whose names suggest they are lightweight tasks
LIGHTWEIGHT_JOB_KEYWORDS = {"lint", "format", "check", "sast", "secret_detection", "docs"}


def _is_job(name: str, job: Dict[str, Any]) -> bool:
    if not isinstance(job, dict):
        return False
    if name.startswith("."):
        return False
    return "script" in job or "stage" in job


# ── DAG / needs: analysis ─────────────────────────────────────

def _build_dag(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Return adjacency list {job -> [upstream dependencies]}."""
    dag: Dict[str, List[str]] = {}
    for name, job in data.items():
        if not _is_job(name, job):
            continue
        needs = job.get("needs", [])
        if isinstance(needs, list):
            upstream = []
            for n in needs:
                if isinstance(n, str):
                    upstream.append(n)
                elif isinstance(n, dict) and "job" in n:
                    upstream.append(n["job"])
            dag[name] = upstream
        else:
            dag[name] = []
    return dag


def _has_cycle(dag: Dict[str, List[str]]) -> bool:
    """Kahn's algorithm: return True if the DAG has a cycle."""
    in_degree: Dict[str, int] = defaultdict(int)
    for node in dag:
        in_degree.setdefault(node, 0)
        for dep in dag[node]:
            in_degree[dep] = in_degree.get(dep, 0)
    for node in dag:
        for dep in dag[node]:
            in_degree[node] += 1
    queue = deque(n for n, d in in_degree.items() if d == 0)
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for node, deps in dag.items():
            if current in deps:
                in_degree[node] -= 1
                if in_degree[node] == 0:
                    queue.append(node)
    return visited < len(in_degree)


def _critical_path_depth(dag: Dict[str, List[str]]) -> int:
    """Return longest chain length in the DAG (1 = no deps)."""
    memo: Dict[str, int] = {}

    def _depth(node: str) -> int:
        if node in memo:
            return memo[node]
        deps = dag.get(node, [])
        if not deps:
            memo[node] = 1
            return 1
        memo[node] = 1 + max(_depth(d) for d in deps)
        return memo[node]

    if not dag:
        return 0
    return max(_depth(n) for n in dag)


def _independent_jobs(dag: Dict[str, List[str]]) -> List[str]:
    """Jobs with no upstream dependency that can run immediately."""
    return [name for name, deps in dag.items() if not deps]


def analyze_dag(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a summary of the needs: dependency graph."""
    dag = _build_dag(data)
    cycle = _has_cycle(dag)
    depth = _critical_path_depth(dag)
    independent = _independent_jobs(dag)
    total_jobs = len(dag)
    parallelism_ratio = round(len(independent) / total_jobs, 2) if total_jobs else 0.0

    return {
        "has_cycle": cycle,
        "critical_path_depth": depth,
        "independent_jobs": independent,
        "total_jobs": total_jobs,
        "parallelism_ratio": parallelism_ratio,
        "dag": {k: v for k, v in dag.items()},
    }


# ── Tag / runner-tier analysis ────────────────────────────────

def _analyze_tags(name: str, job: Dict[str, Any]) -> List[str]:
    """Return recommendations about runner tags for a single job."""
    recs: List[str] = []
    tags = job.get("tags", [])
    lower_name = name.lower()
    is_lightweight = any(kw in lower_name for kw in LIGHTWEIGHT_JOB_KEYWORDS)

    if not tags:
        if is_lightweight:
            recs.append(
                f"Job '{name}' looks lightweight — add tags: ['saas-linux-small-amd64'] "
                f"to use a smaller, cheaper runner."
            )
        else:
            recs.append(
                f"Specify runner tags for '{name}' to control runner selection "
                f"(e.g., 'docker', 'small', or 'spot')."
            )
        return recs

    tag_set = {t.lower() for t in tags}
    if is_lightweight and tag_set & HEAVY_TAGS and not tag_set & LIGHT_TAGS:
        recs.append(
            f"Job '{name}' appears lightweight but uses heavy runner tags {tags}. "
            f"Consider switching to a smaller tier (e.g., 'saas-linux-small-amd64')."
        )

    return recs


# ── Main analysis entry point ─────────────────────────────────

def analyze_ci_config(ci_yaml: str) -> Dict[str, Any]:
    data = yaml.safe_load(ci_yaml) or {}
    issues: List[str] = []
    recommendations: List[str] = []
    impacted_jobs: List[str] = []

    # ── Global checks ────────────────────────────────────────
    if "cache" not in data and "default" not in data:
        issues.append("No global cache configuration found.")
        recommendations.append(
            "Add a top-level cache with a stable key and common paths to speed up builds."
        )

    # ── DAG analysis ─────────────────────────────────────────
    dag_summary = analyze_dag(data)
    if dag_summary["has_cycle"]:
        issues.append("Cycle detected in the needs: dependency graph — pipeline may hang.")
    if dag_summary["total_jobs"] > 2 and dag_summary["parallelism_ratio"] < 0.3:
        recommendations.append(
            f"Only {len(dag_summary['independent_jobs'])}/{dag_summary['total_jobs']} jobs "
            f"are independent (parallelism ratio {dag_summary['parallelism_ratio']}). "
            f"Review needs: to allow more jobs to start earlier."
        )
    if dag_summary["critical_path_depth"] > 5:
        recommendations.append(
            f"Critical path depth is {dag_summary['critical_path_depth']}. "
            f"Try flattening the DAG to reduce overall pipeline duration."
        )

    # ── Per-job checks ───────────────────────────────────────
    for name, job in data.items():
        if not _is_job(name, job):
            continue
        impacted_jobs.append(name)

        # Image pin
        if "image" in job and isinstance(job["image"], str) and ":latest" in job["image"]:
            issues.append(f"Job '{name}' uses a floating :latest image tag.")
            recommendations.append(
                f"Pin '{name}' to a slimmer, versioned image to reduce download size and variability."
            )

        # Rules / skip on non-code
        if "rules" not in job and "only" not in job and "except" not in job:
            recommendations.append(
                f"Consider adding rules:changes for '{name}' to skip the job on docs-only or non-code changes."
            )

        # needs: missing
        if "needs" not in job:
            recommendations.append(
                f"If '{name}' can run earlier, add needs: to enable parallel execution."
            )

        # Tags / runner tier
        tag_recs = _analyze_tags(name, job)
        recommendations.extend(tag_recs)

    confidence = "medium" if issues or recommendations else "high"

    return {
        "issues": sorted(set(issues)),
        "recommendations": sorted(set(recommendations)),
        "impacted_jobs": sorted(set(impacted_jobs)),
        "dag_summary": dag_summary,
        "confidence": confidence,
    }


def parse_ci_yaml(ci_yaml: str) -> Dict[str, Any]:
    return yaml.safe_load(ci_yaml) or {}


def render_ci_yaml(data: Dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False)
