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
