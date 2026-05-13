---
name: rankrgv-prospecting-vps
description: Run RankRGV prospecting on the Hermes VPS using the repo-backed deterministic pipeline. Use this whenever the user asks for prospects, leads, shortlist businesses, overnight prospecting, map-pack prospecting, local SEO opportunities, or asks for prospects in a niche and city like "get me prospects for HVAC in Mission" or "find dental prospects in McAllen." This skill should also trigger when the user asks to resume, summarize, or review the latest prospecting run from runtime outputs.
---

# RankRGV Prospecting VPS

This skill turns Hermes into an operator for the RankRGV VPS prospecting workflow.

## Read first

Before doing prospecting work, read these files in order:

1. `/root/HermesBrain/context/hermes-operator-memory.md`
2. `/root/HermesBrain/context/agency-profile.md`
3. `/root/HermesBrain/config/rgv-exclusions.md`
4. `/root/HermesBrain/docs/prospecting-pipeline.md`

If they conflict with memory or chat history, the repo files win.

## Trigger behavior

Use this skill when the user asks for any of:

- prospects for a service and city
- local businesses to pitch
- overnight prospecting
- shortlist businesses in a niche/city
- review the latest prospecting output
- resume where the last VPS run left off

The user should not need to specify script names or repo paths.

## Core operating rules

- Use deterministic scripts in `/root/HermesBrain/scripts/prospecting` whenever a script exists for a step.
- Never freehand parse DataForSEO responses if raw JSON or a parser script exists.
- Check `/root/HermesBrain/runtime/` before summarizing prior work.
- Obey `/root/HermesBrain/config/rgv-exclusions.md` before shortlisting prospects.
- If required files or env vars are missing, stop and say exactly what is missing.
- Do not change scope without approval. If the requested city returns too few listings or no viable rank 4-8 candidates, summarize the result and ask before broadening to nearby cities, alternate locations, adjacent niches, or modified keywords.
- Lack of user response is not approval. If a clarification request is unanswered or times out, stop and wait. Do not continue automatically.

## Required env vars

Expect these in `/root/HermesBrain/.env`:

- `OPENROUTER_API_KEY`
- `DATAFORSEO_LOGIN`
- `DATAFORSEO_PASSWORD`
- `FIRECRAWL_API_KEY`

## When the user wants a new run

Collect or infer:

1. niche or service
2. city
3. run date (default to today if not specified)

Use the deterministic wrapper:

```bash
cd /root/HermesBrain
bash scripts/prospecting/run_pipeline.sh \
  "[keyword]" \
  "[lat],[lng],0" \
  "[City]" \
  "[niche]" \
  "[YYYY-MM-DD]" \
  "[slug]" \
  "local_finder" \
  "desktop" \
  "windows"
```

Default to `local_finder` because it better matches the Google Places / local discovery experience a prospect sees.

## City coordinates

Use these defaults unless the user explicitly changes scope:

- McAllen: `26.2034,-98.2300,0`
- Mission: `26.2159,-98.3252,0`
- Edinburg: `26.3017,-98.1633,0`

If the city is outside these, say the coordinate mapping is missing and ask for it or fetch it from an approved source/workflow if one exists.

## Keyword construction

Default format:

- `"[service] [city] tx"`

Examples:

- `"hvac mission tx"`
- `"criminal defense lawyer mission tx"`
- `"dentist mcallen tx"`

## Slug construction

Use:

- lowercase
- words separated with hyphens
- example: `defense-attorney-mission`

## Output format

For new runs, return:

1. shortlisted prospects
2. excluded prospects and why
3. scores and recommended offers
4. exact output file paths
5. any API/env failures

For summary-only requests, do not run a new fetch. Read the latest relevant files under `/root/HermesBrain/runtime/` and summarize them.

## Zero-result behavior

If the requested run produces no viable shortlisted prospects:

1. report the exact reason
2. include the raw output path
3. suggest one or more nearby-city or broader-scope options
4. stop and ask which option to run next

Do not automatically launch the fallback runs unless the user explicitly approves the broader scope.

If the user does not answer the clarification request, do not pick an option yourself.

## Fast paths

If the user says "just get me prospects for X in Y":

1. load the source-of-truth files
2. infer today's date
3. build keyword and slug
4. run the pipeline
5. return the required output format

If the user says "what happened last run":

1. inspect the newest files in `/root/HermesBrain/runtime/`
2. summarize from those outputs only

## Examples

Example 1:
User: `Get me some prospects for pest control in McAllen`

Action:
- load source files
- use keyword `pest control mcallen tx`
- use coordinate `26.2034,-98.2300,0`
- run the pipeline
- summarize results

Example 2:
User: `Review the latest Mission legal prospecting run`

Action:
- do not fetch
- inspect latest runtime outputs for the relevant run
- summarize shortlist, exclusions, scores, and paths
