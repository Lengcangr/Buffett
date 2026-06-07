# Buffett Investing Coach

A dual-compatible skill package for `Codex` and `Claude Code`.

It installs the same canonical skill into either agent's local skills directory and gives users a Buffett-style workflow for:

- business-quality analysis;
- moat and management review;
- valuation discipline and margin-of-safety thinking;
- watchlist building for great-but-expensive companies;
- teaching-first investment memos and HTML reports.

> Educational use only. This repository does not provide personalized financial advice, trading instructions, or guaranteed investment outcomes.

## Supported Agents

- `Codex`: native install target `~/.codex/skills/buffett-investing-coach`
- `Claude Code`: native install target `~/.claude/skills/buffett-investing-coach`

The repository keeps one canonical skill source at `skills/buffett-investing-coach` and installs that same folder into the selected agent directory.

## Quick Install

### Windows PowerShell

Install into both `Codex` and `Claude Code`:

```powershell
$tmp = Join-Path $env:TEMP 'install-buffett-skill.ps1'
Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.ps1' -OutFile $tmp
powershell -ExecutionPolicy Bypass -File $tmp -Agent both
Remove-Item $tmp
```

Install only into `Codex`:

```powershell
$tmp = Join-Path $env:TEMP 'install-buffett-skill.ps1'
Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.ps1' -OutFile $tmp
powershell -ExecutionPolicy Bypass -File $tmp -Agent codex
Remove-Item $tmp
```

Install only into `Claude Code`:

```powershell
$tmp = Join-Path $env:TEMP 'install-buffett-skill.ps1'
Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.ps1' -OutFile $tmp
powershell -ExecutionPolicy Bypass -File $tmp -Agent claude
Remove-Item $tmp
```

### macOS / Linux

Install into both `Codex` and `Claude Code`:

```bash
tmp="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.sh -o "$tmp"
bash "$tmp" --agent both
rm -f "$tmp"
```

Install only into `Codex`:

```bash
tmp="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.sh -o "$tmp"
bash "$tmp" --agent codex
rm -f "$tmp"
```

Install only into `Claude Code`:

```bash
tmp="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.sh -o "$tmp"
bash "$tmp" --agent claude
rm -f "$tmp"
```

### Local Clone Install

If the repository is already cloned locally:

```powershell
.\install.ps1 -Agent both
```

```bash
./install.sh --agent both
```

## After Install

Restart `Codex` or `Claude Code`, then ask for the skill directly.

Example prompts:

- `Use $buffett-investing-coach to analyze Microsoft from a Buffett-style owner-analyst lens.`
- `Use $buffett-investing-coach to build a watchlist of high-quality semiconductor companies and separate business quality from current price.`
- `Use $buffett-investing-coach to write a teaching-first memo on Constellation Energy and export an HTML report with screenshot verification.`

## Repository Layout

```text
skills/
  buffett-investing-coach/
    SKILL.md
    agents/
      openai.yaml
    references/
    scripts/
reports/
  company-memos/
    CEG_AI_Power_Buffett_Report_2026-06-05.html
    CEG_AI_Power_Buffett_Report_2026-06-05.screenshot.png
install.ps1
install.sh
```

## What The Skill Does

- Analyzes public companies with a Buffett-style framework
- Separates business quality from current price
- Preserves watchlist candidates even when valuation is currently too rich
- Teaches ordinary users how to reason like long-term owner-investors
- Supports corpus-building workflows for official Buffett/Berkshire source material
- Requires screenshot-based verification for HTML report output

## Compatibility Notes

- `Codex` compatibility uses the standard `SKILL.md` plus `agents/openai.yaml`.
- `Claude Code` compatibility uses the same skill folder structure under `~/.claude/skills`.
- Other coding agents may still be able to reuse the prompt, references, and scripts manually, but they are not treated as first-class install targets in this repository.

## HTML Report Safety

The skill includes a hard verification gate for HTML outputs:

- write HTML using UTF-8;
- render it in a real or headless browser;
- capture a screenshot artifact;
- verify non-English text is not rendered as `????`, mojibake, or replacement glyphs;
- report both the HTML path and screenshot path before claiming completion.

The included CEG memo and screenshot show this workflow.

## What Is Not Included

This public package intentionally excludes large or potentially copyrighted bulk materials such as:

- ebooks;
- downloaded videos or audio;
- raw paid transcripts;
- scraped caches;
- bulk market datasets;
- third-party media files without redistribution rights.

## License

MIT License. The license applies to the original skill code, prompts, references, scripts, and repository documentation in this project. It does not grant rights to third-party books, shareholder letters, filings, audio, video, or datasets referenced by the skill.
