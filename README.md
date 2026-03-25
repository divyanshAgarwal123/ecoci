# EcoCI — AI-Powered CI/CD Optimization Agent

EcoCI is an autonomous optimization agent built for GitLab Duo Agent Platform.  
It analyzes CI/CD pipelines and related code signals, then recommends or generates practical improvements for speed, reliability, security, cost, and carbon impact.

---

## What is EcoCI?

EcoCI is a modular Python-based system that can:

- inspect pipeline configuration and job behavior,
- detect bottlenecks and risky patterns,
- estimate business and operational impact,
- suggest or generate fixes,
- and support merge-request-based optimization workflows.

Core analysis modules include:

- Cost and ROI analysis
- Production impact prediction
- Security scanning
- Flaky test detection
- DORA metrics reporting
- Smart test selection
- Failure prediction
- Auto-fix generation
- Carbon tracking and reporting
- Code performance analysis (slow tests, N+1 patterns, memory and I/O concerns)

---

## What is it used for?

Use EcoCI when you want to improve pipeline and delivery performance with measurable outcomes:

- Reduce CI runtime and wasted compute
- Catch reliability and security issues earlier
- Understand delivery health through DORA metrics
- Lower pipeline cost and carbon emissions
- Automate optimization via merge requests

It is useful for platform teams, DevOps teams, and engineering teams that want continuous pipeline optimization instead of one-time tuning.

---

## How is it better?

EcoCI focuses on actionable optimization from pipeline context, not just generic advice.

| Capability | Generic assistant workflow | EcoCI workflow |
|---|---|---|
| Data collection | Manual copy/paste of YAML and logs | Structured analysis modules over project inputs |
| Output | Recommendations only | Recommendations plus implementation-ready fixes |
| Scope | Usually single concern | Cost, performance, reliability, security, and carbon together |
| Operational flow | Manual follow-up | Supports MR-oriented optimization lifecycle |

In short: EcoCI is designed for repeatable, engineering-grade optimization rather than ad-hoc suggestions.

---

## How to implement

### 1) Prerequisites

- Python 3.10+
- GitLab project access and token for API operations
- GitLab Duo Agent Platform access
- (Optional) Google Cloud project for BigQuery/cloud features

### 2) Clone and install

```bash
git clone <your-repo-url>
cd 34560917
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure

- Agent configuration: [agents/agent.yml](agents/agent.yml)
- Runtime and module settings: [scripts/ecoci/config.py](scripts/ecoci/config.py)
- Optional cloud settings: [scripts/ecoci/gcp_config.json](scripts/ecoci/gcp_config.json)

Provide required credentials and environment variables (for GitLab and optional cloud integrations).

### 4) Run locally (example)

```bash
python scripts/ecoci/main.py
```

You can also run helper scripts for validation and demos:

- [scripts/test_all_modules.py](scripts/test_all_modules.py)
- [scripts/test_business_value.py](scripts/test_business_value.py)
- [scripts/test_performance_analyzer.py](scripts/test_performance_analyzer.py)

### 5) Use in GitLab workflow

- Trigger analysis through your configured Duo Agent/automation flow
- Review optimization output
- Apply generated changes through merge request workflow

---

## Project structure

```text
agents/
  agent.yml
scripts/
  ecoci/
    auto_fix_engine.py
    carbon_calculator.py
    ci_analyzer.py
    code_performance_analyzer.py
    config.py
    cost_analyzer.py
    dora_metrics.py
    failure_predictor.py
    flaky_test_detector.py
    gcp_integration.py
    gitlab_client.py
    main.py
    mr_creator.py
    optimizer.py
    production_impact_predictor.py
    security_scanner.py
    smart_test_selector.py
    webhook_trigger.py
requirements.txt
LICENSE
```

---

## Additional documentation

- [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)
- [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
- [ANTHROPIC_INTEGRATION.md](ANTHROPIC_INTEGRATION.md)
- [CLOUD_INTEGRATION.md](CLOUD_INTEGRATION.md)
- [GCP_QUICKSTART.md](GCP_QUICKSTART.md)

---

## License

MIT — see [LICENSE](LICENSE)
