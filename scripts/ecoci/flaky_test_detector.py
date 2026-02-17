"""
Flaky test detector - find unreliable tests that pass/fail randomly.

Detects:
- Tests that failed then passed without code changes (retried)
- Tests with intermittent failures across pipeline history
- Time-dependent tests (timezone, date-based failures)
- Race conditions in parallel tests
- External dependency flakes (network, API, database)
"""

from __future__ import annotations
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


def detect_flaky_tests_from_logs(job_logs: str) -> Dict[str, Any]:
    """
    Detect flaky tests from job execution logs.
    
    Looks for:
    - Retry patterns (test failed, then passed on retry)
    - Timeout flakes
    - Order-dependent failures
    - Race condition indicators
    """
    results = {
        "flaky_tests": [],
        "flakiness_indicators": [],
        "retry_detected": False,
        "estimated_flakiness_rate": 0.0,
        "recommendations": []
    }
    
    # Detect retry patterns
    retry_patterns = [
        r"Retry\s+(\d+)/(\d+)",
        r"Retrying.*attempt\s+(\d+)",
        r"rspec.*--only-failures",
        r"pytest.*--lf",  # pytest last-failed
        r"Rerunning\s+failed\s+tests",
        r"flaky.*rerun",
    ]
    
    for pattern in retry_patterns:
        if re.search(pattern, job_logs, re.IGNORECASE):
            results["retry_detected"] = True
            results["flakiness_indicators"].append({
                "type": "retry_detected",
                "severity": "high",
                "message": "Tests were retried (indicates flakiness)",
                "impact": "Wastes CI minutes and masks real failures"
            })
            break
    
    # Detect timing-related flakes
    timing_patterns = [
        (r"(?i)timed?\s*out", "timeout", "Test timeout — may be resource-dependent"),
        (r"(?i)deadline\s*exceeded", "deadline", "Deadline exceeded — external dependency slow"),
        (r"(?i)connection\s*refused", "connection", "Connection refused — service not ready"),
        (r"(?i)race\s*condition|data\s*race", "race_condition", "Race condition detected"),
        (r"(?i)stale\s*element|element.*not\s*found", "ui_flake", "UI element not found — timing issue"),
        (r"(?i)sleep\s*\d+|wait_for|Thread\.sleep", "sleep_wait", "Test uses sleep() — timing-dependent"),
        (r"(?i)random|rand\(|Math\.random|uuid", "randomness", "Test uses randomness — non-deterministic"),
        (r"(?i)Time\.now|Date\.today|datetime\.now", "time_dependent", "Test depends on current time"),
        (r"(?i)port\s+already\s+in\s+use", "port_conflict", "Port conflict — parallel test interference"),
        (r"(?i)file.*locked|lock.*timeout", "file_lock", "File lock contention between tests"),
    ]
    
    for pattern, flake_type, message in timing_patterns:
        matches = re.findall(pattern, job_logs)
        if matches:
            results["flakiness_indicators"].append({
                "type": flake_type,
                "severity": "medium",
                "count": len(matches),
                "message": message,
                "impact": f"Found {len(matches)} occurrences"
            })
    
    # Detect specific test failures that look flaky
    # RSpec format
    rspec_failures = re.findall(r"(rspec\s+.*?):(\d+)\s+#\s+(.*?)(?:\n|$)", job_logs)
    for file_path, line, test_name in rspec_failures:
        results["flaky_tests"].append({
            "name": test_name.strip(),
            "file": f"{file_path}:{line}",
            "framework": "rspec"
        })
    
    # pytest format
    pytest_failures = re.findall(r"FAILED\s+([\w/]+\.py::[\w:]+)", job_logs)
    for test_id in pytest_failures:
        results["flaky_tests"].append({
            "name": test_id,
            "file": test_id.split("::")[0],
            "framework": "pytest"
        })
    
    # Jest format
    jest_failures = re.findall(r"✕\s+(.+?)(?:\s+\((\d+)\s*ms\))?$", job_logs, re.MULTILINE)
    for test_name, duration in jest_failures:
        results["flaky_tests"].append({
            "name": test_name.strip(),
            "file": "unknown",
            "framework": "jest"
        })
    
    # Estimate flakiness rate
    total_indicators = len(results["flakiness_indicators"])
    if total_indicators > 5:
        results["estimated_flakiness_rate"] = 15.0
    elif total_indicators > 2:
        results["estimated_flakiness_rate"] = 8.0
    elif total_indicators > 0:
        results["estimated_flakiness_rate"] = 3.0
    
    # Generate recommendations
    if results["retry_detected"]:
        results["recommendations"].append({
            "priority": 1,
            "action": "Quarantine flaky tests into separate job",
            "impact": "Prevent flaky tests from blocking deployments",
            "effort": "low",
            "example": "Create a 'flaky_tests' job with allow_failure: true"
        })
    
    if any(i["type"] == "sleep_wait" for i in results["flakiness_indicators"]):
        results["recommendations"].append({
            "priority": 2,
            "action": "Replace sleep() with explicit waits/polling",
            "impact": "Eliminate 80% of timing-related flakes",
            "effort": "medium",
            "example": "Use WebDriverWait or retry_on_failure instead of sleep(5)"
        })
    
    if any(i["type"] == "time_dependent" for i in results["flakiness_indicators"]):
        results["recommendations"].append({
            "priority": 3,
            "action": "Freeze time in tests using timecop/freezegun",
            "impact": "Eliminate date/time-dependent failures",
            "effort": "low",
            "example": "Python: @freeze_time('2024-01-01') / Ruby: Timecop.freeze"
        })
    
    if any(i["type"] == "connection" for i in results["flakiness_indicators"]):
        results["recommendations"].append({
            "priority": 4,
            "action": "Add service health checks before running tests",
            "impact": "Prevent 'connection refused' errors",
            "effort": "low",
            "example": "Add wait-for-it.sh or dockerize -wait tcp://db:5432"
        })
    
    # Cost of flaky tests
    if results["estimated_flakiness_rate"] > 0:
        results["cost_analysis"] = {
            "retries_per_week": int(results["estimated_flakiness_rate"] * 0.5),
            "wasted_minutes_per_week": int(results["estimated_flakiness_rate"] * 5),
            "developer_frustration": "HIGH" if results["estimated_flakiness_rate"] > 10 else "MEDIUM",
            "false_red_deployments_per_month": int(results["estimated_flakiness_rate"] * 2),
            "trust_in_ci": "LOW" if results["estimated_flakiness_rate"] > 10 else "MEDIUM"
        }
    
    return results


def calculate_flaky_test_cost(
    flakiness_rate: float,
    pipeline_duration_min: float,
    pipelines_per_week: int,
    team_size: int,
    developer_hourly_rate: float = 60
) -> Dict[str, Any]:
    """Calculate the business cost of flaky tests."""
    
    # Time wasted on false failures
    false_failures_per_week = pipelines_per_week * (flakiness_rate / 100)
    
    # Each false failure wastes ~15 min investigating + retry time
    investigation_time_min = 15
    retry_time_min = pipeline_duration_min
    time_wasted_per_false_failure = investigation_time_min + retry_time_min
    
    weekly_wasted_min = false_failures_per_week * time_wasted_per_false_failure
    weekly_wasted_hours = weekly_wasted_min / 60
    
    # Context switching cost (interruption costs ~23 min per incident)
    context_switch_cost_min = false_failures_per_week * 23
    
    # Total cost
    total_weekly_hours = (weekly_wasted_min + context_switch_cost_min) / 60
    weekly_cost = total_weekly_hours * developer_hourly_rate
    annual_cost = weekly_cost * 52
    
    # Deployment delays
    blocked_deploys_per_month = false_failures_per_week * 4.33 * 0.3  # 30% block deploys
    
    return {
        "false_failures_per_week": round(false_failures_per_week, 1),
        "time_wasted_hours_per_week": round(total_weekly_hours, 1),
        "cost_per_week": round(weekly_cost, 2),
        "cost_per_year": round(annual_cost, 2),
        "blocked_deploys_per_month": round(blocked_deploys_per_month, 1),
        "developer_morale_impact": "Severe" if flakiness_rate > 10 else "Moderate" if flakiness_rate > 5 else "Minor",
        "recommendation": (
            "URGENT: Quarantine flaky tests immediately" if flakiness_rate > 10
            else "Create flaky test tracking and fix sprint" if flakiness_rate > 5
            else "Monitor and fix incrementally"
        )
    }
