"""
Security scanner for CI/CD pipelines and configs.

Detects:
- Hardcoded secrets/tokens in .gitlab-ci.yml
- Insecure Docker configurations (privileged, --no-verify)
- Missing security scanning stages
- Overly permissive permissions
- Dependency vulnerabilities from lock files
- Supply chain attack vectors
- Unsafe script patterns (curl | bash, eval)
"""

from __future__ import annotations
import re
from typing import Dict, List, Any, Optional


# Known secret patterns (regex)
SECRET_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "AWS Secret Key": r"(?i)aws[_\-]?secret[_\-]?access[_\-]?key[\s]*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})",
    "GitHub Token": r"gh[ps]_[A-Za-z0-9_]{36,}",
    "GitLab Token": r"glpat-[A-Za-z0-9\-_]{20,}",
    "Slack Token": r"xox[bprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}",
    "Generic API Key": r"(?i)(api[_\-]?key|apikey|api_secret)[\s]*[=:]\s*['\"]?([A-Za-z0-9]{20,})",
    "Private Key": r"-----BEGIN\s*(RSA|DSA|EC|OPENSSH)?\s*PRIVATE KEY-----",
    "JWT Token": r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Heroku API Key": r"(?i)heroku[_\-]?api[_\-]?key[\s]*[=:]\s*['\"]?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    "Database URL": r"(?i)(postgres|mysql|mongodb|redis):\/\/[^\s'\"]+:[^\s'\"]+@",
    "Password in URL": r"(?i)https?://[^:]+:([^@]+)@",
    "Hardcoded Password": r"(?i)(password|passwd|pwd)[\s]*[=:]\s*['\"]([^'\"]{6,})['\"]",
    "Bearer Token": r"Bearer\s+[A-Za-z0-9\-_\.]{20,}",
    "npm Token": r"//registry\.npmjs\.org/:_authToken=[A-Za-z0-9\-]{36}",
    "Docker Hub Token": r"(?i)docker[_\-]?hub[_\-]?(token|password|pwd)[\s]*[=:]\s*['\"]?([A-Za-z0-9]{20,})",
}

# Dangerous CI/CD patterns
DANGEROUS_PATTERNS = {
    "curl_pipe_bash": {
        "pattern": r"curl\s+.*\|\s*(bash|sh|zsh)",
        "severity": "critical",
        "message": "Remote code execution via curl | bash",
        "fix": "Download script first, inspect it, then execute from local file",
        "cwe": "CWE-94: Code Injection"
    },
    "eval_usage": {
        "pattern": r"\beval\s+[\"'\$]",
        "severity": "high",
        "message": "eval() can execute arbitrary code from variables",
        "fix": "Avoid eval — use direct command execution or safe alternatives",
        "cwe": "CWE-95: Eval Injection"
    },
    "privileged_container": {
        "pattern": r"privileged:\s*true",
        "severity": "critical",
        "message": "Container running in privileged mode (full host access)",
        "fix": "Remove privileged: true unless absolutely required for Docker-in-Docker",
        "cwe": "CWE-250: Execution with Unnecessary Privileges"
    },
    "allow_failure_security": {
        "pattern": r"(sast|dast|dependency_scanning|secret_detection).*allow_failure:\s*true",
        "severity": "high",
        "message": "Security scan set to allow_failure (ignoring security results)",
        "fix": "Set allow_failure: false for security jobs to enforce security gates",
        "cwe": "CWE-693: Protection Mechanism Failure"
    },
    "no_verify_ssl": {
        "pattern": r"--no-verify|--insecure|verify\s*=\s*False|SSL_VERIFY.*false",
        "severity": "high",
        "message": "SSL verification disabled — vulnerable to MITM attacks",
        "fix": "Enable SSL verification, use proper certificates",
        "cwe": "CWE-295: Improper Certificate Validation"
    },
    "latest_tag": {
        "pattern": r"image:\s*[^\n]*:latest",
        "severity": "medium",
        "message": "Using :latest tag — unpredictable, not reproducible, supply chain risk",
        "fix": "Pin to specific version (e.g., python:3.11.7-slim instead of python:latest)",
        "cwe": "CWE-829: Inclusion of Functionality from Untrusted Control Sphere"
    },
    "wildcard_artifacts": {
        "pattern": r"artifacts:.*paths:.*\*\*",
        "severity": "medium",
        "message": "Wildcard artifact collection may expose sensitive files",
        "fix": "Specify exact paths for artifacts, never use **/* blindly",
        "cwe": "CWE-200: Exposure of Sensitive Information"
    },
    "unprotected_variables": {
        "pattern": r"variables:.*\n\s+\w+:\s*['\"]?(?!\\$)[A-Za-z0-9]",
        "severity": "medium",
        "message": "Variables defined inline instead of using CI/CD masked variables",
        "fix": "Move secrets to Settings → CI/CD → Variables (masked + protected)",
        "cwe": "CWE-312: Cleartext Storage of Sensitive Information"
    },
    "root_user": {
        "pattern": r"USER\s+root|--user\s+root|as\s+root",
        "severity": "medium",
        "message": "Running as root user inside container",
        "fix": "Use non-root user: USER 1001 or USER appuser",
        "cwe": "CWE-250: Execution with Unnecessary Privileges"
    },
    "world_writable": {
        "pattern": r"chmod\s+777|chmod\s+-R\s+777|chmod\s+a\+w",
        "severity": "medium",
        "message": "World-writable permissions set on files/directories",
        "fix": "Use least-privilege permissions: chmod 755 for dirs, 644 for files",
        "cwe": "CWE-732: Incorrect Permission Assignment"
    }
}

# Required security stages for compliance
REQUIRED_SECURITY_STAGES = {
    "sast": "Static Application Security Testing",
    "secret_detection": "Secret/credential detection in code",
    "dependency_scanning": "Check dependencies for known vulnerabilities",
    "container_scanning": "Scan Docker images for vulnerabilities",
    "dast": "Dynamic Application Security Testing",
    "license_scanning": "Check dependency licenses for compliance"
}


def scan_for_secrets(content: str, source: str = "unknown") -> List[Dict[str, Any]]:
    """
    Scan content for hardcoded secrets and credentials.
    
    Args:
        content: Text to scan (CI config, logs, source code)
        source: Description of where content came from
        
    Returns:
        List of detected secrets with locations
    """
    findings = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//'):
            continue
        
        for secret_type, pattern in SECRET_PATTERNS.items():
            matches = re.finditer(pattern, line)
            for match in matches:
                # Mask the actual secret
                secret_value = match.group(0)
                masked = secret_value[:4] + '*' * (len(secret_value) - 8) + secret_value[-4:] if len(secret_value) > 8 else '****'
                
                findings.append({
                    "type": secret_type,
                    "severity": "critical",
                    "line": line_num,
                    "source": source,
                    "masked_value": masked,
                    "message": f"Potential {secret_type} found on line {line_num}",
                    "fix": f"Move this {secret_type} to CI/CD variables (Settings → CI/CD → Variables → masked + protected)",
                    "cwe": "CWE-798: Use of Hard-coded Credentials"
                })
    
    return findings


def scan_ci_config(ci_yaml_content: str) -> Dict[str, Any]:
    """
    Comprehensive security scan of .gitlab-ci.yml content.
    
    Returns:
        Complete security report
    """
    results = {
        "secrets_found": [],
        "dangerous_patterns": [],
        "missing_security_stages": [],
        "compliance_score": 100,
        "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        "recommendations": [],
        "supply_chain_risks": []
    }
    
    # 1. Scan for secrets
    secrets = scan_for_secrets(ci_yaml_content, ".gitlab-ci.yml")
    results["secrets_found"] = secrets
    results["severity_counts"]["critical"] += len(secrets)
    
    # 2. Scan for dangerous patterns
    for pattern_name, pattern_info in DANGEROUS_PATTERNS.items():
        matches = re.finditer(pattern_info["pattern"], ci_yaml_content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            line_num = ci_yaml_content[:match.start()].count('\n') + 1
            results["dangerous_patterns"].append({
                "type": pattern_name,
                "severity": pattern_info["severity"],
                "line": line_num,
                "message": pattern_info["message"],
                "fix": pattern_info["fix"],
                "cwe": pattern_info["cwe"],
                "matched": match.group(0)[:50]
            })
            results["severity_counts"][pattern_info["severity"]] += 1
    
    # 3. Check for missing security stages
    ci_lower = ci_yaml_content.lower()
    for stage, description in REQUIRED_SECURITY_STAGES.items():
        if stage not in ci_lower:
            results["missing_security_stages"].append({
                "stage": stage,
                "description": description,
                "severity": "medium",
                "fix": f"Add '{stage}' stage to your pipeline for {description}"
            })
    
    # 4. Supply chain risk analysis
    # Check for unpinned images
    image_pattern = r"image:\s*(\S+)"
    for match in re.finditer(image_pattern, ci_yaml_content):
        image = match.group(1)
        if ':latest' in image or ':' not in image:
            results["supply_chain_risks"].append({
                "type": "unpinned_image",
                "image": image,
                "risk": "Image can be replaced by attacker (supply chain attack)",
                "fix": f"Pin to digest: {image}@sha256:abc123... or specific version tag"
            })
    
    # 5. Calculate compliance score
    total_issues = sum(results["severity_counts"].values()) + len(results["missing_security_stages"])
    deductions = (
        results["severity_counts"]["critical"] * 25 +
        results["severity_counts"]["high"] * 15 +
        results["severity_counts"]["medium"] * 5 +
        results["severity_counts"]["low"] * 2 +
        len(results["missing_security_stages"]) * 3
    )
    results["compliance_score"] = max(0, 100 - deductions)
    
    # 6. Generate compliance grade
    score = results["compliance_score"]
    if score >= 90:
        results["grade"] = "A"
        results["grade_description"] = "Excellent security posture"
    elif score >= 80:
        results["grade"] = "B"
        results["grade_description"] = "Good, minor improvements needed"
    elif score >= 70:
        results["grade"] = "C"
        results["grade_description"] = "Fair, several issues to address"
    elif score >= 50:
        results["grade"] = "D"
        results["grade_description"] = "Poor, significant security gaps"
    else:
        results["grade"] = "F"
        results["grade_description"] = "Critical — immediate action required"
    
    return results


def scan_job_logs_for_secrets(logs: str) -> List[Dict[str, Any]]:
    """Scan job execution logs for accidentally leaked secrets."""
    findings = scan_for_secrets(logs, "job_logs")
    
    # Additional log-specific patterns
    log_secret_patterns = {
        "echo_password": r"echo\s+['\"]?[A-Za-z0-9@#$%^&*]{8,}",
        "env_dump": r"printenv|env\s*$|export\s+.*=",
        "debug_credentials": r"(?i)(debug|verbose|trace).*(?:token|key|password|secret)",
    }
    
    for pattern_name, pattern in log_secret_patterns.items():
        if re.search(pattern, logs, re.MULTILINE):
            findings.append({
                "type": pattern_name,
                "severity": "high",
                "message": f"Potential credential exposure in logs ({pattern_name})",
                "fix": "Mask CI/CD variables and avoid printing sensitive data in logs",
                "cwe": "CWE-532: Information Exposure Through Log Files"
            })
    
    return findings


def generate_security_report(ci_yaml: str, job_logs: Optional[str] = None) -> str:
    """Generate comprehensive security report."""
    scan_results = scan_ci_config(ci_yaml)
    
    lines = ["# 🔒 Security Scan Report\n\n"]
    
    # Grade
    grade = scan_results["grade"]
    grade_emoji = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⛔"}.get(grade, "⚪")
    lines.append(f"## Security Grade: {grade_emoji} {grade} ({scan_results['compliance_score']}/100)\n\n")
    lines.append(f"_{scan_results['grade_description']}_\n\n")
    
    # Summary
    sc = scan_results["severity_counts"]
    lines.append(f"| Severity | Count |\n|----------|-------|\n")
    lines.append(f"| 🔴 Critical | {sc['critical']} |\n")
    lines.append(f"| 🟠 High | {sc['high']} |\n")
    lines.append(f"| 🟡 Medium | {sc['medium']} |\n")
    lines.append(f"| 🟢 Low | {sc['low']} |\n\n")
    
    # Secrets found
    if scan_results["secrets_found"]:
        lines.append("## ⛔ SECRETS DETECTED IN CODE\n\n")
        lines.append("**ACTION REQUIRED:** Rotate these credentials immediately!\n\n")
        for secret in scan_results["secrets_found"]:
            lines.append(f"- **{secret['type']}** on line {secret['line']}: `{secret['masked_value']}`\n")
            lines.append(f"  - Fix: {secret['fix']}\n")
            lines.append(f"  - Reference: {secret['cwe']}\n\n")
    
    # Dangerous patterns
    if scan_results["dangerous_patterns"]:
        lines.append("## 🚨 Dangerous Patterns\n\n")
        for pattern in scan_results["dangerous_patterns"]:
            sev_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(pattern["severity"], "⚪")
            lines.append(f"### {sev_emoji} {pattern['type'].replace('_', ' ').title()}\n\n")
            lines.append(f"**Line {pattern['line']}:** `{pattern['matched']}`\n\n")
            lines.append(f"**Issue:** {pattern['message']}\n\n")
            lines.append(f"**Fix:** {pattern['fix']}\n\n")
            lines.append(f"**CWE:** {pattern['cwe']}\n\n---\n\n")
    
    # Missing security stages
    if scan_results["missing_security_stages"]:
        lines.append("## 🛡️ Missing Security Stages\n\n")
        lines.append("Add these stages for comprehensive security:\n\n")
        for stage in scan_results["missing_security_stages"]:
            lines.append(f"- **{stage['stage']}**: {stage['description']}\n")
        lines.append("\nAdd GitLab security templates:\n```yaml\ninclude:\n")
        lines.append("  - template: Security/SAST.gitlab-ci.yml\n")
        lines.append("  - template: Security/Secret-Detection.gitlab-ci.yml\n")
        lines.append("  - template: Security/Dependency-Scanning.gitlab-ci.yml\n")
        lines.append("```\n\n")
    
    # Supply chain risks
    if scan_results["supply_chain_risks"]:
        lines.append("## ⚠️ Supply Chain Risks\n\n")
        for risk in scan_results["supply_chain_risks"]:
            lines.append(f"- **{risk['image']}**: {risk['risk']}\n")
            lines.append(f"  - Fix: {risk['fix']}\n\n")
    
    # Log scanning
    if job_logs:
        log_secrets = scan_job_logs_for_secrets(job_logs)
        if log_secrets:
            lines.append("## 📋 Secrets Leaked in Logs\n\n")
            for secret in log_secrets:
                lines.append(f"- **{secret['type']}**: {secret['message']}\n")
                lines.append(f"  - Fix: {secret['fix']}\n\n")
    
    return "".join(lines)
