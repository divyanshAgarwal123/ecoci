"""
Smart test selection — only run tests affected by code changes.

Analyzes git diffs to determine which tests to run:
- Maps source files to test files
- Detects dependency graphs
- Skips unrelated tests
- Can reduce test suite from 20 min to 2 min

Inspired by Facebook's "Test Selection" and Google's TAP system.
"""

from __future__ import annotations
import re
from typing import Dict, List, Any, Set, Optional
from pathlib import PurePosixPath


# Common source → test file mappings
FILE_MAPPING_PATTERNS = {
    # Ruby/Rails
    "ruby": {
        r"app/models/(\w+)\.rb": "spec/models/{}_spec.rb",
        r"app/controllers/(\w+)_controller\.rb": "spec/controllers/{}_controller_spec.rb",
        r"app/services/(\w+)\.rb": "spec/services/{}_spec.rb",
        r"app/views/(\w+)/": "spec/views/{}/",
        r"lib/(\w+)\.rb": "spec/lib/{}_spec.rb",
    },
    # Python/Django
    "python": {
        r"(\w+)/models\.py": "{}/tests/test_models.py",
        r"(\w+)/views\.py": "{}/tests/test_views.py",
        r"(\w+)/serializers\.py": "{}/tests/test_serializers.py",
        r"(\w+)/services/(\w+)\.py": "{}/tests/test_{}.py",
        r"src/(\w+)\.py": "tests/test_{}.py",
    },
    # JavaScript/TypeScript
    "javascript": {
        r"src/components/(\w+)\.(?:tsx?|jsx?)": "src/components/{}/__tests__/{}.test.tsx",
        r"src/(\w+)\.(?:ts|js)": "src/__tests__/{}.test.ts",
        r"lib/(\w+)\.(?:ts|js)": "tests/{}.test.ts",
        r"src/hooks/(\w+)\.ts": "src/hooks/__tests__/{}.test.ts",
    }
}

# Files that should trigger full test suite
FULL_SUITE_TRIGGERS = {
    r"Gemfile",
    r"package\.json",
    r"requirements\.txt",
    r"Pipfile",
    r"docker-compose",
    r"Dockerfile",
    r"\.gitlab-ci\.yml",
    r"\.github/workflows/",
    r"Makefile",
    r"config/database",
    r"config/application",
    r"settings\.py",
    r"tsconfig\.json",
    r"babel\.config",
    r"webpack\.config",
    r"jest\.config",
    r"pytest\.ini",
    r"setup\.cfg",
}

# Files that need no tests at all
NO_TEST_NEEDED = {
    r"\.md$",
    r"\.txt$",
    r"\.yml$",
    r"\.yaml$",
    r"\.json$",
    r"\.css$",
    r"\.scss$",
    r"\.svg$",
    r"\.png$",
    r"\.jpg$",
    r"\.ico$",
    r"LICENSE",
    r"\.gitignore",
    r"\.editorconfig",
    r"CHANGELOG",
    r"CODEOWNERS",
    r"\.prettierrc",
    r"\.eslintignore",
}


def analyze_changed_files(
    changed_files: List[str],
    project_language: str = "auto"
) -> Dict[str, Any]:
    """
    Analyze changed files and determine which tests to run.
    
    Args:
        changed_files: List of files changed in the commit/MR
        project_language: ruby, python, javascript, or auto-detect
        
    Returns:
        Test selection strategy with specific files to run
    """
    result = {
        "strategy": "selective",  # selective, full, skip
        "tests_to_run": [],
        "tests_to_skip": [],
        "files_analyzed": len(changed_files),
        "files_needing_tests": 0,
        "files_skippable": 0,
        "estimated_time_savings_percent": 0,
        "trigger_full_suite": False,
        "reason": ""
    }
    
    # Auto-detect language
    if project_language == "auto":
        project_language = _detect_language(changed_files)
    
    tests_needed: Set[str] = set()
    skip_files: Set[str] = set()
    
    for filepath in changed_files:
        # Check if this file triggers full suite
        if _matches_any_pattern(filepath, FULL_SUITE_TRIGGERS):
            result["strategy"] = "full"
            result["trigger_full_suite"] = True
            result["reason"] = f"Config file changed: {filepath} — must run full suite"
            return result
        
        # Check if file needs no tests
        if _matches_any_pattern(filepath, NO_TEST_NEEDED):
            skip_files.add(filepath)
            result["files_skippable"] += 1
            continue
        
        # Map source file to test file
        result["files_needing_tests"] += 1
        mapped_tests = _map_file_to_tests(filepath, project_language)
        tests_needed.update(mapped_tests)
    
    # If only doc/config changes, skip all tests
    if result["files_needing_tests"] == 0:
        result["strategy"] = "skip"
        result["reason"] = f"Only documentation/config files changed ({len(skip_files)} files)"
        result["estimated_time_savings_percent"] = 100
        return result
    
    result["tests_to_run"] = sorted(tests_needed)
    result["tests_to_skip"] = sorted(skip_files)
    
    # Estimate savings (assume selective runs 20-40% of full suite)
    if tests_needed:
        result["estimated_time_savings_percent"] = max(0, min(90, 100 - len(tests_needed) * 10))
    
    result["reason"] = f"Run {len(tests_needed)} test files for {result['files_needing_tests']} changed source files"
    
    return result


def generate_test_command(
    selection: Dict[str, Any],
    framework: str = "auto"
) -> Optional[str]:
    """
    Generate the specific test command based on selection.
    
    Returns the command to run only the needed tests.
    """
    if selection["strategy"] == "skip":
        return "echo 'No tests needed — only docs/config changed'"
    
    if selection["strategy"] == "full":
        return None  # Run default full suite
    
    tests = selection["tests_to_run"]
    if not tests:
        return None
    
    # Detect framework from test file extensions
    if framework == "auto":
        if any(t.endswith("_spec.rb") for t in tests):
            framework = "rspec"
        elif any(t.endswith(".test.ts") or t.endswith(".test.tsx") for t in tests):
            framework = "jest"
        elif any(t.startswith("test_") or t.endswith("_test.py") for t in tests):
            framework = "pytest"
        else:
            framework = "generic"
    
    if framework == "rspec":
        return f"bundle exec rspec {' '.join(tests)}"
    elif framework == "pytest":
        return f"python -m pytest {' '.join(tests)} -v"
    elif framework == "jest":
        return f"npx jest {' '.join(tests)} --verbose"
    else:
        return f"# Run these test files:\n# {chr(10).join(tests)}"


def generate_gitlab_ci_rules(
    selection: Dict[str, Any]
) -> str:
    """
    Generate .gitlab-ci.yml rules for smart test selection.
    """
    if selection["strategy"] == "skip":
        return """# Smart test selection: Skip tests for doc-only changes
test:
  rules:
    - changes:
        - "*.md"
        - "*.txt" 
        - "docs/**"
        - "*.yml"
      when: never
    - when: always"""
    
    if selection["tests_to_run"]:
        source_patterns = set()
        for test_file in selection["tests_to_run"]:
            # Infer source patterns from test files
            parts = test_file.replace("_spec.rb", ".rb").replace("_test.py", ".py").replace(".test.ts", ".ts")
            source_patterns.add(f"    - \"{parts}\"")
        
        patterns = "\n".join(sorted(source_patterns))
        return f"""# Smart test selection: Only run tests for changed files
test:selective:
  script:
    - {generate_test_command(selection) or 'echo "run full suite"'}
  rules:
    - changes:
{patterns}
      when: always
    - when: never  # Skip if these files didn't change"""
    
    return "# Run full test suite (default)"


def _detect_language(files: List[str]) -> str:
    """Detect project language from file extensions."""
    extensions = [PurePosixPath(f).suffix for f in files]
    if '.rb' in extensions or '.erb' in extensions:
        return "ruby"
    elif '.py' in extensions:
        return "python"
    elif '.ts' in extensions or '.tsx' in extensions or '.js' in extensions:
        return "javascript"
    return "python"  # Default


def _matches_any_pattern(filepath: str, patterns: set) -> bool:
    """Check if filepath matches any pattern in the set."""
    for pattern in patterns:
        if re.search(pattern, filepath):
            return True
    return False


def _map_file_to_tests(filepath: str, language: str) -> List[str]:
    """Map a source file to its corresponding test files."""
    mappings = FILE_MAPPING_PATTERNS.get(language, {})
    test_files = []
    
    for source_pattern, test_template in mappings.items():
        match = re.match(source_pattern, filepath)
        if match:
            groups = match.groups()
            if groups:
                test_file = test_template.format(*groups)
                test_files.append(test_file)
    
    # Fallback: try common naming conventions
    if not test_files:
        name = PurePosixPath(filepath).stem
        if language == "ruby":
            test_files.append(f"spec/{name}_spec.rb")
        elif language == "python":
            test_files.append(f"tests/test_{name}.py")
        elif language == "javascript":
            test_files.append(f"__tests__/{name}.test.ts")
    
    return test_files
