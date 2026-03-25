#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"

mkdir -p "$DIST_DIR"

echo "📦 Building Python distribution artifacts"
python -m pip install --upgrade pip build
python -m build --sdist --wheel --outdir "$DIST_DIR"

echo "🧩 Building VS Code extension artifact"
chmod +x "$ROOT_DIR/scripts/package_vscode_extension.sh"
"$ROOT_DIR/scripts/package_vscode_extension.sh"

echo "✅ Release artifacts in $DIST_DIR"
ls -la "$DIST_DIR"
