# EcoCI — Complete Beginner's Guide

## What is this project? (ELI5 version)

**The Simple Answer:**
EcoCI is a smart assistant (AI agent) that looks at your GitLab pipelines (the automated tests that run when you push code) and tells you how to make them faster and more energy-efficient.

But unlike ChatGPT where you paste YAML and it gives suggestions, **EcoCI actually goes into your project, reads real data, and creates a merge request with fixes** — all by itself.

---

## The Real Problem

### Background: What are CI/CD Pipelines?

When you push code to GitLab, it automatically:
1. Downloads your code
2. Installs dependencies (npm install, pip install)
3. Runs linters (checks code quality)
4. Runs tests
5. Builds Docker images
6. Deploys to servers

This is called a **CI/CD pipeline**. It's automated — every time you commit.

### The Problem

Most developers write `.gitlab-ci.yml` (the config file) without thinking about efficiency. They:
- Use `:latest` Docker images (1GB each)
- Don't cache dependencies (reinstall every time)
- Run all jobs sequentially (even when they could be parallel)
- Run ALL jobs even on README changes
- Use expensive runners (servers) for simple tasks

**Result:**
- Pipelines take 20-30 minutes instead of 5 minutes
- Company pays $500/month for CI instead of $50/month
- Wastes electricity → more CO₂ emissions

### Example: A Real Waste

```yaml
# BAD (what most people write)
test:
  image: python:latest          # 1GB download EVERY run
  script:
    - pip install -r requirements.txt  # Reinstalls EVERY run (30 seconds)
    - pytest
```

Every time you commit (20 times/day × 5 devs = 100 runs/day):
- Downloads 1GB image: 100 times
- Reinstalls packages: 100 times
- Wastes: 50 minutes of install time per day

**Over a year:**
- Wastes: ~300 hours of pipeline time
- Costs: ~$3,000 extra
- Emits: ~15 kg extra CO₂

---

## The Solution (What EcoCI Does)

### Instead of you manually fixing it...

EcoCI is an AI agent that:
1. **Looks at your real pipeline data** (not just the YAML file)
2. **Reads job logs** to see what's actually slow
3. **Calculates actual carbon emissions** from real job durations
4. **Generates an optimized .gitlab-ci.yml**
5. **Creates a merge request** with the fix

You just say: *"Optimize my pipeline"* → and boom, you get a merge request.

---

## What's Different About EcoCI vs ChatGPT?

| Task | ChatGPT | EcoCI |
|------|---------|-------|
| You: "Analyze this YAML" | You paste the file | ✅ EcoCI fetches it from GitLab API |
| Gets job durations | You tell it: "test takes 5 min" | ✅ EcoCI calls GitLab API to get REAL durations |
| Reads logs to find slow steps | ❌ Can't | ✅ EcoCI reads actual job logs |
| Calculates CO₂ | ❌ Guesses | ✅ Uses real duration × CPU cores × grid intensity |
| Creates MR with fix | ❌ Gives you code to paste | ✅ Calls GitLab API to create branch + commit + MR |

**Key difference:** EcoCI is an **autonomous agent**, not a chatbot.

---

## Technical Terms Explained

### 1. **Agent** (GitLab Duo Agent)
A special AI that can:
- Use tools (call GitLab API, read files, create commits)
- Take actions (not just answer questions)
- Work autonomously (you give it a goal, it does everything)

Think: "Siri that can actually DO stuff in GitLab"

### 2. **Flow**
A multi-step workflow. EcoCI's flow has 4 agents that run in sequence:
```
Step 1: Analyzer  → reads pipeline data
Step 2: Carbon    → calculates emissions
Step 3: Optimizer → generates better YAML
Step 4: MR Creator→ creates the merge request
```

### 3. **Tools** (in `agent.yml`)
Functions the agent can call:
- `get_pipeline_failing_jobs` — gets list of jobs + durations from latest pipeline
- `get_job_logs` — reads the actual log output of a job
- `create_commit` — creates a Git commit
- `create_merge_request` — opens a merge request

### 4. **Carbon Emissions**
Formula: `CO₂ = (job_duration × CPU_cores × energy_per_core) × grid_carbon_intensity`

Example:
- Job runs for 300 seconds (5 min)
- On a 2-core runner
- Energy: 300s / 3600 × 2 × 0.5 kWh = 0.083 Wh
- CO₂: 0.083 × 0.475 kg/kWh = **39 grams**

If you run this 100 times/day → 3.9 kg CO₂/day → **1.4 tons/year**

### 5. **DAG (Directed Acyclic Graph)**
The dependency tree of your jobs.

```
Without needs: (everything sequential)
lint → build → test → deploy
  3m     5m     8m     2m
Total: 18 min

With needs: (parallel where possible)
lint ─┐
build ┼─→ test → deploy
      │    5m      2m
Total: 10 min (44% faster!)
```

### 6. **Cache**
Store files between pipeline runs.

```yaml
cache:
  key: pip-cache
  paths:
    - .cache/pip
```

First run: installs packages (30s)
Second run: uses cached packages (2s)

### 7. **Rules (rules:changes)**
Run jobs only when relevant files change.

```yaml
test:
  rules:
    - changes:
        - "**/*.py"
        - "requirements.txt"
```

Now if you edit README.md → test job doesn't run (saves time + money)

---

## What Have We Built? (Project Inventory)

### Core Files

1. **`agents/agent.yml`** (80 lines)
   - The AI agent definition
   - Tells the agent: "You MUST call these tools in this order"
   - 4 steps: fetch data → calculate carbon → optimize → create MR

2. **`flows/flow.yml`** (220 lines)
   - Multi-agent workflow
   - 4 agents working in sequence
   - Each has its own prompt + tools

3. **`scripts/ecoci/`** (Python modules)
   - Alternative way to run EcoCI from command line
   - Same logic as the agent, but in Python
   - Files:
     - `main.py` — entry point
     - `ci_analyzer.py` — reads .gitlab-ci.yml, detects issues
     - `carbon_calculator.py` — calculates CO₂
     - `optimizer.py` — rewrites the YAML with fixes
     - `mr_creator.py` — creates the merge request

4. **`demo/`** (Demo files)
   - `bad-gitlab-ci.yml` — deliberately slow 15-job pipeline
   - `optimized-gitlab-ci.yml` — same pipeline after EcoCI fixes
   - `DEMO_GUIDE.md` — explains all 10 optimization techniques

---

## How to Test It (Step by Step)

### Option 1: Test with Duo Chat (Easiest)

**Step 1: Make sure your agent is visible**
1. Open [GitLab Duo Chat](https://gitlab.com/-/duo_chat)
2. Check if "EcoCI Pipeline Optimizer" appears in the dropdown
3. If not, wait 2-3 minutes (catalog is updating)

**Step 2: Find a project with a pipeline**
1. Go to any GitLab project you own
2. Note the project ID (e.g., 79403566)
3. Make sure it has at least 1 completed pipeline

**Step 3: Ask EcoCI to analyze it**
In Duo Chat, type:
```
Analyze the pipeline for project 79403566 and create an MR with optimizations
```

**Step 4: Watch it work**
You'll see:
- Tool calls: `get_project`, `get_pipeline_failing_jobs`, `get_job_logs`
- Analysis output
- "Creating merge request..."

**Step 5: Check the MR**
Go to your project → Merge Requests → you'll see a new MR from EcoCI!

---

### Option 2: Test with a Demo Project (Best for Video)

**Step 1: Create a test project**
1. Go to https://gitlab.com/projects/new
2. Name: `ecoci-demo`
3. Visibility: Public
4. Create project

**Step 2: Add the bad CI config**
1. Copy `demo/bad-gitlab-ci.yml` from this repo
2. Create `.gitlab-ci.yml` in your new project
3. Paste the content
4. Commit

**Step 3: Add some dummy files**
Create these files (GitLab Web IDE is easiest):

`package.json`:
```json
{
  "name": "demo",
  "dependencies": {
    "express": "^4.18.0"
  }
}
```

`requirements.txt`:
```
requests==2.32.0
flask==3.0.0
```

`src/app.py`:
```python
def hello():
    return "Hello"
```

**Step 4: Let the pipeline run**
1. Go to CI/CD → Pipelines
2. Wait for it to finish (or fail — doesn't matter)

**Step 5: Run EcoCI**
In Duo Chat:
```
Analyze the pipeline for project YOUR_PROJECT_ID and create an MR
```

**Step 6: See the magic**
You'll get an MR with:
- Optimized .gitlab-ci.yml
- Before/after comparison
- Carbon savings calculation
- Cost savings estimate

---

## The 10 Problems EcoCI Fixes

| Problem | Waste | Fix |
|---------|-------|-----|
| 1. `:latest` images (1GB) | 900MB per pull | Pin to `-slim` (200MB) |
| 2. No cache | 30s reinstall every run | Cache deps → 2s |
| 3. Sequential jobs | 25 min total | `needs:` → 8 min (parallel) |
| 4. Runs on README edits | 100% waste | `rules:changes` → skip |
| 5. xlarge runner for lint | $0.12/min for 5% CPU | small runner → $0.01/min |
| 6. No timeout | Hung job runs forever | `timeout: 15m` |
| 7. Full git clone | 5 min clone | `GIT_DEPTH: 20` → 1 min |
| 8. `npm install` | Modifies lock file | `npm ci --prefer-offline` |
| 9. Single-thread tests | 10 min tests | `pytest -n auto` → 3 min |
| 10. Old `only:` syntax | Deprecated | `rules:` (future-proof) |

---

## What Happens When You Run EcoCI

```
YOU: "Optimize project 12345"
  ↓
AGENT: Calls get_project(12345)
  → Gets: name, default_branch, etc.
  ↓
AGENT: Calls get_repository_file('.gitlab-ci.yml')
  → Reads the CI config
  ↓
AGENT: Calls get_pipeline_failing_jobs(12345)
  → Gets: [{name: "test", duration: 342s}, {name: "lint", duration: 45s}, ...]
  ↓
AGENT: Calls get_job_logs for slowest 2 jobs
  → Sees: "pip install took 180s", "npm install took 90s"
  ↓
AGENT: Calculates carbon
  → test: 342s × 2 cores × 0.5 kWh/core/hr × 0.475 kg/kWh = 45g CO₂
  → lint: 45s × 2 × 0.5 × 0.475 = 6g CO₂
  → Total: 51g per run
  ↓
AGENT: Generates optimized YAML
  → Adds cache for pip, npm
  → Changes node:latest → node:22-slim
  → Adds needs: [] for parallel jobs
  → Adds rules:changes
  ↓
AGENT: Calls create_commit
  → Creates branch: ecoci/optimize-pipeline
  → Commits the new .gitlab-ci.yml
  ↓
AGENT: Calls create_merge_request
  → Title: "🌱 EcoCI: Optimize pipeline — save 8m, reduce 30g CO₂/run"
  → Description: full analysis + carbon table
  ↓
AGENT: Calls create_merge_request_note
  → Posts carbon dashboard comment
  ↓
DONE! You now have an MR ready to merge.
```

---

## Summary: The Full Story

**Problem:** GitLab pipelines are slow and wasteful because developers don't optimize them.

**Solution:** EcoCI — an AI agent that:
1. Fetches real pipeline data
2. Calculates actual carbon emissions
3. Generates optimized config
4. Creates MR with the fix

**What makes it special:**
- Uses REAL data (not guesses)
- Takes ACTION (creates MRs)
- Autonomous (you don't have to do anything)

**What you built:**
- 1 agent (`agents/agent.yml`)
- 1 flow (`flows/flow.yml`)
- Python scripts (alternative CLI)
- Demo files (for testing + video)

**How to test:**
1. Open Duo Chat
2. Select "EcoCI Pipeline Optimizer"
3. Say: "Optimize project [ID]"
4. Get a merge request with fixes

**For hackathon demo:**
1. Create a test project
2. Use `demo/bad-gitlab-ci.yml`
3. Let pipeline run
4. Show EcoCI creating an MR
5. Record screen → that's your video

That's everything! 🎉
