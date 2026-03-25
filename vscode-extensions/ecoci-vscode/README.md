# EcoCI VS Code Extension (MVP)

This extension provides a lightweight UI wrapper around the `ecoci` CLI.

## Dashboard (Phase 2.2)

EcoCI now includes an Activity Bar view:

- Open **EcoCI** icon in Activity Bar
- Use **Analyze**, **Optimize**, and **PR Dry Run** actions
- View top findings, prioritized fixes, quality gate status, and key metrics

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
