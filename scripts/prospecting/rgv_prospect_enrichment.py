#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "prospect"


def load_shortlisted_rows(index_path: Path, *, run_date: str, city: str, niche: str | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, Any]] = set()
    if not index_path.exists():
        return rows
    with index_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("date") != run_date:
                continue
            if (row.get("city") or "").lower() != city.lower():
                continue
            if niche and (row.get("niche") or "").lower() != niche.lower():
                continue
            if row.get("status") != "shortlisted":
                continue
            key = (str(row.get("business_name") or "").strip().lower(), row.get("rank"))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def firecrawl_scrape(url: str, api_key: str) -> dict[str, Any]:
    payload = {
        "url": url,
        "formats": ["markdown", "html", "links"],
        "onlyMainContent": True,
        "timeout": 60000,
        "location": {"country": "US", "languages": ["en-US"]},
    }
    request = urllib.request.Request(
        FIRECRAWL_SCRAPE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def summarize_scrape(row: dict[str, Any], scrape: dict[str, Any] | None) -> dict[str, Any]:
    base = {
        "business_name": row.get("business_name"),
        "city": row.get("city"),
        "niche": row.get("niche"),
        "rank": row.get("rank"),
        "phone": row.get("phone"),
        "website": row.get("website"),
    }

    if not row.get("website"):
        base.update(
            {
                "enrichment_status": "no_website",
                "opportunity_flags": ["high_opportunity_no_website"],
                "notes": ["No website in Phase 1 parser output. Firecrawl scrape skipped."],
            }
        )
        return base

    if not scrape:
        base.update(
            {
                "enrichment_status": "scrape_failed",
                "opportunity_flags": [],
                "notes": ["Firecrawl scrape failed or returned no data."],
            }
        )
        return base

    data = scrape.get("data") or scrape
    markdown = data.get("markdown") or ""
    links = data.get("links") or []
    metadata = data.get("metadata") or {}

    signals: list[str] = []
    notes: list[str] = []

    city = (row.get("city") or "").lower()
    if city and city not in markdown.lower():
        signals.append("city_not_obvious_in_main_content")
    if "faq" not in markdown.lower():
        signals.append("no_obvious_faq")
    if "call" not in markdown.lower() and "contact" not in markdown.lower():
        signals.append("no_obvious_cta")
    if len(markdown.strip()) < 500:
        signals.append("thin_main_content")
    if not any("/about" in str(link).lower() for link in links):
        signals.append("no_obvious_about_page")

    notes.append(f"Firecrawl scrape executed for {row.get('website')}")
    notes.append(f"Source URL: {metadata.get('sourceURL') or row.get('website')}")
    notes.append(f"Status code: {metadata.get('statusCode') or metadata.get('pageStatusCode') or 'unknown'}")

    base.update(
        {
            "enrichment_status": "scraped",
            "opportunity_flags": signals,
            "notes": notes,
            "firecrawl_metadata": {
                "title": metadata.get("title"),
                "description": metadata.get("description"),
                "sourceURL": metadata.get("sourceURL"),
                "statusCode": metadata.get("statusCode") or metadata.get("pageStatusCode"),
            },
        }
    )
    return base


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Firecrawl enrichment for shortlisted RGV prospects.")
    parser.add_argument("--index-jsonl", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--niche", required=False)
    parser.add_argument("--firecrawl-api-key", required=False)
    args = parser.parse_args()

    api_key = args.firecrawl_api_key or os.getenv("FIRECRAWL_API_KEY")
    rows = load_shortlisted_rows(args.index_jsonl, run_date=args.date, city=args.city, niche=args.niche)
    if not rows:
        print("No shortlisted rows found for the requested date/city/niche.", file=sys.stderr)
        return 1

    summaries: list[dict[str, Any]] = []
    for row in rows:
        slug = slugify(str(row.get("business_name") or "prospect"))
        scrape_payload = None
        if row.get("website"):
            if not api_key:
                summary = summarize_scrape(row, None)
                summary["enrichment_status"] = "missing_api_key"
                summary["notes"] = ["FIRECRAWL_API_KEY missing. Scrape not attempted."]
                summaries.append(summary)
                continue
            try:
                scrape_payload = firecrawl_scrape(f"http://{row['website']}" if not str(row["website"]).startswith("http") else row["website"], api_key)
                save_json(args.output_dir / f"{slug}.firecrawl.json", scrape_payload)
            except urllib.error.HTTPError as exc:
                error_text = exc.read().decode("utf-8", errors="replace")
                scrape_payload = {"error": {"status": exc.code, "body": error_text}}
                save_json(args.output_dir / f"{slug}.firecrawl.error.json", scrape_payload)
            except Exception as exc:  # noqa: BLE001
                scrape_payload = {"error": {"message": str(exc)}}
                save_json(args.output_dir / f"{slug}.firecrawl.error.json", scrape_payload)

        summary = summarize_scrape(row, scrape_payload if scrape_payload and "error" not in scrape_payload else None)
        if scrape_payload and "error" in scrape_payload:
            summary["enrichment_status"] = "scrape_failed"
            summary["notes"] = [f"Firecrawl scrape failed: {scrape_payload['error']}"]
        summaries.append(summary)

    save_json(args.output_dir / "enrichment-summary.json", summaries)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
