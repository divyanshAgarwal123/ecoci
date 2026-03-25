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

## Phase 2: Optimization quality and safety

- Add confidence scoring to workflow changes.
- Add richer action pinning / security hardening checks.
- Add before/after KPI section in markdown + PR body.
- Add deterministic patch output mode for CI bots.

---

## Phase 3: VS Code extension GA

- Commands:
  - Analyze Current Repo
  - Optimize CI Workflows
  - Create Optimization PR
  - Show Carbon & Cost Summary
- Side panel UI for issues and recommendations.
- Inline diff preview before PR creation.

---

## Phase 4: Website + distribution

- Public website with:
  - Install docs (`pipx`, `pip`, VSIX)
  - Command examples
  - Screenshots and demo video
  - Quick start for GitHub repos
- Add release artifacts and versioned changelog.

---

## Phase 5: Multi-provider expansion

- GitLab parity under provider interface
- Jenkins and CircleCI read-only analyzers
- Enterprise policy profiles and org-level dashboards
