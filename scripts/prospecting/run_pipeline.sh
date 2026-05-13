#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 6 ] || [ "$#" -gt 9 ]; then
  echo "Usage: $0 <keyword> <location_coordinate> <city> <niche> <run_date> <slug> [se_type] [device] [os]" >&2
  exit 1
fi

KEYWORD="$1"
LOCATION_COORDINATE="$2"
CITY="$3"
NICHE="$4"
RUN_DATE="$5"
SLUG="$6"
SE_TYPE="${7:-local_finder}"
DEVICE="${8:-desktop}"
OS="${9:-windows}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

RAW_JSON="$(bash "$ROOT_DIR/scripts/prospecting/fetch_dataforseo_maps.sh" "$KEYWORD" "$LOCATION_COORDINATE" "$RUN_DATE" "$SLUG" "$SE_TYPE" "$DEVICE" "$OS")"
INDEX_JSONL="$ROOT_DIR/runtime/data/dataforseo/index.jsonl"
EXCLUSIONS_MD="$ROOT_DIR/config/rgv-exclusions.md"
FIRECRAWL_DIR="$ROOT_DIR/runtime/data/firecrawl/$RUN_DATE"
SCORES_JSON="$ROOT_DIR/runtime/data/prospects/${RUN_DATE}-${SLUG}-scores.json"
DIGEST_MD="$ROOT_DIR/runtime/output/digests/${RUN_DATE}-${SLUG}.md"
NOTES_DIR="$ROOT_DIR/runtime/output/notes"
FINAL_SCORE_JSON="$ROOT_DIR/runtime/data/scores/$RUN_DATE/${CITY,,}-${SLUG}.json"

mkdir -p "$(dirname "$INDEX_JSONL")" "$(dirname "$SCORES_JSON")" "$(dirname "$DIGEST_MD")" "$(dirname "$FINAL_SCORE_JSON")" "$NOTES_DIR"

python3 "$ROOT_DIR/scripts/prospecting/rgv_prospect_selector.py" \
  --input-json "$RAW_JSON" \
  --index-jsonl "$INDEX_JSONL" \
  --exclusions-md "$EXCLUSIONS_MD" \
  --city "$CITY" \
  --niche "$NICHE" \
  --date "$RUN_DATE" \
  --append-index

python3 "$ROOT_DIR/scripts/prospecting/rgv_prospect_enrichment.py" \
  --index-jsonl "$INDEX_JSONL" \
  --output-dir "$FIRECRAWL_DIR" \
  --date "$RUN_DATE" \
  --city "$CITY" \
  --niche "$NICHE"

python3 "$ROOT_DIR/scripts/prospecting/rgv_prospect_score.py" \
  --index-jsonl "$INDEX_JSONL" \
  --enrichment-summary "$FIRECRAWL_DIR/enrichment-summary.json" \
  --output-json "$SCORES_JSON" \
  --date "$RUN_DATE" \
  --city "$CITY" \
  --niche "$NICHE"

cp "$SCORES_JSON" "$FINAL_SCORE_JSON"

python3 "$ROOT_DIR/scripts/prospecting/rgv_write_digest.py" \
  --scores-json "$SCORES_JSON" \
  --output-md "$DIGEST_MD"

python3 "$ROOT_DIR/scripts/prospecting/rgv_write_prospect_notes.py" \
  --scores-json "$SCORES_JSON" \
  --output-dir "$NOTES_DIR"

echo "Raw JSON: $RAW_JSON"
echo "Index: $INDEX_JSONL"
echo "Enrichment: $FIRECRAWL_DIR/enrichment-summary.json"
echo "Scores: $SCORES_JSON"
echo "Digest: $DIGEST_MD"
echo "Notes dir: $NOTES_DIR/$RUN_DATE"
echo "SERP mode: $SE_TYPE | device: $DEVICE | os: $OS"
