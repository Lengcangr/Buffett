# Buffett Corpus Map

Default corpus root:

`C:/Users/64939/.codex/data/buffett-corpus`

Override with environment variable `BUFFETT_CORPUS_DIR` when needed.

## Folder Layout

- `raw/shareholder_letters/html` and `raw/shareholder_letters/pdf`: official Berkshire shareholder letter source files.
- `raw/annual_reports/html` and `raw/annual_reports/pdf`: official Berkshire annual report source files.
- `raw/meeting_transcripts`: user-supplied or licensed meeting transcripts.
- `raw/interviews`: user-supplied or licensed interview/speech transcripts.
- `raw/user_supplied_books`: user-owned ebooks/PDFs/notes.
- `raw/user_supplied_audio_video`: registered audio/video files; transcripts are required for text analysis.
- `processed/shareholder_letters`: extracted text from official letters.
- `processed/annual_reports`: extracted text from annual reports.
- `processed/user_materials`: extracted text from imported user-owned materials.
- `metadata/corpus_manifest.json`: source audit and quality status.
- `metadata/public_source_registry.json`: link catalog for public Berkshire/CNBC/SEC source locations.
- `distilled`: deterministic navigation maps generated from local text.

## Scripts

Run from the skill directory or by absolute path.

- `scripts/fetch_berkshire_letters.py --include-annual-reports`: download official Berkshire letters and annual reports, extract text, and create fetch records.
- `scripts/extract_letter_sections.py`: repair short 1998-2003 standalone letter notes by extracting the shareholder-letter section from official annual reports.
- `scripts/catalog_public_sources.py`: catalog public Berkshire, SEC, and CNBC archive pages without downloading protected media.
- `scripts/fetch_public_buffett_sources.py`: download legally accessible public transcript/audio files and catalog CNBC video metadata without downloading commercial video.
- `scripts/build_corpus_manifest.py`: scan the corpus and create `metadata/corpus_manifest.json` and CSV.
- `scripts/distill_buffett_corpus.py`: build deterministic theme and case maps under `distilled/`.
- `scripts/import_user_materials.py <path> --kind book|transcript|audio|video`: import user-owned materials and extract text when possible.

## Distilled Agent Brain

- Skill reference: `references/buffett-agent-brain.md`
- Corpus maps: `distilled/principle_evidence_map.md`, `distilled/case_mentions.md`, `distilled/chronology_by_year.md`, `distilled/interview_evidence_map.md`
- Interview transcripts: `processed/interviews/`

The brain file is the default agent behavior layer. The corpus maps remain evidence navigation, not final citations.

## How To Use The Corpus In An Answer

1. Check `metadata/corpus_manifest.json` for the source you need.
2. Use `distilled/principle_evidence_map.md` or `distilled/case_mentions.md` only to locate relevant years/cases.
3. Open the original processed text and, when needed, the raw PDF/HTML.
4. Cite the original URL from the manifest, not just the distilled map.
5. If the local text is short or marked `needs_review`, verify against the annual report or official page.

## Known Gaps To Expect

- Some 1998-2003 official shareholder letter pages are short notes pointing into annual reports; use the annual report for full context.
- CNBC video/audio archives are cataloged as links first. They are not bulk-downloaded by default.
- Books are not bundled because most are copyrighted. Import user-owned copies with `import_user_materials.py`.
- A deterministic map is not the same as semantic LLM distillation. Treat it as a retrieval scaffold.
