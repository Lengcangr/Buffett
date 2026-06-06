#!/usr/bin/env python3
"""Create deterministic Buffett corpus navigation maps from local text files."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

DEFAULT_ROOT = Path(os.environ.get("BUFFETT_CORPUS_DIR", Path.home() / ".codex" / "data" / "buffett-corpus"))

THEMES: dict[str, list[str]] = {
    "circle_of_competence": ["circle of competence", "too hard", "understand", "predict", "know"],
    "owner_earnings": ["owner earnings", "look-through earnings", "cash flow", "depreciation", "capital expenditures"],
    "moat_franchise": ["moat", "franchise", "competitive advantage", "brand", "pricing power"],
    "management_candor": ["candor", "managers", "integrity", "compensation", "shareholders"],
    "capital_allocation": ["capital allocation", "repurchase", "buyback", "dividend", "acquisition", "retained earnings"],
    "insurance_float": ["float", "underwriting", "insurance", "GEICO", "reinsurance"],
    "margin_of_safety": ["margin of safety", "intrinsic value", "discount", "price", "value"],
    "risk_temperament": ["risk", "permanent loss", "leverage", "debt", "temperament", "speculation"],
    "mistakes": ["mistake", "error", "lesson", "Dexter", "Salomon", "General Re"],
}

CASES: dict[str, list[str]] = {
    "GEICO": ["GEICO", "Government Employees Insurance"],
    "See's Candies": ["See's", "See’s", "Sees Candies"],
    "Coca-Cola": ["Coca-Cola", "Coke"],
    "American Express": ["American Express", "AmEx"],
    "BNSF": ["BNSF", "Burlington Northern"],
    "Apple": ["Apple"],
    "IBM": ["IBM", "International Business Machines"],
    "Wells Fargo": ["Wells Fargo"],
    "Salomon": ["Salomon"],
    "Dexter Shoe": ["Dexter"],
    "General Re": ["General Re", "Gen Re"],
    "Nebraska Furniture Mart": ["Nebraska Furniture Mart", "NFM"],
    "Berkshire Hathaway Energy": ["MidAmerican", "Berkshire Hathaway Energy", "BHE"],
    "Clayton Homes": ["Clayton"],
    "Precision Castparts": ["Precision Castparts", "PCC"],
}


def read_manifest(root: Path) -> dict:
    path = root / "metadata" / "corpus_manifest.json"
    if not path.exists():
        return {"records": []}
    return json.loads(path.read_text(encoding="utf-8"))


def iter_letter_texts(root: Path, manifest: dict) -> Iterable[tuple[int, Path, str]]:
    records = manifest.get("records", [])
    seen: set[Path] = set()
    for record in records:
        if record.get("source_type") != "shareholder_letter":
            continue
        text_path = record.get("text_path") or record.get("raw_path")
        year = record.get("year")
        if not text_path or not year:
            continue
        path = Path(text_path)
        if not path.exists() or path in seen:
            continue
        seen.add(path)
        yield int(year), path, path.read_text(encoding="utf-8", errors="replace")


def iter_interview_texts(root: Path, manifest: dict) -> Iterable[tuple[str, int | None, Path, str]]:
    records = manifest.get("records", [])
    seen: set[Path] = set()
    for record in records:
        source_type = str(record.get("source_type") or "")
        if source_type not in {"public_speech_or_interview", "public_audio", "user_transcript", "user_interview", "user_speech"}:
            continue
        text_path = record.get("text_path")
        if not text_path:
            continue
        path = Path(text_path)
        if not path.exists() or path in seen:
            continue
        seen.add(path)
        yield str(record.get("title") or path.stem), record.get("year"), path, path.read_text(encoding="utf-8", errors="replace")


def count_terms(text: str, terms: list[str]) -> int:
    lower = text.lower()
    return sum(lower.count(term.lower()) for term in terms)


def paragraphs_with_terms(text: str, terms: list[str], limit: int = 5) -> list[int]:
    paras = [p for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    hits: list[int] = []
    lower_terms = [t.lower() for t in terms]
    for idx, para in enumerate(paras, start=1):
        low = para.lower()
        if any(term in low for term in lower_terms):
            hits.append(idx)
        if len(hits) >= limit:
            break
    return hits


def theme_summary(root: Path, manifest: dict) -> tuple[dict, str]:
    theme_index: dict[str, dict] = {theme: {"total_hits": 0, "years": {}} for theme in THEMES}
    lines = [
        "# Buffett Corpus Principle Evidence Map",
        "",
        "Deterministic navigation map generated from local text. It is not a substitute for reading the original source before citing a principle.",
        "",
    ]
    for year, path, text in sorted(iter_letter_texts(root, manifest)):
        year_hits = []
        for theme, terms in THEMES.items():
            hits = count_terms(text, terms)
            if hits:
                paras = paragraphs_with_terms(text, terms)
                theme_index[theme]["total_hits"] += hits
                theme_index[theme]["years"][str(year)] = {"hits": hits, "paragraphs": paras, "text_path": str(path)}
                year_hits.append((theme, hits, paras))
        if year_hits:
            top = sorted(year_hits, key=lambda x: x[1], reverse=True)[:5]
            lines.append(f"## {year}")
            for theme, hits, paras in top:
                para_note = ", ".join(str(p) for p in paras[:5]) or "n/a"
                lines.append(f"- {theme}: {hits} term hits; review paragraphs {para_note} in `{path}`.")
            lines.append("")
    return theme_index, "\n".join(lines).strip() + "\n"


def case_summary(root: Path, manifest: dict) -> tuple[dict, str]:
    case_index: dict[str, dict] = {case: {"total_hits": 0, "years": {}} for case in CASES}
    lines = [
        "# Buffett Corpus Case Mention Map",
        "",
        "Use this as a pointer map. Read the cited local source before turning a case into a lesson.",
        "",
    ]
    for case, terms in CASES.items():
        year_items = []
        for year, path, text in sorted(iter_letter_texts(root, manifest)):
            hits = count_terms(text, terms)
            if hits:
                paras = paragraphs_with_terms(text, terms, limit=8)
                case_index[case]["total_hits"] += hits
                case_index[case]["years"][str(year)] = {"hits": hits, "paragraphs": paras, "text_path": str(path)}
                year_items.append((year, hits, paras, path))
        if year_items:
            lines.append(f"## {case}")
            for year, hits, paras, path in sorted(year_items, key=lambda x: x[1], reverse=True)[:12]:
                para_note = ", ".join(str(p) for p in paras[:5]) or "n/a"
                lines.append(f"- {year}: {hits} hits; review paragraphs {para_note} in `{path}`.")
            lines.append("")
    return case_index, "\n".join(lines).strip() + "\n"


def chronology(root: Path, manifest: dict) -> str:
    lines = [
        "# Buffett Corpus Chronology By Year",
        "",
        "This file records source coverage and the most visible themes by year. It avoids long verbatim quotation.",
        "",
        "| Year | Words | Status | Top themes | Source |",
        "|---:|---:|---|---|---|",
    ]
    records_by_year = {int(r["year"]): r for r in manifest.get("records", []) if r.get("source_type") == "shareholder_letter" and r.get("year")}
    for year, path, text in sorted(iter_letter_texts(root, manifest)):
        counts = Counter({theme: count_terms(text, terms) for theme, terms in THEMES.items()})
        top = ", ".join(theme for theme, n in counts.most_common(4) if n)
        record = records_by_year.get(year, {})
        status = record.get("status", "unknown")
        words = len(re.findall(r"\b\w+\b", text))
        lines.append(f"| {year} | {words} | {status} | {top or 'none detected'} | `{path}` |")
    return "\n".join(lines) + "\n"


def interview_summary(root: Path, manifest: dict) -> str:
    lines = [
        "# Buffett Interview And Speech Evidence Map",
        "",
        "This map covers locally available interview/speech transcripts. Use it to locate source context; verify audio/PDF before exact quotation.",
        "",
    ]
    any_items = False
    for title, year, path, text in sorted(iter_interview_texts(root, manifest), key=lambda x: (x[1] or 0, x[0])):
        any_items = True
        counts = [(theme, count_terms(text, terms), paragraphs_with_terms(text, terms, limit=6)) for theme, terms in THEMES.items()]
        counts = [item for item in counts if item[1]]
        counts.sort(key=lambda x: x[1], reverse=True)
        words = len(re.findall(r"\b\w+\b", text))
        lines.append(f"## {title} ({year or 'undated'})")
        lines.append(f"- Source text: `{path}`")
        lines.append(f"- Words: {words}")
        if counts:
            for theme, hits, paras in counts[:8]:
                para_note = ", ".join(str(p) for p in paras[:6]) or "n/a"
                lines.append(f"- {theme}: {hits} term hits; review paragraphs {para_note}.")
        else:
            lines.append("- No theme hits detected by the deterministic keyword map.")
        lines.append("")
    if not any_items:
        lines.append("- No interview/speech transcript text found in the manifest.")
    return "\n".join(lines).strip() + "\n"


def quality_report(manifest: dict) -> str:
    counts = manifest.get("counts", {})
    records = manifest.get("records", [])
    problem = [
        r for r in records
        if not str(r.get("status", "")).startswith("ok") and r.get("status") != "untracked"
    ]
    lines = [
        "# Buffett Corpus Quality Report",
        "",
        f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
        "## Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}")
    lines.extend(["", "## Items Needing Review", ""])
    if not problem:
        lines.append("- None detected by manifest status checks.")
    else:
        for r in problem[:200]:
            lines.append(f"- {r.get('source_type')} {r.get('year')}: {r.get('status')} - {r.get('notes','')} `{r.get('raw_relpath') or r.get('raw_path')}`")
    lines.extend([
        "",
        "## Use Notes",
        "",
        "- Treat this as a retrieval index, not as Buffett's complete thinking.",
        "- Before citing a lesson, open the original letter/report and verify context.",
        "- For copyrighted books, interviews, and videos, import only user-owned or licensed materials and store transcript provenance.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.corpus_root.expanduser().resolve()
    distilled = root / "distilled"
    distilled.mkdir(parents=True, exist_ok=True)
    manifest = read_manifest(root)

    theme_idx, theme_md = theme_summary(root, manifest)
    case_idx, case_md = case_summary(root, manifest)
    (distilled / "theme_index.json").write_text(json.dumps(theme_idx, indent=2, ensure_ascii=False), encoding="utf-8")
    (distilled / "case_index.json").write_text(json.dumps(case_idx, indent=2, ensure_ascii=False), encoding="utf-8")
    (distilled / "principle_evidence_map.md").write_text(theme_md, encoding="utf-8")
    (distilled / "case_mentions.md").write_text(case_md, encoding="utf-8")
    (distilled / "chronology_by_year.md").write_text(chronology(root, manifest), encoding="utf-8")
    (distilled / "interview_evidence_map.md").write_text(interview_summary(root, manifest), encoding="utf-8")
    (distilled / "corpus_quality_report.md").write_text(quality_report(manifest), encoding="utf-8")
    print(f"distilled={distilled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
