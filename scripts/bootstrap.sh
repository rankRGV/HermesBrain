#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$ROOT_DIR/context"
mkdir -p "$ROOT_DIR/docs"
mkdir -p "$ROOT_DIR/prompts"
mkdir -p "$ROOT_DIR/scripts"

if [ ! -f "$ROOT_DIR/.env" ] && [ -f "$ROOT_DIR/.env.example" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "Created $ROOT_DIR/.env from template"
fi

chmod 700 "$ROOT_DIR/scripts"

echo "HermesBrain bootstrap complete at $ROOT_DIR"
