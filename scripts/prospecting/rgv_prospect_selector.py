#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


def default_exclusions_path() -> Path:
    repo_config = Path(__file__).resolve().parents[2] / "config" / "rgv-exclusions.md"
    if repo_config.exists():
        return repo_config
    return Path.home() / ".hermes" / "skills" / "rgv-exclusions.md"


def normalize_name(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def compact_domain(url: str | None) -> str | None:
    if not url:
        return None
    value = re.sub(r"^https?://", "", url, flags=re.I).strip().rstrip("/")
    return value or None


def city_from_address_info(item: dict[str, Any]) -> str | None:
    return (((item.get("address_info") or {}).get("city")) or "").strip() or None


@dataclass
class Exclusions:
    active_clients: set[str]
    known_prospects: set[str]
    recent: dict[str, date]


def parse_exclusions(path: Path) -> Exclusions:
    active_clients: set[str] = set()
    known_prospects: set[str] = set()
    recent: dict[str, date] = {}
    current_section = ""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line[3:].strip().lower()
            continue
        if not line or line.startswith("#"):
            continue
        if current_section.startswith("active clients") and line.startswith("- "):
            active_clients.add(normalize_name(line[2:]))
        elif current_section.startswith("known prospects") and line.startswith("- "):
            known_prospects.add(normalize_name(line[2:]))
        elif current_section.startswith("recently researched"):
            match = re.match(r"(\d{4}-\d{2}-\d{2})\s+\|\s+([^|]+)\s+\|", line)
            if match:
                try:
                    recent[normalize_name(match.group(2).strip())] = date.fromisoformat(match.group(1))
                except ValueError:
                    pass

    return Exclusions(active_clients=active_clients, known_prospects=known_prospects, recent=recent)


def load_items(input_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    task = (data.get("tasks") or [{}])[0]
    result = (task.get("result") or [{}])[0]
    items = result.get("items") or []
    return result, items


def exclusion_reason(
    item: dict[str, Any],
    exclusions: Exclusions,
    target_city: str | None,
    today: date,
) -> str | None:
    title = (item.get("title") or "").strip()
    normalized = normalize_name(title)
    if not title:
        return "missing_title"
    if normalized in exclusions.active_clients:
        return "active_client"
    if normalized in exclusions.known_prospects:
        return "known_prospect"
    recent_date = exclusions.recent.get(normalized)
    if recent_date and today - recent_date <= timedelta(days=30):
        return "recently_researched"
    city = city_from_address_info(item)
    if target_city and city and normalize_name(city) != normalize_name(target_city):
        return "outside_target_city_competitor_signal"
    phone = item.get("phone")
    website = item.get("url")
    if not phone and not website:
        return "no_contact_path"
    rating = ((item.get("rating") or {}).get("value"))
    if isinstance(rating, (int, float)) and rating < 2.5:
        return "terrible_reputation"
    return None


def to_index_row(
    item: dict[str, Any],
    *,
    run_date: str,
    city: str,
    niche: str,
    keyword: str,
    status: str,
    exclusion_reason_value: str | None,
) -> dict[str, Any]:
    rating = item.get("rating") or {}
    return {
        "date": run_date,
        "niche": niche,
        "city": city,
        "keyword": keyword,
        "business_name": item.get("title"),
        "rank": item.get("rank_absolute"),
        "rating": rating.get("value"),
        "review_count": rating.get("votes_count"),
        "website": compact_domain(item.get("url")),
        "phone": item.get("phone"),
        "status": status,
        "exclusion_reason": exclusion_reason_value,
    }


def append_index(index_path: Path, rows: list[dict[str, Any]]) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("a", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")


def render_summary(
    *,
    input_path: Path,
    index_path: Path,
    keyword: str,
    target_city: str,
    items: list[dict[str, Any]],
    shortlisted: list[dict[str, Any]],
    excluded: list[tuple[dict[str, Any], str]],
    appended_count: int,
) -> str:
    lines: list[str] = []
    lines.append(f"Query: {keyword}")
    lines.append(f"Target city: {target_city}")
    lines.append(f"Raw JSON: {input_path}")
    lines.append(f"Index file: {index_path}")
    lines.append(f"Total returned items: {len(items)}")
    lines.append("")
    lines.append("Exact rank 4-6 items:")
    ranks = [item for item in items if item.get("rank_absolute") in {4, 5, 6}]
    if not ranks:
        lines.append("- none")
    for item in ranks:
        rating = item.get("rating") or {}
        lines.append(
            f"- rank {item.get('rank_absolute')}: {item.get('title')} | "
            f"rating={rating.get('value')} reviews={rating.get('votes_count')} | "
            f"website={compact_domain(item.get('url')) or 'missing'} | "
            f"phone={item.get('phone') or 'missing'} | "
            f"city={city_from_address_info(item) or 'missing'} | "
            f"category={item.get('category') or 'missing'}"
        )
    lines.append("")
    lines.append("Shortlist:")
    if not shortlisted:
        lines.append("- none")
    for item in shortlisted:
        rating = item.get("rating") or {}
        notes: list[str] = []
        if not item.get("url") and item.get("phone"):
            notes.append("high_opportunity_no_website")
        lines.append(
            f"- {item.get('title')} (rank {item.get('rank_absolute')}) | "
            f"rating={rating.get('value')} reviews={rating.get('votes_count')} | "
            f"website={compact_domain(item.get('url')) or 'missing'} | "
            f"phone={item.get('phone') or 'missing'}"
            + (f" | notes={','.join(notes)}" if notes else "")
        )
    lines.append("")
    lines.append("Excluded:")
    if not excluded:
        lines.append("- none")
    for item, reason in excluded:
        lines.append(f"- {item.get('title')} (rank {item.get('rank_absolute')}): {reason}")
    lines.append("")
    competitor_signals = [(item, reason) for item, reason in excluded if reason == "outside_target_city_competitor_signal"]
    if competitor_signals:
        lines.append("Competitor signals:")
        for item, _reason in competitor_signals:
            rating = item.get("rating") or {}
            lines.append(
                f"- {item.get('title')} (rank {item.get('rank_absolute')}) is outside {target_city} "
                f"but still ranking here | city={city_from_address_info(item) or 'missing'} | "
                f"rating={rating.get('value')} reviews={rating.get('votes_count')}"
            )
        lines.append("")
    lines.append(f"Index rows appended: {appended_count}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic RGV prospect selector from saved DataForSEO JSON.")
    parser.add_argument("--input-json", required=True, type=Path)
    parser.add_argument("--index-jsonl", required=True, type=Path)
    parser.add_argument("--exclusions-md", default=default_exclusions_path(), type=Path)
    parser.add_argument("--city", required=True)
    parser.add_argument("--niche", required=True)
    parser.add_argument("--date", dest="run_date", required=False)
    parser.add_argument("--append-index", action="store_true")
    args = parser.parse_args()

    result, items = load_items(args.input_json)
    keyword = result.get("keyword") or ""
    run_date = args.run_date or args.input_json.parent.name
    exclusions = parse_exclusions(args.exclusions_md)
    today = date.fromisoformat(run_date)

    shortlisted: list[dict[str, Any]] = []
    excluded: list[tuple[dict[str, Any], str]] = []
    index_rows: list[dict[str, Any]] = []

    for item in items:
        rank = item.get("rank_absolute")
        if not isinstance(rank, int):
            continue
        if rank not in {4, 5, 6}:
            continue
        reason = exclusion_reason(item, exclusions, args.city, today)
        status = "shortlisted" if reason is None else "excluded"
        index_rows.append(
            to_index_row(
                item,
                run_date=run_date,
                city=args.city,
                niche=args.niche,
                keyword=keyword,
                status=status,
                exclusion_reason_value=reason,
            )
        )
        if reason is None:
            shortlisted.append(item)
        else:
            excluded.append((item, reason))

    if args.append_index and index_rows:
        append_index(args.index_jsonl, index_rows)

    print(
        render_summary(
            input_path=args.input_json,
            index_path=args.index_jsonl,
            keyword=keyword,
            target_city=args.city,
            items=items,
            shortlisted=shortlisted,
            excluded=excluded,
            appended_count=len(index_rows) if args.append_index else 0,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
