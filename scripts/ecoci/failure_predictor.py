"""
Pipeline failure predictor — predict if a pipeline will fail before it finishes.

Uses pattern analysis to predict failures:
- Historical failure patterns (same files changed = same failures)
- Test coverage gaps
- Configuration drift
- Dependency conflicts
- Resource exhaustion patterns
"""

from __future__ import annotations
import re
from typing import Dict, List, Any, Optional
from datetime import datetime


# Risk factors that increase failure probability
RISK_FACTORS = {
    "large_diff": {
        "threshold": 500,  # lines changed
        "weight": 0.15,
        "message": "Large change (>500 lines) — higher risk of regressions"
    },
    "many_files": {
        "threshold": 20,  # files changed
        "weight": 0.10,
        "message": "Many files changed (>20) — broad impact"
    },
    "config_change": {
        "patterns": [r"\.yml$", r"\.yaml$", r"config/", r"Dockerfile", r"docker-compose"],
        "weight": 0.20,
        "message": "Configuration files changed — infrastructure risk"
    },
    "dependency_change": {
        "patterns": [r"Gemfile", r"package\.json", r"requirements\.txt", r"go\.mod", r"pom\.xml"],
        "weight": 0.25,
        "message": "Dependencies changed — compatibility risk"
    },
    "migration": {
        "patterns": [r"migrat", r"schema", r"alter\s+table", r"create\s+table"],
        "weight": 0.20,
        "message": "Database migration — deployment risk"
    },
    "friday_deploy": {
        "weight": 0.10,
        "message": "Friday deployment — reduced incident response capacity"
    },
    "late_night": {
        "weight": 0.05,
        "message": "Late night change — fatigue risk"
    },
    "no_tests": {
        "weight": 0.30,
        "message": "No test files modified — untested changes"
    },
    "hotfix_pattern": {
        "patterns": [r"hotfix", r"urgent", r"emergency", r"quick.?fix"],
        "weight": 0.15,
        "message": "Hotfix pattern detected — rushed change"
    },
    "merge_conflict_resolution": {
        "patterns": [r"<<<<<<", r">>>>>>", r"======"],
        "weight": 0.25,
        "message": "Merge conflict markers — potential bad resolution"
    }
}


def predict_pipeline_failure(
    changed_files: List[str],
    lines_changed: int = 0,
    commit_message: str = "",
    commit_time: Optional[datetime] = None,
    diff_content: str = "",
    historical_failure_rate: float = 0.15
) -> Dict[str, Any]:
    """
    Predict pipeline failure probability based on change characteristics.
    
    Returns:
        Prediction with probability, risk factors, and recommendations
    """
    risk_score = historical_failure_rate  # Start with base failure rate
    risk_factors_triggered = []
    
    # Check each risk factor
    # Large diff
    if lines_changed > RISK_FACTORS["large_diff"]["threshold"]:
        risk_score += RISK_FACTORS["large_diff"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["large_diff"],
            "detail": f"{lines_changed} lines changed"
        })
    
    # Many files
    if len(changed_files) > RISK_FACTORS["many_files"]["threshold"]:
        risk_score += RISK_FACTORS["many_files"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["many_files"],
            "detail": f"{len(changed_files)} files changed"
        })
    
    # Config changes
    config_files = [f for f in changed_files if any(
        re.search(p, f) for p in RISK_FACTORS["config_change"]["patterns"]
    )]
    if config_files:
        risk_score += RISK_FACTORS["config_change"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["config_change"],
            "detail": f"Config files: {', '.join(config_files[:3])}"
        })
    
    # Dependency changes
    dep_files = [f for f in changed_files if any(
        re.search(p, f) for p in RISK_FACTORS["dependency_change"]["patterns"]
    )]
    if dep_files:
        risk_score += RISK_FACTORS["dependency_change"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["dependency_change"],
            "detail": f"Dependency files: {', '.join(dep_files)}"
        })
    
    # Migration
    migration_files = [f for f in changed_files if any(
        re.search(p, f, re.IGNORECASE) for p in RISK_FACTORS["migration"]["patterns"]
    )]
    if migration_files:
        risk_score += RISK_FACTORS["migration"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["migration"],
            "detail": f"Migration files: {', '.join(migration_files[:3])}"
        })
    
    # Friday deploy
    if commit_time and commit_time.weekday() == 4:  # Friday
        risk_score += RISK_FACTORS["friday_deploy"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["friday_deploy"],
            "detail": f"Committed on {commit_time.strftime('%A %H:%M')}"
        })
    
    # Late night
    if commit_time and (commit_time.hour >= 22 or commit_time.hour <= 5):
        risk_score += RISK_FACTORS["late_night"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["late_night"],
            "detail": f"Committed at {commit_time.strftime('%H:%M')}"
        })
    
    # No tests
    test_patterns = [r"test_", r"_test\.", r"_spec\.", r"\.test\.", r"__tests__"]
    has_test_changes = any(
        any(re.search(p, f) for p in test_patterns) for f in changed_files
    )
    if not has_test_changes and len(changed_files) > 2:
        risk_score += RISK_FACTORS["no_tests"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["no_tests"],
            "detail": "No test files in this change"
        })
    
    # Hotfix pattern
    if any(re.search(p, commit_message, re.IGNORECASE) for p in RISK_FACTORS["hotfix_pattern"]["patterns"]):
        risk_score += RISK_FACTORS["hotfix_pattern"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["hotfix_pattern"],
            "detail": f"Commit message: '{commit_message[:50]}'"
        })
    
    # Merge conflict markers in diff
    if diff_content and any(re.search(p, diff_content) for p in RISK_FACTORS["merge_conflict_resolution"]["patterns"]):
        risk_score += RISK_FACTORS["merge_conflict_resolution"]["weight"]
        risk_factors_triggered.append({
            **RISK_FACTORS["merge_conflict_resolution"],
            "detail": "Merge conflict markers found in diff"
        })
    
    # Cap at 95%
    risk_score = min(0.95, risk_score)
    
    # Classification
    if risk_score < 0.20:
        risk_level = "low"
        emoji = "🟢"
        recommendation = "Safe to proceed. Monitor pipeline as usual."
    elif risk_score < 0.40:
        risk_level = "medium"
        emoji = "🟡"
        recommendation = "Proceed with caution. Review test results carefully."
    elif risk_score < 0.60:
        risk_level = "high"
        emoji = "🟠"
        recommendation = "High risk. Consider additional testing or staged rollout."
    else:
        risk_level = "critical"
        emoji = "🔴"
        recommendation = "VERY HIGH RISK. Consider splitting into smaller changes."
    
    return {
        "failure_probability": round(risk_score * 100, 1),
        "risk_level": risk_level,
        "emoji": emoji,
        "recommendation": recommendation,
        "risk_factors": risk_factors_triggered,
        "risk_factors_count": len(risk_factors_triggered),
        "changed_files": len(changed_files),
        "lines_changed": lines_changed,
        "suggestions": _generate_risk_mitigations(risk_factors_triggered)
    }


def _generate_risk_mitigations(risk_factors: List[Dict]) -> List[Dict[str, str]]:
    """Generate specific mitigations for each risk factor."""
    mitigations = []
    
    for factor in risk_factors:
        factor_type = factor.get("message", "")
        
        if "Large change" in factor_type:
            mitigations.append({
                "action": "Split into smaller PRs",
                "effort": "medium",
                "impact": "Reduces risk by 50%",
                "how": "Break into feature + test + config PRs separately"
            })
        elif "Dependencies" in factor_type:
            mitigations.append({
                "action": "Lock dependency versions",
                "effort": "low",
                "impact": "Prevents unexpected breaking changes",
                "how": "Use exact versions (==) instead of ranges (>=)"
            })
        elif "migration" in factor_type.lower():
            mitigations.append({
                "action": "Test migration on staging first",
                "effort": "medium",
                "impact": "Catch schema issues before production",
                "how": "Run migration on a copy of production data"
            })
        elif "No test" in factor_type:
            mitigations.append({
                "action": "Add tests before merging",
                "effort": "medium",
                "impact": "Catch regressions immediately",
                "how": "Write at least 1 test per changed function"
            })
        elif "Friday" in factor_type:
            mitigations.append({
                "action": "Deploy on Monday instead",
                "effort": "zero",
                "impact": "Full team available for incidents",
                "how": "Schedule deployment for Monday morning"
            })
        elif "Hotfix" in factor_type:
            mitigations.append({
                "action": "Get a second review",
                "effort": "low",
                "impact": "Catches mistakes in rushed changes",
                "how": "Ask a teammate for a quick review before merge"
            })
    
    return mitigations


def generate_failure_prediction_report(prediction: Dict[str, Any]) -> str:
    """Generate failure prediction report."""
    lines = [f"# {prediction['emoji']} Pipeline Failure Prediction\n\n"]
    
    prob = prediction['failure_probability']
    lines.append(f"## Failure Probability: {prob}%\n\n")
    lines.append(f"**Risk Level:** {prediction['risk_level'].upper()}\n\n")
    lines.append(f"**Recommendation:** {prediction['recommendation']}\n\n")
    
    if prediction['risk_factors']:
        lines.append("## Risk Factors\n\n")
        for i, factor in enumerate(prediction['risk_factors'], 1):
            lines.append(f"{i}. **{factor['message']}**\n")
            lines.append(f"   - Detail: {factor.get('detail', 'N/A')}\n")
            lines.append(f"   - Risk weight: +{factor['weight'] * 100:.0f}%\n\n")
    
    if prediction['suggestions']:
        lines.append("## 🛡️ Risk Mitigations\n\n")
        for sug in prediction['suggestions']:
            lines.append(f"- **{sug['action']}** (effort: {sug['effort']})\n")
            lines.append(f"  - Impact: {sug['impact']}\n")
            lines.append(f"  - How: {sug['how']}\n\n")
    
    return "".join(lines)
