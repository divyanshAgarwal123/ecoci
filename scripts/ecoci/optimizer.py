from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .ci_analyzer import DEFAULT_CODE_PATTERNS, parse_ci_yaml, render_ci_yaml


IMAGE_MAP = {
    "node:latest": "node:lts-slim",
    "python:latest": "python:3.12-slim",
    "ruby:latest": "ruby:3.3-slim",
    "golang:latest": "golang:1.22-alpine",
}


def optimize_ci_yaml(ci_yaml: str) -> Tuple[str, List[str], List[str]]:
    data = parse_ci_yaml(ci_yaml)
    changes: List[str] = []
    warnings: List[str] = []

    if "cache" not in data and "default" not in data:
        data["cache"] = {
            "key": "$CI_COMMIT_REF_SLUG",
            "paths": [".cache/pip", "node_modules/", ".npm/"],
        }
        changes.append("Added top-level cache configuration for common dependencies.")

    for name, job in list(data.items()):
        if not isinstance(job, dict) or name.startswith("."):
            continue
        if "script" not in job and "stage" not in job:
            continue

        image = job.get("image")
        if isinstance(image, str) and image in IMAGE_MAP:
            job["image"] = IMAGE_MAP[image]
            changes.append(f"Pinned {name} image from {image} to {job['image']}.")

        if "rules" not in job and "only" not in job and "except" not in job:
            job["rules"] = [
                {"changes": DEFAULT_CODE_PATTERNS},
                {"when": "never"},
            ]
            changes.append(f"Added rules:changes to {name} to skip non-code changes.")

        if "needs" not in job:
            warnings.append(f"Consider adding needs: to {name} for better parallelism.")

        data[name] = job

    return render_ci_yaml(data), changes, warnings
