# EcoCI Optimization Techniques — What It Detects & Fixes

## How to Use the Demo

### Setup
1. Create a **personal GitLab project** (e.g., `gitlab.com/your-username/ecoci-demo`)
2. Copy `demo/bad-gitlab-ci.yml` → `.gitlab-ci.yml` in that project
3. Add a simple `package.json`, `requirements.txt`, some dummy `src/` files
4. Let the pipeline run once (it will be slow — that's the point!)
5. Open **GitLab Duo Chat** → select **EcoCI Pipeline Optimizer**
6. Say: "Analyze the pipeline for project YOUR_PROJECT_ID and create an MR with optimizations"

### What EcoCI Will Do (record this for your video)
1. 🔍 Fetch real pipeline data (you'll see tool calls in the chat)
2. 📊 Calculate carbon emissions from actual job durations
3. ⚡ Generate optimized .gitlab-ci.yml
4. 🔀 Create a branch and merge request automatically
5. 💬 Post carbon dashboard comment on the MR

---

## The 10 Optimization Techniques

### 1. 🐳 IMAGE PINNING — `:latest` → slim/alpine
| Before | After | Savings |
|--------|-------|---------|
| `node:latest` (1.1 GB) | `node:22-slim` (200 MB) | ~900 MB less to pull |
| `python:latest` (1.0 GB) | `python:3.12-slim` (150 MB) | ~850 MB less to pull |
| `ruby:latest` (900 MB) | `ruby:3.3-slim` (200 MB) | ~700 MB less to pull |
| `postgres:latest` (400 MB) | `postgres:16-alpine` (80 MB) | ~320 MB less to pull |

**Why it matters**: Every pipeline run pulls these images. Smaller images = faster starts + less network I/O + less energy.

### 2. 📦 DEPENDENCY CACHING
| Before | After | Savings |
|--------|-------|---------|
| `npm install` every run (~45s) | Cached `node_modules/` (~2s) | ~43s per job |
| `pip install` every run (~30s) | Cached `.cache/pip` (~3s) | ~27s per job |
| `gem install` every run (~20s) | Cached `vendor/bundle` (~2s) | ~18s per job |

**Why it matters**: Without cache, EVERY pipeline run downloads the same packages from the internet. With 15 jobs × 30s install = 7.5 minutes wasted per run.

### 3. 🔀 DAG PARALLELISM — `needs:` declarations
| Before | After | Savings |
|--------|-------|---------|
| All lint jobs wait for previous stage | `needs: []` — start immediately | ~3 min |
| All test jobs wait for ALL builds | `needs: ["build-backend"]` — start as soon as needed build finishes | ~2 min |
| Security jobs wait for tests | `needs: []` — security runs in parallel | ~4 min |

**Why it matters**: Without `needs:`, GitLab runs jobs sequentially by stage. A 15-job pipeline that could finish in 8 min takes 25+ min.

```
BEFORE (sequential):                AFTER (parallel):
lint ──→ build ──→ test ──→ sec    lint ──┐
  3m       5m       8m      4m    build ──┤──→ test ──→ deploy
                                  security┘     5m       2m
Total: ~20 min                    Total: ~8 min
```

### 4. 🎯 SMART SKIP RULES — `rules:changes`
| Scenario | Before | After |
|----------|--------|-------|
| Edit README.md | All 15 jobs run (25 min) | 0 jobs run (0 min) |
| Edit a Python file | All 15 jobs run | Only Python lint + test + security (5 min) |
| Edit Dockerfile | All 15 jobs run | Only docker-build + deploy (3 min) |

**Why it matters**: ~40% of commits in typical projects are docs/config changes. Running all jobs wastes 40% of your CI budget.

### 5. 🏃 RUNNER RIGHT-SIZING
| Job | Before | After | Cost Savings |
|-----|--------|-------|-------------|
| eslint (lint) | `xlarge` ($0.12/min) | `small` ($0.01/min) | 92% |
| sast (security) | `xlarge` ($0.12/min) | `small` ($0.01/min) | 92% |
| e2e-tests | `xlarge` ($0.12/min) | `medium` ($0.04/min) | 67% |

**Why it matters**: Linting uses <5% CPU. Running it on an xlarge runner (8 vCPU, 32GB) is like using a truck to deliver a letter.

### 6. ⏱️ TIMEOUT PROTECTION
| Before | After |
|--------|-------|
| No timeout (job can run forever) | `timeout: 15m` on E2E tests |
| Hung job costs $7.20/hr on xlarge | Max cost capped at $1.80 |

### 7. 📥 SHALLOW GIT CLONE
| Before | After | Savings |
|--------|-------|---------|
| Full clone (all history) | `GIT_DEPTH: 20` | 60-90% less clone time |

### 8. 🔧 `npm ci` over `npm install`
| Before | After |
|--------|-------|
| `npm install` (modifies lock file, slower) | `npm ci --prefer-offline` (deterministic, faster, uses cache) |

### 9. ⚡ PARALLEL TEST EXECUTION
| Before | After | Savings |
|--------|-------|---------|
| `pytest tests/` (single process) | `pytest -n auto` (all CPU cores) | 50-75% faster |

### 10. 📋 `only:` → `rules:` MIGRATION
| Before | After |
|--------|-------|
| `only: [main]` (deprecated) | `rules: - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH` |

---

## Carbon Impact Summary (example 15-job pipeline)

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Total duration | ~25 min | ~8 min | 68% faster |
| Compute minutes | 25 min × 15 jobs = 375 min | ~60 min (parallel) | 84% less |
| Energy per run | 3.13 Wh | 1.00 Wh | 68% less |
| CO₂ per run | 1.49 g | 0.48 g | 68% less |
| Monthly (20 runs/week) | 119 g CO₂ | 38 g CO₂ | 81 g saved |
| Yearly | 1.43 kg CO₂ | 0.46 kg CO₂ | **0.97 kg saved** |
| Cost/month ($0.10/min) | $37.50 | $6.00 | **$31.50/month saved** |
| Cost/year | $450 | $72 | **$378/year saved** |

> **"EcoCI reduced this pipeline from 25 minutes to 8 minutes, saving $378/year
> and eliminating 0.97 kg CO₂ — equivalent to driving 4 km less per year."**

---

## Demo Video Script (under 3 minutes)

### 0:00–0:20 — The Problem
"Here's a typical GitLab CI pipeline. 15 jobs, using :latest images, no caching,
running sequentially. It takes 25 minutes and wastes energy on every commit."
→ Show the bad pipeline running in GitLab

### 0:20–0:40 — Meet EcoCI
"EcoCI is an autonomous agent built on GitLab Duo that analyzes real pipeline
data — not just YAML — and creates merge requests with optimizations."
→ Show opening Duo Chat, selecting EcoCI agent

### 0:40–1:40 — The Action
"Watch — I ask EcoCI to optimize this project's pipeline."
→ Type: "Analyze and optimize the pipeline for project [ID]"
→ Show the agent making tool calls (get_pipeline_failing_jobs, get_job_logs, etc.)
→ Show it creating the commit and merge request

### 1:40–2:30 — The Result
→ Click through to the MR EcoCI created
→ Show the YAML diff (images, caching, needs:, rules:)
→ Show the carbon dashboard comment
→ Show before/after metrics

### 2:30–2:50 — The Impact
"EcoCI found 14 optimizations. It reduced pipeline time from 25 to 8 minutes,
saving $378 per year and eliminating nearly 1 kg of CO₂ emissions annually.
All autonomously — no human intervention needed."

### 2:50–3:00 — Closing
"EcoCI: making CI/CD faster, cheaper, and greener — one pipeline at a time."
