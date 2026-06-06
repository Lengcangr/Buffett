# Buffett Investing Coach

A Codex/agent skill for Buffett-style company analysis, value-investing education, watchlist building, and investment memo generation.

This skill helps users reason like long-term owner-analysts:

- understand how a business makes money;
- separate business quality from current price;
- evaluate moats, owner earnings, management quality, and capital allocation;
- preserve great-but-expensive companies on a watchlist;
- avoid overconfident buy/sell calls and false precision.

> Educational use only. This repository does not provide personalized financial advice or trading instructions.

## Repository Layout

```text
skills/
  buffett-investing-coach/
    SKILL.md
    references/
    scripts/
    agents/
reports/
  company-memos/
    CEG_AI_Power_Buffett_Report_2026-06-05.html
    CEG_AI_Power_Buffett_Report_2026-06-05.screenshot.png
```

## Install Locally

Copy the skill folder into your Codex skills directory:

```powershell
Copy-Item -Recurse -Force .\skills\buffett-investing-coach $env:USERPROFILE\.codex\skills\buffett-investing-coach
```

Then start a new Codex session and ask for Buffett-style company analysis, watchlists, valuation discipline, or value-investing memos.

## Example Use Cases

- Analyze a public company with a Buffett-style owner-analyst framework.
- Build a watchlist that separates business quality from current price.
- Generate a company memo with moat, owner earnings, management, valuation, risks, and watchlist triggers.
- Export an HTML report and verify the screenshot is not garbled.

## HTML Report Safety

The skill includes a hard verification gate for HTML outputs:

- write HTML as UTF-8;
- render the file in a real or headless browser;
- create a screenshot artifact;
- verify non-English text does not render as `????`, mojibake, or replacement glyphs;
- report both the HTML path and screenshot path.

The included CEG memo and screenshot are examples of this workflow.

## What Is Not Included

This public package intentionally excludes large or potentially copyrighted corpus materials such as ebooks, downloaded videos, audio, raw transcripts, caches, and bulk financial datasets.

## License

MIT License. The license applies to the original skill code, prompts, references, and documentation in this repository. It does not grant rights to third-party books, shareholder letters, filings, media, or external datasets referenced by the skill.
