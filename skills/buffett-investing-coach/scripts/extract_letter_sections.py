#!/usr/bin/env python3
"""Extract shareholder letter sections from Berkshire annual reports when letter pages are short notes."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path(os.environ.get("BUFFETT_CORPUS_DIR", Path.home() / ".codex" / "data" / "buffett-corpus"))


def stats(text: str) -> tuple[int, int]:
    return len(text), len(re.findall(r"\b\w+\b", text))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_letter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.search(r"to the shareholders of berkshire hathaway", line, re.I):
            start = i
            break
    if start is None:
        return "", "start_not_found"

    end = None
    for i in range(start + 50, min(len(lines), start + 1600)):
        if re.search(r"^\s*Warren\s+E\.\s+Buffett\s*$", lines[i], re.I):
            end = min(len(lines), i + 4)
            break
    if end is None:
        # Fallback: stop before audited financials or management discussion if signature extraction fails.
        for i in range(start + 200, min(len(lines), start + 2000)):
            if re.search(r"independent auditors|management.?s discussion|consolidated balance sheets", lines[i], re.I):
                end = i
                break
    if end is None:
        end = min(len(lines), start + 1200)

    section = "\n".join(lines[start:end]).strip() + "\n"
    chars, words = stats(section)
    if words < 1000:
        return section, "needs_review_short_extraction"
    return section, "ok_extracted_from_annual_report"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--years", nargs="*", type=int, default=[1998, 1999, 2000, 2001, 2002, 2003])
    args = parser.parse_args()
    root = args.corpus_root.expanduser().resolve()
    metadata_path = root / "metadata" / "fetch_records.json"
    if not metadata_path.exists():
        raise SystemExit(f"missing {metadata_path}; run fetch_berkshire_letters.py first")
    payload: dict[str, Any] = json.loads(metadata_path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = payload.get("records", [])
    annual_by_year = {int(r["year"]): r for r in records if r.get("source_type") == "annual_report" and r.get("year")}
    repairs: list[dict[str, Any]] = []

    for year in args.years:
        annual_text_path = root / "processed" / "annual_reports" / f"{year}.txt"
        if not annual_text_path.exists():
            repairs.append({"year": year, "status": "missing_annual_text"})
            continue
        text = annual_text_path.read_text(encoding="utf-8", errors="replace")
        section, status = extract_letter(text)
        if not section:
            repairs.append({"year": year, "status": status})
            continue
        out_path = root / "processed" / "shareholder_letters" / f"{year}.txt"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(section, encoding="utf-8")
        chars, words = stats(section)
        annual_record = annual_by_year.get(year, {})
        raw_path = annual_record.get("raw_path", "")
        raw_bytes = Path(raw_path).stat().st_size if raw_path and Path(raw_path).exists() else 0
        raw_hash = sha256_file(Path(raw_path)) if raw_path and Path(raw_path).exists() else ""
        for record in records:
            if record.get("source_type") == "shareholder_letter" and int(record.get("year") or 0) == year:
                record.update(
                    {
                        "title": f"Berkshire Hathaway shareholder letter {year} (section extracted from annual report)",
                        "source_url": annual_record.get("source_url", record.get("source_url", "")),
                        "raw_path": raw_path or record.get("raw_path", ""),
                        "text_path": str(out_path),
                        "content_type": annual_record.get("content_type", record.get("content_type")),
                        "bytes": raw_bytes or record.get("bytes", 0),
                        "sha256": raw_hash or record.get("sha256", ""),
                        "chars": chars,
                        "words": words,
                        "status": status,
                        "notes": "Official standalone letter page is a short note; text section extracted from the official annual report.",
                    }
                )
                break
        repairs.append({"year": year, "status": status, "text_path": str(out_path), "chars": chars, "words": words})

    payload["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    payload["records"] = records
    metadata_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    repairs_path = root / "metadata" / "letter_section_repairs.json"
    repairs_path.write_text(json.dumps({"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "repairs": repairs}, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for r in repairs if str(r.get("status", "")).startswith("ok"))
    print(f"repairs={len(repairs)} ok={ok} metadata={repairs_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
