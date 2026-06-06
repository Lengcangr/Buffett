#!/usr/bin/env python3
"""Import user-owned Buffett books, transcripts, audio, or video into the local corpus."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None

DEFAULT_ROOT = Path(os.environ.get("BUFFETT_CORPUS_DIR", Path.home() / ".codex" / "data" / "buffett-corpus"))
KIND_DIRS = {
    "book": "raw/user_supplied_books",
    "ebook": "raw/user_supplied_books",
    "transcript": "raw/meeting_transcripts",
    "speech": "raw/interviews",
    "interview": "raw/interviews",
    "audio": "raw/user_supplied_audio_video",
    "video": "raw/user_supplied_audio_video",
}
TEXT_EXTS = {".txt", ".md", ".srt", ".vtt", ".csv"}
AUDIO_VIDEO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".aac", ".mp4", ".mov", ".mkv", ".webm"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style"}:
            self.skip += 1
        elif tag.lower() in {"p", "br", "div", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style"} and self.skip:
            self.skip -= 1
        elif tag.lower() in {"p", "div", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self) -> str:
        raw = html.unescape("".join(self.parts))
        lines = [" ".join(line.split()) for line in raw.splitlines()]
        return "\n".join(line for line in lines if line).strip() + "\n"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-.") or "material"
    return stem[:120] + path.suffix.lower()


def iter_inputs(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    elif path.is_dir():
        for item in sorted(path.rglob("*")):
            if item.is_file():
                yield item


def extract_pdf(path: Path) -> str:
    if PdfReader is None:
        return ""
    parts: list[str] = []
    try:
        reader = PdfReader(str(path))
        for page_num, page in enumerate(reader.pages, start=1):
            txt = page.extract_text() or ""
            if txt.strip():
                parts.append(f"\n\n[page {page_num}]\n{txt.strip()}")
    except Exception as exc:
        return f"[PDF extraction failed: {exc}]\n"
    return "\n".join(parts).strip() + "\n"


def extract_epub(path: Path) -> str:
    parts: list[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith((".html", ".xhtml", ".htm"))]
            for name in sorted(names):
                data = zf.read(name)
                doc = data.decode("utf-8", errors="replace")
                parser = TextExtractor()
                parser.feed(doc)
                text = parser.text()
                if text.strip():
                    parts.append(f"\n\n[{name}]\n{text.strip()}")
    except Exception as exc:
        return f"[EPUB extraction failed: {exc}]\n"
    return "\n".join(parts).strip() + "\n"


def extract_html(path: Path) -> str:
    doc = path.read_text(encoding="utf-8", errors="replace")
    parser = TextExtractor()
    parser.feed(doc)
    return parser.text()


def extract_text(path: Path) -> tuple[str | None, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(path), "pdf_text"
    if suffix == ".epub":
        return extract_epub(path), "epub_text"
    if suffix in {".html", ".htm"}:
        return extract_html(path), "html_text"
    if suffix in TEXT_EXTS:
        return path.read_text(encoding="utf-8", errors="replace"), "plain_text"
    if suffix in AUDIO_VIDEO_EXTS:
        return None, "media_registered_no_transcript"
    return None, "unsupported_for_text_extraction"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="file or directory to import")
    parser.add_argument("--kind", choices=sorted(KIND_DIRS), default="book")
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--copy", action="store_true", default=True, help="copy files into corpus (default)")
    parser.add_argument("--link-only", action="store_true", help="register original path without copying")
    parser.add_argument("--source-name", default="user supplied material")
    parser.add_argument("--rights-note", default="User supplied this material and is responsible for rights/licensing.")
    args = parser.parse_args()

    root = args.corpus_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    raw_dir = root / KIND_DIRS[args.kind]
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = root / "processed" / "user_materials"
    processed_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = root / "metadata" / "user_materials.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    existing = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {"records": []}
    records = existing.get("records", [])

    imported = 0
    for src in iter_inputs(args.path.expanduser().resolve()):
        if args.link_only:
            dest = src
        else:
            dest = raw_dir / safe_name(src)
            if dest.resolve() != src.resolve():
                shutil.copy2(src, dest)
        text, extraction_status = extract_text(dest)
        text_path = None
        chars = words = 0
        status = extraction_status
        if text is not None:
            text_path_obj = processed_dir / (dest.stem + ".txt")
            text_path_obj.write_text(text, encoding="utf-8")
            text_path = str(text_path_obj)
            chars = len(text)
            words = len(re.findall(r"\b\w+\b", text))
            if words < 100:
                status = "needs_review_short_text"
            else:
                status = "ok"
        records.append(
            {
                "source_type": f"user_{args.kind}",
                "year": None,
                "title": src.stem,
                "source_url": "",
                "raw_path": str(dest),
                "text_path": text_path,
                "content_type": dest.suffix.lower().lstrip("."),
                "bytes": dest.stat().st_size,
                "sha256": sha256_file(dest),
                "chars": chars,
                "words": words,
                "status": status,
                "notes": f"{args.source_name}. {args.rights_note}",
                "imported_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "original_path": str(src),
            }
        )
        imported += 1

    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": "Import only user-owned, public-domain, or properly licensed material. Media files are registered; provide transcripts for analysis.",
        "records": records,
    }
    metadata_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"imported={imported} metadata={metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
