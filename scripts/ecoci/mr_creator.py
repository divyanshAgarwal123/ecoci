from __future__ import annotations

from typing import Any, Dict, List

from .gitlab_client import GitLabClient

# Labels applied to every EcoCI merge request.
# These must also exist in the project:  Settings → Labels.
# The MR template at .gitlab/merge_request_templates/ecoci_optimization.md
# uses /label quick-actions for the same set.
ECOCI_LABELS = [
    "ecoci",
    "ci-optimization",
    "carbon-reduction",
    "pipeline-optimization",
]


def _label_line(labels: List[str]) -> str:
    """Build a /label quick-action line compatible with all Python versions."""
    parts = " ".join(f'~"{lbl}"' for lbl in labels)
    return f"/label {parts}\n\n"


def build_mr_description(summary: Dict[str, Any], pipeline_id: str) -> str:
    """Build the MR body.  Mirrors the MR template structure."""
    changes = "\n".join(
        [f"- {item}" for item in summary.get("changes", [])]
    ) or "- No changes recorded"
    metrics = summary.get("metrics", {})
    dag = summary.get("dag_summary", {})

    dag_section = ""
    if dag:
        dag_section = (
            "### DAG analysis\n"
            f"- Total jobs: {dag.get('total_jobs', '?')}\n"
            f"- Independent (parallelisable): {len(dag.get('independent_jobs', []))}\n"
            f"- Critical-path depth: {dag.get('critical_path_depth', '?')}\n"
            f"- Parallelism ratio: {dag.get('parallelism_ratio', '?')}\n\n"
        )

    return (
        "## EcoCI Optimization Summary\n"
        f"{summary.get('headline', 'Pipeline optimization')}\n\n"
        "### Changes\n"
        f"{changes}\n\n"
        f"{dag_section}"
        "### Impact (est.)\n"
        f"| Metric | Value |\n"
        f"| ------ | ----: |\n"
        f"| Time saved | {metrics.get('time_saved', 'TBD')} |\n"
        f"| Cost saved | {metrics.get('cost_saved', 'TBD')} |\n"
        f"| CO2 reduced | {metrics.get('co2_saved', 'TBD')} |\n\n"
        "### Checklist\n"
        "- [ ] Reviewed the optimised `.gitlab-ci.yml` diff\n"
        "- [ ] Verified caching keys and paths\n"
        "- [ ] Confirmed rules:changes patterns match source files\n"
        "- [ ] Ran a pipeline on this branch to confirm it passes\n\n"
        + _label_line(ECOCI_LABELS)
        + f"Triggered by pipeline `#{pipeline_id}`\n"
    )


def create_merge_request(
    client: GitLabClient,
    project_id: str,
    ref: str,
    optimized_ci_yaml: str,
    summary: Dict[str, Any],
    pipeline_id: str,
) -> Dict[str, Any]:
    # Use a protected-branch prefix so branch-protection rules
    # can be scoped to ecoci/* (Settings → Repository → Protected branches).
    branch = f"ecoci/optimize-{pipeline_id}"
    client.ensure_branch(project_id, branch, ref)

    actions = [
        {
            "action": "update",
            "file_path": ".gitlab-ci.yml",
            "content": optimized_ci_yaml,
        }
    ]

    client.create_commit(
        project_id=project_id,
        branch=branch,
        commit_message=f"EcoCI: optimize pipeline {pipeline_id}",
        actions=actions,
    )

    default_branch = client.get_default_branch(project_id)
    mr = client.create_merge_request(
        project_id=project_id,
        source_branch=branch,
        target_branch=default_branch,
        title=f"EcoCI: Optimize CI for pipeline {pipeline_id}",
        description=build_mr_description(summary, pipeline_id),
        labels=ECOCI_LABELS,
    )

    # Post carbon dashboard as a separate MR comment
    dashboard = summary.get("carbon_dashboard", "")
    if dashboard:
        client.create_merge_request_note(project_id, str(mr["iid"]), dashboard)

    return mr
