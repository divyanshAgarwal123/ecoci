"""
Production impact prediction - predict how code issues will affect production.

Analyzes performance issues detected in CI and predicts:
- Latency impact at scale
- Database load under traffic
- Memory consumption with real users
- API timeout risks
"""

from __future__ import annotations
from typing import Dict, List, Any


def predict_n1_impact(
    queries_detected: int,
    avg_query_time_ms: float = 5.0,
    requests_per_second: int = 100
) -> Dict[str, Any]:
    """
    Predict production impact of N+1 query problems.
    
    Args:
        queries_detected: Number of queries in N+1 pattern
        avg_query_time_ms: Average query execution time
        requests_per_second: Expected production traffic
        
    Returns:
        Impact prediction with severity
    """
    # Calculate latency per request
    latency_ms = queries_detected * avg_query_time_ms
    
    # Database queries per second
    db_queries_per_second = queries_detected * requests_per_second
    
    # Classify severity
    if latency_ms < 100:
        severity = "low"
        impact = "Minor slowdown"
    elif latency_ms < 500:
        severity = "medium"
        impact = "Noticeable latency"
    elif latency_ms < 1000:
        severity = "high"
        impact = "Page load degradation"
    else:
        severity = "critical"
        impact = "Timeout risk, user experience severely degraded"
    
    # Database connection pool exhaustion risk
    if db_queries_per_second > 1000:
        pool_warning = "⚠️ Database connection pool may be exhausted"
    else:
        pool_warning = None
    
    return {
        "severity": severity,
        "impact_description": impact,
        "latency_per_request_ms": round(latency_ms, 0),
        "db_queries_per_second": db_queries_per_second,
        "queries_detected": queries_detected,
        "pool_warning": pool_warning,
        "recommendation": (
            f"Fix urgency: {severity.upper()}. "
            f"This will add {latency_ms:.0f}ms to every request at {requests_per_second} req/s."
        )
    }


def predict_slow_query_impact(
    query_time_seconds: float,
    requests_per_second: int = 100,
    timeout_threshold_seconds: float = 30.0
) -> Dict[str, Any]:
    """Predict impact of slow database queries."""
    
    # Will it cause timeouts?
    will_timeout = query_time_seconds > timeout_threshold_seconds
    
    # Concurrent slow queries
    concurrent_slow_queries = query_time_seconds * requests_per_second
    
    # Database CPU usage
    if query_time_seconds < 0.1:
        cpu_impact = "negligible"
    elif query_time_seconds < 1.0:
        cpu_impact = "low"
    elif query_time_seconds < 5.0:
        cpu_impact = "medium"
    else:
        cpu_impact = "high"
    
    severity = "critical" if will_timeout else ("high" if query_time_seconds > 5 else "medium")
    
    return {
        "severity": severity,
        "query_time_seconds": query_time_seconds,
        "will_timeout": will_timeout,
        "timeout_threshold": timeout_threshold_seconds,
        "concurrent_slow_queries": round(concurrent_slow_queries, 1),
        "database_cpu_impact": cpu_impact,
        "recommendation": (
            "Add database index immediately" if query_time_seconds > 1 
            else "Consider adding index for optimization"
        )
    }


def predict_memory_leak_impact(
    memory_mb_per_request: float,
    requests_per_hour: int = 10000,
    server_memory_gb: int = 4
) -> Dict[str, Any]:
    """
    Predict when memory leak will cause OOM crashes.
    
    Args:
        memory_mb_per_request: Memory leaked per request
        requests_per_hour: Expected traffic
        server_memory_gb: Available server RAM
        
    Returns:
        Time until crash and severity
    """
    # Memory leaked per hour
    memory_leaked_per_hour_mb = memory_mb_per_request * requests_per_hour
    memory_leaked_per_hour_gb = memory_leaked_per_hour_mb / 1024
    
    # Time until OOM (assuming 80% of RAM available)
    available_memory_gb = server_memory_gb * 0.8
    hours_until_oom = available_memory_gb / memory_leaked_per_hour_gb if memory_leaked_per_hour_gb > 0 else 999
    
    # Severity
    if hours_until_oom < 1:
        severity = "critical"
        impact = "Server will crash within 1 hour"
    elif hours_until_oom < 24:
        severity = "high"
        impact = f"Server will crash within {hours_until_oom:.1f} hours (requires daily restarts)"
    elif hours_until_oom < 168:  # 1 week
        severity = "medium"
        impact = f"Server will crash within {hours_until_oom / 24:.1f} days (requires weekly restarts)"
    else:
        severity = "low"
        impact = "Slow memory leak, monitor long-term"
    
    return {
        "severity": severity,
        "impact_description": impact,
        "hours_until_oom": round(hours_until_oom, 1),
        "memory_leaked_per_hour_mb": round(memory_leaked_per_hour_mb, 1),
        "memory_leaked_per_hour_gb": round(memory_leaked_per_hour_gb, 2),
        "server_memory_gb": server_memory_gb,
        "recommendation": (
            "FIX IMMEDIATELY - Production will crash" if severity == "critical"
            else "Fix before production deployment" if severity == "high"
            else "Use pagination/streaming to prevent memory buildup"
        )
    }


def predict_api_timeout_risk(
    api_call_duration_seconds: float,
    calls_per_request: int = 1,
    timeout_threshold_seconds: float = 30.0
) -> Dict[str, Any]:
    """Predict risk of API timeouts in production."""
    
    total_blocking_time = api_call_duration_seconds * calls_per_request
    will_timeout = total_blocking_time > timeout_threshold_seconds
    
    # Calculate severity
    if will_timeout:
        severity = "critical"
        impact = f"Request will timeout ({total_blocking_time:.1f}s > {timeout_threshold_seconds}s limit)"
    elif total_blocking_time > timeout_threshold_seconds * 0.8:
        severity = "high"
        impact = f"Near timeout threshold ({total_blocking_time:.1f}s / {timeout_threshold_seconds}s limit)"
    elif total_blocking_time > 5:
        severity = "medium"
        impact = f"Slow API calls ({total_blocking_time:.1f}s per request)"
    else:
        severity = "low"
        impact = "Acceptable API call duration"
    
    # If made parallel, how fast?
    parallel_time = api_call_duration_seconds  # All calls in parallel
    time_saved = total_blocking_time - parallel_time
    
    return {
        "severity": severity,
        "impact_description": impact,
        "current_duration_seconds": total_blocking_time,
        "will_timeout": will_timeout,
        "calls_per_request": calls_per_request,
        "if_parallel_duration_seconds": parallel_time,
        "time_saved_by_parallelizing_seconds": time_saved,
        "recommendation": (
            "Use async/await or Promise.all() to parallelize" if calls_per_request > 1
            else "Add timeout handling and retry logic"
        )
    }


def predict_scalability_issues(
    algorithm_complexity: str,
    current_data_size: int,
    expected_growth_factor: int = 10
) -> Dict[str, Any]:
    """
    Predict scalability issues based on algorithm complexity.
    
    Args:
        algorithm_complexity: O(n), O(n²), O(n log n), etc.
        current_data_size: Current number of items processed
        expected_growth_factor: Expected data growth (10x, 100x)
        
    Returns:
        Scalability prediction
    """
    complexity_factors = {
        "O(1)": lambda n: 1,
        "O(log n)": lambda n: __import__('math').log2(n) if n > 0 else 1,
        "O(n)": lambda n: n,
        "O(n log n)": lambda n: n * __import__('math').log2(n) if n > 0 else n,
        "O(n²)": lambda n: n * n,
        "O(n³)": lambda n: n * n * n,
        "O(2^n)": lambda n: 2 ** min(n, 20),  # Cap to prevent overflow
    }
    
    complexity_func = complexity_factors.get(algorithm_complexity, lambda n: n)
    
    current_operations = complexity_func(current_data_size)
    future_size = current_data_size * expected_growth_factor
    future_operations = complexity_func(future_size)
    
    slowdown_factor = future_operations / current_operations if current_operations > 0 else 1
    
    # Severity based on slowdown
    if slowdown_factor < 2:
        severity = "low"
        impact = "Scales well"
    elif slowdown_factor < 10:
        severity = "medium"
        impact = f"Will be {slowdown_factor:.1f}x slower at scale"
    elif slowdown_factor < 100:
        severity = "high"
        impact = f"Will be {slowdown_factor:.0f}x slower - optimization needed"
    else:
        severity = "critical"
        impact = f"Will be {slowdown_factor:.0f}x slower - algorithm redesign required"
    
    return {
        "severity": severity,
        "impact_description": impact,
        "algorithm_complexity": algorithm_complexity,
        "current_data_size": current_data_size,
        "future_data_size": future_size,
        "slowdown_factor": round(slowdown_factor, 1),
        "recommendation": _get_complexity_recommendation(algorithm_complexity)
    }


def _get_complexity_recommendation(complexity: str) -> str:
    """Get recommendation based on complexity."""
    recommendations = {
        "O(n²)": "Use hash maps (O(n)) or database indices instead of nested loops",
        "O(n³)": "CRITICAL: Redesign algorithm - this will not scale",
        "O(2^n)": "CRITICAL: Exponential complexity - use dynamic programming or caching",
        "O(n log n)": "Good for sorting, but ensure data is pre-sorted when possible",
        "O(n)": "Good linear complexity - optimize constant factors if needed",
        "O(log n)": "Excellent - maintain indexed/sorted data structures",
        "O(1)": "Optimal - constant time complexity"
    }
    return recommendations.get(complexity, "Profile and optimize hotspots")


def generate_production_impact_report(performance_issues: List[Dict[str, Any]]) -> str:
    """Generate comprehensive production impact report."""
    
    lines = ["# 🚨 Production Impact Prediction\n\n"]
    lines.append("_Based on performance issues detected in CI/CD logs_\n\n")
    
    critical_issues = []
    high_issues = []
    medium_issues = []
    
    for issue in performance_issues:
        issue_type = issue.get("type")
        
        if issue_type == "n+1_queries":
            prediction = predict_n1_impact(
                issue.get("queries_count", 10),
                5.0,
                100  # Assume 100 req/s
            )
        elif issue_type == "slow_query":
            prediction = predict_slow_query_impact(
                issue.get("query_time_seconds", 5.0),
                100
            )
        elif issue_type == "memory_leak":
            prediction = predict_memory_leak_impact(
                issue.get("memory_mb", 10),
                10000,
                4
            )
        elif issue_type == "api_timeout":
            prediction = predict_api_timeout_risk(
                issue.get("duration_seconds", 5.0),
                issue.get("calls_count", 1)
            )
        else:
            continue
        
        issue_report = {
            "type": issue_type,
            "prediction": prediction,
            "location": issue.get("location", "unknown")
        }
        
        if prediction["severity"] == "critical":
            critical_issues.append(issue_report)
        elif prediction["severity"] == "high":
            high_issues.append(issue_report)
        else:
            medium_issues.append(issue_report)
    
    # Critical issues
    if critical_issues:
        lines.append("## 🔴 CRITICAL - Will Cause Production Failures\n\n")
        for issue in critical_issues:
            lines.append(f"### {issue['type'].replace('_', ' ').title()}\n")
            lines.append(f"**Location:** {issue['location']}\n\n")
            lines.append(f"**Impact:** {issue['prediction']['impact_description']}\n\n")
            lines.append(f"**Action:** {issue['prediction']['recommendation']}\n\n")
            lines.append("---\n\n")
    
    # High severity
    if high_issues:
        lines.append("## 🟠 HIGH - Significant Performance Degradation\n\n")
        for issue in high_issues:
            lines.append(f"### {issue['type'].replace('_', ' ').title()}\n")
            lines.append(f"**Impact:** {issue['prediction']['impact_description']}\n\n")
    
    # Summary
    lines.append(f"\n## Summary\n\n")
    lines.append(f"- 🔴 Critical issues: {len(critical_issues)}\n")
    lines.append(f"- 🟠 High severity: {len(high_issues)}\n")
    lines.append(f"- 🟡 Medium severity: {len(medium_issues)}\n\n")
    
    if critical_issues:
        lines.append("**DO NOT DEPLOY** until critical issues are resolved.\n")
    
    return "".join(lines)
