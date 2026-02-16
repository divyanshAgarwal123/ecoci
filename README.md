# EcoCI — Autonomous CI/CD Carbon Optimizer

> **GitLab AI Hackathon 2026** — Built on GitLab Duo Agent Platform  
> 🤖 **Powered by Anthropic Claude Opus 4.5** | ☁️ **Google Cloud Ready**

EcoCI is an autonomous agent that **fetches real pipeline data**, **calculates actual carbon emissions** from job durations, **generates an optimized `.gitlab-ci.yml`**, and **creates a merge request** — all without human intervention.

**Unlike a basic chatbot**, EcoCI uses GitLab tools to pull live data (`get_pipeline_failing_jobs`, `get_job_logs`) and take real action (`create_commit`, `create_merge_request`).

## 🏆 Hackathon Prize Eligibility

- ✅ **Green Agent Prize** — Reduces CO₂ emissions by 64% per pipeline
- ✅ **Anthropic Integration Prize** — Uses Claude Opus 4.5 for intelligent optimization decisions → [Read how](ANTHROPIC_INTEGRATION.md)
- ✅ **Google Cloud Integration** — Optional BigQuery & Carbon Footprint API support → [Integration guide](CLOUD_INTEGRATION.md)
- ✅ **Sustainable Design Bonus** — Built specifically for environmental impact

---

## What makes this different from asking ChatGPT?

| | ChatGPT / Claude | EcoCI Agent |
|---|---|---|
| Data source | You paste YAML | Fetches live pipeline data via GitLab API |
| Metrics | Guesses durations | Uses **actual** job durations from `get_pipeline_failing_jobs` |
| Log analysis | Can't see logs | Reads real `get_job_logs` to find slow steps |
| Carbon math | Estimates | Calculates from real `duration × cores × grid_intensity` |
| Action | Gives suggestions | **Creates branch, commits, opens MR** autonomously |
| Follow-up | None | Posts carbon dashboard comment on the MR |

---

## How it works

```
User: "Optimize the pipeline for this project"
  │
  ├─ Agent calls get_project ──────────── gets project metadata
  ├─ Agent calls get_repository_file ──── fetches .gitlab-ci.yml
  ├─ Agent calls get_pipeline_failing_jobs ── gets REAL job durations
  ├─ Agent calls get_job_logs ─────────── reads logs for slow jobs
  │
  ├─ Calculates CO₂ from actual durations
  ├─ Identifies: missing cache, sequential jobs, heavy images
  │
  ├─ Agent calls create_commit ────────── creates branch + optimized YAML
  ├─ Agent calls create_merge_request ─── opens MR with metrics
  └─ Agent calls create_merge_request_note ── posts carbon dashboard
```

**Result**: A merge request appears with the optimized config, real before/after metrics, and a carbon impact summary.

---

## Project structure

```
agents/
  agent.yml              # EcoCI agent definition (Duo Agent Platform)
flows/
  flow.yml               # Multi-step flow: analyze → carbon → optimize → MR
.gitlab/
  merge_request_templates/
    ecoci_optimization.md  # MR template with carbon checklist
scripts/
  ecoci/
    main.py              # CLI entry point (alternative trigger via CI job)
    config.py            # Environment-based configuration
    gitlab_client.py     # GitLab REST API wrapper
    ci_analyzer.py       # Pipeline analysis with DAG inspection
    carbon_calculator.py # Energy and CO₂ estimation
    optimizer.py         # YAML rewriter
    mr_creator.py        # Branch + commit + MR creation
    webhook_trigger.py   # Pipeline Trigger API helper
.gitlab-ci.yml           # CI job for webhook/manual trigger
requirements.txt         # Python dependencies
LICENSE                  # MIT License
```

## Key features

- **Real data, not guesses** — fetches actual job durations and logs from GitLab API
- **Carbon footprint tracking** — `CO₂ = (duration × cores × 0.5 kWh) × 0.475 kg/kWh`
- **DAG analysis** — detects sequential bottlenecks, missing `needs:`, cycle detection
- **Runner tag optimization** — flags heavyweight runners on lightweight jobs
- **Autonomous MR creation** — creates branch, commits optimized YAML, opens MR
- **Carbon dashboard** — posts per-job emissions breakdown as MR comment

## Agent (Duo Chat)

Chat with `EcoCI Pipeline Optimizer` in GitLab Duo Chat:

> "Analyze and optimize the pipeline for this project"

The agent will fetch real data, calculate emissions, generate an optimized config, and create an MR.

## Flow (triggered by @mention)

The flow runs 4 steps in sequence:
1. **Pipeline Analyzer** — fetches real job data and identifies inefficiencies
2. **Carbon Calculator** — computes emissions from actual durations
3. **Optimization Engine** — generates improved `.gitlab-ci.yml`
4. **MR Creator** — creates branch, commits, opens MR, posts carbon dashboard

Trigger by mentioning the flow's user in an issue or MR.

## Alternative: CI job trigger

You can also trigger EcoCI via a CI pipeline:

```bash
# Go to CI/CD > Run pipeline and set:
#   ECOCI_PROJECT_ID  = target project ID
#   ECOCI_PIPELINE_ID = pipeline ID to analyze
#   ECOCI_REF         = branch ref
```

---

## 📚 Deep Dives

Want to learn more about how EcoCI works?

- **[🧠 Anthropic Claude Integration](ANTHROPIC_INTEGRATION.md)** — How Claude Opus 4.5 powers intelligent pipeline analysis and optimization decisions
- **[☁️ Google Cloud Integration](CLOUD_INTEGRATION.md)** — Optional enhancements: BigQuery for historical tracking, Carbon Footprint API for region-specific calculations, Cloud Run deployment
- **[📖 Beginner Guide](BEGINNER_GUIDE.md)** — Complete project explanation for those new to GitLab Duo Agents
- **[🎬 Demo Guide](demo/DEMO_GUIDE.md)** — 10 optimization techniques with before/after comparison (64% CO₂ reduction)

---

## License

MIT — see [LICENSE](LICENSE)

---

For hackathon onboarding, see the [onboarding issue](../../work_items/1).
