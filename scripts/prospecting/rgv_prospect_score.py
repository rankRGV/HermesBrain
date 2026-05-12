#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_index_rows(index_path: Path, *, run_date: str, city: str, niche: str | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, Any, Any]] = set()
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
            key = (
                str(row.get("business_name") or "").strip().lower(),
                row.get("rank"),
                row.get("status"),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def load_enrichment(summary_path: Path) -> dict[str, dict[str, Any]]:
    if not summary_path.exists():
        return {}
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    return {entry["business_name"]: entry for entry in payload}


def score_rank(rank: int | None) -> tuple[int, str]:
    mapping = {
        4: (26, "rank_4_in_target_band"),
        5: (28, "rank_5_in_target_band"),
        6: (30, "rank_6_in_target_band"),
    }
    return mapping.get(rank, (0, "rank_outside_target_band"))


def score_reviews(review_count: int | None, rating: float | int | None) -> tuple[int, str]:
    count = review_count or 0
    value = float(rating or 0)
    if count <= 5 and value >= 4.0:
        return 18, "low_review_count_high_rating"
    if count <= 10:
        return 16, "low_review_count"
    if count <= 25:
        return 12, "moderate_review_count"
    return 8, "heavier_review_gap"


def score_website(row: dict[str, Any], enrichment: dict[str, Any] | None) -> tuple[int, str]:
    website = row.get("website")
    if not website:
        return 30, "no_website_greenfield_opportunity"
    if not enrichment:
        return 12, "website_present_no_verified_enrichment"

    flags = set(enrichment.get("opportunity_flags") or [])
    if enrichment.get("enrichment_status") == "scraped":
        score = 10
        if "thin_main_content" in flags:
            score += 6
        if "no_obvious_cta" in flags:
            score += 5
        if "no_obvious_faq" in flags:
            score += 4
        if "no_obvious_about_page" in flags:
            score += 5
        return min(score, 30), "verified_website_gaps"
    return 12, "website_present_limited_signal"


def score_opportunity(row: dict[str, Any], enrichment: dict[str, Any] | None) -> tuple[int, str]:
    phone = row.get("phone")
    website = row.get("website")
    if not phone:
        return 4, "weak_contact_path"
    if not website:
        return 20, "phone_present_no_website"
    if enrichment and enrichment.get("enrichment_status") == "scraped":
        return 18, "verified_fixable_website"
    return 14, "contactable_but_less_verified"


def bucket(total: int) -> str:
    if total >= 80:
        return "A"
    if total >= 60:
        return "B"
    return "C"


def recommended_offer(row: dict[str, Any], enrichment: dict[str, Any] | None) -> str:
    if not row.get("website"):
        return "full_website_gbp_reviews"
    if enrichment and enrichment.get("enrichment_status") == "scraped":
        return "website_refresh_gbp_optimization"
    return "gbp_optimization"


def summarize_row(row: dict[str, Any], enrichment: dict[str, Any] | None) -> dict[str, Any]:
    rank_points, rank_reason = score_rank(row.get("rank"))
    review_points, review_reason = score_reviews(row.get("review_count"), row.get("rating"))
    website_points, website_reason = score_website(row, enrichment)
    opportunity_points, opportunity_reason = score_opportunity(row, enrichment)
    total = rank_points + review_points + website_points + opportunity_points
    return {
        "business_name": row.get("business_name"),
        "rank": row.get("rank"),
        "rating": row.get("rating"),
        "review_count": row.get("review_count"),
        "website": row.get("website"),
        "phone": row.get("phone"),
        "score_total": total,
        "bucket": bucket(total),
        "recommended_offer": recommended_offer(row, enrichment),
        "score_breakdown": {
            "rank": {"points": rank_points, "max": 30, "reason": rank_reason},
            "reviews": {"points": review_points, "max": 20, "reason": review_reason},
            "website": {"points": website_points, "max": 30, "reason": website_reason},
            "opportunity": {"points": opportunity_points, "max": 20, "reason": opportunity_reason},
        },
        "opportunity_flags": (enrichment or {}).get("opportunity_flags") or [],
        "enrichment_status": (enrichment or {}).get("enrichment_status"),
        "notes": (enrichment or {}).get("notes") or [],
    }


def render_text(scores: list[dict[str, Any]], competitor_rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("Deterministic Prospect Scoring")
    lines.append("")
    for entry in scores:
        lines.append(f"{entry['business_name']}")
        lines.append(f"Score: {entry['score_total']}/100")
        lines.append(
            f"- Rank: {entry['score_breakdown']['rank']['points']}/30 ({entry['score_breakdown']['rank']['reason']})"
        )
        lines.append(
            f"- Reviews: {entry['score_breakdown']['reviews']['points']}/20 ({entry['score_breakdown']['reviews']['reason']})"
        )
        lines.append(
            f"- Website: {entry['score_breakdown']['website']['points']}/30 ({entry['score_breakdown']['website']['reason']})"
        )
        lines.append(
            f"- Opportunity: {entry['score_breakdown']['opportunity']['points']}/20 ({entry['score_breakdown']['opportunity']['reason']})"
        )
        lines.append(f"Bucket: {entry['bucket']}")
        lines.append(f"Recommended offer: {entry['recommended_offer']}")
        if entry["opportunity_flags"]:
            lines.append(f"Opportunity flags: {', '.join(entry['opportunity_flags'])}")
        lines.append("")

    if competitor_rows:
        lines.append("Competitor Context")
        for row in competitor_rows:
            lines.append(
                f"- {row.get('business_name')} (rank {row.get('rank')}) excluded: {row.get('exclusion_reason')}"
            )
        lines.append("")

    if scores:
        best = max(scores, key=lambda item: item["score_total"])
        lines.append("Best First Outreach Target")
        lines.append(f"- {best['business_name']} ({best['score_total']}/100)")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic RGV prospect scoring.")
    parser.add_argument("--index-jsonl", required=True, type=Path)
    parser.add_argument("--enrichment-summary", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--niche", required=False)
    args = parser.parse_args()

    rows = load_index_rows(args.index_jsonl, run_date=args.date, city=args.city, niche=args.niche)
    enrichment = load_enrichment(args.enrichment_summary)

    shortlisted = [row for row in rows if row.get("status") == "shortlisted"]
    competitors = [row for row in rows if row.get("status") == "excluded"]

    scores = [summarize_row(row, enrichment.get(row.get("business_name"))) for row in shortlisted]
    scores.sort(key=lambda item: item["score_total"], reverse=True)

    payload = {
        "date": args.date,
        "city": args.city,
        "niche": args.niche,
        "scores": scores,
        "competitor_context": competitors,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(render_text(scores, competitors))
    return 0


if __name__ == "__main__":
    sys.exit(main())
