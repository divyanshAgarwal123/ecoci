# EcoCI - GitLab AI Hackathon

EcoCI is a multi-agent GitLab Duo flow that optimizes GitLab CI/CD pipelines to be faster, cheaper, and lower-carbon.
It triggers on pipeline completion, analyzes `.gitlab-ci.yml`, estimates carbon emissions, proposes improvements, and
creates a merge request with a clear before/after summary.

---

## Table of contents

1. [What is included](#what-is-included)
2. [Key features](#key-features)
3. [One-time project setup](#one-time-project-setup)
4. [Pipeline trigger configuration](#pipeline-trigger-configuration)
5. [How EcoCI runs end-to-end](#how-ecoci-runs-end-to-end)
6. [Local / manual testing](#local--manual-testing)
7. [MR template and labels](#mr-template-and-labels)
8. [Demo storyline](#demo-storyline)

---

## What is included

```
.gitlab-ci.yml                           # CI pipeline: validate + ecoci_runner job
.gitlab/
  agents/
    ecocl-flow.yml                       # Duo multi-agent flow (4 agents)
    pipeline-analyzer.yml                # Agent 1 - analyse CI config
    carbon-calculator.yml                # Agent 2 - estimate emissions
    optimizer.yml                        # Agent 3 - generate improved YAML
    mr-creator.yml                       # Agent 4 - create MR
  merge_request_templates/
    ecoci_optimization.md                # Standardised MR template
scripts/
  ecoci/
    __init__.py
    main.py                              # CLI entry point
    config.py                            # Environment-based config
    gitlab_client.py                     # GitLab REST API wrapper
    ci_analyzer.py                       # Inefficiency + DAG + tag analysis
    carbon_calculator.py                 # Energy and CO2 estimation
    optimizer.py                         # YAML rewriter
    mr_creator.py                        # MR creation with labels and template
    webhook_trigger.py                   # Pipeline Trigger API helper
requirements.txt
```

## Key features

- Trigger on pipeline completion and pull pipeline data
- Analyse `.gitlab-ci.yml` for caching, parallelism, runner tags, image size, and unnecessary jobs
- Deep **`needs:` DAG inspection** - cycle detection, critical-path depth, parallelism ratio
- **Runner-tier recommendations** - flags heavy-runner tags on lightweight jobs
- Estimate emissions using `CO2 = (duration x runner_cores x 0.5 kWh) x carbon_intensity`
- Generate optimised `.gitlab-ci.yml`
- Create MR with changes, carbon dashboard, DAG summary, and `/label` quick-actions

---

## One-time project setup

All steps below use **GitLab only** (no external services).

### 1. Set your Duo namespace

Go to **User Settings > GitLab Duo > Default namespace** and select **GitLab AI Hackathon**.

### 2. Create a project access token

Go to **Settings > Access tokens > Add new token**.

| Field | Value |
| ----- | ----- |
| Name | `ecoci-bot` |
| Scopes | `api`, `read_repository`, `write_repository` |
| Role | Maintainer |
| Expiry | 90 days (or as needed) |

Copy the token value.

### 3. Store it as a masked CI/CD variable

Go to **Settings > CI/CD > Variables > Add variable**.

| Field | Value |
| ----- | ----- |
| Key | `GITLAB_TOKEN` |
| Value | *(paste the token)* |
| Mask variable | Yes |
| Protect variable | Yes |

### 4. Create a pipeline trigger token

Go to **Settings > CI/CD > Pipeline trigger tokens > Add trigger**.

| Field | Value |
| ----- | ----- |
| Description | `ecoci-webhook` |

Store the trigger token as another CI/CD variable:

| Key | Flags |
| --- | ----- |
| `ECOCI_TRIGGER_TOKEN` | Mask: Yes, Protect: Yes |

### 5. Protect the `ecoci/*` branch pattern

Go to **Settings > Repository > Protected branches > Add**.

| Field | Value |
| ----- | ----- |
| Branch | `ecoci/*` |
| Allowed to merge | Maintainers |
| Allowed to push | `ecoci-bot` (the token user) |

This ensures only the bot can push to `ecoci/optimize-*` branches.

### 6. Create project labels

Go to **Project > Labels** and create:

- `ecoci`
- `ci-optimization`
- `carbon-reduction`
- `pipeline-optimization`

### 7. (Optional) Tune carbon defaults

Add these CI/CD variables if the defaults do not match your environment:

| Variable | Default | Description |
| -------- | ------: | ----------- |
| `CARBON_INTENSITY_KG_PER_KWH` | 0.475 | Regional grid carbon intensity |
| `DEFAULT_RUNNER_CPU_CORES` | 2 | Assumed CPU cores per runner |
| `KWH_PER_CORE_HOUR` | 0.5 | Energy per core-hour |
| `GITLAB_BASE_URL` | `https://gitlab.com` | GitLab instance URL |

---

## Pipeline trigger configuration

EcoCI is triggered when a pipeline completes. Two approaches:

### Option A: Webhook into Trigger API (recommended)

1. Go to **Settings > Webhooks > Add webhook**.
2. URL: point to a small relay (or use a GitLab serverless function) that calls `scripts/ecoci/webhook_trigger.py`.
3. Trigger: **Pipeline events** only.
4. The script extracts `project_id`, `pipeline_id`, `ref` from the `pipeline:completed` payload and fires the Pipeline Trigger API:

```
POST /projects/:id/trigger/pipeline
  token=ECOCI_TRIGGER_TOKEN
  ref=main
  variables[ECOCI_PROJECT_ID]=...
  variables[ECOCI_PIPELINE_ID]=...
  variables[ECOCI_REF]=...
```

5. This starts a new pipeline that runs the `ecoci_runner` job.

### Option B: Manual / scheduled run

Go to **CI/CD > Run pipeline** and set:

| Variable | Value |
| -------- | ----- |
| `ECOCI_PROJECT_ID` | numeric project ID |
| `ECOCI_PIPELINE_ID` | pipeline ID to analyse |
| `ECOCI_REF` | branch ref of that pipeline |

Click **Run pipeline**. The `ecoci_runner` job picks up and executes.

---

## How EcoCI runs end-to-end

```
Pipeline completes
      |
      v
Webhook / manual trigger
      |
      v
ecoci_runner CI job
  python -m scripts.ecoci.main --project-id --pipeline-id --ref
      |
      v
  1. Fetch .gitlab-ci.yml
  2. Analyse (cache, DAG, tags)
  3. Estimate carbon emissions
  4. Generate optimised YAML
  5. Create branch ecoci/optimize-*
  6. Commit optimised config
  7. Open MR with labels + metrics
  8. Post carbon dashboard comment
```

The Duo Flow (`.gitlab/agents/ecocl-flow.yml`) follows the same
four-agent chain when invoked from Duo Chat or a flow trigger.

---

## Local / manual testing

```bash
export GITLAB_TOKEN=glpat-...
export GITLAB_BASE_URL=https://gitlab.com

python -m scripts.ecoci.main \
  --project-id 34560917 \
  --pipeline-id 12345 \
  --ref main
```

---

## MR template and labels

Every MR opened by EcoCI uses the template at
`.gitlab/merge_request_templates/ecoci_optimization.md`.

It includes:
- Optimisation checklist
- Before / after carbon impact table
- `/label` quick-actions for `~carbon-reduction`, `~pipeline-optimization`, `~ecoci`
- Link to the triggering pipeline

---

## Demo storyline

1. Commit a deliberately slow `.gitlab-ci.yml` (`:latest` images, no cache, no `needs:`).
2. Let the pipeline run and complete.
3. Trigger EcoCI (webhook or manual).
4. Show the MR that EcoCI opened:
   - Optimised YAML diff
   - Carbon dashboard comment
   - DAG parallelism improvement
   - Labels applied automatically
5. Show metrics: *"Reduced from 45 min to 28 min, saved $420/month, eliminated 840 kg CO2/year."*

---

For instructions on how to get started take a look at the [onboarding issue](../../work_items/1) in this project.
