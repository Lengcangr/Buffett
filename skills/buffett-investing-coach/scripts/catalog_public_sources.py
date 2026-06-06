#!/usr/bin/env python3
"""Catalog public Buffett/Berkshire source pages without downloading protected media."""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
import zlib
from html.parser import HTMLParser
from pathlib import Path

try:
    import brotli  # type: ignore
except Exception:  # pragma: no cover
    brotli = None

DEFAULT_ROOT = Path(os.environ.get("BUFFETT_CORPUS_DIR", Path.home() / ".codex" / "data" / "buffett-corpus"))
USER_AGENT = "Codex Buffett Public Source Catalog/1.0"
SEED_PAGES = [
    {
        "name": "Berkshire shareholder letters",
        "url": "https://www.berkshirehathaway.com/letters/letters.html",
        "publisher": "Berkshire Hathaway",
        "category": "shareholder_letters",
    },
    {
        "name": "Berkshire annual and interim reports",
        "url": "https://www.berkshirehathaway.com/reports.html",
        "publisher": "Berkshire Hathaway",
        "category": "annual_reports",
    },
    {
        "name": "Berkshire shareholder meeting page",
        "url": "https://www.berkshirehathaway.com/sharehold.html",
        "publisher": "Berkshire Hathaway",
        "category": "annual_meetings",
    },
    {
        "name": "CNBC Warren Buffett Archive",
        "url": "https://buffett.cnbc.com/warren-buffett-archive/",
        "publisher": "CNBC",
        "category": "interviews_and_video_archive",
    },
    {
        "name": "CNBC Berkshire annual meetings",
        "url": "https://buffett.cnbc.com/annual-meetings/",
        "publisher": "CNBC",
        "category": "annual_meeting_video_archive",
    },
    {
        "name": "SEC EDGAR Berkshire filings",
        "url": "https://www.sec.gov/edgar/browse/?CIK=1067983&owner=exclude",
        "publisher": "SEC",
        "category": "regulatory_filings",
    },
]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            d = {k.lower(): v for k, v in attrs}
            self._href = d.get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href:
            label = " ".join("".join(self._text).split())
            self.links.append((self._href, html.unescape(label)))
            self._href = None
            self._text = []


def decode(data: bytes, enc: str | None) -> bytes:
    enc = (enc or "").lower()
    if enc == "br":
        if brotli is None:
            raise RuntimeError("Brotli response requires: python -m pip install brotli")
        return brotli.decompress(data)
    if enc == "gzip":
        return gzip.decompress(data)
    if enc == "deflate":
        return zlib.decompress(data)
    return data


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return decode(r.read(), r.headers.get("Content-Encoding"))


def classify(url: str, label: str, fallback: str) -> str:
    low = f"{url} {label}".lower()
    if "annual-meeting" in low or "annual meeting" in low:
        return "annual_meeting_video_or_transcript"
    if "letter" in low or re.search(r"\d{4}ltr\.pdf", low):
        return "shareholder_letter"
    if "annual" in low or "10-k" in low or "10k" in low:
        return "annual_report_or_filing"
    if "video" in low or "watch" in low:
        return "video_page"
    if "interview" in low or "cnbc" in low:
        return "interview_or_media_archive"
    if "sec.gov" in low:
        return "regulatory_filing"
    return fallback


def should_keep(url: str, label: str) -> bool:
    low = f"{url} {label}".lower()
    return any(token in low for token in [
        "buffett", "berkshire", "annual", "letter", "meeting", "interview", "transcript", "video", "10-k", "sec.gov",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--sleep", type=float, default=0.3)
    args = parser.parse_args()
    root = args.corpus_root.expanduser().resolve()
    metadata = root / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    for seed in SEED_PAGES:
        records.append({
            "title": seed["name"],
            "url": seed["url"],
            "publisher": seed["publisher"],
            "category": seed["category"],
            "source_level": "seed_page",
            "notes": "Public index page; review site terms before bulk downloading media.",
        })
        try:
            data = fetch(seed["url"])
            parser_obj = LinkParser()
            parser_obj.feed(data.decode("utf-8", errors="replace"))
            for href, label in parser_obj.links:
                url = urllib.parse.urljoin(seed["url"], href)
                if not should_keep(url, label):
                    continue
                records.append({
                    "title": label or Path(urllib.parse.urlparse(url).path).name or url,
                    "url": url,
                    "publisher": seed["publisher"],
                    "category": classify(url, label, seed["category"]),
                    "source_level": "linked_page_or_asset",
                    "parent": seed["url"],
                    "notes": "Cataloged link only; download text/PDF separately when allowed. Do not scrape protected video/audio without rights.",
                })
        except Exception as exc:
            records.append({
                "title": seed["name"],
                "url": seed["url"],
                "publisher": seed["publisher"],
                "category": seed["category"],
                "source_level": "seed_page_error",
                "notes": f"Fetch failed: {exc}",
            })
        time.sleep(args.sleep)

    # Deduplicate by URL while preserving first high-level record.
    dedup: dict[str, dict] = {}
    for record in records:
        dedup.setdefault(record["url"], record)
    records = list(dedup.values())
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": "Catalog public source locations. Download only official PDFs/text or user-authorized material; for CNBC/video/audio prefer transcripts or user-provided files.",
        "records": records,
    }
    (metadata / "public_source_registry.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["# Public Buffett Source Registry", "", payload["policy"], ""]
    for record in records:
        lines.append(f"- {record['category']}: [{record['title']}]({record['url']}) - {record.get('publisher','')}")
    (metadata / "public_source_registry.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"records={len(records)} registry={metadata / 'public_source_registry.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
