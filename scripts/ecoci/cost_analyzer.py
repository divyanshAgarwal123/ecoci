"""
Cost analysis for CI/CD pipelines - show real $ savings.

Tracks:
- Runner costs per pipeline
- Monthly CI/CD spending
- Cost per developer
- ROI from optimizations
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


# GitLab runner pricing (approximate market rates)
RUNNER_COSTS = {
    "saas-linux-small-amd64": 0.008,      # $0.008/min
    "saas-linux-medium-amd64": 0.016,     # $0.016/min
    "saas-linux-large-amd64": 0.032,      # $0.032/min
    "saas-linux-xlarge-amd64": 0.064,     # $0.064/min
    "saas-macos-medium-m1": 0.083,        # $0.083/min (expensive!)
    "shared-runner": 0.010,               # Default estimate
    "self-hosted": 0.005,                 # Amortized infrastructure cost
}

# Average developer hourly cost (global averages)
DEVELOPER_COSTS = {
    "junior": 35,      # $35/hour
    "mid": 60,         # $60/hour
    "senior": 90,      # $90/hour
    "staff": 120,      # $120/hour
}


def calculate_pipeline_cost(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate the $ cost of running a pipeline.
    
    Args:
        jobs: List of job data with duration, runner tags
        
    Returns:
        Cost breakdown by job and total
    """
    total_cost = 0.0
    job_costs = []
    
    for job in jobs:
        duration_min = job.get("duration", 0) / 60
        runner_tags = job.get("runner", {}).get("tags", [])
        
        # Determine runner cost
        runner_cost_per_min = RUNNER_COSTS.get("shared-runner", 0.010)
        for tag in runner_tags:
            if tag in RUNNER_COSTS:
                runner_cost_per_min = RUNNER_COSTS[tag]
                break
        
        job_cost = duration_min * runner_cost_per_min
        total_cost += job_cost
        
        job_costs.append({
            "name": job.get("name", "unknown"),
            "duration_min": round(duration_min, 2),
            "cost_per_min": runner_cost_per_min,
            "total_cost": round(job_cost, 3),
            "runner_tags": runner_tags
        })
    
    return {
        "total_cost": round(total_cost, 2),
        "job_costs": job_costs,
        "currency": "USD"
    }


def calculate_monthly_spending(
    avg_pipeline_cost: float,
    pipelines_per_day: int,
    working_days_per_month: int = 22
) -> Dict[str, Any]:
    """Calculate monthly CI/CD spending."""
    daily_cost = avg_pipeline_cost * pipelines_per_day
    monthly_cost = daily_cost * working_days_per_month
    annual_cost = monthly_cost * 12
    
    return {
        "daily_cost": round(daily_cost, 2),
        "monthly_cost": round(monthly_cost, 2),
        "annual_cost": round(annual_cost, 2),
        "pipelines_per_day": pipelines_per_day,
        "pipelines_per_month": pipelines_per_day * working_days_per_month,
        "avg_pipeline_cost": round(avg_pipeline_cost, 2)
    }


def calculate_developer_wait_cost(
    pipeline_duration_minutes: float,
    developer_level: str = "mid",
    pipelines_waiting_on: int = 10  # Pipelines/week developer waits for
) -> Dict[str, Any]:
    """
    Calculate cost of developers waiting for slow pipelines.
    
    Waiting for a 15-minute pipeline = 15 min of wasted developer time.
    """
    hourly_rate = DEVELOPER_COSTS.get(developer_level, 60)
    cost_per_minute = hourly_rate / 60
    
    cost_per_wait = (pipeline_duration_minutes * cost_per_minute)
    weekly_wait_cost = cost_per_wait * pipelines_waiting_on
    monthly_wait_cost = weekly_wait_cost * 4.33
    annual_wait_cost = monthly_wait_cost * 12
    
    return {
        "cost_per_pipeline_wait": round(cost_per_wait, 2),
        "weekly_cost": round(weekly_wait_cost, 2),
        "monthly_cost": round(monthly_wait_cost, 2),
        "annual_cost": round(annual_wait_cost, 2),
        "developer_level": developer_level,
        "hourly_rate": hourly_rate,
        "hours_wasted_per_month": round(pipeline_duration_minutes * pipelines_waiting_on * 4.33 / 60, 1)
    }


def calculate_roi(
    current_cost: float,
    optimized_cost: float,
    current_duration_min: float,
    optimized_duration_min: float,
    team_size: int = 10,
    developer_level: str = "mid",
    pipelines_per_week: int = 50
) -> Dict[str, Any]:
    """
    Calculate ROI from pipeline optimization.
    
    Includes:
    - Runner cost savings
    - Developer productivity gains
    - Time to implement (opportunity cost)
    """
    # Runner cost savings
    runner_savings_per_pipeline = current_cost - optimized_cost
    runner_savings_weekly = runner_savings_per_pipeline * pipelines_per_week
    runner_savings_annual = runner_savings_weekly * 52
    
    # Time saved per pipeline
    time_saved_min = current_duration_min - optimized_duration_min
    time_saved_per_week_hours = (time_saved_min * pipelines_per_week) / 60
    
    # Developer productivity value
    hourly_rate = DEVELOPER_COSTS.get(developer_level, 60)
    
    # Assuming 20% of pipeline time is spent waiting/blocked
    productive_time_regained_hours = time_saved_per_week_hours * 0.2 * team_size
    productivity_value_weekly = productive_time_regained_hours * hourly_rate
    productivity_value_annual = productivity_value_weekly * 52
    
    total_annual_savings = runner_savings_annual + productivity_value_annual
    
    # Implementation cost (estimate: 4 hours to implement optimizations)
    implementation_cost = 4 * hourly_rate
    
    # Payback period
    weekly_total_savings = runner_savings_weekly + productivity_value_weekly
    payback_weeks = implementation_cost / weekly_total_savings if weekly_total_savings > 0 else 999
    
    return {
        "runner_cost_savings": {
            "per_pipeline": round(runner_savings_per_pipeline, 2),
            "weekly": round(runner_savings_weekly, 2),
            "annual": round(runner_savings_annual, 2)
        },
        "developer_productivity_gains": {
            "hours_saved_per_week": round(time_saved_per_week_hours, 1),
            "productive_hours_regained_per_week": round(productive_time_regained_hours, 1),
            "value_weekly": round(productivity_value_weekly, 2),
            "value_annual": round(productivity_value_annual, 2)
        },
        "total_annual_value": round(total_annual_savings, 2),
        "implementation_cost": round(implementation_cost, 2),
        "payback_period_weeks": round(payback_weeks, 1),
        "roi_percentage": round((total_annual_savings / implementation_cost - 1) * 100, 0) if implementation_cost > 0 else 0,
        "team_size": team_size,
        "pipelines_per_week": pipelines_per_week
    }


def compare_with_industry_benchmarks(
    pipeline_duration_min: float,
    project_type: str = "web_app"
) -> Dict[str, Any]:
    """
    Compare pipeline performance with industry benchmarks.
    
    Benchmarks based on industry data from GitLab, CircleCI, GitHub Actions reports.
    """
    benchmarks = {
        "web_app": {"p50": 8, "p75": 15, "p90": 25, "p99": 45},
        "mobile_app": {"p50": 12, "p75": 20, "p90": 35, "p99": 60},
        "api_service": {"p50": 5, "p75": 10, "p90": 18, "p99": 30},
        "library": {"p50": 4, "p75": 7, "p90": 12, "p99": 20},
        "data_pipeline": {"p50": 15, "p75": 30, "p90": 60, "p99": 120},
    }
    
    benchmark = benchmarks.get(project_type, benchmarks["web_app"])
    
    # Determine percentile
    if pipeline_duration_min <= benchmark["p50"]:
        percentile = "top 50% (excellent!)"
        status = "excellent"
    elif pipeline_duration_min <= benchmark["p75"]:
        percentile = "50-75th percentile (good)"
        status = "good"
    elif pipeline_duration_min <= benchmark["p90"]:
        percentile = "75-90th percentile (average)"
        status = "average"
    elif pipeline_duration_min <= benchmark["p99"]:
        percentile = "90-99th percentile (slow)"
        status = "slow"
    else:
        percentile = "bottom 1% (very slow)"
        status = "very_slow"
    
    # Calculate how much slower than median
    slowness_factor = pipeline_duration_min / benchmark["p50"]
    
    return {
        "your_duration_min": pipeline_duration_min,
        "benchmark_p50": benchmark["p50"],
        "benchmark_p90": benchmark["p90"],
        "percentile": percentile,
        "status": status,
        "slowness_factor": round(slowness_factor, 1),
        "project_type": project_type,
        "recommendation": _get_speed_recommendation(status, slowness_factor)
    }


def _get_speed_recommendation(status: str, slowness_factor: float) -> str:
    """Get recommendation based on pipeline speed."""
    if status == "excellent":
        return "Your pipeline is faster than most! Focus on reliability and test coverage."
    elif status == "good":
        return "Good performance. Consider caching and parallelization for further gains."
    elif status == "average":
        return "Average performance. Significant optimization opportunities exist."
    elif status == "slow":
        return f"Your pipeline is {slowness_factor}x slower than median. Priority: parallelize jobs and add caching."
    else:
        return f"CRITICAL: {slowness_factor}x slower than median. This is blocking developer productivity."


def generate_cost_report(
    current_pipeline: Dict[str, Any],
    optimized_pipeline: Optional[Dict[str, Any]] = None,
    team_size: int = 10,
    pipelines_per_week: int = 50
) -> str:
    """Generate comprehensive cost analysis report."""
    
    current_cost_data = calculate_pipeline_cost(current_pipeline.get("jobs", []))
    current_duration_min = current_pipeline.get("duration", 0) / 60
    
    lines = ["# 💰 Pipeline Cost Analysis\n"]
    
    # Current costs
    lines.append("## Current Pipeline Costs\n")
    lines.append(f"**Per Pipeline:** ${current_cost_data['total_cost']:.2f}\n")
    
    monthly = calculate_monthly_spending(
        current_cost_data['total_cost'],
        pipelines_per_week // 5,  # per day
        22
    )
    lines.append(f"**Monthly (@ {pipelines_per_week} runs/week):** ${monthly['monthly_cost']:.2f}\n")
    lines.append(f"**Annual:** ${monthly['annual_cost']:.2f}\n\n")
    
    # Job breakdown
    lines.append("### Cost by Job\n\n")
    lines.append("| Job | Duration | Cost/min | Total Cost |\n")
    lines.append("|-----|----------|----------|------------|\n")
    for job in current_cost_data['job_costs']:
        lines.append(f"| {job['name']} | {job['duration_min']:.1f}m | ${job['cost_per_min']:.3f} | ${job['total_cost']:.2f} |\n")
    lines.append("\n")
    
    # Developer wait cost
    wait_cost = calculate_developer_wait_cost(current_duration_min, "mid", pipelines_per_week // 5)
    lines.append("## Developer Productivity Cost\n\n")
    lines.append(f"**Time spent waiting per month:** {wait_cost['hours_wasted_per_month']} hours\n")
    lines.append(f"**Cost of waiting (@ ${wait_cost['hourly_rate']}/hr):** ${wait_cost['monthly_cost']:.2f}/month\n")
    lines.append(f"**Annual developer time cost:** ${wait_cost['annual_cost']:.2f}\n\n")
    
    # Industry benchmark
    benchmark = compare_with_industry_benchmarks(current_duration_min, "web_app")
    lines.append("## Industry Benchmark\n\n")
    lines.append(f"**Your pipeline:** {current_duration_min:.1f} minutes\n")
    lines.append(f"**Industry median (p50):** {benchmark['benchmark_p50']} minutes\n")
    lines.append(f"**Your percentile:** {benchmark['percentile']}\n")
    lines.append(f"**Status:** {benchmark['status'].upper()}\n\n")
    lines.append(f"💡 {benchmark['recommendation']}\n\n")
    
    # If optimized version provided, show ROI
    if optimized_pipeline:
        optimized_cost_data = calculate_pipeline_cost(optimized_pipeline.get("jobs", []))
        optimized_duration_min = optimized_pipeline.get("duration", 0) / 60
        
        roi = calculate_roi(
            current_cost_data['total_cost'],
            optimized_cost_data['total_cost'],
            current_duration_min,
            optimized_duration_min,
            team_size,
            "mid",
            pipelines_per_week
        )
        
        lines.append("## 🚀 Optimization ROI\n\n")
        lines.append(f"**Runner cost savings:** ${roi['runner_cost_savings']['annual']:.2f}/year\n")
        lines.append(f"**Productivity gains:** ${roi['developer_productivity_gains']['value_annual']:.2f}/year\n")
        lines.append(f"**Total annual value:** ${roi['total_annual_value']:.2f}\n\n")
        lines.append(f"**Implementation cost:** ${roi['implementation_cost']:.2f} (one-time)\n")
        lines.append(f"**Payback period:** {roi['payback_period_weeks']:.1f} weeks\n")
        lines.append(f"**ROI:** {roi['roi_percentage']:.0f}%\n\n")
        
        lines.append(f"✅ **Hours saved per week:** {roi['developer_productivity_gains']['hours_saved_per_week']:.1f} hours\n")
        lines.append(f"✅ **For {team_size} developers:** {roi['developer_productivity_gains']['productive_hours_regained_per_week']:.1f} productive hours/week regained\n")
    
    return "".join(lines)
