#!/usr/bin/env python3
"""Fetch official Berkshire Hathaway Buffett source material into a local corpus.

The script favors official Berkshire pages and keeps a source audit for every
file it downloads. It does not fetch pirated books or third-party video assets.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

try:
    import brotli  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    brotli = None

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

USER_AGENT = "Codex Buffett Corpus Builder/1.0 (+local educational corpus)"
BERKSHIRE_ROOT = "https://www.berkshirehathaway.com/"
LETTERS_INDEX = urllib.parse.urljoin(BERKSHIRE_ROOT, "letters/letters.html")
REPORTS_INDEX = urllib.parse.urljoin(BERKSHIRE_ROOT, "reports.html")
DEFAULT_ROOT = Path(os.environ.get("BUFFETT_CORPUS_DIR", Path.home() / ".codex" / "data" / "buffett-corpus"))


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            attrs_dict = {k.lower(): v for k, v in attrs}
            self._href = attrs_dict.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            label = " ".join("".join(self._text).split())
            self.links.append((self._href, label))
            self._href = None
            self._text = []


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self.skip_depth += 1
        elif tag.lower() in {"p", "br", "div", "tr", "li", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        elif tag.lower() in {"p", "div", "tr", "li", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        raw = html.unescape("".join(self.parts))
        lines = [" ".join(line.split()) for line in raw.splitlines()]
        lines = [line for line in lines if line]
        return "\n".join(lines).strip() + "\n"


@dataclass
class FetchRecord:
    source_type: str
    year: int | None
    title: str
    source_url: str
    raw_path: str
    text_path: str | None
    content_type: str | None
    bytes: int
    sha256: str
    chars: int
    words: int
    status: str
    notes: str = ""


def ensure_layout(root: Path) -> None:
    for rel in [
        "raw/source_pages",
        "raw/shareholder_letters/html",
        "raw/shareholder_letters/pdf",
        "raw/annual_reports/html",
        "raw/annual_reports/pdf",
        "raw/meeting_transcripts",
        "raw/interviews",
        "raw/user_supplied_books",
        "raw/user_supplied_audio_video",
        "processed/shareholder_letters",
        "processed/annual_reports",
        "processed/chunks",
        "distilled",
        "metadata",
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)


def decode_payload(data: bytes, encoding: str | None) -> bytes:
    enc = (encoding or "").lower().strip()
    if enc == "br":
        if brotli is None:
            raise RuntimeError("Brotli-compressed response requires: python -m pip install brotli")
        return brotli.decompress(data)
    if enc == "gzip":
        return gzip.decompress(data)
    if enc == "deflate":
        return zlib.decompress(data)
    return data


def fetch_bytes(url: str, timeout: int = 30) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/pdf,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        headers = {k.lower(): v for k, v in response.headers.items()}
        data = response.read()
    return decode_payload(data, headers.get("content-encoding")), headers


def probe_url(url: str, timeout: int = 12) -> bool:
    try:
        fetch_bytes(url, timeout=timeout)
        return True
    except Exception:
        return False


def write_if_needed(path: Path, data: bytes, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_html_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "windows-1252", "latin-1"):
        try:
            doc = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        doc = data.decode("utf-8", errors="replace")
    parser = TextExtractor()
    parser.feed(doc)
    return parser.text()


def extract_pdf_text(path: Path) -> str:
    if PdfReader is None:
        return ""
    chunks: list[str] = []
    try:
        reader = PdfReader(str(path))
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                text = f"\n[page {page_number} extraction failed: {exc}]\n"
            if text.strip():
                chunks.append(f"\n\n[page {page_number}]\n{text.strip()}")
    except Exception as exc:
        return f"[PDF extraction failed for {path.name}: {exc}]\n"
    return "\n".join(chunks).strip() + "\n"


def extract_links_from_html_bytes(data: bytes, base_url: str) -> list[tuple[str, str]]:
    for enc in ("utf-8", "windows-1252", "latin-1"):
        try:
            doc = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        doc = data.decode("utf-8", errors="replace")
    parser = LinkParser()
    parser.feed(doc)
    return [(urllib.parse.urljoin(base_url, href), label) for href, label in parser.links]


def collect_letter_sources(root: Path, force: bool, max_year: int, sleep_s: float) -> dict[int, str]:
    index_bytes, _ = fetch_bytes(LETTERS_INDEX)
    index_path = root / "raw" / "source_pages" / "berkshire_letters_index.html"
    write_if_needed(index_path, index_bytes, force)

    sources: dict[int, str] = {}
    for url, _label in extract_links_from_html_bytes(index_bytes, LETTERS_INDEX):
        name = Path(urllib.parse.urlparse(url).path).name.lower()
        m = re.match(r"(19\d{2}|20\d{2})(?:ltr)?\.(html|pdf)$", name)
        if not m:
            continue
        year = int(m.group(1))
        if 1977 <= year <= max_year:
            sources.setdefault(year, url)

    # Berkshire sometimes posts a current PDF before adding it to letters.html.
    # Do not probe every indexed HTML year; failed probes can be slow on this site.
    for year in range(1977, max_year + 1):
        if year in sources:
            continue
        for candidate in [
            urllib.parse.urljoin(BERKSHIRE_ROOT, f"letters/{year}ltr.pdf"),
            urllib.parse.urljoin(BERKSHIRE_ROOT, f"letters/{year}.html"),
        ]:
            if probe_url(candidate):
                sources[year] = candidate
                time.sleep(sleep_s)
                break
    (root / "metadata" / "shareholder_letter_sources.json").write_text(
        json.dumps(sources, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return dict(sorted(sources.items()))


def find_annual_pdf_from_page(page_url: str, page_bytes: bytes) -> str | None:
    links = extract_links_from_html_bytes(page_bytes, page_url)
    pdfs = []
    for url, label in links:
        lower = url.lower()
        if not lower.endswith(".pdf"):
            continue
        score = 0
        name = Path(urllib.parse.urlparse(url).path).name.lower()
        if re.search(r"\d{4}ar\.pdf$", name):
            score += 10
        if "10-k" in name or "10k" in name:
            score -= 3
        if "fortune" in name:
            score -= 5
        if "annual" in label.lower():
            score += 2
        pdfs.append((score, url))
    if not pdfs:
        return None
    pdfs.sort(reverse=True)
    return pdfs[0][1]


def collect_annual_sources(root: Path, force: bool) -> dict[int, str]:
    index_bytes, _ = fetch_bytes(REPORTS_INDEX)
    index_path = root / "raw" / "source_pages" / "berkshire_reports_index.html"
    write_if_needed(index_path, index_bytes, force)

    candidate_pages: dict[int, list[tuple[int, str]]] = {}
    direct_sources: dict[int, list[tuple[int, str]]] = {}
    for url, _label in extract_links_from_html_bytes(index_bytes, REPORTS_INDEX):
        path = urllib.parse.urlparse(url).path.lower()
        year_match = re.search(r"/(19\d{2}|20\d{2})ar/", path)
        if not year_match:
            # Relative URLs may not include a leading slash after urljoin quirks.
            year_match = re.search(r"(19\d{2}|20\d{2})ar/", path)
        if not year_match:
            continue
        year = int(year_match.group(1))
        if path.endswith(".pdf") and re.search(r"(?:\d{4}ar|annual|10-k|10k).*\.pdf$", path):
            score = 10 if re.search(rf"{year}ar\.pdf$", path) else 1
            if "10-k" in path or "10k" in path:
                score -= 2
            direct_sources.setdefault(year, []).append((score, url))
        elif path.endswith(".html"):
            score = 1
            annual_match = re.search(r"linksannual(\d{2})\.html$", path)
            if annual_match:
                score += 10 if int(annual_match.group(1)) == year % 100 else -5
            if re.search(rf"(impnote{year % 100:02d}|{year}ar\.html|{str(year)[-2:]}arindx)", path):
                score += 5
            candidate_pages.setdefault(year, []).append((score, url))

    sources: dict[int, str] = {
        year: sorted(items, reverse=True)[0][1] for year, items in direct_sources.items()
    }
    best_pages = {year: sorted(items, reverse=True)[0][1] for year, items in candidate_pages.items()}
    for year, page_url in sorted(best_pages.items()):
        if year in sources and sources[year].lower().endswith(".pdf"):
            continue
        try:
            page_bytes, _ = fetch_bytes(page_url)
        except Exception:
            sources.setdefault(year, page_url)
            continue
        page_store = root / "raw" / "source_pages" / f"berkshire_annual_{year}_index.html"
        write_if_needed(page_store, page_bytes, force)
        pdf_url = find_annual_pdf_from_page(page_url, page_bytes)
        sources[year] = pdf_url or page_url
    (root / "metadata" / "annual_report_sources.json").write_text(
        json.dumps(dict(sorted(sources.items())), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return dict(sorted(sources.items()))


def store_source(root: Path, source_type: str, year: int | None, url: str, force: bool) -> FetchRecord:
    data, headers = fetch_bytes(url)
    content_type = headers.get("content-type")
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".html"
    safe_year = str(year) if year else "undated"
    if source_type == "shareholder_letter":
        subdir = "pdf" if suffix == ".pdf" else "html"
        raw_path = root / "raw" / "shareholder_letters" / subdir / f"{safe_year}_letter{suffix}"
        text_path = root / "processed" / "shareholder_letters" / f"{safe_year}.txt"
        title = f"Berkshire Hathaway shareholder letter {safe_year}"
    else:
        subdir = "pdf" if suffix == ".pdf" else "html"
        raw_path = root / "raw" / "annual_reports" / subdir / f"{safe_year}_annual_report{suffix}"
        text_path = root / "processed" / "annual_reports" / f"{safe_year}.txt"
        title = f"Berkshire Hathaway annual report {safe_year}"

    write_if_needed(raw_path, data, force)
    if suffix == ".pdf":
        text = extract_pdf_text(raw_path)
    else:
        text = read_html_text(raw_path)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(text, encoding="utf-8")

    words = len(re.findall(r"\b\w+\b", text))
    chars = len(text)
    if chars < 300:
        status = "extraction_failed"
    elif source_type == "shareholder_letter" and words < 500:
        status = "needs_review_short_text"
    else:
        status = "ok"
    notes = ""
    if status == "needs_review_short_text":
        notes = "Official page is short; for 1998-2003 the full letter may live inside the annual report."

    return FetchRecord(
        source_type=source_type,
        year=year,
        title=title,
        source_url=url,
        raw_path=str(raw_path),
        text_path=str(text_path),
        content_type=content_type,
        bytes=raw_path.stat().st_size,
        sha256=sha256_file(raw_path),
        chars=chars,
        words=words,
        status=status,
        notes=notes,
    )


def write_records(root: Path, records: list[FetchRecord]) -> None:
    metadata = root / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_policy": "Official Berkshire Hathaway pages only; no pirated books or third-party videos.",
        "records": [asdict(r) for r in records],
    }
    (metadata / "fetch_records.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with (metadata / "fetch_records.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()) if records else ["source_type"])
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--from-year", type=int, default=1977)
    parser.add_argument("--to-year", type=int, default=dt.datetime.now().year - 1)
    parser.add_argument("--include-annual-reports", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.2, help="polite delay between downloads")
    parser.add_argument("--max-items", type=int, default=0, help="debug limit; 0 means all")
    args = parser.parse_args(argv)

    root = args.corpus_root.expanduser().resolve()
    ensure_layout(root)
    print(f"corpus_root={root}")

    records: list[FetchRecord] = []
    letter_sources = collect_letter_sources(root, args.force, args.to_year, args.sleep)
    selected_letters = [(y, u) for y, u in letter_sources.items() if args.from_year <= y <= args.to_year]
    if args.max_items:
        selected_letters = selected_letters[: args.max_items]
    for year, url in selected_letters:
        try:
            print(f"letter {year}: {url}")
            records.append(store_source(root, "shareholder_letter", year, url, args.force))
        except Exception as exc:
            print(f"WARN: failed letter {year}: {exc}", file=sys.stderr)
        time.sleep(args.sleep)

    if args.include_annual_reports:
        annual_sources = collect_annual_sources(root, args.force)
        selected_annuals = [(y, u) for y, u in annual_sources.items() if args.from_year <= y <= args.to_year]
        if args.max_items:
            selected_annuals = selected_annuals[: args.max_items]
        for year, url in selected_annuals:
            try:
                print(f"annual {year}: {url}")
                records.append(store_source(root, "annual_report", year, url, args.force))
            except Exception as exc:
                print(f"WARN: failed annual {year}: {exc}", file=sys.stderr)
            time.sleep(args.sleep)

    write_records(root, records)
    ok = sum(1 for r in records if r.status == "ok")
    review = sum(1 for r in records if r.status != "ok")
    print(f"records={len(records)} ok={ok} needs_review={review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
