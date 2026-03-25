# EcoCI — Autonomous CI/CD Optimization Suite

EcoCI is a Python-based optimization suite for GitLab CI/CD workflows.
It combines pipeline analysis, performance diagnostics, security checks, reliability heuristics, cost/ROI modeling, and carbon estimation into one system that can produce implementation-ready improvements.

This repository includes:

- a GitLab Duo Agent definition,
- a reusable Python package and CLI,
- GitLab API automation for branch/commit/MR workflows,
- optional Google Cloud analytics integrations,
- demo assets and a deliberately problematic sample project.

---

## 1) What EcoCI is

EcoCI is not a single script. It is a multi-surface platform with four operating modes:

1. **Duo Agent mode** using [agents/agent.yml](agents/agent.yml)  
  Conversational analysis and tool-driven optimization logic.
2. **Python automation mode** using [scripts/ecoci/main.py](scripts/ecoci/main.py)  
  End-to-end pipeline analysis + MR creation via GitLab API.
3. **CLI mode** using [scripts/ecoci/cli.py](scripts/ecoci/cli.py)  
  Modular local commands for security, DORA, cost, prediction, flaky tests, and more.
4. **Webhook service mode** using [scripts/ecoci/webhook_trigger.py](scripts/ecoci/webhook_trigger.py) + [Dockerfile](Dockerfile)  
  Cloud Run-ready service for event-driven execution.

---

## 2) What problem it solves

EcoCI targets common CI/CD inefficiencies and delivery risks:

- long pipelines due to missing caches and weak parallelism,
- risky CI patterns (secrets, insecure scripts, privileged jobs),
- flaky tests and avoidable failure patterns,
- expensive runner usage and avoidable developer wait costs,
- hidden application-level bottlenecks visible in CI logs,
- missing visibility into emissions and optimization impact over time.

---

## 3) How it works (end-to-end)

Typical automated run flow:

1. Fetch project and pipeline context via GitLab API.
2. Read `.gitlab-ci.yml` and job metadata/logs.
3. Run analyzers (CI graph, security, flaky tests, DORA, cost, failure prediction, performance).
4. Estimate emissions with assumptions:

  $$
  	ext{energy (kWh)} = \frac{\text{duration\_seconds}}{3600} \times \text{cpu\_cores} \times \text{kWh\_per\_core\_hour}
  $$

  $$
  	ext{CO2 (kg)} = \text{energy (kWh)} \times \text{carbon\_intensity\_kg\_per\_kWh}
  $$

5. Generate optimized CI config candidates and fix recommendations.
6. Create branch, commit, merge request, and optional carbon dashboard comment.

Core execution entrypoint: [scripts/ecoci/main.py](scripts/ecoci/main.py)

---

## 4) Why EcoCI is better for this use case

| Area | Manual / generic workflow | EcoCI approach |
|---|---|---|
| Data ingestion | Human copy-paste of config and logs | Structured API + parser + analyzer pipeline |
| Scope | One issue at a time | Cost, performance, reliability, security, carbon, delivery metrics |
| Output quality | Advice-only | Actionable recommendations and automation-ready outputs |
| Operationalization | Ad hoc | CLI, CI job, webhook, and MR workflows |

---

## 5) Complete module inventory

All core modules are in [scripts/ecoci](scripts/ecoci).

### Orchestration and platform

- [scripts/ecoci/main.py](scripts/ecoci/main.py): end-to-end run orchestration.
- [scripts/ecoci/cli.py](scripts/ecoci/cli.py): command-line interface (`security`, `cost`, `dora`, `predict`, `flaky`, `tests`, `fix`, `report`, `version`).
- [scripts/ecoci/config.py](scripts/ecoci/config.py): environment-driven runtime config.
- [scripts/ecoci/gitlab_client.py](scripts/ecoci/gitlab_client.py): typed GitLab REST API wrapper.
- [scripts/ecoci/mr_creator.py](scripts/ecoci/mr_creator.py): branch/commit/MR creation and MR dashboard notes.
- [scripts/ecoci/webhook_trigger.py](scripts/ecoci/webhook_trigger.py): pipeline-trigger utility and HTTP webhook server.

### Optimization and analysis engines

- [scripts/ecoci/ci_analyzer.py](scripts/ecoci/ci_analyzer.py): CI YAML parsing, DAG analysis, runner/tag heuristics, recommendations.
- [scripts/ecoci/optimizer.py](scripts/ecoci/optimizer.py): conservative CI transformations (`cache`, image pinning map, `rules:changes`).
- [scripts/ecoci/carbon_calculator.py](scripts/ecoci/carbon_calculator.py): per-job and total energy/CO2 estimation.
- [scripts/ecoci/code_performance_analyzer.py](scripts/ecoci/code_performance_analyzer.py): slow-test and anti-pattern detection from logs + Docker analysis.
- [scripts/ecoci/cost_analyzer.py](scripts/ecoci/cost_analyzer.py): runner spend, monthly projections, productivity loss, ROI, benchmark comparison.
- [scripts/ecoci/production_impact_predictor.py](scripts/ecoci/production_impact_predictor.py): production risk estimation for N+1, slow queries, memory, timeout, scalability.
- [scripts/ecoci/security_scanner.py](scripts/ecoci/security_scanner.py): secret scanning, dangerous pattern detection, compliance grading.
- [scripts/ecoci/flaky_test_detector.py](scripts/ecoci/flaky_test_detector.py): flaky signal extraction and business cost modeling.
- [scripts/ecoci/dora_metrics.py](scripts/ecoci/dora_metrics.py): full DORA classification and report generation.
- [scripts/ecoci/smart_test_selector.py](scripts/ecoci/smart_test_selector.py): change-aware test targeting and CI rule generation.
- [scripts/ecoci/failure_predictor.py](scripts/ecoci/failure_predictor.py): pre-run failure risk scoring from change characteristics.
- [scripts/ecoci/auto_fix_engine.py](scripts/ecoci/auto_fix_engine.py): fix templates with confidence labels, rollback guidance, impact estimates.

### Optional cloud analytics

- [scripts/ecoci/gcp_integration.py](scripts/ecoci/gcp_integration.py): BigQuery persistence, region-aware carbon intensity, trends query helpers.
- [scripts/ecoci/gcp_config.json](scripts/ecoci/gcp_config.json): cloud integration defaults.

---

## 6) Repository map

### Core runtime

- [agents/agent.yml](agents/agent.yml): Duo Agent definition and operating instructions.
- [.gitlab-ci.yml](.gitlab-ci.yml): `ecoci_runner` CI job and runtime variables.
- [Dockerfile](Dockerfile): containerized webhook deployment target.

### Scripts and utilities

- [scripts/test_all_modules.py](scripts/test_all_modules.py): broad module smoke/integration demo script.
- [scripts/test_business_value.py](scripts/test_business_value.py): cost and production impact demonstration.
- [scripts/test_performance_analyzer.py](scripts/test_performance_analyzer.py): code performance analysis demonstration.
- [scripts/setup_bigquery.sh](scripts/setup_bigquery.sh): BigQuery dataset/table bootstrap.
- [scripts/deploy_cloud_run.sh](scripts/deploy_cloud_run.sh): Cloud Run deployment helper.
- [scripts/insert_sample_data.py](scripts/insert_sample_data.py): sample BigQuery data insertion.

### Demo assets

- [demo/bad-gitlab-ci.yml](demo/bad-gitlab-ci.yml): intentionally inefficient CI config.
- [demo/optimized-gitlab-ci.yml](demo/optimized-gitlab-ci.yml): optimized reference config.
- [demo/DEMO_GUIDE.md](demo/DEMO_GUIDE.md): walkthrough of optimization techniques.

### Sample target application

- [ecoci-test-project](ecoci-test-project): Node.js sample app with intentionally embedded CI/code issues.
- [ecoci-test-project/src/index.js](ecoci-test-project/src/index.js): includes N+1 pattern, slow blocking function, and memory pressure pattern.
- [ecoci-test-project/src/index.test.js](ecoci-test-project/src/index.test.js): includes intentionally slow/flaky/race-prone tests.

### CI coverage in GitHub

- [.github/workflows/test.yml](.github/workflows/test.yml): matrix tests on Python 3.10/3.11/3.12 with CLI smoke checks.

### Documentation set

- [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)
- [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
- [CODE_PERFORMANCE_ANALYSIS.md](CODE_PERFORMANCE_ANALYSIS.md)
- [CLOUD_INTEGRATION.md](CLOUD_INTEGRATION.md)
- [GCP_QUICKSTART.md](GCP_QUICKSTART.md)
- [ANTHROPIC_INTEGRATION.md](ANTHROPIC_INTEGRATION.md)

---

## 7) Installation and setup

### Prerequisites

- Python 3.10+ (project metadata allows 3.9+)
- GitLab token with API access for write automation features
- Optional Google Cloud project for BigQuery/cloud workflows

### Install

```bash
git clone <repo-url>
cd 34560917
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Dependencies are defined in [requirements.txt](requirements.txt) and [pyproject.toml](pyproject.toml).

---

## 8) Configuration

Main environment variables:

| Variable | Required | Purpose | Default |
|---|---|---|---|
| `GITLAB_TOKEN` | Yes (for API actions) | Auth for GitLab API calls | none |
| `GITLAB_BASE_URL` | No | GitLab base URL | `https://gitlab.com` |
| `CARBON_INTENSITY_KG_PER_KWH` | No | Carbon intensity factor | `0.475` |
| `DEFAULT_RUNNER_CPU_CORES` | No | CPU core assumption for emissions | `2` |
| `KWH_PER_CORE_HOUR` | No | Energy factor per core-hour | `0.5` |
| `GCP_PROJECT_ID` | Optional | Enable GCP integration | none |
| `BIGQUERY_DATASET` | Optional | BigQuery dataset | `ecoci_metrics` |
| `GCP_SERVICE_ACCOUNT_KEY` | Optional | Service account JSON string | none |

See [scripts/ecoci/config.py](scripts/ecoci/config.py) and [scripts/ecoci/gcp_integration.py](scripts/ecoci/gcp_integration.py).

---

## 9) Usage

### A) Full pipeline automation

```bash
python -m scripts.ecoci.main \
  --project-id <gitlab_project_id> \
  --pipeline-id <pipeline_id> \
  --ref <branch_or_tag>
```

### B) CLI modular usage

```bash
ecoci version
ecoci security .gitlab-ci.yml
ecoci dora --deploys 20 --lead 24 --cfr 0.05 --mttr 1
ecoci cost --duration 600 --jobs 8 --runs-per-month 200
ecoci predict --files "src/a.py,src/b.py" --lines 300 --message "hotfix"
ecoci tests --changed "src/user.py,README.md" --lang python
ecoci fix
ecoci report
```

### C) GitHub-first universal CLI (MVP)

```bash
# Analyze first workflow in repo (auto-detect owner/repo from git remote)
ecoci analyze --provider github --json

# Analyze using real run job durations
ecoci analyze --provider github --run-id <actions_run_id> --markdown ecoci-report.md

# Generate optimized workflow YAML patch/preview
ecoci optimize --provider github --json

# Generate optimization plus unified diff preview
ecoci optimize --provider github --show-diff

# Generate deterministic patch for CI bot consumption
ecoci optimize --provider github --deterministic-patch --patch-file ecoci.patch

# Write optimized workflow to a file
ecoci optimize --provider github --workflow .github/workflows/test.yml --out optimized-workflow.yml

# Create PR with optimized workflow
ecoci pr create --provider github --title "EcoCI: Optimize workflow"

# Create PR + post carbon/cost dashboard from a real run
ecoci pr create --provider github --run-id <actions_run_id>

# Preview PR body and confidence-scored fix plan without creating PR
ecoci pr create --provider github --dry-run --json

# Validate setup/auth/workflow discovery
ecoci doctor --provider github
```

Phase 2.0 enhancements now included in CLI output:

- Confidence-scored findings in `analyze`
- Confidence-scored fix metadata in `optimize`
- Unified diff preview via `ecoci optimize --show-diff`
- Structured PR body with expected impact + rollback plan in `pr create`

Phase 2.1 enhancements now included in `analyze` output:

- Workflow quality gate summary (`PASS`, `WARN`, `FAIL`)
- Prioritized fix list with severity + confidence + score
- Expanded GitHub Actions security checks (permissions, `pull_request_target`, secret exposure patterns)
- More realistic run energy estimates using runner metadata when available

Phase 2.3 enhancements now included:

- Deterministic patch output mode for CI bots (`ecoci optimize --deterministic-patch`)
- Unified patch file export via `--patch-file`
- Before/after KPI projection blocks in markdown reports and PR body

### C) Webhook/server mode

Run as HTTP service:

```bash
RUN_MODE=server python -m scripts.ecoci.webhook_trigger
```

Container deployment helpers:

- [Dockerfile](Dockerfile)
- [scripts/deploy_cloud_run.sh](scripts/deploy_cloud_run.sh)

### D) VS Code extension (MVP)

A lightweight VS Code extension wrapper is included:

- [vscode-extensions/ecoci-vscode/package.json](vscode-extensions/ecoci-vscode/package.json)
- [vscode-extensions/ecoci-vscode/src/extension.js](vscode-extensions/ecoci-vscode/src/extension.js)
- [vscode-extensions/ecoci-vscode/media/leaf.svg](vscode-extensions/ecoci-vscode/media/leaf.svg)

Contributed commands:

- `EcoCI: Analyze Current Repo`
- `EcoCI: Optimize CI Workflows`
- `EcoCI: Create Optimization PR`
- `EcoCI: Show Carbon & Cost Summary`

Dashboard UX (Phase 2.2):

- Activity Bar **EcoCI** view with interactive actions
- In-editor summary of findings, prioritized fixes, and quality gate
- PR dry-run preview surfaced directly in dashboard panel

### E) Product roadmap + website scaffold

- Product roadmap: [ROADMAP.md](ROADMAP.md)
- Website landing page: [website/index.html](website/index.html)
- Downloads/install matrix: [website/downloads.html](website/downloads.html)
- Guided quickstart: [website/quickstart.html](website/quickstart.html)
- Command examples cookbook: [website/examples.html](website/examples.html)

Website now includes:

- Product landing flow with install + release CTAs
- CLI and extension verification paths
- Artifact-level release guidance (wheel/sdist/VSIX)

### F) Release readiness assets

- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Release checklist: [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- VSIX packaging script: [scripts/package_vscode_extension.sh](scripts/package_vscode_extension.sh)
- Release artifact builder: [scripts/build_release_artifacts.sh](scripts/build_release_artifacts.sh)
- GitHub release workflow: [.github/workflows/release.yml](.github/workflows/release.yml)

```bash
# Package VS Code extension artifact (.vsix)
bash scripts/package_vscode_extension.sh

# Build release artifacts locally (wheel + sdist + VSIX)
bash scripts/build_release_artifacts.sh

# Create release by pushing a tag (GitHub Actions will publish artifacts)
git tag v0.1.3
git push github v0.1.3
```

---

## 10) Validation and testing

Local test/demo scripts:

- [scripts/test_all_modules.py](scripts/test_all_modules.py)
- [scripts/test_business_value.py](scripts/test_business_value.py)
- [scripts/test_performance_analyzer.py](scripts/test_performance_analyzer.py)

GitHub Actions coverage:

- [.github/workflows/test.yml](.github/workflows/test.yml)

---

## 11) Implementation notes and current limits

- Agent-level write operations may depend on runtime permissions of the host platform.
- CLI/Python-token mode provides direct control for commit/MR automation.
- Optimizer behavior is intentionally conservative to reduce pipeline break risk.
- Cloud integration is optional and designed as an additive capability.

---

## 12) License

MIT — see [LICENSE](LICENSE)
