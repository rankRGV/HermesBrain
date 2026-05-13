#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="$ROOT_DIR/skills/rankrgv-prospecting-vps"
SKILL_DEST="${HOME}/.hermes/skills/rankrgv-prospecting-vps"

mkdir -p "${HOME}/.hermes/skills"
rm -rf "$SKILL_DEST"
cp -r "$SKILL_SRC" "$SKILL_DEST"

echo "Installed skill to $SKILL_DEST"
