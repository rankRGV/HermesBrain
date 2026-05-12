#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$ROOT_DIR/context"
mkdir -p "$ROOT_DIR/config"
mkdir -p "$ROOT_DIR/docs"
mkdir -p "$ROOT_DIR/examples"
mkdir -p "$ROOT_DIR/prompts"
mkdir -p "$ROOT_DIR/scripts"
mkdir -p "$ROOT_DIR/runtime/data"
mkdir -p "$ROOT_DIR/runtime/output"

if [ ! -f "$ROOT_DIR/.env" ] && [ -f "$ROOT_DIR/.env.example" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "Created $ROOT_DIR/.env from template"
fi

chmod 700 "$ROOT_DIR/scripts"
find "$ROOT_DIR/scripts" -type f -name "*.sh" -exec chmod 700 {} \;

echo "HermesBrain bootstrap complete at $ROOT_DIR"
