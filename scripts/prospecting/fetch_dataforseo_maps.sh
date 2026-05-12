#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 <keyword> <location_coordinate> <run_date> <slug>" >&2
  exit 1
fi

KEYWORD="$1"
LOCATION_COORDINATE="$2"
RUN_DATE="$3"
SLUG="$4"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

: "${DATAFORSEO_LOGIN:?DATAFORSEO_LOGIN is required}"
: "${DATAFORSEO_PASSWORD:?DATAFORSEO_PASSWORD is required}"

OUTPUT_DIR="$ROOT_DIR/runtime/data/dataforseo/$RUN_DATE"
mkdir -p "$OUTPUT_DIR"
OUTPUT_PATH="$OUTPUT_DIR/$SLUG.json"

curl -sS \
  -u "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" \
  -H "Content-Type: application/json" \
  -X POST "https://api.dataforseo.com/v3/serp/google/maps/live/advanced" \
  -d "[{\"keyword\":\"$KEYWORD\",\"location_coordinate\":\"$LOCATION_COORDINATE\",\"language_code\":\"en\",\"device\":\"mobile\",\"depth\":10}]" \
  > "$OUTPUT_PATH"

echo "$OUTPUT_PATH"
