# EcoCI Product Roadmap

## Vision

EcoCI becomes a developer-facing CI optimization product with three install surfaces:

1. Universal CLI (`ecoci`)  
2. VS Code extension (`ecoci-vscode`)  
3. Public website for download, docs, and onboarding

---

## Phase 1 (Now): CLI reliability + GitHub-first MVP

### Goals
- Stabilize `analyze`, `optimize`, and `pr create` for GitHub.
- Improve setup diagnostics and onboarding.
- Preserve provider-pluggable architecture for future CI platforms.

### Delivered in this phase
- Provider abstraction (`CIProvider`)
- GitHub provider with workflow/runs/jobs/logs + PR + comments
- GitLab provider wrapper for backward compatibility
- New CLI diagnostics: `ecoci doctor`
- New safe PR preview mode: `ecoci pr create --dry-run`

### Exit criteria
- A new user can run:
  - `ecoci doctor --provider github`
  - `ecoci analyze --provider github --json`
  - `ecoci optimize --provider github`
  - `ecoci pr create --provider github --dry-run`

  ### Phase 1.1 (Current): Distribution onboarding

  - Add website download/install matrix for CLI + VS Code extension MVP.
  - Add quick verification command set for first-time users.
  - Link homepage to downloads and release sources.

  ### Phase 1.2 (Current): Release readiness

  - Add changelog and structured release checklist.
  - Add dynamic `ecoci version` resolution from package metadata.
  - Add VSIX packaging script scaffold for extension releases.

  ### Phase 1.3 (Current): Release automation

  - Add GitHub Actions release workflow for tag-based publishing.
  - Build and attach wheel/sdist/VSIX artifacts to GitHub Releases.
  - Add extension release metadata files required by packaging tooling.

---

## Phase 2 (In Progress): Optimization quality and safety

- Add confidence scoring to workflow changes.
- Add richer action pinning / security hardening checks.
- Add before/after KPI section in markdown + PR body.
- Add deterministic patch output mode for CI bots.

### Phase 2.0 (Current increment)

- Confidence-scored findings in `ecoci analyze` output and markdown report.
- Confidence-scored fix metadata and risk labels in `ecoci optimize` output.
- Unified diff preview support via `ecoci optimize --show-diff`.
- Structured PR body with impact section + rollback plan for safer PR review.

### Phase 2.1 (Current increment)

- Added workflow quality gate output (`pass` / `warn` / `fail`) based on finding severity.
- Added prioritized fix list with severity + confidence scoring for faster triage.
- Expanded GitHub workflow security checks:
  - `write-all` and broad write permission detection
  - `pull_request_target` risk flag
  - `actions/checkout` persisted credential warning
  - potential secret echo and hardcoded credential pattern detection
- Improved run metric realism with runner-core and OS-aware energy estimation.

### Phase 2.2 (Current increment)

- Upgraded VS Code extension from command-only output to dashboard UX.
- Added Activity Bar EcoCI container + webview dashboard panel.
- Added one-click dashboard actions for Analyze, Optimize, and PR Dry Run.
- Surfaced findings, prioritized fixes, quality gate, and key metrics directly in extension UI.

### Phase 2.3 (Current increment)

- Added deterministic unified patch mode for CI bots (`optimize --deterministic-patch`).
- Added patch export option (`optimize --patch-file`) for automation workflows.
- Added heuristic before/after KPI projection in markdown reports.
- Added before/after KPI projection section to generated PR body.

---

## Phase 3: VS Code extension GA

- Commands:
  - Analyze Current Repo
  - Optimize CI Workflows
  - Create Optimization PR
  - Show Carbon & Cost Summary
- Side panel UI for issues and recommendations.
- Inline diff preview before PR creation.

### Phase 3.1 (Current increment)

- Added dashboard provider selector (`github` / `gitlab`) with optional repo/project input.
- Added inline diff preview rendering in dashboard Optimize action.
- Added provider-aware Analyze/Optimize/PR dry-run execution from dashboard.

### Phase 3.2 (Current increment)

- Added one-click **Create PR** action directly from dashboard.
- Added optional dashboard fields for PR title and run-id.
- Added success state rendering with created PR link and key run metrics (when available).

---

## Phase 4: Website + distribution

- Public website with:
  - Install docs (`pipx`, `pip`, VSIX)
  - Command examples
  - Screenshots and demo video
  - Quick start for GitHub repos
- Add release artifacts and versioned changelog.

### Phase 4.1 (Current increment)

- Upgraded website homepage to product-style landing page with clearer navigation and CTAs.
- Expanded downloads page with direct artifact guidance (wheel/sdist/VSIX).
- Added quick verification paths for both CLI and VS Code dashboard workflows.

### Phase 4.2 (Current increment)

- Added dedicated website quickstart page for first-run onboarding.
- Linked quickstart from homepage and downloads pages.
- Added install → analyze → optimize → PR flow in one guided sequence.

### Phase 4.3 (Current increment)

- Added command examples cookbook page for common CLI workflows.
- Added troubleshooting tips for repo detection, token scope, and run metrics.
- Linked examples page across website navigation for faster onboarding.

### Phase 4.4 (Current increment)

- Added dedicated media kit page for screenshots and demo video flow.
- Added reusable demo checklist for CLI and VS Code extension walkthroughs.
- Linked media kit across website pages to support release storytelling.

---

## Phase 5: Multi-provider expansion

- GitLab parity under provider interface
- Jenkins and CircleCI read-only analyzers
- Enterprise policy profiles and org-level dashboards

### Phase 5.1 (Current increment)

- Enabled CLI provider selector for both GitHub and GitLab on `doctor`, `analyze`, `optimize`, and `pr create`.
- Added provider-aware repo handling (`owner/repo` for GitHub, `project_id_or_path` for GitLab).
- Added GitLab default branch parity and MR URL handling in PR flow.
- Added README examples for GitLab provider usage.

### Phase 5.2 (Current increment)

- Added GitLab pipeline job retrieval for `--run-id` flows (`run-id` as pipeline id).
- Added GitLab run metrics computation (duration, cost, energy, CO2) parity.
- Enabled provider-agnostic metric reporting path in analysis for GitHub and GitLab.
