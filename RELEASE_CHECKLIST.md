# Release Checklist

Use this checklist for each public release.

## 1) Code and quality
- [ ] `git status` is clean.
- [ ] Core CLI commands pass manual smoke tests:
  - [ ] `ecoci version`
  - [ ] `ecoci doctor --provider github`
  - [ ] `ecoci analyze --provider github --json`
  - [ ] `ecoci optimize --provider github --json`
  - [ ] `ecoci pr create --provider github --dry-run`
- [ ] No critical lint/compile errors in changed files.

## 2) Packaging and docs
- [ ] `pyproject.toml` version updated.
- [ ] `CHANGELOG.md` updated with release notes.
- [ ] README quickstart still matches actual CLI behavior.
- [ ] Website pages updated if commands/install changed:
  - [ ] `website/index.html`
  - [ ] `website/downloads.html`

## 3) VS Code extension (MVP)
- [ ] Extension command list validated:
  - [ ] Analyze Current Repo
  - [ ] Optimize CI Workflows
  - [ ] Create Optimization PR
  - [ ] Show Carbon & Cost Summary
- [ ] VSIX package built (when release-ready):
  - [ ] Run `scripts/package_vscode_extension.sh`

## 4) GitHub release prep
- [ ] Create a release branch/tag.
- [ ] Push commits to `main`.
- [ ] Create GitHub Release notes from changelog.
- [ ] Attach VSIX artifact (if produced) and any additional binaries.

## 5) Post-release
- [ ] Validate install from clean environment.
- [ ] Validate sample workflow optimization on a public test repo.
- [ ] Update roadmap status in `ROADMAP.md`.
