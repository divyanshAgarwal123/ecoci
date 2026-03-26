# EcoCI VS Code Extension (MVP)

This extension provides a lightweight UI wrapper around the `ecoci` CLI.

## Dashboard (Phase 2.2)

EcoCI now includes an Activity Bar view:

- Open **EcoCI** icon in Activity Bar
- Select provider (`github` or `gitlab`) and optional repo/project value
- Optionally set PR title and run ID from the dashboard inputs
- Use **Analyze**, **Optimize**, **PR Dry Run**, and **Create PR** actions
- View top findings, prioritized fixes, quality gate status, and key metrics
- View inline optimization diff preview from the dashboard

## Commands

- EcoCI: Open Dashboard
- EcoCI: Analyze Current Repo
- EcoCI: Optimize CI Workflows
- EcoCI: Create Optimization PR
- EcoCI: Show Carbon & Cost Summary

## Requirements

- `ecoci` CLI installed and available on PATH
- For GitHub PR creation: `GITHUB_TOKEN` environment variable

## Development

Run this extension in VS Code Extension Development Host using this folder:

`vscode-extensions/ecoci-vscode`
