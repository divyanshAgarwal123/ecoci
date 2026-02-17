"""
Code performance analyzer for EcoCI.

Analyzes application code and test logs to identify:
- Slow functions/methods
- N+1 query problems
- Inefficient algorithms
- Memory leaks
- CPU-intensive operations
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def analyze_test_performance(job_logs: str) -> Dict[str, Any]:
    """
    Analyze test execution logs to find slow tests and performance issues.
    
    Args:
        job_logs: Raw logs from test job execution
        
    Returns:
        Dictionary with performance analysis results
    """
    results = {
        "slow_tests": [],
        "performance_warnings": [],
        "recommendations": [],
        "total_test_time": 0,
        "slowest_test_time": 0,
    }
    
    # Pattern matching for common test frameworks
    patterns = {
        # RSpec (Ruby)
        "rspec": r"(.+?)\s+\((\d+\.\d+)s\)",
        # pytest (Python)
        "pytest": r"(.+?)\s+PASSED.*?\[(\d+\.\d+)s\]",
        # Jest (JavaScript)
        "jest": r"✓\s+(.+?)\s+\((\d+)\s*ms\)",
        # PHPUnit
        "phpunit": r"(.+?)\s+(\d+\.\d+)\s+seconds",
    }
    
    slow_tests = []
    total_time = 0
    
    for framework, pattern in patterns.items():
        matches = re.findall(pattern, job_logs, re.MULTILINE)
        for test_name, duration in matches:
            duration_sec = float(duration) if '.' in str(duration) else float(duration) / 1000
            total_time += duration_sec
            
            if duration_sec > 5.0:  # Tests taking >5 seconds are slow
                slow_tests.append({
                    "name": test_name.strip(),
                    "duration": duration_sec,
                    "framework": framework
                })
    
    # Sort by duration
    slow_tests.sort(key=lambda x: x["duration"], reverse=True)
    
    results["slow_tests"] = slow_tests[:10]  # Top 10 slowest
    results["total_test_time"] = round(total_time, 2)
    results["slowest_test_time"] = slow_tests[0]["duration"] if slow_tests else 0
    
    # Generate recommendations
    if slow_tests:
        results["recommendations"].append({
            "type": "slow_tests",
            "severity": "high",
            "message": f"Found {len(slow_tests)} tests taking >5 seconds",
            "impact": "High CPU usage, long pipeline times",
            "fix": "Optimize slow tests with mocking, test data factories, or parallelization"
        })
    
    # Check for common performance anti-patterns in logs
    analyze_common_antipatterns(job_logs, results)
    
    return results


def analyze_common_antipatterns(logs: str, results: Dict[str, Any]) -> None:
    """Detect common performance anti-patterns in logs."""
    
    # N+1 query detection
    if re.search(r"(SELECT.*FROM.*){10,}", logs, re.IGNORECASE):
        results["performance_warnings"].append({
            "type": "n+1_queries",
            "severity": "high",
            "message": "Possible N+1 query detected (multiple SELECT queries)",
            "impact": "Database overload, slow response times, high CPU",
            "fix": "Use eager loading (e.g., .includes() in Rails, .select_related() in Django)",
            "savings": "Can reduce query time by 90%+ and CPU usage by 50%"
        })
    
    # Missing database indices
    if re.search(r"Seq Scan|Sequential Scan", logs, re.IGNORECASE):
        results["performance_warnings"].append({
            "type": "missing_index",
            "severity": "medium",
            "message": "Database sequential scan detected (missing index)",
            "impact": "Slow queries, high database CPU",
            "fix": "Add database index on frequently queried columns",
            "savings": "Can speed up queries by 100-1000x"
        })
    
    # Memory leaks
    if re.search(r"(out of memory|OOM|heap|memory allocation failed)", logs, re.IGNORECASE):
        results["performance_warnings"].append({
            "type": "memory_issue",
            "severity": "critical",
            "message": "Memory allocation issue detected",
            "impact": "Job failures, OOM kills, high memory usage",
            "fix": "Use streaming/pagination for large datasets, free unused objects",
            "savings": "Reduce memory usage by 70%+, prevent job failures"
        })
    
    # Inefficient sorting/processing
    if re.search(r"sorting.*\d+\s+(records|items|rows)", logs, re.IGNORECASE):
        results["performance_warnings"].append({
            "type": "large_sort",
            "severity": "medium",
            "message": "Large in-memory sort detected",
            "impact": "High CPU usage, potential memory issues",
            "fix": "Sort at database level or use streaming sort",
            "savings": "Reduce CPU time by 40-60%"
        })
    
    # Synchronous external API calls
    if re.search(r"(waiting for|timeout|connection timeout)", logs, re.IGNORECASE):
        results["performance_warnings"].append({
            "type": "blocking_io",
            "severity": "medium",
            "message": "Blocking I/O operations detected (synchronous API calls)",
            "impact": "Wasted CPU time waiting for network responses",
            "fix": "Use async/await, job queues, or parallel requests",
            "savings": "Reduce job time by 30-50% with parallel requests"
        })


def analyze_docker_performance(dockerfile_content: str) -> Dict[str, Any]:
    """
    Analyze Dockerfile for performance issues.
    
    Args:
        dockerfile_content: Content of Dockerfile
        
    Returns:
        Performance analysis with recommendations
    """
    results = {
        "issues": [],
        "recommendations": [],
        "estimated_savings": {}
    }
    
    lines = dockerfile_content.split('\n')
    
    # Check for large base images
    for line in lines:
        if line.strip().startswith('FROM'):
            if 'ubuntu' in line.lower() and 'slim' not in line.lower():
                results["issues"].append({
                    "type": "large_base_image",
                    "severity": "medium",
                    "line": line,
                    "message": "Using full Ubuntu image (500MB+)",
                    "fix": "Use ubuntu:22.04-slim or alpine-based image",
                    "savings": "Reduce image size by 60-80%, faster pulls"
                })
    
    # Check for apt-get without cleanup
    has_apt_get = any('apt-get' in line for line in lines)
    has_cleanup = any('rm -rf /var/lib/apt' in line for line in lines)
    
    if has_apt_get and not has_cleanup:
        results["issues"].append({
            "type": "no_cleanup",
            "severity": "low",
            "message": "apt-get used without cleanup",
            "fix": "Add: RUN apt-get clean && rm -rf /var/lib/apt/lists/*",
            "savings": "Reduce image size by 50-100MB"
        })
    
    # Check for missing multi-stage builds
    from_count = sum(1 for line in lines if line.strip().startswith('FROM'))
    if from_count == 1 and 'node' in dockerfile_content.lower():
        results["recommendations"].append({
            "type": "multi_stage_build",
            "message": "Consider using multi-stage Docker build",
            "benefit": "Reduce final image size by excluding build dependencies",
            "example": "FROM node:18 AS builder\n...build...\nFROM node:18-slim\nCOPY --from=builder /app/dist /app/dist"
        })
    
    return results


def estimate_computational_savings(current_metrics: Dict[str, Any], 
                                   optimizations: List[str]) -> Dict[str, Any]:
    """
    Estimate CPU time and cost savings from proposed optimizations.
    
    Args:
        current_metrics: Current job performance metrics
        optimizations: List of optimization types applied
        
    Returns:
        Estimated savings in time, CPU, cost, and carbon
    """
    savings = {
        "time_saved_seconds": 0,
        "cpu_hours_saved": 0,
        "cost_saved_usd": 0,
        "co2_saved_grams": 0,
        "percentage_improvement": 0
    }
    
    current_duration = current_metrics.get("total_duration_seconds", 0)
    current_cpu_cores = current_metrics.get("cpu_cores", 4)
    
    # Optimization impact factors
    optimization_impacts = {
        "parallel_tests": 0.60,      # 60% faster with 4 cores
        "database_index": 0.80,       # 80% faster queries
        "n+1_fix": 0.90,             # 90% fewer queries
        "caching": 0.70,             # 70% faster with cache
        "async_io": 0.40,            # 40% faster with async
        "docker_optimization": 0.20,  # 20% faster image pulls
        "code_profiling": 0.30       # 30% faster after profiling
    }
    
    total_speedup = 1.0
    for opt in optimizations:
        if opt in optimization_impacts:
            # Multiplicative speedup
            total_speedup *= (1 - optimization_impacts[opt])
    
    new_duration = current_duration * total_speedup
    time_saved = current_duration - new_duration
    
    # Calculate savings
    savings["time_saved_seconds"] = round(time_saved, 0)
    savings["percentage_improvement"] = round((1 - total_speedup) * 100, 1)
    
    # CPU hours saved (duration × cores)
    cpu_hours_saved = (time_saved / 3600) * current_cpu_cores
    savings["cpu_hours_saved"] = round(cpu_hours_saved, 3)
    
    # Cost savings ($0.10 per CPU hour is typical for CI runners)
    savings["cost_saved_usd"] = round(cpu_hours_saved * 0.10, 2)
    
    # Carbon savings (assuming 0.5 kWh per CPU-hour and 0.475 kg/kWh grid intensity)
    kwh_saved = cpu_hours_saved * 0.5
    savings["co2_saved_grams"] = round(kwh_saved * 0.475 * 1000, 0)
    
    return savings


def generate_performance_report(job_logs: str, 
                                dockerfile: Optional[str] = None) -> str:
    """
    Generate a comprehensive performance analysis report.
    
    Args:
        job_logs: Job execution logs
        dockerfile: Optional Dockerfile content
        
    Returns:
        Markdown-formatted performance report
    """
    test_analysis = analyze_test_performance(job_logs)
    
    report = ["# 🚀 Performance Analysis Report\n"]
    
    # Slow tests section
    if test_analysis["slow_tests"]:
        report.append("## ⚠️ Slow Tests Detected\n")
        report.append(f"**Total test time:** {test_analysis['total_test_time']}s\n")
        report.append(f"**Slowest test:** {test_analysis['slowest_test_time']}s\n\n")
        
        report.append("| Test Name | Duration | Framework |\n")
        report.append("|-----------|----------|----------|\n")
        for test in test_analysis["slow_tests"][:5]:
            report.append(f"| {test['name'][:50]} | {test['duration']}s | {test['framework']} |\n")
        report.append("\n")
    
    # Performance warnings section
    if test_analysis["performance_warnings"]:
        report.append("## 🔴 Performance Issues\n\n")
        for warning in test_analysis["performance_warnings"]:
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            emoji = severity_emoji.get(warning["severity"], "⚪")
            
            report.append(f"### {emoji} {warning['type'].replace('_', ' ').title()}\n\n")
            report.append(f"**Severity:** {warning['severity'].upper()}\n\n")
            report.append(f"**Issue:** {warning['message']}\n\n")
            report.append(f"**Impact:** {warning['impact']}\n\n")
            report.append(f"**Fix:** {warning['fix']}\n\n")
            if "savings" in warning:
                report.append(f"**Potential Savings:** {warning['savings']}\n\n")
            report.append("---\n\n")
    
    # Recommendations section
    if test_analysis["recommendations"]:
        report.append("## 💡 Optimization Recommendations\n\n")
        for rec in test_analysis["recommendations"]:
            report.append(f"- **{rec['message']}**\n")
            report.append(f"  - Impact: {rec['impact']}\n")
            report.append(f"  - Fix: {rec['fix']}\n\n")
    
    # Docker analysis if provided
    if dockerfile:
        docker_analysis = analyze_docker_performance(dockerfile)
        if docker_analysis["issues"]:
            report.append("## 🐳 Docker Performance Issues\n\n")
            for issue in docker_analysis["issues"]:
                report.append(f"- **{issue['message']}**\n")
                report.append(f"  - Fix: {issue['fix']}\n")
                report.append(f"  - Savings: {issue['savings']}\n\n")
    
    return "".join(report)
