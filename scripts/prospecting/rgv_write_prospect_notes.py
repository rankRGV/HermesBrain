#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def package_name(offer: str) -> tuple[str, str]:
    mapping = {
        "full_website_gbp_reviews": ("Local SEO Starter", "$600-$1200/mo"),
        "website_refresh_gbp_optimization": ("GBP + Website Refresh", "$400-$900/mo"),
        "gbp_optimization": ("GBP Only", "$300-$600/mo"),
    }
    return mapping.get(offer, ("Local SEO Starter", "$300-$900/mo"))


def quick_wins(entry: dict[str, Any]) -> list[str]:
    flags = entry.get("opportunity_flags") or []
    wins: list[str] = []
    if "high_opportunity_no_website" in flags:
        wins.append("Launch a simple website with clear service and location signals")
        wins.append("Connect the website to GBP and add a conversion-focused contact flow")
        wins.append("Start a review generation system to widen the trust gap")
        return wins
    if "thin_main_content" in flags:
        wins.append("Expand homepage content with clear service and location language")
    if "no_obvious_cta" in flags:
        wins.append("Add a stronger call now and consultation CTA")
    if "no_obvious_faq" in flags:
        wins.append("Add FAQ content around common legal questions")
    if "no_obvious_about_page" in flags:
        wins.append("Add a stronger attorney profile and trust section")
    return wins[:3] or ["Tighten GBP and website support signals"]


def why_this_prospect(entry: dict[str, Any], city: str) -> str:
    flags = entry.get("opportunity_flags") or []
    if "high_opportunity_no_website" in flags:
        return (
            f"{entry['business_name']} is already ranking in {city} without a website, which makes the upside unusually clean. "
            "Adding a basic site and stronger GBP support could improve both trust and conversion quickly."
        )
    return (
        f"{entry['business_name']} is already in the target ranking band, but the website is underbuilt. "
        "The current gaps are visible and fixable, which makes this a practical 60 to 90 day opportunity."
    )


def outreach_opener(entry: dict[str, Any], city: str) -> str:
    flags = entry.get("opportunity_flags") or []
    if "high_opportunity_no_website" in flags:
        return (
            f"I was looking at who is showing up for local searches in {city} and noticed you are already ranking without a website. "
            "That usually means there is room to gain pretty fast once the missing support is in place."
        )
    return (
        f"I was reviewing who shows up for local searches in {city} and noticed your business is already visible, "
        "but the site looks pretty thin. There may be a straightforward way to tighten the support around what is already working."
    )


def build_note(entry: dict[str, Any], run_date: str, city: str, niche: str) -> str:
    package, price = package_name(entry.get("recommended_offer"))
    website = entry.get("website") or "None found"
    phone = entry.get("phone") or "Unknown"
    lines: list[str] = []
    lines.append(f"# {entry['business_name']} — {niche}, {city} TX")
    lines.append("")
    lines.append(f"**Status:** Research — {run_date} overnight run")
    lines.append(f"**Niche:** {niche}")
    lines.append(f"**GBP Rank:** #{entry['rank']} in the target local search band")
    lines.append(f"**Website:** {website}")
    lines.append(f"**Opportunity Score:** {entry['score_total']}/100 — Grade {entry['bucket']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Why This Prospect")
    lines.append("")
    lines.append(why_this_prospect(entry, city))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Website Findings")
    lines.append("")
    for flag in entry.get("opportunity_flags") or []:
        lines.append(f"- [ ] {flag}")
    if not entry.get("opportunity_flags"):
        lines.append("- [x] No major website findings captured")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Likely Quick Wins")
    lines.append("")
    for idx, win in enumerate(quick_wins(entry), start=1):
        lines.append(f"{idx}. {win}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Estimated Pitch")
    lines.append("")
    lines.append(f"**Package:** {package}")
    lines.append(f"**Price range:** {price}")
    lines.append("**Time to visible movement:** 60-90 days")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Suggested Outreach Opener")
    lines.append("")
    lines.append(outreach_opener(entry, city))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Contact")
    lines.append("")
    lines.append(f"- Phone: {phone}")
    lines.append("- Best channel: Phone")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Score Breakdown")
    lines.append("")
    lines.append("| Dimension | Score | Note |")
    lines.append("|-----------|-------|------|")
    for name, data in entry["score_breakdown"].items():
        lines.append(f"| {name.title()} | {data['points']}/{data['max']} | {data['reason']} |")
    lines.append(f"| **Total** | **{entry['score_total']}/100** | **Grade {entry['bucket']}** |")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write deterministic per-prospect notes from scored prospects.")
    parser.add_argument("--scores-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    payload = load_json(args.scores_json)
    run_date = payload["date"]
    city = payload["city"]
    niche = payload["niche"]
    output_dir = args.output_dir / run_date
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for entry in payload.get("scores") or []:
        if entry.get("bucket") != "A":
            continue
        filename = f"{entry['business_name']}.md"
        path = output_dir / filename
        path.write_text(build_note(entry, run_date, city, niche), encoding="utf-8")
        written.append(str(path))

    print(json.dumps(written, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
