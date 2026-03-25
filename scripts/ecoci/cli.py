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

    # ─── optimize (GitHub-first universal flow) ───
    optimize_parser = subparsers.add_parser("optimize", help="Generate optimized workflow YAML")
    optimize_parser.add_argument("--provider", default="github", choices=["github"], help="CI provider")
    optimize_parser.add_argument("--repo", help="Repository as owner/repo (auto-detected if omitted)")
    optimize_parser.add_argument("--ref", default="main", help="Git ref (branch/tag)")
    optimize_parser.add_argument("--workflow", help="Workflow path to optimize")
    optimize_parser.add_argument("--out", help="Output file path for optimized YAML")
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
    payload = {
        "provider": "github",
        "repo": repo,
        "ref": args.ref,
        "workflow": workflow_path,
        "analysis": analysis,
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
    print(f"\n  Issues: {len(issues)}")
    for i in issues:
        print(f"    - {i}")
    print(f"\n  Recommendations: {len(recs)}")
    for r in recs:
        print(f"    - {r}")

    if metrics:
        print("\n📊 Real run metrics")
        print(f"  Total duration: {metrics['total_duration_seconds']}s")
        print(f"  Estimated cost: ${metrics['total_cost_usd']}")
        print(f"  Estimated energy: {metrics['total_kwh']} kWh")
        print(f"  Estimated CO2: {metrics['total_co2_kg']} kg")

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
        lines.extend(["", "## Recommendations"])
        for r in recs:
            lines.append(f"- {r}")
        if metrics:
            lines.extend([
                "",
                "## Metrics",
                f"- Total duration: {metrics['total_duration_seconds']}s",
                f"- Estimated cost: ${metrics['total_cost_usd']}",
                f"- Energy: {metrics['total_kwh']} kWh",
                f"- CO2: {metrics['total_co2_kg']} kg",
            ])
        Path(args.markdown).write_text("\n".join(lines))
        print(f"\n📝 Wrote markdown report to {args.markdown}")


def cmd_optimize(args):
    from ecoci.providers.github import GitHubProvider

    provider = GitHubProvider()
    repo = _resolve_repo(args.repo)
    workflow_path = _pick_workflow(provider, repo, args.ref, args.workflow)
    workflow_yaml = provider.get_workflow_content(repo, workflow_path, args.ref)

    optimized, changes = provider.optimize_workflow(workflow_yaml)
    payload = {
        "provider": "github",
        "repo": repo,
        "ref": args.ref,
        "workflow": workflow_path,
        "changes": changes,
    }

    if args.out:
        Path(args.out).write_text(optimized)
        payload["output_file"] = args.out

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

    if args.out:
        print(f"\n✅ Wrote optimized workflow to {args.out}")
    else:
        print("\n--- Optimized workflow preview ---\n")
        print(optimized)


def cmd_pr(args):
    if not getattr(args, "pr_command", None):
        # Backward compatibility: treat `ecoci pr ...` as `ecoci pr create ...`
        setattr(args, "pr_command", "create")

    if args.pr_command != "create":
        raise RuntimeError(f"Unsupported pr command: {args.pr_command}")

    from ecoci.providers.github import GitHubProvider

    provider = GitHubProvider()
    repo = _resolve_repo(args.repo)

    base_branch = args.base or provider.get_default_branch(repo)
    workflow_path = _pick_workflow(provider, repo, base_branch, args.workflow)
    workflow_yaml = provider.get_workflow_content(repo, workflow_path, base_branch)
    optimized, changes = provider.optimize_workflow(workflow_yaml)

    body_lines = [
        "## EcoCI Optimization Summary",
        "",
        "Automated GitHub Actions workflow improvements:",
        "",
    ]
    for c in changes:
        body_lines.append(f"- {c}")
    if not changes:
        body_lines.append("- No structural changes required")

    body_lines.extend([
        "",
        "Generated by EcoCI CLI.",
    ])
    pr_body = "\n".join(body_lines)

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

    metrics = None
    if args.run_id:
        jobs = provider.get_run_jobs(repo, args.run_id)
        metrics = provider.compute_run_metrics(jobs)
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
    print("EcoCI v1.0.0")
    print("The most comprehensive AI CI/CD optimizer")
    print("Works with: GitLab CI, GitHub Actions, Jenkins, CircleCI, and more")
    print("")
    print("GitHub:  https://github.com/divyanshAgarwal123/ecoci")
    print("GitLab:  https://gitlab.com/gitlab-ai-hackathon/participants/34560917")


if __name__ == "__main__":
    # Allow running from scripts/ directory
    scripts_dir = Path(__file__).parent.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
