# Prospecting Pipeline

This repo now contains the deterministic overnight prospecting pipeline that was running locally.

## Layout

```text
config/rgv-exclusions.md
context/agency-profile.md
scripts/prospecting/
examples/data/
```

## Required VPS env vars

Put these in `/root/HermesBrain/.env`:

```env
OPENROUTER_API_KEY=
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=
FIRECRAWL_API_KEY=
```

## Pipeline Stages

1. Fetch raw map-pack data from DataForSEO
2. Parse ranks 4-6 and apply exclusions
3. Enrich shortlisted prospects with Firecrawl when a website exists
4. Score prospects deterministically
5. Write digest and per-prospect notes

## Linux Commands

Run a manual fetch:

```bash
cd /root/HermesBrain
bash scripts/prospecting/fetch_dataforseo_maps.sh "defense attorney mission tx" "26.2159,-98.3252,0" "2026-05-12" "defense-attorney-mission"
```

Run the full deterministic pipeline:

```bash
cd /root/HermesBrain
bash scripts/prospecting/run_pipeline.sh \
  "defense attorney mission tx" \
  "26.2159,-98.3252,0" \
  "Mission" \
  "criminal defense lawyer" \
  "2026-05-12" \
  "defense-attorney-mission"
```

## Outputs

The wrapper writes to:

- `runtime/data/dataforseo/YYYY-MM-DD/*.json`
- `runtime/data/dataforseo/index.jsonl`
- `runtime/data/firecrawl/YYYY-MM-DD/`
- `runtime/data/prospects/`
- `runtime/data/scores/YYYY-MM-DD/`
- `runtime/output/digests/`
- `runtime/output/notes/`

## Resume Prompt

Use this in Hermes after pulling the repo:

```text
Read /root/HermesBrain/context/agency-profile.md, /root/HermesBrain/config/rgv-exclusions.md, and /root/HermesBrain/docs/prospecting-pipeline.md. Then use the deterministic scripts in /root/HermesBrain/scripts/prospecting for any prospecting work instead of freehand parsing.
```
