#!/usr/bin/env python3
"""Build a corpus manifest for the local Buffett knowledge base."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path(os.environ.get("BUFFETT_CORPUS_DIR", Path.home() / ".codex" / "data" / "buffett-corpus"))
TEXT_EXTS = {".txt", ".md", ".csv", ".json", ".html", ".htm"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text_stats(path: Path) -> tuple[int, int]:
    if not path.exists() or path.suffix.lower() not in TEXT_EXTS:
        return 0, 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0, 0
    return len(text), len(re.findall(r"\b\w+\b", text))


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_record(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    raw_path = Path(record.get("raw_path", ""))
    text_path = Path(record.get("text_path", "")) if record.get("text_path") else None
    raw_exists = raw_path.exists()
    text_exists = text_path.exists() if text_path else False
    chars = words = 0
    if text_path and text_exists:
        chars, words = text_stats(text_path)
    status = record.get("status") or "unknown"
    if not raw_exists:
        status = "missing_raw"
    elif text_path and not text_exists:
        status = "missing_text"
    elif words and words < 500 and record.get("source_type") == "shareholder_letter":
        status = "needs_review_short_text"
    elif text_path and words == 0:
        status = "text_empty_or_binary"
    elif status == "unknown":
        status = "ok"
    item = dict(record)
    item.update(
        {
            "raw_exists": raw_exists,
            "text_exists": text_exists,
            "bytes": raw_path.stat().st_size if raw_exists else 0,
            "sha256": sha256_file(raw_path) if raw_exists else "",
            "chars": chars or int(record.get("chars") or 0),
            "words": words or int(record.get("words") or 0),
            "status": status,
        }
    )
    try:
        item["raw_relpath"] = str(raw_path.relative_to(root))
    except Exception:
        item["raw_relpath"] = str(raw_path)
    if text_path:
        try:
            item["text_relpath"] = str(text_path.relative_to(root))
        except Exception:
            item["text_relpath"] = str(text_path)
    return item


def discover_untracked(root: Path, tracked: set[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "metadata" in path.relative_to(root).parts:
            continue
        if str(path) in tracked:
            continue
        rel = path.relative_to(root)
        chars, words = text_stats(path)
        records.append(
            {
                "source_type": "untracked",
                "year": None,
                "title": path.stem,
                "source_url": "",
                "raw_path": str(path),
                "text_path": str(path) if path.suffix.lower() in TEXT_EXTS else None,
                "raw_relpath": str(rel),
                "content_type": None,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "chars": chars,
                "words": words,
                "status": "untracked",
                "notes": "Discovered by manifest scan; add source metadata if this should be cited.",
                "raw_exists": True,
                "text_exists": path.suffix.lower() in TEXT_EXTS,
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.corpus_root.expanduser().resolve()
    metadata = root / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    fetch_payload = load_json(metadata / "fetch_records.json") or {}
    for record in fetch_payload.get("records", []):
        records.append(normalize_record(root, record))

    user_payload = load_json(metadata / "user_materials.json") or {}
    for record in user_payload.get("records", []):
        records.append(normalize_record(root, record))

    public_media_payload = load_json(metadata / "public_media_records.json") or {}
    for record in public_media_payload.get("records", []):
        records.append(normalize_record(root, record))

    tracked = {r.get("raw_path", "") for r in records}
    tracked.update(r.get("text_path", "") for r in records if r.get("text_path"))
    records.extend(discover_untracked(root, tracked))

    counts: dict[str, int] = {"records": len(records)}
    for record in records:
        counts[f"source_type:{record.get('source_type')}"] = counts.get(f"source_type:{record.get('source_type')}", 0) + 1
        counts[f"status:{record.get('status')}"] = counts.get(f"status:{record.get('status')}", 0) + 1

    manifest = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "corpus_root": str(root),
        "policy": "Use local corpus for educational Buffett-style analysis. Verify source URLs and do not treat copyrighted books/videos as redistributable unless user supplied rights.",
        "counts": counts,
        "records": records,
    }
    (metadata / "corpus_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    fieldnames = [
        "source_type", "year", "title", "source_url", "raw_relpath", "text_relpath",
        "bytes", "chars", "words", "status", "notes",
    ]
    with (metadata / "corpus_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)

    print(json.dumps(counts, indent=2, ensure_ascii=False))
    print(f"manifest={metadata / 'corpus_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
