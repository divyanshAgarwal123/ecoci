#!/usr/bin/env python3
"""
EcoCI CLI — Run all analysis modules from the command line.

Works anywhere: GitHub, GitLab, Bitbucket, local repos — no vendor lock-in.

Usage:
    ecoci analyze .                      # Full analysis of current project
    ecoci security .gitlab-ci.yml        # Security scan a CI config
    ecoci cost --duration 300 --jobs 5   # Calculate pipeline cost
    ecoci dora --deploys 20 --lead 48    # Calculate DORA metrics
    ecoci predict --files "a.py,b.py"    # Predict pipeline failure risk
    ecoci flaky logs.txt                 # Detect flaky tests from logs
    ecoci tests --changed "src/user.py"  # Smart test selection
    ecoci fix                            # Generate auto-fixes
    ecoci report                         # Full report (all modules)
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from importlib.metadata import version as _pkg_version
except Exception:  # pragma: no cover
    _pkg_version = None


def main():
    parser = argparse.ArgumentParser(
        prog="ecoci",
        description="EcoCI — The most comprehensive CI/CD optimizer. "
                    "Works with any CI system: GitHub Actions, GitLab CI, Jenkins, CircleCI, etc.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ecoci security .gitlab-ci.yml          Scan CI config for secrets & vulnerabilities
  ecoci security .github/workflows/ci.yml  Works with GitHub Actions too!
  ecoci dora --deploys 20 --lead 48      Calculate your DORA metrics
  ecoci cost --duration 600 --jobs 8     Calculate pipeline costs
  ecoci predict --files src/main.py,src/db.py  Predict failure probability
  ecoci flaky test-output.log            Detect flaky tests
  ecoci tests --changed src/user.py      Smart test selection
  ecoci report                           Full analysis report

GitHub:  https://github.com/divyanshAgarwal123/ecoci
GitLab:  https://gitlab.com/gitlab-ai-hackathon/participants/34560917
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # ─── security ───
    sec_parser = subparsers.add_parser("security", help="Scan CI config for secrets & dangerous patterns")
    sec_parser.add_argument("file", nargs="?", help="CI config file to scan (any CI system)")
    sec_parser.add_argument("--logs", help="Job log file to scan for leaked secrets")

    # ─── analyze (GitHub-first universal flow) ───
    analyze_parser = subparsers.add_parser("analyze", help="Analyze CI workflow on a provider (default: GitHub)")
    analyze_parser.add_argument("--provider", default="github", choices=["github"], help="CI provider")
    analyze_parser.add_argument("--repo", help="Repository as owner/repo (auto-detected from git remote if omitted)")
    analyze_parser.add_argument("--ref", default="main", help="Git ref (branch/tag) for reading workflow files")
    analyze_parser.add_argument("--workflow", help="Workflow path (e.g., .github/workflows/test.yml). Defaults to first found.")
    analyze_parser.add_argument("--run-id", type=int, help="GitHub Actions run ID for real job duration data")
    analyze_parser.add_argument("--json", action="store_true", help="Output JSON")
    analyze_parser.add_argument("--markdown", help="Write markdown report to file")

    # ─── doctor (setup diagnostics) ───
    doctor_parser = subparsers.add_parser("doctor", help="Validate local setup and provider connectivity")
    doctor_parser.add_argument("--provider", default="github", choices=["github"], help="CI provider")
    doctor_parser.add_argument("--repo", help="Repository as owner/repo (auto-detected if omitted)")
    doctor_parser.add_argument("--ref", default="main", help="Ref used to check workflow discovery")
    doctor_parser.add_argument("--json", action="store_true", help="Output JSON")

    # ─── optimize (GitHub-first universal flow) ───
    optimize_parser = subparsers.add_parser("optimize", help="Generate optimized workflow YAML")
    optimize_parser.add_argument("--provider", default="github", choices=["github"], help="CI provider")
    optimize_parser.add_argument("--repo", help="Repository as owner/repo (auto-detected if omitted)")
    optimize_parser.add_argument("--ref", default="main", help="Git ref (branch/tag)")
    optimize_parser.add_argument("--workflow", help="Workflow path to optimize")
    optimize_parser.add_argument("--out", help="Output file path for optimized YAML")
    optimize_parser.add_argument("--show-diff", action="store_true", help="Show unified diff preview")
    optimize_parser.add_argument("--deterministic-patch", action="store_true", help="Generate deterministic unified patch output for CI bots")
    optimize_parser.add_argument("--patch-file", help="Write unified diff patch to file")
    optimize_parser.add_argument("--json", action="store_true", help="Output JSON")

    # ─── pr (GitHub-first universal flow) ───
    pr_parser = subparsers.add_parser("pr", help="Pull request operations")
    pr_subparsers = pr_parser.add_subparsers(dest="pr_command", help="PR commands")

    pr_create_parser = pr_subparsers.add_parser("create", help="Create optimization pull request (GitHub)")
    pr_create_parser.add_argument("--provider", default="github", choices=["github"], help="CI provider")
    pr_create_parser.add_argument("--repo", help="Repository as owner/repo (auto-detected if omitted)")
    pr_create_parser.add_argument("--base", help="Base branch (defaults to repository default branch)")
    pr_create_parser.add_argument("--branch", default="ecoci/optimize-workflow", help="PR source branch")
    pr_create_parser.add_argument("--workflow", help="Workflow path to optimize and commit")
    pr_create_parser.add_argument("--title", default="EcoCI: Optimize GitHub Actions workflow", help="Pull request title")
    pr_create_parser.add_argument("--commit-message", default="chore(ci): optimize workflow with EcoCI", help="Commit message")
    pr_create_parser.add_argument("--run-id", type=int, help="Actions run ID used to generate dashboard metrics")
    pr_create_parser.add_argument("--dry-run", action="store_true", help="Print planned PR payload without creating commit/PR")
    pr_create_parser.add_argument("--json", action="store_true", help="Output JSON")
    
    # ─── cost ───
    cost_parser = subparsers.add_parser("cost", help="Calculate pipeline cost")
    cost_parser.add_argument("--duration", type=int, default=300, help="Pipeline duration in seconds")
    cost_parser.add_argument("--jobs", type=int, default=5, help="Number of jobs")
    cost_parser.add_argument("--runs-per-month", type=int, default=200, help="Pipeline runs per month")
    cost_parser.add_argument("--runner-cost", type=float, default=0.01, help="Cost per minute ($)")
    
    # ─── dora ───
    dora_parser = subparsers.add_parser("dora", help="Calculate DORA metrics")
    dora_parser.add_argument("--deploys", type=float, default=12, help="Deployments per month")
    dora_parser.add_argument("--lead", type=float, default=48, help="Lead time in hours")
    dora_parser.add_argument("--cfr", type=float, default=0.10, help="Change failure rate (0-1)")
    dora_parser.add_argument("--mttr", type=float, default=4, help="MTTR in hours")
    
    # ─── predict ───
    pred_parser = subparsers.add_parser("predict", help="Predict pipeline failure probability")
    pred_parser.add_argument("--files", help="Comma-separated list of changed files")
    pred_parser.add_argument("--lines", type=int, default=100, help="Lines changed")
    pred_parser.add_argument("--message", default="", help="Commit message")
    
    # ─── flaky ───
    flaky_parser = subparsers.add_parser("flaky", help="Detect flaky tests from log output")
    flaky_parser.add_argument("logfile", nargs="?", help="Log file to analyze")
    
    # ─── tests ───
    test_parser = subparsers.add_parser("tests", help="Smart test selection based on changed files")
    test_parser.add_argument("--changed", help="Comma-separated list of changed files")
    test_parser.add_argument("--lang", default="auto", help="Language: ruby, python, javascript, auto")
    
    # ─── fix ───
    fix_parser = subparsers.add_parser("fix", help="Generate auto-fixes with confidence scores")
    fix_parser.add_argument("--issues", help="JSON file with detected issues")
    
    # ─── report ───
    report_parser = subparsers.add_parser("report", help="Full analysis report")
    report_parser.add_argument("--ci-file", help="CI config file to analyze")
    report_parser.add_argument("--log-file", help="Job log file to analyze")
    report_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # ─── version ───
    subparsers.add_parser("version", help="Show version")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\n💡 Try: ecoci security <ci-config-file>")
        sys.exit(0)
    
    # Route to handlers
    handlers = {
        "analyze": cmd_analyze,
        "doctor": cmd_doctor,
        "optimize": cmd_optimize,
        "pr": cmd_pr,
        "security": cmd_security,
        "cost": cmd_cost,
        "dora": cmd_dora,
        "predict": cmd_predict,
        "flaky": cmd_flaky,
        "tests": cmd_tests,
        "fix": cmd_fix,
        "report": cmd_report,
        "version": cmd_version,
    }
    
    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


def cmd_security(args):
    from ecoci.security_scanner import scan_for_secrets, scan_ci_config, generate_security_report
    
    if args.file and os.path.exists(args.file):
        content = Path(args.file).read_text()
        print(f"🔒 Scanning: {args.file}\n")
        report = generate_security_report(content)
        print(report)
    elif args.logs and os.path.exists(args.logs):
        from ecoci.security_scanner import scan_job_logs_for_secrets
        logs = Path(args.logs).read_text()
        secrets = scan_job_logs_for_secrets(logs)
        if secrets:
            print(f"⛔ Found {len(secrets)} potential secrets in logs!")
            for s in secrets:
                print(f"  - {s['type']}: {s.get('masked_value', 'REDACTED')}")
        else:
            print("✅ No secrets found in logs")
    else:
        print("❌ Please provide a CI config file: ecoci security .gitlab-ci.yml")
        print("   Also works with: .github/workflows/ci.yml, Jenkinsfile, etc.")


def _resolve_repo(repo_arg: Optional[str]) -> str:
    from ecoci.providers.github import GitHubProvider

    repo = repo_arg or GitHubProvider.infer_repo_from_git()
    if not repo:
        raise RuntimeError("Repository not provided and could not be inferred. Use --repo owner/repo")
    return repo


def _pick_workflow(provider, repo: str, ref: str, workflow: Optional[str]) -> str:
    if workflow:
        return workflow
    workflows = provider.list_workflow_files(repo, ref)
    if not workflows:
        raise RuntimeError(f"No GitHub workflow files found in {repo} at ref {ref}")
    return workflows[0]


def cmd_doctor(args):
    from ecoci.providers.github import GitHubProvider

    provider = GitHubProvider()
    repo = None
    errors = []
    warnings = []
    checks = {
        "provider": "github",
        "token_present": bool(provider.token),
        "repo_detected": False,
        "repo": None,
        "workflow_count": 0,
        "workflows": [],
    }

    try:
        repo = _resolve_repo(args.repo)
        checks["repo_detected"] = True
        checks["repo"] = repo
    except Exception as e:
        errors.append(str(e))

    if not provider.token:
        warnings.append("GITHUB_TOKEN is not set. Read-only APIs may be rate-limited and PR creation will fail.")

    if repo:
        try:
            workflows = provider.list_workflow_files(repo, args.ref)
            checks["workflow_count"] = len(workflows)
            checks["workflows"] = workflows
            if not workflows:
                warnings.append(f"No workflows found at ref '{args.ref}' in {repo}")
        except Exception as e:
            errors.append(f"GitHub API check failed: {e}")

    result = {
        "ok": len(errors) == 0,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("🩺 EcoCI Doctor\n")
    print(f"  Provider:        {checks['provider']}")
    print(f"  Token present:   {'yes' if checks['token_present'] else 'no'}")
    print(f"  Repo detected:   {'yes' if checks['repo_detected'] else 'no'}")
    if checks["repo"]:
        print(f"  Repo:            {checks['repo']}")
    print(f"  Workflows found: {checks['workflow_count']}")

    if warnings:
        print("\n⚠️ Warnings")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\n❌ Errors")
        for e in errors:
            print(f"  - {e}")
        print("\nDoctor result: FAILED")
    else:
        print("\nDoctor result: OK")


def cmd_analyze(args):
    from ecoci.providers.github import GitHubProvider

    provider = GitHubProvider()
    repo = _resolve_repo(args.repo)
    workflow_path = _pick_workflow(provider, repo, args.ref, args.workflow)
    workflow_yaml = provider.get_workflow_content(repo, workflow_path, args.ref)

    run_jobs = None
    if args.run_id:
        run_jobs = provider.get_run_jobs(repo, args.run_id)

    analysis = provider.analyze_workflow(workflow_yaml, run_jobs=run_jobs)
    metrics = provider.compute_run_metrics(run_jobs or []) if run_jobs else None
    optimization_preview = provider.optimize_workflow_with_metadata(workflow_yaml, workflow_path=workflow_path)
    kpi_impact = provider.estimate_kpi_impact(optimization_preview.get("changes", []), metrics)
    payload = {
        "provider": "github",
        "repo": repo,
        "ref": args.ref,
        "workflow": workflow_path,
        "analysis": analysis,
        "kpi_impact": kpi_impact,
    }
    if metrics:
        payload["metrics"] = metrics

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print("🔍 EcoCI Workflow Analysis\n")
    print(f"  Repo:       {repo}")
    print(f"  Workflow:   {workflow_path}")
    print(f"  Job count:  {analysis.get('job_count', 0)}")
    if analysis.get("observed_total_duration_seconds"):
        print(f"  Observed duration: {analysis['observed_total_duration_seconds']}s")

    issues = analysis.get("issues", [])
    recs = analysis.get("recommendations", [])
    findings = analysis.get("findings", [])
    ranked_recs = analysis.get("prioritized_recommendations", [])
    quality_gate = analysis.get("quality_gate", {})
    print(f"\n  Issues: {len(issues)}")
    for i in issues:
        print(f"    - {i}")
    print(f"\n  Recommendations: {len(recs)}")
    for r in recs:
        print(f"    - {r}")

    if findings:
        print(f"\n  Findings (confidence-scored): {len(findings)}")
        for f in findings:
            conf_pct = round(float(f.get("confidence", 0.0)) * 100)
            print(f"    - [{f.get('severity', 'info')}] {f.get('message')} (confidence: {conf_pct}%)")

    if ranked_recs:
        print("\n  Priority fixes")
        for rec in ranked_recs[:5]:
            conf_pct = round(float(rec.get("confidence", 0.0)) * 100)
            print(
                f"    - [{rec.get('severity', 'low')}] {rec.get('fix')} "
                f"(confidence: {conf_pct}%, score: {rec.get('priority_score', 0)})"
            )

    if quality_gate:
        print(
            f"\n  Quality gate: {quality_gate.get('status', 'unknown').upper()} "
            f"(critical={quality_gate.get('critical_count', 0)}, high={quality_gate.get('high_count', 0)})"
        )

    if metrics:
        print("\n📊 Real run metrics")
        print(f"  Total duration: {metrics['total_duration_seconds']}s")
        print(f"  Estimated cost: ${metrics['total_cost_usd']}")
        print(f"  Estimated energy: {metrics['total_kwh']} kWh")
        print(f"  Estimated CO2: {metrics['total_co2_kg']} kg")

    if kpi_impact:
        imp = kpi_impact.get("estimated_improvements", {})
        print("\n📈 Projected KPI impact (heuristic)")
        print(f"  Duration improvement: {imp.get('duration_percent', 0)}%")
        print(f"  Cost improvement:     {imp.get('cost_percent', 0)}%")
        print(f"  CO2 improvement:      {imp.get('co2_percent', 0)}%")

    if args.markdown:
        lines = [
            "# EcoCI Analysis Report",
            "",
            f"- Provider: github",
            f"- Repo: {repo}",
            f"- Workflow: {workflow_path}",
            "",
            "## Issues",
        ]
        for i in issues:
            lines.append(f"- {i}")
        if findings:
            lines.extend(["", "## Findings (Confidence-Scored)"])
            for f in findings:
                conf_pct = round(float(f.get("confidence", 0.0)) * 100)
                lines.append(
                    f"- [{f.get('severity', 'info')}] {f.get('message')} "
                    f"→ {f.get('fix', 'N/A')} (confidence: {conf_pct}%)"
                )
        if ranked_recs:
            lines.extend(["", "## Priority Fixes"])
            for rec in ranked_recs[:8]:
                conf_pct = round(float(rec.get("confidence", 0.0)) * 100)
                lines.append(
                    f"- [{rec.get('severity', 'low')}] {rec.get('fix')} "
                    f"(confidence: {conf_pct}%, score: {rec.get('priority_score', 0)})"
                )
        lines.extend(["", "## Recommendations"])
        for r in recs:
            lines.append(f"- {r}")
        if quality_gate:
            lines.extend([
                "",
                "## Quality Gate",
                f"- Status: {quality_gate.get('status', 'unknown')}",
                f"- Critical findings: {quality_gate.get('critical_count', 0)}",
                f"- High findings: {quality_gate.get('high_count', 0)}",
            ])
        if metrics:
            lines.extend([
                "",
                "## Metrics",
                f"- Total duration: {metrics['total_duration_seconds']}s",
                f"- Estimated cost: ${metrics['total_cost_usd']}",
                f"- Energy: {metrics['total_kwh']} kWh",
                f"- CO2: {metrics['total_co2_kg']} kg",
            ])
        if kpi_impact:
            imp = kpi_impact.get("estimated_improvements", {})
            lines.extend([
                "",
                "## Before/After KPI Projection",
                f"- Estimated duration improvement: {imp.get('duration_percent', 0)}%",
                f"- Estimated cost improvement: {imp.get('cost_percent', 0)}%",
                f"- Estimated CO2 improvement: {imp.get('co2_percent', 0)}%",
            ])
            baseline = kpi_impact.get("baseline")
            projected = kpi_impact.get("projected")
            if baseline and projected:
                lines.extend([
                    "",
                    "| KPI | Before | After (Projected) |",
                    "| --- | ---: | ---: |",
                    f"| Duration (s) | {baseline.get('duration_seconds', 0)} | {projected.get('duration_seconds', 0)} |",
                    f"| Cost (USD) | {baseline.get('cost_usd', 0)} | {projected.get('cost_usd', 0)} |",
                    f"| CO2 (kg) | {baseline.get('co2_kg', 0)} | {projected.get('co2_kg', 0)} |",
                ])
        Path(args.markdown).write_text("\n".join(lines))
        print(f"\n📝 Wrote markdown report to {args.markdown}")


def cmd_optimize(args):
    from ecoci.providers.github import GitHubProvider

    provider = GitHubProvider()
    repo = _resolve_repo(args.repo)
    workflow_path = _pick_workflow(provider, repo, args.ref, args.workflow)
    workflow_yaml = provider.get_workflow_content(repo, workflow_path, args.ref)

    if hasattr(provider, "optimize_workflow_with_metadata"):
        optimization = provider.optimize_workflow_with_metadata(workflow_yaml, workflow_path=workflow_path)
        optimized = optimization.get("optimized_workflow", workflow_yaml)
        changes = optimization.get("changes", [])
        fixes = optimization.get("fixes", [])
        diff_text = optimization.get("diff", "")
    else:
        optimized, changes = provider.optimize_workflow(workflow_yaml)
        fixes = []
        diff_text = ""

    payload = {
        "provider": "github",
        "repo": repo,
        "ref": args.ref,
        "workflow": workflow_path,
        "changes": changes,
    }
    if fixes:
        payload["fixes"] = fixes
    if args.show_diff and diff_text:
        payload["diff"] = diff_text

    if args.out:
        Path(args.out).write_text(optimized)
        payload["output_file"] = args.out

    if args.patch_file and diff_text:
        Path(args.patch_file).write_text(diff_text)
        payload["patch_file"] = args.patch_file

    if args.deterministic_patch and diff_text:
        payload["deterministic_patch"] = diff_text

    if args.json:
        payload["optimized_workflow"] = optimized
        print(json.dumps(payload, indent=2))
        return

    print("⚡ EcoCI Workflow Optimization\n")
    print(f"  Repo:       {repo}")
    print(f"  Workflow:   {workflow_path}")
    print(f"  Changes:    {len(changes)}")
    for c in changes:
        print(f"    - {c}")

    if fixes:
        print("\n  Fix confidence")
        for f in fixes:
            conf_pct = round(float(f.get("confidence", 0.0)) * 100)
            print(f"    - {f.get('title')} [{conf_pct}% | risk: {f.get('risk', 'unknown')}]")

    if args.out:
        print(f"\n✅ Wrote optimized workflow to {args.out}")
    if args.patch_file and diff_text:
        print(f"✅ Wrote unified patch to {args.patch_file}")
    if not args.out:
        print("\n--- Optimized workflow preview ---\n")
        print(optimized)

    if (args.show_diff or args.deterministic_patch) and diff_text:
        print("\n--- Unified diff preview ---\n")
        print(diff_text)


def cmd_pr(args):
    if not getattr(args, "pr_command", None):
        # Backward compatibility: treat `ecoci pr ...` as `ecoci pr create ...`
        setattr(args, "pr_command", "create")

    if args.pr_command != "create":
        raise RuntimeError(f"Unsupported pr command: {args.pr_command}")

    from ecoci.providers.github import GitHubProvider

    provider = GitHubProvider()
    repo = _resolve_repo(args.repo)

    if not provider.token and not args.dry_run:
        raise RuntimeError("GITHUB_TOKEN is required for `ecoci pr create`. Set it and retry.")

    base_branch = args.base or provider.get_default_branch(repo)
    workflow_path = _pick_workflow(provider, repo, base_branch, args.workflow)
    workflow_yaml = provider.get_workflow_content(repo, workflow_path, base_branch)
    if hasattr(provider, "optimize_workflow_with_metadata"):
        optimization = provider.optimize_workflow_with_metadata(workflow_yaml, workflow_path=workflow_path)
        optimized = optimization.get("optimized_workflow", workflow_yaml)
        changes = optimization.get("changes", [])
        fixes = optimization.get("fixes", [])
        diff_text = optimization.get("diff", "")
    else:
        optimized, changes = provider.optimize_workflow(workflow_yaml)
        fixes = []
        diff_text = ""

    metrics = None
    if args.run_id:
        jobs = provider.get_run_jobs(repo, args.run_id)
        metrics = provider.compute_run_metrics(jobs)

    kpi_impact = provider.estimate_kpi_impact(changes, metrics)

    body_lines = [
        "## EcoCI Optimization Summary",
        "",
        "### Automated workflow improvements",
        "",
    ]
    if fixes:
        for fx in fixes:
            conf_pct = round(float(fx.get("confidence", 0.0)) * 100)
            body_lines.append(
                f"- {fx.get('title')} (confidence: {conf_pct}%, risk: {fx.get('risk', 'unknown')})"
            )
    else:
        for c in changes:
            body_lines.append(f"- {c}")
        if not changes:
            body_lines.append("- No structural changes required")

    body_lines.extend([
        "",
        "### Expected impact",
        f"- Estimated duration improvement: {kpi_impact.get('estimated_improvements', {}).get('duration_percent', 0)}%",
        f"- Estimated cost improvement: {kpi_impact.get('estimated_improvements', {}).get('cost_percent', 0)}%",
        f"- Estimated CO2 improvement: {kpi_impact.get('estimated_improvements', {}).get('co2_percent', 0)}%",
        "",
        "### Rollback plan",
        f"- Revert {workflow_path} to the previous commit if any regression is observed",
        "- Re-run CI to verify baseline behavior is restored",
    ])

    baseline = kpi_impact.get("baseline")
    projected = kpi_impact.get("projected")
    if baseline and projected:
        body_lines.extend([
            "",
            "### Before/After KPI Projection",
            "| KPI | Before | After (Projected) |",
            "| --- | ---: | ---: |",
            f"| Duration (s) | {baseline.get('duration_seconds', 0)} | {projected.get('duration_seconds', 0)} |",
            f"| Cost (USD) | {baseline.get('cost_usd', 0)} | {projected.get('cost_usd', 0)} |",
            f"| CO2 (kg) | {baseline.get('co2_kg', 0)} | {projected.get('co2_kg', 0)} |",
        ])

    if diff_text:
        body_lines.extend([
            "",
            "### Diff preview",
            "<details><summary>Show workflow diff</summary>",
            "",
            "```diff",
            diff_text[:12000],
            "```",
            "",
            "</details>",
        ])

    body_lines.extend([
        "",
        "Generated by EcoCI CLI.",
    ])
    pr_body = "\n".join(body_lines)

    if args.dry_run:
        payload = {
            "provider": "github",
            "repo": repo,
            "base": base_branch,
            "branch": args.branch,
            "workflow": workflow_path,
            "title": args.title,
            "commit_message": args.commit_message,
            "changes": changes,
            "body": pr_body,
            "kpi_impact": kpi_impact,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("🧪 Dry run (no commit/PR created)\n")
            print(f"  Repo:      {repo}")
            print(f"  Workflow:  {workflow_path}")
            print(f"  Base:      {base_branch}")
            print(f"  Branch:    {args.branch}")
            print(f"  Changes:   {len(changes)}")
        return

    result = provider.create_optimization_pr(
        repo=repo,
        workflow_path=workflow_path,
        optimized_content=optimized,
        base_branch=base_branch,
        branch=args.branch,
        title=args.title,
        body=pr_body,
        commit_message=args.commit_message,
    )

    if args.run_id and metrics:
        pr_number = result.get("pull_request", {}).get("number")
        if pr_number:
            dashboard = provider.build_dashboard_markdown(repo, workflow_path, args.run_id, metrics)
            comment = provider.create_pr_comment(repo, int(pr_number), dashboard)
            result["dashboard_comment"] = comment

    if metrics:
        result["metrics"] = metrics

    if args.json:
        print(json.dumps(result, indent=2))
        return

    pr = result.get("pull_request", {})
    print("✅ Pull request created")
    print(f"  Repo:      {repo}")
    print(f"  Workflow:  {workflow_path}")
    print(f"  Base:      {base_branch}")
    print(f"  Branch:    {args.branch}")
    print(f"  URL:       {pr.get('html_url', 'N/A')}")


def cmd_cost(args):
    from ecoci.cost_analyzer import calculate_pipeline_cost, calculate_monthly_spending
    
    jobs = [{"name": f"job_{i+1}", "duration": args.duration / args.jobs}
            for i in range(args.jobs)]
    
    cost = calculate_pipeline_cost(jobs)
    monthly = calculate_monthly_spending(cost["total_cost"], args.runs_per_month // 30)
    
    print("💰 Pipeline Cost Analysis\n")
    print(f"  Duration:       {args.duration}s ({args.duration/60:.1f} min)")
    print(f"  Jobs:           {args.jobs}")
    print(f"  Cost per run:   ${cost['total_cost']:.3f}")
    print(f"  Monthly cost:   ${monthly['monthly_cost']:.2f}")
    print(f"  Annual cost:    ${monthly['annual_cost']:.2f}")
    print(f"  Runs/month:     {args.runs_per_month}")


def cmd_dora(args):
    from ecoci.dora_metrics import calculate_dora_metrics, generate_dora_report
    
    metrics = calculate_dora_metrics(
        deploys_per_month=args.deploys,
        lead_time_hours=args.lead,
        change_failure_rate=args.cfr,
        mttr_hours=args.mttr
    )
    
    report = generate_dora_report(metrics)
    print(report)


def cmd_predict(args):
    from ecoci.failure_predictor import predict_pipeline_failure, generate_failure_prediction_report
    
    files = args.files.split(",") if args.files else ["unknown_file.py"]
    
    prediction = predict_pipeline_failure(
        changed_files=files,
        lines_changed=args.lines,
        commit_message=args.message
    )
    
    report = generate_failure_prediction_report(prediction)
    print(report)


def cmd_flaky(args):
    from ecoci.flaky_test_detector import detect_flaky_tests_from_logs, calculate_flaky_test_cost
    
    if args.logfile and os.path.exists(args.logfile):
        logs = Path(args.logfile).read_text()
    else:
        print("Reading from stdin (paste logs, then Ctrl+D)...")
        logs = sys.stdin.read()
    
    results = detect_flaky_tests_from_logs(logs)
    
    print("🎲 Flaky Test Detection\n")
    indicators = results.get("flakiness_indicators", [])
    print(f"  Flakiness indicators found: {len(indicators)}")
    for ind in indicators:
        print(f"    - {ind.get('type', 'unknown')}: {ind.get('match', '')[:60]}")
    
    rate = results.get("estimated_flakiness_rate", 0)
    if rate > 0:
        cost = calculate_flaky_test_cost(rate, 15, 50, 5)
        print(f"\n  Estimated flakiness rate: {rate:.1f}%")
        print(f"  Cost per year: ${cost.get('cost_per_year', 0):,.0f}")
        print(f"  Recommendation: {cost.get('recommendation', 'Monitor')}")


def cmd_tests(args):
    from ecoci.smart_test_selector import analyze_changed_files, generate_test_command
    
    if args.changed:
        files = args.changed.split(",")
    else:
        # Try to get from git
        import subprocess
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True, text=True, cwd="."
            )
            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        except Exception:
            files = []
    
    if not files:
        print("❌ No changed files. Use --changed or run from a git repo")
        return
    
    selection = analyze_changed_files(files, args.lang)
    cmd = generate_test_command(selection)
    
    print("🎯 Smart Test Selection\n")
    print(f"  Strategy:      {selection['strategy']}")
    print(f"  Files changed: {selection['files_analyzed']}")
    print(f"  Tests to run:  {len(selection['tests_to_run'])}")
    print(f"  Time savings:  {selection['estimated_time_savings_percent']}%")
    print(f"  Reason:        {selection['reason']}")
    if cmd:
        print(f"\n  Command:\n    {cmd}")


def cmd_fix(args):
    from ecoci.auto_fix_engine import generate_fixes_for_issues, generate_mr_description, FIX_TEMPLATES
    
    if args.issues and os.path.exists(args.issues):
        issues = json.loads(Path(args.issues).read_text())
    else:
        # Show available fix templates
        print("🔧 Auto-Fix Engine — Available Fix Templates\n")
        for key, fix in FIX_TEMPLATES.items():
            d = fix.to_dict()
            print(f"  {d['confidence_label'][:2]} {d['title']}")
            print(f"     Type: {key} | Confidence: {d['confidence']*100:.0f}%")
            print(f"     {d['explanation'][:80]}...\n")
        print(f"  Total templates: {len(FIX_TEMPLATES)}")
        print(f"\n  Usage: ecoci fix --issues issues.json")


def cmd_report(args):
    """Run all modules and generate a comprehensive report."""
    print("=" * 60)
    print("🌱 EcoCI — Comprehensive Analysis Report")
    print("=" * 60)
    
    # Security
    if args.ci_file and os.path.exists(args.ci_file):
        print(f"\n{'─' * 40}")
        print("🔒 Security Scan")
        print(f"{'─' * 40}")
        cmd_security(argparse.Namespace(file=args.ci_file, logs=None))
    
    # DORA (with defaults)
    print(f"\n{'─' * 40}")
    print("📊 DORA Metrics (using defaults)")
    print(f"{'─' * 40}")
    cmd_dora(argparse.Namespace(deploys=12, lead=48, cfr=0.10, mttr=4))
    
    # Auto-fix templates
    print(f"\n{'─' * 40}")
    print("🔧 Available Auto-Fixes")
    print(f"{'─' * 40}")
    cmd_fix(argparse.Namespace(issues=None))
    
    print(f"\n{'=' * 60}")
    print("Report complete! Run individual commands for detailed analysis.")
    print(f"{'=' * 60}")


def cmd_version(args):
    v = _resolve_version()
    print(f"EcoCI v{v}")
    print("The most comprehensive AI CI/CD optimizer")
    print("Works with: GitLab CI, GitHub Actions, Jenkins, CircleCI, and more")
    print("")
    print("GitHub:  https://github.com/divyanshAgarwal123/ecoci")
    print("GitLab:  https://gitlab.com/gitlab-ai-hackathon/participants/34560917")


def _resolve_version() -> str:
    # Preferred: installed package metadata
    if _pkg_version:
        try:
            return _pkg_version("ecoci")
        except Exception:
            pass

    # Fallback: pyproject.toml in repo root
    try:
        root = Path(__file__).resolve().parents[2]
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            for line in pyproject.read_text().splitlines():
                line = line.strip()
                if line.startswith("version") and "=" in line:
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass

    return "0.0.0"


if __name__ == "__main__":
    # Allow running from scripts/ directory
    scripts_dir = Path(__file__).parent.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
