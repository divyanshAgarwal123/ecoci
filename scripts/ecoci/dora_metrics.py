"""
DORA Metrics Calculator - Measure team DevOps performance.

Tracks the four key DORA (DevOps Research and Assessment) metrics:
1. Deployment Frequency - How often you deploy
2. Lead Time for Changes - Time from commit to production
3. Change Failure Rate - % of deployments causing failures
4. Mean Time to Recovery (MTTR) - How fast you recover from failures

These are the gold standard metrics used by Google, Netflix, and top engineering orgs.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


# DORA performance levels (from Accelerate book / Google DORA research)
DORA_BENCHMARKS = {
    "deployment_frequency": {
        "elite": {"min_per_day": 1, "label": "Multiple times per day"},
        "high": {"min_per_week": 1, "label": "Weekly to monthly"},
        "medium": {"min_per_month": 1, "label": "Monthly to every 6 months"},
        "low": {"label": "Less than once every 6 months"}
    },
    "lead_time": {
        "elite": {"max_hours": 24, "label": "Less than 1 day"},
        "high": {"max_hours": 168, "label": "1 day to 1 week"},
        "medium": {"max_hours": 720, "label": "1 week to 1 month"},
        "low": {"label": "More than 1 month"}
    },
    "change_failure_rate": {
        "elite": {"max_percent": 5, "label": "0-5%"},
        "high": {"max_percent": 10, "label": "5-10%"},
        "medium": {"max_percent": 15, "label": "10-15%"},
        "low": {"label": "16-30%+"}
    },
    "mttr": {
        "elite": {"max_hours": 1, "label": "Less than 1 hour"},
        "high": {"max_hours": 24, "label": "Less than 1 day"},
        "medium": {"max_hours": 168, "label": "Less than 1 week"},
        "low": {"label": "More than 1 week"}
    }
}


def classify_deployment_frequency(deploys_per_month: float) -> Dict[str, Any]:
    """Classify deployment frequency into DORA levels."""
    deploys_per_day = deploys_per_month / 30
    deploys_per_week = deploys_per_month / 4.33
    
    if deploys_per_day >= 1:
        level = "elite"
        emoji = "🏆"
    elif deploys_per_week >= 1:
        level = "high"
        emoji = "🟢"
    elif deploys_per_month >= 1:
        level = "medium"
        emoji = "🟡"
    else:
        level = "low"
        emoji = "🔴"
    
    return {
        "metric": "Deployment Frequency",
        "value": f"{deploys_per_month:.1f} deploys/month",
        "level": level,
        "emoji": emoji,
        "benchmark": DORA_BENCHMARKS["deployment_frequency"][level]["label"],
        "improvement": _get_deploy_freq_improvement(level, deploys_per_month)
    }


def classify_lead_time(hours: float) -> Dict[str, Any]:
    """Classify lead time for changes."""
    if hours <= 24:
        level = "elite"
        emoji = "🏆"
    elif hours <= 168:
        level = "high"
        emoji = "🟢"
    elif hours <= 720:
        level = "medium"
        emoji = "🟡"
    else:
        level = "low"
        emoji = "🔴"
    
    if hours < 1:
        display = f"{hours * 60:.0f} minutes"
    elif hours < 24:
        display = f"{hours:.1f} hours"
    else:
        display = f"{hours / 24:.1f} days"
    
    return {
        "metric": "Lead Time for Changes",
        "value": display,
        "level": level,
        "emoji": emoji,
        "benchmark": DORA_BENCHMARKS["lead_time"][level]["label"],
        "improvement": _get_lead_time_improvement(level, hours)
    }


def classify_change_failure_rate(failure_percent: float) -> Dict[str, Any]:
    """Classify change failure rate."""
    if failure_percent <= 5:
        level = "elite"
        emoji = "🏆"
    elif failure_percent <= 10:
        level = "high"
        emoji = "🟢"
    elif failure_percent <= 15:
        level = "medium"
        emoji = "🟡"
    else:
        level = "low"
        emoji = "🔴"
    
    return {
        "metric": "Change Failure Rate",
        "value": f"{failure_percent:.1f}%",
        "level": level,
        "emoji": emoji,
        "benchmark": DORA_BENCHMARKS["change_failure_rate"][level]["label"],
        "improvement": _get_cfr_improvement(level, failure_percent)
    }


def classify_mttr(hours: float) -> Dict[str, Any]:
    """Classify Mean Time to Recovery."""
    if hours <= 1:
        level = "elite"
        emoji = "🏆"
    elif hours <= 24:
        level = "high"
        emoji = "🟢"
    elif hours <= 168:
        level = "medium"
        emoji = "🟡"
    else:
        level = "low"
        emoji = "🔴"
    
    if hours < 1:
        display = f"{hours * 60:.0f} minutes"
    elif hours < 24:
        display = f"{hours:.1f} hours"
    else:
        display = f"{hours / 24:.1f} days"
    
    return {
        "metric": "Mean Time to Recovery",
        "value": display,
        "level": level,
        "emoji": emoji,
        "benchmark": DORA_BENCHMARKS["mttr"][level]["label"],
        "improvement": _get_mttr_improvement(level, hours)
    }


def calculate_dora_metrics(
    deploys_per_month: float,
    lead_time_hours: float,
    change_failure_rate: float,
    mttr_hours: float
) -> Dict[str, Any]:
    """
    Calculate all four DORA metrics and provide an overall assessment.
    """
    metrics = {
        "deployment_frequency": classify_deployment_frequency(deploys_per_month),
        "lead_time": classify_lead_time(lead_time_hours),
        "change_failure_rate": classify_change_failure_rate(change_failure_rate),
        "mttr": classify_mttr(mttr_hours),
    }
    
    # Calculate overall level
    levels = [m["level"] for m in metrics.values()]
    level_scores = {"elite": 4, "high": 3, "medium": 2, "low": 1}
    avg_score = sum(level_scores[l] for l in levels) / len(levels)
    
    if avg_score >= 3.5:
        overall_level = "elite"
        overall_emoji = "🏆"
        overall_description = "Elite Performer — Top 15% of engineering orgs"
    elif avg_score >= 2.5:
        overall_level = "high"
        overall_emoji = "🟢"
        overall_description = "High Performer — Above average"
    elif avg_score >= 1.5:
        overall_level = "medium"
        overall_emoji = "🟡"
        overall_description = "Medium Performer — Room for improvement"
    else:
        overall_level = "low"
        overall_emoji = "🔴"
        overall_description = "Low Performer — Significant transformation needed"
    
    metrics["overall"] = {
        "level": overall_level,
        "emoji": overall_emoji,
        "description": overall_description,
        "score": round(avg_score, 1),
        "max_score": 4.0
    }
    
    return metrics


def estimate_dora_from_pipelines(
    recent_pipelines: List[Dict[str, Any]],
    days_window: int = 30
) -> Dict[str, Any]:
    """
    Estimate DORA metrics from pipeline data.
    
    Args:
        recent_pipelines: List of pipeline data with status, created_at, duration
        days_window: Number of days to analyze
        
    Returns:
        Estimated DORA metrics
    """
    if not recent_pipelines:
        return calculate_dora_metrics(0, 999, 100, 999)
    
    total = len(recent_pipelines)
    
    # Deployment frequency (successful pipelines on default branch)
    successful = [p for p in recent_pipelines if p.get("status") == "success"]
    deploys_per_month = len(successful) * (30 / max(days_window, 1))
    
    # Lead time (average pipeline duration for successful runs)
    durations = [p.get("duration", 0) for p in successful if p.get("duration")]
    avg_duration_hours = (sum(durations) / len(durations) / 3600) if durations else 24
    
    # Change failure rate
    failed = [p for p in recent_pipelines if p.get("status") == "failed"]
    failure_rate = (len(failed) / total * 100) if total > 0 else 0
    
    # MTTR (estimated from failed pipeline patterns)
    mttr_hours = avg_duration_hours * 2  # Rough estimate: 2x pipeline time to fix
    
    return calculate_dora_metrics(deploys_per_month, avg_duration_hours, failure_rate, mttr_hours)


def generate_dora_report(metrics: Dict[str, Any]) -> str:
    """Generate DORA metrics report."""
    lines = ["# 📊 DORA Metrics Report\n\n"]
    lines.append("_Industry-standard DevOps performance metrics (used by Google, Netflix, Amazon)_\n\n")
    
    overall = metrics.get("overall", {})
    lines.append(f"## Overall: {overall.get('emoji', '⚪')} {overall.get('level', 'unknown').upper()}\n\n")
    lines.append(f"_{overall.get('description', '')}_\n\n")
    lines.append(f"**Score:** {overall.get('score', 0)}/4.0\n\n")
    
    # Metrics table
    lines.append("## Metrics\n\n")
    lines.append("| Metric | Value | Level | Benchmark |\n")
    lines.append("|--------|-------|-------|----------|\n")
    
    for key in ["deployment_frequency", "lead_time", "change_failure_rate", "mttr"]:
        m = metrics.get(key, {})
        lines.append(f"| {m.get('emoji', '')} {m.get('metric', key)} | {m.get('value', 'N/A')} | {m.get('level', '').upper()} | {m.get('benchmark', '')} |\n")
    
    lines.append("\n")
    
    # Improvements
    lines.append("## 🎯 Improvement Plan\n\n")
    for key in ["deployment_frequency", "lead_time", "change_failure_rate", "mttr"]:
        m = metrics.get(key, {})
        if m.get("improvement"):
            lines.append(f"### {m.get('metric', key)}\n")
            lines.append(f"{m.get('improvement')}\n\n")
    
    # Comparison with industry
    lines.append("## 📈 Industry Comparison\n\n")
    lines.append("Based on the DORA State of DevOps Report (Google Cloud):\n\n")
    lines.append("| Level | % of Teams | Your Metrics |\n")
    lines.append("|-------|------------|-------------|\n")
    lines.append(f"| 🏆 Elite | 15% | {'✅ You are here!' if overall.get('level') == 'elite' else ''} |\n")
    lines.append(f"| 🟢 High | 25% | {'✅ You are here!' if overall.get('level') == 'high' else ''} |\n")
    lines.append(f"| 🟡 Medium | 35% | {'✅ You are here!' if overall.get('level') == 'medium' else ''} |\n")
    lines.append(f"| 🔴 Low | 25% | {'✅ You are here!' if overall.get('level') == 'low' else ''} |\n")
    
    return "".join(lines)


def _get_deploy_freq_improvement(level: str, deploys_per_month: float) -> str:
    if level == "elite":
        return "Excellent! Maintain high deployment frequency with feature flags and trunk-based development."
    elif level == "high":
        return f"Good! To reach elite ({'>'}1x/day): Adopt trunk-based development, reduce branch lifetime to <1 day, use feature flags."
    elif level == "medium":
        return f"To improve: Break large features into small PRs (<200 lines), automate deployments, reduce manual approval gates."
    return f"Critical: Currently {deploys_per_month:.1f}/month. Start with CI/CD automation, automated testing, and removing manual gates."


def _get_lead_time_improvement(level: str, hours: float) -> str:
    if level == "elite":
        return "Excellent! Your team ships fast. Keep pipeline optimization as a priority."
    elif level == "high":
        return f"Good! To reach elite (<1 day): Optimize slow pipeline stages, parallelize tests, reduce review bottlenecks."
    elif level == "medium":
        return f"To improve: Currently {hours:.0f}h. Automate code reviews, add auto-merge, parallelize CI stages."
    return f"Critical: {hours / 24:.0f} day lead time. Focus on pipeline speed, automated testing, and reducing approval bottlenecks."


def _get_cfr_improvement(level: str, rate: float) -> str:
    if level == "elite":
        return "Excellent! Low failure rate indicates strong testing and review practices."
    elif level == "high":
        return f"Good! To reach elite (<5%): Add integration tests, canary deployments, feature flags for risky changes."
    elif level == "medium":
        return f"To improve: Currently {rate:.0f}%. Increase test coverage, add staging environment, implement code review requirements."
    return f"Critical: {rate:.0f}% failure rate. Implement comprehensive testing, staging environments, and automated rollbacks."


def _get_mttr_improvement(level: str, hours: float) -> str:
    if level == "elite":
        return "Excellent! Fast recovery indicates good observability and rollback procedures."
    elif level == "high":
        return f"Good! To reach elite (<1 hour): Add automated rollbacks, feature flags for instant disable, improved alerting."
    elif level == "medium":
        return f"To improve: Currently {hours:.0f}h MTTR. Add monitoring/alerting, one-click rollback, runbooks for common failures."
    return f"Critical: {hours / 24:.0f} day MTTR. Implement monitoring, automated rollbacks, on-call procedures, and incident response."
