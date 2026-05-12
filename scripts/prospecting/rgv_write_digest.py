#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def price_estimate(offer: str) -> str:
    mapping = {
        "full_website_gbp_reviews": "$600-$1200/mo",
        "website_refresh_gbp_optimization": "$400-$900/mo",
        "gbp_optimization": "$300-$600/mo",
    }
    return mapping.get(offer, "$300-$900/mo")


def key_gap(entry: dict[str, Any]) -> str:
    flags = entry.get("opportunity_flags") or []
    if "high_opportunity_no_website" in flags:
        return "No website while already ranking"
    if "thin_main_content" in flags:
        return "Thin website content"
    if "no_obvious_cta" in flags:
        return "Weak call to action"
    if "no_obvious_faq" in flags:
        return "No FAQ content"
    return "Fixable local SEO gap"


def opener(entry: dict[str, Any]) -> str:
    if "high_opportunity_no_website" in (entry.get("opportunity_flags") or []):
        return (
            f"{entry['business_name']} is already ranking in Mission without a website, "
            "which makes this the cleanest upside case in the batch."
        )
    return (
        f"{entry['business_name']} already ranks in the target band but the site is thin and underbuilt, "
        "so there is a clear fixable support gap."
    )


def build_digest(scores_payload: dict[str, Any]) -> str:
    scores = scores_payload.get("scores") or []
    competitors = scores_payload.get("competitor_context") or []
    run_date = scores_payload.get("date")
    city = scores_payload.get("city")
    niche = scores_payload.get("niche")
    top_a = [entry for entry in scores if entry.get("bucket") == "A"]
    top_b = [entry for entry in scores if entry.get("bucket") == "B"]
    top_c = [entry for entry in scores if entry.get("bucket") == "C"]

    lines: list[str] = []
    lines.append(f"# Prospect Digest — {run_date}")
    lines.append("")
    lines.append(f"**Niches searched:** {niche}")
    lines.append(f"**Cities searched:** {city}")
    lines.append(f"**Prospects reviewed:** {len(scores)}")
    lines.append(
        f"**Grade A:** {len(top_a)} | **Grade B:** {len(top_b)} | "
        f"**Grade C:** {len(top_c)} | **Disqualified:** {len(competitors)}"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Top Picks — Call This Week")
    lines.append("")
    lines.append("| Business | City | Niche | Rank | Key Gap | Score | Price Est. |")
    lines.append("|----------|------|-------|------|---------|-------|------------|")
    for entry in scores:
        lines.append(
            f"| {entry['business_name']} | {city} | {niche} | #{entry['rank']} | "
            f"{key_gap(entry)} | {entry['score_total']}/100 | {price_estimate(entry['recommended_offer'])} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    best = scores[0] if scores else None
    if best:
        lines.append("## Best First Call")
        lines.append("")
        lines.append(f"**{best['business_name']}** — {opener(best)}")
        lines.append("")
        lines.append("---")
        lines.append("")

    if len(scores) > 1:
        lines.append("## Grade B — Save for Later")
        lines.append("")
        for entry in scores[1:]:
            lines.append(f"- {entry['business_name']} ({city}, {niche}) — {key_gap(entry)}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Run Log")
    lines.append("")
    lines.append(f"- Date: {run_date}")
    lines.append(f"- Businesses reviewed: {len(scores)}")
    lines.append(f"- Competitor signals: {len(competitors)}")
    lines.append(f"- Errors: None in deterministic writer")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write deterministic RGV morning digest from scored prospects.")
    parser.add_argument("--scores-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args()

    payload = load_json(args.scores_json)
    digest = build_digest(payload)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(digest, encoding="utf-8")
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
