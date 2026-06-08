# Buffett Investing Coach

![Codex supported](https://img.shields.io/badge/Codex-supported-0A7CFF)
![Claude Code supported](https://img.shields.io/badge/Claude%20Code-supported-D97757)
![License MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Skill format](https://img.shields.io/badge/SKILL.md-portable-black)

A Buffett-style investing skill for `Codex` and `Claude Code`.

It installs one canonical skill into your local agent environment and helps users analyze businesses like long-term owner-analysts instead of chasing shallow buy/sell calls.

What it is built for:

- business-quality analysis before price opinions;
- moat, management, and capital-allocation review;
- valuation discipline and margin-of-safety thinking;
- watchlists for great companies that are not cheap yet;
- teaching-first investment memos and verified HTML reports.

> Educational use only. This repository does not provide personalized financial advice, trading instructions, or guaranteed investment outcomes.

## Demo

An example report generated with the skill:

![CEG Buffett memo screenshot](reports/company-memos/CEG_AI_Power_Buffett_Report_2026-06-05.screenshot.png)

- Example HTML memo: `reports/company-memos/CEG_AI_Power_Buffett_Report_2026-06-05.html`
- Example screenshot: `reports/company-memos/CEG_AI_Power_Buffett_Report_2026-06-05.screenshot.png`

## Install In 30 Seconds

### Windows PowerShell

Install into both `Codex` and `Claude Code`:

```powershell
$tmp = Join-Path $env:TEMP 'install-buffett-skill.ps1'
Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.ps1' -OutFile $tmp
powershell -ExecutionPolicy Bypass -File $tmp -Agent both
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

After install, restart your agent and ask for the skill directly.

## First Prompt

Use one of these right after restart:

```text
Use $buffett-investing-coach to analyze Microsoft from a Buffett-style owner-analyst lens.
```

```text
Use $buffett-investing-coach to build a watchlist of high-quality semiconductor companies and separate business quality from current price.
```

```text
Use $buffett-investing-coach to write a teaching-first memo on Constellation Energy and export an HTML report with screenshot verification.
```

## Why This Skill Feels Different

Most investing assistants collapse everything into a binary action answer. This one is opinionated in a different direction:

- it separates business quality from current price;
- it keeps great-but-expensive companies on a watchlist instead of discarding them;
- it teaches the user the reasoning, not only the conclusion;
- it refuses false precision when source quality is weak;
- it treats report rendering quality as part of correctness.

## What You Get

| Capability | What it produces |
| --- | --- |
| Buffett-style company analysis | A moat, management, owner-earnings, and valuation view of a public company |
| Watchlist discipline | Clear separation between `wonderful business` and `not a good price yet` |
| Teaching mode | Explanations that help ordinary users learn the framework |
| Corpus workflows | Scripts and references for building a Buffett source map from official or user-owned material |
| HTML report gate | UTF-8 output, browser rendering, and screenshot verification before completion |

## Agent Compatibility

| Agent | Status | Install target | Notes |
| --- | --- | --- | --- |
| `Codex` | First-class | `~/.codex/skills/buffett-investing-coach` | Uses `SKILL.md` plus `agents/openai.yaml` |
| `Claude Code` | First-class | `~/.claude/skills/buffett-investing-coach` | Uses the same canonical skill folder |
| Other code agents | Manual reuse only | N/A | Prompt, references, and scripts may still be reused manually |

The repository keeps one canonical skill source at `skills/buffett-investing-coach` and installs that same folder into the selected agent directory.

## Advanced Install Options

<details>
<summary>Install only Codex</summary>

Windows PowerShell:

```powershell
$tmp = Join-Path $env:TEMP 'install-buffett-skill.ps1'
Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.ps1' -OutFile $tmp
powershell -ExecutionPolicy Bypass -File $tmp -Agent codex
Remove-Item $tmp
```

macOS / Linux:

```bash
tmp="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.sh -o "$tmp"
bash "$tmp" --agent codex
rm -f "$tmp"
```

</details>

<details>
<summary>Install only Claude Code</summary>

Windows PowerShell:

```powershell
$tmp = Join-Path $env:TEMP 'install-buffett-skill.ps1'
Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.ps1' -OutFile $tmp
powershell -ExecutionPolicy Bypass -File $tmp -Agent claude
Remove-Item $tmp
```

macOS / Linux:

```bash
tmp="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/Lengcangr/Buffett/main/install.sh -o "$tmp"
bash "$tmp" --agent claude
rm -f "$tmp"
```

</details>

<details>
<summary>Install from a local clone</summary>

Windows PowerShell:

```powershell
.\install.ps1 -Agent both
```

macOS / Linux:

```bash
./install.sh --agent both
```

</details>

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

## Safety And Scope

- This is an educational analysis skill, not a portfolio-management service.
- It does not tell users to go all-in, leverage up, or treat one model output as certainty.
- It prefers primary sources, explicit missing-evidence notes, and `too hard` when the facts do not support conviction.
- HTML outputs must pass a render-verification gate: UTF-8 file, browser render, screenshot artifact, and no garbled non-English text.

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
