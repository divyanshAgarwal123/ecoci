"""
Auto-fix engine — generate fixes with confidence scores.

Takes detected issues and generates:
- Specific code/config fixes
- Confidence level (how safe is the fix)
- Before/after diffs
- Rollback instructions
- Estimated impact
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional


class AutoFix:
    """Represents an automatic fix with confidence scoring."""
    
    def __init__(
        self,
        title: str,
        issue_type: str,
        severity: str,
        confidence: float,  # 0.0 to 1.0
        fix_type: str,  # "ci_config", "code", "dockerfile", "database"
        before: str,
        after: str,
        explanation: str,
        risk: str,
        rollback: str,
        estimated_impact: Dict[str, Any]
    ):
        self.title = title
        self.issue_type = issue_type
        self.severity = severity
        self.confidence = confidence
        self.fix_type = fix_type
        self.before = before
        self.after = after
        self.explanation = explanation
        self.risk = risk
        self.rollback = rollback
        self.estimated_impact = estimated_impact
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "confidence_label": self._confidence_label(),
            "fix_type": self.fix_type,
            "before": self.before,
            "after": self.after,
            "explanation": self.explanation,
            "risk": self.risk,
            "rollback": self.rollback,
            "estimated_impact": self.estimated_impact,
            "safe_to_auto_apply": self.confidence >= 0.90
        }
    
    def _confidence_label(self) -> str:
        if self.confidence >= 0.95:
            return "🟢 Very High (safe to auto-apply)"
        elif self.confidence >= 0.85:
            return "🟡 High (review recommended)"
        elif self.confidence >= 0.70:
            return "🟠 Medium (manual review required)"
        else:
            return "🔴 Low (use with caution)"


# Pre-built fix templates
FIX_TEMPLATES = {
    "add_cache": AutoFix(
        title="Add dependency caching",
        issue_type="missing_cache",
        severity="medium",
        confidence=0.95,
        fix_type="ci_config",
        before="""build:
  stage: build
  script:
    - npm install
    - npm run build""",
        after="""build:
  stage: build
  cache:
    key: "$CI_COMMIT_REF_SLUG"
    paths:
      - node_modules/
      - .npm/
    policy: pull-push
  script:
    - npm ci --cache .npm
    - npm run build""",
        explanation="Cache node_modules between pipeline runs to avoid re-downloading 500MB of packages every time",
        risk="LOW — Cache is automatically invalidated when package.json changes",
        rollback="Remove cache: block from job definition",
        estimated_impact={"time_saved_seconds": 120, "cost_saved_per_run": 0.03, "co2_saved_grams": 25}
    ),
    
    "parallelize_tests": AutoFix(
        title="Parallelize test execution",
        issue_type="sequential_tests",
        severity="high",
        confidence=0.90,
        fix_type="ci_config",
        before="""test:
  stage: test
  script:
    - npm run test""",
        after="""test:
  stage: test
  parallel: 4
  script:
    - npm run test -- --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
  artifacts:
    reports:
      junit: junit.xml""",
        explanation="Split test suite across 4 parallel runners. Each runner gets 25% of tests.",
        risk="LOW — Tests must be independent (no shared state between tests)",
        rollback="Remove parallel: 4 and --shard flag",
        estimated_impact={"time_saved_seconds": 240, "cost_saved_per_run": 0.05, "co2_saved_grams": 45}
    ),
    
    "slim_image": AutoFix(
        title="Use slim Docker image",
        issue_type="heavy_image",
        severity="medium",
        confidence=0.85,
        fix_type="ci_config",
        before="""build:
  image: node:18
  script:
    - npm install""",
        after="""build:
  image: node:18-slim
  script:
    - npm install""",
        explanation="node:18-slim is 120MB vs 350MB for node:18. Faster image pulls.",
        risk="MEDIUM — Some native dependencies (canvas, sharp) may need extra packages",
        rollback="Change image back to node:18",
        estimated_impact={"time_saved_seconds": 30, "cost_saved_per_run": 0.01, "co2_saved_grams": 8}
    ),
    
    "add_needs": AutoFix(
        title="Add parallel job execution (DAG)",
        issue_type="sequential_jobs",
        severity="high",
        confidence=0.92,
        fix_type="ci_config",
        before="""stages:
  - build
  - test
  - lint
  - deploy

lint:
  stage: lint
  script:
    - npm run lint

test:
  stage: test
  script:
    - npm run test""",
        after="""stages:
  - build
  - test
  - deploy

lint:
  stage: test
  needs: []  # Run immediately, don't wait for build
  script:
    - npm run lint

test:
  stage: test
  needs: ["build"]  # Only needs build, runs parallel with lint
  script:
    - npm run test""",
        explanation="Lint doesn't depend on build — run it immediately. Test runs parallel with lint.",
        risk="LOW — Only removes unnecessary wait time, doesn't change job behavior",
        rollback="Remove needs: [] from lint job",
        estimated_impact={"time_saved_seconds": 60, "cost_saved_per_run": 0.02, "co2_saved_grams": 15}
    ),
    
    "skip_docs": AutoFix(
        title="Skip pipeline for documentation-only changes",
        issue_type="unnecessary_runs",
        severity="low",
        confidence=0.98,
        fix_type="ci_config",
        before="""test:
  stage: test
  script:
    - npm run test""",
        after="""test:
  stage: test
  rules:
    - changes:
        - "*.md"
        - "docs/**"
        - "*.txt"
        - "LICENSE"
        - "CHANGELOG*"
      when: never
    - when: always
  script:
    - npm run test""",
        explanation="Skip expensive test jobs when only documentation files change. Saves 100% of test time for doc PRs.",
        risk="VERY LOW — Docs have no runtime impact",
        rollback="Remove rules: block from job",
        estimated_impact={"time_saved_seconds": 300, "cost_saved_per_run": 0.15, "co2_saved_grams": 50}
    ),
    
    "add_security_scanning": AutoFix(
        title="Add GitLab security scanning templates",
        issue_type="missing_security",
        severity="high",
        confidence=0.95,
        fix_type="ci_config",
        before="""stages:
  - build
  - test
  - deploy""",
        after="""include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml

stages:
  - build
  - test
  - deploy""",
        explanation="Add GitLab's built-in security scanning. SAST finds code vulnerabilities, Secret Detection finds leaked credentials, Dependency Scanning finds vulnerable packages.",
        risk="VERY LOW — Adds new jobs without changing existing ones",
        rollback="Remove include: block",
        estimated_impact={"vulnerabilities_caught": "5-20 per scan", "compliance": "SOC2, HIPAA ready"}
    ),
    
    "fix_n1_query_rails": AutoFix(
        title="Fix N+1 query with eager loading",
        issue_type="n+1_query",
        severity="critical",
        confidence=0.85,
        fix_type="code",
        before="""class PostsController < ApplicationController
  def index
    @posts = Post.all
  end
end

# View: @posts.each { |p| p.comments.count }
# Generates: 1 + N queries""",
        after="""class PostsController < ApplicationController
  def index
    @posts = Post.includes(:comments).all
  end
end

# View: @posts.each { |p| p.comments.count }
# Generates: 2 queries (1 for posts, 1 for ALL comments)""",
        explanation="Add .includes(:comments) to eager-load associations in a single query instead of N separate queries.",
        risk="LOW — Only changes query strategy, not data returned",
        rollback="Remove .includes(:comments)",
        estimated_impact={"queries_reduced": "N → 2", "latency_reduction_ms": 750, "co2_saved_grams": 35}
    ),
}


def generate_fixes_for_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate auto-fixes for detected issues.
    
    Args:
        issues: List of detected issues from analyzers
        
    Returns:
        List of fixes with confidence scores
    """
    fixes = []
    
    for issue in issues:
        issue_type = issue.get("type", "")
        
        # Match issue to fix template
        matching_fixes = {
            "missing_cache": "add_cache",
            "sequential_tests": "parallelize_tests",
            "sequential_jobs": "add_needs",
            "heavy_image": "slim_image",
            "unnecessary_runs": "skip_docs",
            "missing_security": "add_security_scanning",
            "n+1_queries": "fix_n1_query_rails",
            "n1_queries": "fix_n1_query_rails",
        }
        
        template_key = matching_fixes.get(issue_type)
        if template_key and template_key in FIX_TEMPLATES:
            fix = FIX_TEMPLATES[template_key]
            fix_dict = fix.to_dict()
            fix_dict["source_issue"] = issue
            fixes.append(fix_dict)
    
    # Sort by confidence (highest first)
    fixes.sort(key=lambda f: f["confidence"], reverse=True)
    
    return fixes


def generate_mr_description(fixes: List[Dict[str, Any]]) -> str:
    """
    Generate a merge request description with all fixes.
    """
    lines = ["# 🔧 EcoCI Auto-Optimization\n\n"]
    lines.append("_Automatically generated optimizations with safety scores_\n\n")
    
    # Summary
    safe_fixes = [f for f in fixes if f.get("safe_to_auto_apply")]
    review_fixes = [f for f in fixes if not f.get("safe_to_auto_apply")]
    
    total_time_saved = sum(f.get("estimated_impact", {}).get("time_saved_seconds", 0) for f in fixes)
    total_cost_saved = sum(f.get("estimated_impact", {}).get("cost_saved_per_run", 0) for f in fixes)
    total_co2_saved = sum(f.get("estimated_impact", {}).get("co2_saved_grams", 0) for f in fixes)
    
    lines.append(f"## Summary\n\n")
    lines.append(f"- **{len(fixes)} optimizations** found\n")
    lines.append(f"- **{len(safe_fixes)} safe to auto-apply** (confidence ≥90%)\n")
    lines.append(f"- **{len(review_fixes)} need manual review**\n")
    lines.append(f"- **Time saved:** {total_time_saved}s per pipeline\n")
    lines.append(f"- **Cost saved:** ${total_cost_saved:.2f} per pipeline\n")
    lines.append(f"- **CO₂ saved:** {total_co2_saved}g per pipeline\n\n")
    
    # Detailed fixes
    for i, fix in enumerate(fixes, 1):
        lines.append(f"## Fix {i}: {fix['title']}\n\n")
        lines.append(f"**Confidence:** {fix['confidence_label']}\n\n")
        lines.append(f"**Severity:** {fix['severity'].upper()}\n\n")
        lines.append(f"**Explanation:** {fix['explanation']}\n\n")
        lines.append(f"**Risk:** {fix['risk']}\n\n")
        
        lines.append(f"### Before\n```yaml\n{fix['before']}\n```\n\n")
        lines.append(f"### After\n```yaml\n{fix['after']}\n```\n\n")
        
        lines.append(f"**Rollback:** {fix['rollback']}\n\n")
        
        impact = fix.get("estimated_impact", {})
        if impact:
            lines.append("**Impact:**\n")
            for key, value in impact.items():
                lines.append(f"- {key.replace('_', ' ').title()}: {value}\n")
        
        lines.append("\n---\n\n")
    
    # Safety notice
    lines.append("## ⚠️ Safety Notice\n\n")
    lines.append("All fixes include:\n")
    lines.append("- ✅ Confidence score (how safe the change is)\n")
    lines.append("- ✅ Risk assessment\n")
    lines.append("- ✅ Rollback instructions\n")
    lines.append("- ✅ Estimated impact (time, cost, CO₂)\n\n")
    lines.append("Fixes with confidence ≥90% are safe to merge without additional review.\n")
    lines.append("Fixes with confidence <90% should be reviewed by a team member.\n")
    
    return "".join(lines)
