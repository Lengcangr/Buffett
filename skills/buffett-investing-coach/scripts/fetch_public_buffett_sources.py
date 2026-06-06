#!/usr/bin/env python3
"""Fetch legally accessible supplemental Buffett transcripts/audio and catalog video pages.

This script downloads only official/public files that are intended for direct
access, and catalogs commercial video metadata without downloading the video.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None

DEFAULT_ROOT = Path(os.environ.get("BUFFETT_CORPUS_DIR", Path.home() / ".codex" / "data" / "buffett-corpus"))
USER_AGENT = "Codex Buffett Legal Source Fetcher/1.0"

DOWNLOADS = [
    {
        "id": "economic-club-warren-buffett-remarks-2012",
        "title": "Warren Buffett Remarks - Economic Club of Washington transcript",
        "publisher": "Economic Club of Washington, D.C.",
        "date": "2012-06-05",
        "url": "https://www.economicclub.org/sites/default/files/transcripts/Final%20Transcript%20of%20June%205th%20Warren%20Buffett%20Remarks.pdf",
        "kind": "speech_transcript_pdf",
        "path": "raw/interviews/transcripts/economic-club-warren-buffett-remarks-2012.pdf",
    },
    {
        "id": "fcic-warren-buffett-interview-audio-2010",
        "title": "FCIC staff audiotape of interview with Warren Buffett, Berkshire Hathaway",
        "publisher": "Financial Crisis Inquiry Commission / Stanford Law archive",
        "date": "2010-05-26",
        "url": "http://fcic-static.law.stanford.edu/cdn_media/fcic-audio/2010-05-26 FCIC staff audiotape of interview with Warren Buffett, Berkshire Hathaway.mp3",
        "kind": "interview_audio_mp3",
        "path": "raw/interviews/audio/fcic-warren-buffett-interview-2010-05-26.mp3",
    },
]

CATALOG_PAGES = [
    "https://buffett.cnbc.com/annual-meetings/",
]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = {k.lower(): v for k, v in attrs}.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            self.links.append((self._href, html.unescape(" ".join("".join(self._text).split()))))
            self._href = None
            self._text = []


def safe_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    # Preserve existing percent-encoding while encoding spaces and punctuation.
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, urllib.parse.quote(parts.path, safe="/%"), parts.query, parts.fragment))


def fetch_bytes(url: str, timeout: int = 60) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(safe_url(url), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = response.read()
        headers = {k.lower(): v for k, v in response.headers.items()}
        return data, headers


def download_file(url: str, path: Path, force: bool) -> dict[str, Any]:
    if path.exists() and not force:
        return {"downloaded": False, "bytes": path.stat().st_size, "content_type": None}
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(safe_url(url), headers={"User-Agent": USER_AGENT})
    total = 0
    content_type = None
    with urllib.request.urlopen(req, timeout=120) as response, path.open("wb") as out:
        content_type = response.headers.get("Content-Type")
        while True:
            chunk = response.read(1024 * 512)
            if not chunk:
                break
            out.write(chunk)
            total += len(chunk)
    return {"downloaded": True, "bytes": total, "content_type": content_type}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_pdf_text(path: Path) -> str:
    if PdfReader is None:
        return ""
    parts: list[str] = []
    try:
        reader = PdfReader(str(path))
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                parts.append(f"\n\n[page {page_num}]\n{text.strip()}")
    except Exception as exc:
        return f"[PDF extraction failed: {exc}]\n"
    return "\n".join(parts).strip() + "\n"


def text_stats(text: str) -> tuple[int, int]:
    return len(text), len(re.findall(r"\b\w+\b", text))


def extract_s_data(html_text: str) -> dict[str, Any] | None:
    marker = "window.__s_data="
    idx = html_text.find(marker)
    if idx < 0:
        return None
    idx += len(marker)
    try:
        data, _end = json.JSONDecoder().raw_decode(html_text[idx:])
        return data
    except Exception:
        return None


def walk_assets(o: Any) -> Iterable[dict[str, Any]]:
    if isinstance(o, dict):
        if o.get("__typename") == "cnbcvideo" or o.get("playbackURL"):
            yield o
        for v in o.values():
            yield from walk_assets(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_assets(v)


def asset_record(asset: dict[str, Any], parent_url: str) -> dict[str, Any]:
    playback = asset.get("playbackURL")
    if isinstance(playback, str) and playback.startswith("//"):
        playback = "https:" + playback
    return {
        "id": asset.get("id"),
        "title": asset.get("title") or asset.get("headline"),
        "headline": asset.get("headline"),
        "url": asset.get("url"),
        "parent_url": parent_url,
        "datePublished": asset.get("datePublished"),
        "duration_seconds": asset.get("duration"),
        "description": asset.get("description"),
        "playbackURL": playback,
        "transcript_available_in_page": bool(asset.get("transcript")),
        "publisher": "CNBC Buffett Archive",
        "download_status": "ok_metadata_only_video_not_downloaded",
        "notes": "CNBC video metadata and streaming URL cataloged; media not downloaded to avoid copying commercial video assets.",
    }


def catalog_cnbc(root: Path, force: bool, sleep_s: float) -> list[dict[str, Any]]:
    source_dir = root / "raw" / "source_pages" / "cnbc"
    source_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    data, _headers = fetch_bytes("https://buffett.cnbc.com/annual-meetings/")
    hub_html = data.decode("utf-8", errors="replace")
    (source_dir / "annual-meetings.html").write_text(hub_html, encoding="utf-8")
    parser = LinkParser()
    parser.feed(hub_html)
    meeting_urls = sorted({urllib.parse.urljoin("https://buffett.cnbc.com/annual-meetings/", href) for href, _ in parser.links if re.search(r"/\d{4}-berkshire-hathaway-annual-meeting/?$", href)})
    for url in meeting_urls:
        year_match = re.search(r"/(\d{4})-berkshire", url)
        year = year_match.group(1) if year_match else "unknown"
        try:
            page_bytes, _ = fetch_bytes(url)
            page_html = page_bytes.decode("utf-8", errors="replace")
            (source_dir / f"annual-meeting-{year}.html").write_text(page_html, encoding="utf-8")
            s_data = extract_s_data(page_html)
            if s_data:
                assets = [asset_record(a, url) for a in walk_assets(s_data.get("page", {}).get("page", s_data))]
                # Deduplicate repeated module instances by video id/url.
                dedup: dict[str, dict[str, Any]] = {}
                for asset in assets:
                    key = str(asset.get("id") or asset.get("url") or json.dumps(asset, sort_keys=True))
                    dedup.setdefault(key, asset)
                records.extend(dedup.values())
        except Exception as exc:
            records.append({"parent_url": url, "publisher": "CNBC Buffett Archive", "download_status": "metadata_fetch_failed", "notes": str(exc)})
        time.sleep(sleep_s)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-audio", action="store_true", help="do not download large MP3 files")
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    root = args.corpus_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    metadata_dir = root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = root / "processed" / "interviews"
    processed_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    for item in DOWNLOADS:
        if args.skip_audio and item["kind"].endswith("audio_mp3"):
            records.append({**item, "source_type": "public_audio", "status": "skipped_audio_by_flag"})
            continue
        raw_path = root / item["path"]
        try:
            info = download_file(item["url"], raw_path, args.force)
            text_path = None
            chars = words = 0
            status = "ok_binary_no_text"
            if raw_path.suffix.lower() == ".pdf":
                text = extract_pdf_text(raw_path)
                chars, words = text_stats(text)
                text_path_obj = processed_dir / f"{item['id']}.txt"
                text_path_obj.write_text(text, encoding="utf-8")
                text_path = str(text_path_obj)
                status = "ok" if words > 100 else "needs_review_short_text"
            records.append({
                "source_type": "public_speech_or_interview" if raw_path.suffix.lower() == ".pdf" else "public_audio",
                "year": int(item["date"][:4]),
                "title": item["title"],
                "publisher": item["publisher"],
                "source_url": item["url"],
                "raw_path": str(raw_path),
                "text_path": text_path,
                "content_type": info.get("content_type"),
                "bytes": raw_path.stat().st_size,
                "sha256": sha256_file(raw_path),
                "chars": chars,
                "words": words,
                "status": status,
                "notes": "Official/public source downloaded for local educational research use.",
            })
        except Exception as exc:
            records.append({
                "source_type": "public_speech_or_interview",
                "year": int(item["date"][:4]),
                "title": item["title"],
                "publisher": item["publisher"],
                "source_url": item["url"],
                "raw_path": str(raw_path),
                "text_path": None,
                "content_type": None,
                "bytes": 0,
                "sha256": "",
                "chars": 0,
                "words": 0,
                "status": "download_failed",
                "notes": str(exc),
            })

    cnbc_records = catalog_cnbc(root, args.force, args.sleep)
    cnbc_payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": "CNBC video metadata is cataloged; commercial video media is not downloaded.",
        "records": cnbc_records,
    }
    (metadata_dir / "cnbc_annual_meeting_video_index.json").write_text(json.dumps(cnbc_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# CNBC Annual Meeting Video Index", "", cnbc_payload["policy"], ""]
    for record in cnbc_records:
        title = record.get("title") or record.get("parent_url")
        url = record.get("url") or record.get("parent_url")
        dur = record.get("duration_seconds")
        lines.append(f"- {title} ({dur or 'n/a'} sec): {url}")
    (metadata_dir / "cnbc_annual_meeting_video_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    records.extend({
        "source_type": "public_video_index",
        "year": None,
        "title": r.get("title") or "CNBC annual meeting video metadata",
        "publisher": "CNBC Buffett Archive",
        "source_url": r.get("url") or r.get("parent_url"),
        "raw_path": str(metadata_dir / "cnbc_annual_meeting_video_index.json"),
        "text_path": str(metadata_dir / "cnbc_annual_meeting_video_index.md"),
        "content_type": "metadata/json+markdown",
        "bytes": 0,
        "sha256": "",
        "chars": 0,
        "words": 0,
        "status": r.get("download_status", "ok_metadata_only_video_not_downloaded"),
        "notes": r.get("notes", "CNBC video metadata cataloged; media not downloaded."),
    } for r in cnbc_records)

    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": "Downloads are restricted to official/public transcript/audio files; commercial video/book files are cataloged or require user-supplied rights.",
        "records": records,
    }
    out = metadata_dir / "public_media_records.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"records={len(records)} cnbc_videos={len(cnbc_records)} metadata={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

