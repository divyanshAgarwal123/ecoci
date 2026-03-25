#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EXT_DIR="$ROOT_DIR/vscode-extensions/ecoci-vscode"
OUT_DIR="$ROOT_DIR/dist"

mkdir -p "$OUT_DIR"

if ! command -v npx >/dev/null 2>&1; then
  echo "❌ npx is required to package the VS Code extension."
  exit 1
fi

if [[ ! -f "$EXT_DIR/package.json" ]]; then
  echo "❌ Extension package.json not found at $EXT_DIR"
  exit 1
fi

pushd "$EXT_DIR" >/dev/null

# Install vsce on-demand if missing in cache
npx @vscode/vsce --version >/dev/null

OUT_FILE="$OUT_DIR/ecoci-vscode.vsix"
npx @vscode/vsce package --out "$OUT_FILE"

popd >/dev/null

echo "✅ VSIX package created: $OUT_FILE"
