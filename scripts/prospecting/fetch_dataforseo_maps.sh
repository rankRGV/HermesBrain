#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 4 ] || [ "$#" -gt 7 ]; then
  echo "Usage: $0 <keyword> <location_coordinate> <run_date> <slug> [se_type] [device] [os]" >&2
  exit 1
fi

KEYWORD="$1"
LOCATION_COORDINATE="$2"
RUN_DATE="$3"
SLUG="$4"
SE_TYPE="${5:-local_finder}"
DEVICE="${6:-desktop}"
OS="${7:-windows}"

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

case "$SE_TYPE" in
  local_finder|maps)
    ;;
  *)
    echo "Unsupported se_type: $SE_TYPE" >&2
    exit 1
    ;;
esac

curl -sS \
  -u "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" \
  -H "Content-Type: application/json" \
  -X POST "https://api.dataforseo.com/v3/serp/google/$SE_TYPE/live/advanced" \
  -d "[{\"keyword\":\"$KEYWORD\",\"location_coordinate\":\"$LOCATION_COORDINATE\",\"language_code\":\"en\",\"device\":\"$DEVICE\",\"os\":\"$OS\",\"depth\":20}]" \
  > "$OUTPUT_PATH"

echo "$OUTPUT_PATH"
