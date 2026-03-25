# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

## [0.1.2] - 2026-03-26

### Added
- `ecoci doctor --provider github` diagnostics command for setup/auth/workflow checks.
- `ecoci pr create --dry-run` mode to preview PR payload safely.
- Product roadmap document [ROADMAP.md](ROADMAP.md).
- Website scaffold and install/download matrix pages in [website/index.html](website/index.html) and [website/downloads.html](website/downloads.html).
- Provider-pluggable architecture with:
  - [scripts/ecoci/providers/base.py](scripts/ecoci/providers/base.py)
  - [scripts/ecoci/providers/github.py](scripts/ecoci/providers/github.py)
  - [scripts/ecoci/providers/gitlab.py](scripts/ecoci/providers/gitlab.py)
- GitHub-first CLI commands:
  - `ecoci analyze --provider github`
  - `ecoci optimize --provider github`
  - `ecoci pr create --provider github`
- GitHub run metrics + PR dashboard comment support.
- VS Code extension MVP scaffold under [vscode-extensions/ecoci-vscode](vscode-extensions/ecoci-vscode).

### Changed
- `ecoci version` now resolves version dynamically from package metadata with pyproject fallback.
- Converted `ecoci-test-project` from embedded gitlink to regular tracked files.

## [0.1.1] - 2026-03-25

### Added
- Complex demo pipeline and demo project assets for optimization demonstrations.

## [0.1.0] - 2026-02-15

### Added
- Initial EcoCI agent, analyzers, optimization engine, and MR automation foundation.
