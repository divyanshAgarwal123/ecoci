#!/usr/bin/env python3
"""
Webhook receiver / trigger script for EcoCI.

This script is designed to be called by a GitLab project webhook
(Pipeline events) or from a scheduled pipeline.  It extracts the
completed-pipeline metadata and triggers a new pipeline via the
GitLab Pipeline Trigger API, passing the three ECOCI_* variables
that the `ecoci_runner` CI job expects.

─── Setup ──────────────────────────────────────────────────────
1. Go to Settings → CI/CD → Pipeline trigger tokens → Add trigger.
   Save the token as CI/CD variable `ECOCI_TRIGGER_TOKEN` (masked).

2. Go to Settings → Webhooks → Add webhook.
   URL   : (your server or GitLab function URL)
   Trigger: Pipeline events
   Secret : (optional shared secret)

   OR  run this script as a downstream CI job that reacts
   to the `CI_PIPELINE_SOURCE == "pipeline"` predefined var.

3. Alternatively, invoke the script from the CLI:
     export GITLAB_TOKEN=glpat-...
     export ECOCI_TRIGGER_TOKEN=...
     python scripts/ecoci/webhook_trigger.py \\
       --project-id 34560917 \\
       --pipeline-id 12345 \\
       --ref main

─── How it works ───────────────────────────────────────────────
The script calls:
  POST /projects/:id/trigger/pipeline
    ?token=ECOCI_TRIGGER_TOKEN
    &ref=main
    &variables[ECOCI_PROJECT_ID]=...
    &variables[ECOCI_PIPELINE_ID]=...
    &variables[ECOCI_REF]=...

This starts a new pipeline on the default branch that picks up
the `ecoci_runner` job automatically.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

import requests


def trigger_ecoci_pipeline(
    base_url: str,
    project_id: str,
    trigger_token: str,
    ref: str,
    ecoci_project_id: str,
    ecoci_pipeline_id: str,
    ecoci_ref: str,
) -> Dict[str, Any]:
    """Fire a pipeline via the Trigger API with EcoCI variables."""
    url = f"{base_url.rstrip('/')}/api/v4/projects/{project_id}/trigger/pipeline"
    payload = {
        "token": trigger_token,
        "ref": ref,
        "variables[ECOCI_PROJECT_ID]": ecoci_project_id,
        "variables[ECOCI_PIPELINE_ID]": ecoci_pipeline_id,
        "variables[ECOCI_REF]": ecoci_ref,
    }
    resp = requests.post(url, data=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_webhook_payload(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Extract project/pipeline/ref from a Pipeline webhook event."""
    attrs = payload.get("object_attributes", {})
    status = attrs.get("status", "")
    if status != "success":
        return None
    project = payload.get("project", {})
    return {
        "project_id": str(project.get("id", "")),
        "pipeline_id": str(attrs.get("id", "")),
        "ref": str(attrs.get("ref", "main")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger EcoCI pipeline from webhook or CLI")
    parser.add_argument("--project-id", required=False, help="Project that hosts EcoCI (defaults to CI_PROJECT_ID)")
    parser.add_argument("--pipeline-id", required=False, help="Completed pipeline ID to analyze")
    parser.add_argument("--ref", required=False, default="main", help="Ref to trigger the EcoCI pipeline on")
    parser.add_argument("--webhook-payload", required=False, help="Path to JSON file with webhook body")
    args = parser.parse_args()

    base_url = os.getenv("GITLAB_BASE_URL", os.getenv("CI_SERVER_URL", "https://gitlab.com"))
    trigger_token = os.getenv("ECOCI_TRIGGER_TOKEN", "")
    ecoci_host_project = args.project_id or os.getenv("CI_PROJECT_ID", "")

    if not trigger_token:
        print("❌ ECOCI_TRIGGER_TOKEN is not set. Create one in Settings → CI/CD → Pipeline trigger tokens.", file=sys.stderr)
        sys.exit(1)

    if args.webhook_payload:
        with open(args.webhook_payload) as f:
            payload = json.load(f)
        parsed = parse_webhook_payload(payload)
        if parsed is None:
            print("⏭  Pipeline status is not 'success'; skipping.")
            sys.exit(0)
        ecoci_project_id = parsed["project_id"]
        ecoci_pipeline_id = parsed["pipeline_id"]
        ecoci_ref = parsed["ref"]
    else:
        ecoci_project_id = args.project_id or ecoci_host_project
        ecoci_pipeline_id = args.pipeline_id or ""
        ecoci_ref = args.ref

    if not ecoci_project_id or not ecoci_pipeline_id:
        print("❌ --project-id and --pipeline-id (or --webhook-payload) are required.", file=sys.stderr)
        sys.exit(1)

    print(f"🚀 Triggering EcoCI pipeline on project {ecoci_host_project}, ref={args.ref}")
    print(f"   ECOCI_PROJECT_ID={ecoci_project_id}")
    print(f"   ECOCI_PIPELINE_ID={ecoci_pipeline_id}")
    print(f"   ECOCI_REF={ecoci_ref}")

    result = trigger_ecoci_pipeline(
        base_url=base_url,
        project_id=ecoci_host_project,
        trigger_token=trigger_token,
        ref=args.ref,
        ecoci_project_id=ecoci_project_id,
        ecoci_pipeline_id=ecoci_pipeline_id,
        ecoci_ref=ecoci_ref,
    )

    print(f"✅ Pipeline triggered: {result.get('web_url', result.get('id'))}")


if __name__ == "__main__":
    main()
