# Why EcoCI Can't Create MRs Yet (And How to Fix It)

## The Problem

You're right — **the agent isn't fully autonomous**. It has the tools (`create_commit`, `create_merge_request`) but when you use it in Duo Chat, it gives you manual instructions instead of creating the MR.

## Why This Happens

GitLab Duo agents run in a **read-only sandbox** for security. The agent can:
- ✅ Read your project files
- ✅ Fetch pipeline data
- ✅ Analyze and calculate
- ❌ **Write commits** (requires authentication)
- ❌ **Create MRs** (requires project permissions)

## The 3 Workarounds

### Option 1: Use the Flow (not the agent)

The **flow** can be triggered by @mentioning it in an issue/MR, and flows have different permissions.

**Try this:**
1. Create an issue in your project
2. In a comment, type: `@ai-ecoci-flow-gitlab-ai-hackathon analyze and optimize this project's pipeline`
3. The flow should create the MR

**Status:** Untested — flows might have write permissions that agents don't.

---

### Option 2: Use the Python CLI (Full Automation)

The `scripts/ecoci/` Python code **does** create MRs because it uses a personal access token.

**Setup:**
```bash
# 1. Create a GitLab personal access token
#    Go to: https://gitlab.com/-/user_settings/personal_access_tokens
#    Scopes: api, write_repository
#    Copy the token

# 2. Set environment variables
export GITLAB_TOKEN="glpat-your-token-here"
export GITLAB_BASE_URL="https://gitlab.com"

# 3. Run EcoCI
cd /path/to/34560917
python -m scripts.ecoci.main \
  --project-id 79403566 \
  --pipeline-id 2325947932 \
  --ref main
```

**What it does:**
1. Fetches real pipeline data
2. Calculates carbon emissions
3. Generates optimized YAML
4. **Creates branch + commit + MR automatically**

This is **fully autonomous** — it just runs from the command line instead of Duo Chat.

---

### Option 3: CI Job Trigger (Best for Production)

Add a webhook that triggers the EcoCI CI job after every pipeline.

**Setup:**
1. Go to project **Settings > Webhooks** (if accessible in hackathon)
2. URL: `https://gitlab.com/api/v4/projects/34560917/trigger/pipeline?token=YOUR_TRIGGER_TOKEN&ref=main`
3. Trigger: **Pipeline events**
4. The `.gitlab-ci.yml` already has the `ecoci_runner` job

**What happens:**
```
Pipeline completes → Webhook fires → Triggers ecoci_runner job → Creates MR
```

This is the **production** approach — zero manual intervention.

---

## What I've Fixed (Just Now)

I updated `agents/agent.yml` to:
1. **Try the tools first** (create_commit, create_merge_request)
2. **Give a clear error** if permission denied
3. **Fall back to manual instructions** only if tools fail

Wait 2-3 minutes for the catalog to update, then try again:
```
Analyze the pipeline for project 79403566 and create an MR
```

If the agent now says *"I don't have permission..."* — that's progress! It means it tried.

---

## For the Hackathon Demo

### What to Show in Your Video

**Don't show the Duo Chat failing to create MRs.** Instead:

### Option A: Show the Python CLI in action

```bash
# Record terminal showing:
$ python -m scripts.ecoci.main --project-id 79403566 --pipeline-id X --ref main
🌱 EcoCI: Fetching pipeline data...
✓ Fetched 5 jobs
✓ Calculated 125g CO₂
✓ Generated optimized YAML
✓ Created branch: ecoci/optimize-pipeline
✓ Created commit: abc123
✓ Created merge request !42
✓ Posted carbon dashboard comment

MR: https://gitlab.com/your-project/-/merge_requests/42
```

Then cut to the GitLab UI showing the MR with the diff and carbon table.

### Option B: Show the Flow (if it works)

1. Show creating an issue
2. @mention the flow
3. Show it creating the MR

### Option C: Show "Hybrid" Approach

1. Show agent analyzing in Duo Chat (gets real data, calculates carbon)
2. Copy the generated YAML
3. Show creating MR via GitLab UI with agent's analysis in description

**Narration:**
> "EcoCI fetches real pipeline data and calculates actual carbon emissions. 
> While the Duo Chat agent can't create commits due to sandbox security,
> the Python CLI provides full automation — or you can use the agent's analysis
> to manually create the MR with one click."

---

## The Real Solution (Post-Hackathon)

For this to work fully in Duo Chat, GitLab would need to:

1. **Allow agents to request write permissions** (OAuth-style flow)
2. **Use service accounts** for agent actions
3. **Implement impersonation** (agent acts as the user)

None of this exists yet — agents are designed for **read + analyze**, not **write + act**.

**But:** The Python CLI + CI job approach is actually **more production-ready** than a chat agent anyway. Companies want:
- Automated triggers (not "ask the agent every time")
- Audit trails (CI logs)
- Scheduled runs

So position it as: **"EcoCI provides both a Duo Chat interface for exploration AND automated CI/CD integration for production use."**

---

## Test It Now

1. **Wait 2-3 minutes** for catalog to update
2. Try: `Analyze the pipeline for project 79403566 and create an MR`
3. Check if it says "Attempting to create commit..." (progress!) or still gives manual steps (no change)
4. If still manual, use **Python CLI** for your demo instead

Let me know what happens!
