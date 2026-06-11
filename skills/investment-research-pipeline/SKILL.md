---
name: investment-research-pipeline
description: Use when turning a public-company or industry investment question into a repeatable research workflow with plans, source audits, adversarial review, HTML reports, and wiki updates.
---

# Investment Research Pipeline

## Overview

Run an ARIS-inspired investment research workflow for public companies and sectors. The goal is not to produce a one-off stock opinion; the goal is to create a repeatable, auditable research packet that a normal long-term investor can read, challenge, update, and learn from.

Use this skill alongside `buffett-investing-coach` whenever Buffett-style judgment, owner earnings, moat, management, valuation, or margin of safety is needed.

## When To Use

Use this skill when the user asks to:

- turn a company report into a workflow;
- research a public company deeply;
- scan an industry and choose companies for underwriting;
- create an HTML investment report with source verification;
- keep a watchlist or investment wiki updated;
- review whether a previous investment memo is too optimistic, thin, or unsupported.

Do not use it for intraday trading, options tactics, crypto tokens, leveraged ETFs, or personalized allocation advice.

## Operating Modes

| Mode | Use when | Main output |
|---|---|---|
| `company-underwrite` | One company/ticker is named | Full research packet and optional HTML |
| `sector-scan` | A sector/theme is named | Candidate universe, triage table, next company queue |
| `watchlist-update` | Existing thesis needs refresh | Updated triggers, price status, thesis changes |
| `review-only` | User wants critique of an existing report | Adversarial review and fix list |

## Workflow Contract

Every full run should create or update these artifacts unless the user asks for a lighter run:

```text
research_plan.md
source_audit.md
memo_draft.md
adversarial_review.md
memo_final.md
final_report.html
final_report.screenshot.png
wiki_update.md
```

Use `workflows/company-underwrite/templates/` from this repository when available.

## Phase 1: Intake And Scope

Clarify or infer:

- company, ticker, exchange, reporting currency, fiscal year;
- report mode and depth;
- date cutoff for market data and filings;
- industry template or value-chain lens;
- whether HTML and screenshot verification are required;
- whether the report is for learning, watchlist tracking, or decision support.

If the security identity is ambiguous, do not give a security-level conclusion until clarified.

## Phase 2: Research Plan

Create `research_plan.md` before collecting evidence. Include:

- research question;
- business-quality questions;
- price/valuation questions;
- key sources to fetch;
- peer set;
- expected risks and anti-thesis;
- deliverables and verification gates.

The plan is allowed to change, but changes should be recorded in `progress.md` or the final update log.

## Phase 3: Evidence And Source Audit

Prefer primary sources:

1. 10-K / annual report;
2. latest 10-Q / interim filing;
3. proxy / governance filing;
4. investor presentation and earnings release;
5. earnings call transcript if available;
6. regulator documents when relevant;
7. market data provider only for price, market cap, multiples, and peer snapshots.

Write `source_audit.md` with source, publisher, date, URL, facts supported, and confidence. Every material number in the memo must map back to this file.

## Phase 4: Draft Memo

Use `buffett-investing-coach` for the investment logic. Draft in this order:

1. safety box;
2. business from zero;
3. industry profit pool;
4. moat evidence;
5. financial quality and owner earnings proxy;
6. management and capital allocation;
7. peer comparison;
8. valuation scenario tree;
9. risks and anti-thesis;
10. investor action panel;
11. transferable lesson.

Separate business quality from current price. A great business can be watchlist-only.

## Phase 5: Adversarial Review

Review the draft before finalizing. The reviewer must look for:

- unsupported numbers or claims;
- stale market data;
- management claims presented as facts;
- AI/theme narrative overpowering cash-flow evidence;
- cheapness inferred from price decline rather than owner earnings;
- missing debt, cyclicality, regulation, customer concentration, or dilution risks;
- conclusion too strong for the evidence;
- report too advanced for ordinary users.

If subagents or independent reviewers are available and the user explicitly authorized parallel/agent work, use them for this phase. Otherwise, run the review locally and label it as self-review.

## Phase 6: Iterate And Finalize

Fix every critical review issue before writing `memo_final.md`. If something cannot be resolved, preserve it as an open question instead of hiding it.

The final memo should end with:

- current status;
- what would make it more attractive;
- what would break the thesis;
- next review trigger;
- principle the user should learn.

## Phase 7: Render HTML

If the user asks for HTML, use the deep report structure from `buffett-investing-coach`:

- side navigation;
- source audit;
- peer table;
- valuation scenario tree;
- investor action panel;
- update log.

Hard gate:

1. write UTF-8 HTML with `<meta charset="utf-8">`;
2. render in a real or headless browser;
3. save a screenshot artifact;
4. check for replacement characters and repeated question-mark runs;
5. do not claim completion until visual and source checks pass.

## Phase 8: Persist To Wiki

Update `wiki/` so future research compounds:

```text
wiki/companies/<TICKER>.md
wiki/industries/<industry>.md
wiki/watchlists/<theme>-watchlist.md
wiki/principles/<principle>.md
```

Write what changed, what remains uncertain, and what should be checked next. Do not let the wiki become a graveyard of stale conclusions; include `last_reviewed`, `data_cutoff`, and `next_review_trigger`.

## Output Discipline

- Say "using a Buffett-style framework," never "Buffett would buy."
- Use educational analysis, not personalized financial advice.
- Keep source limitations visible.
- Do not rank operating companies, ETFs, options, and crypto together.
- Preserve great-but-expensive companies as watchlist names with price/evidence triggers.
- Prefer `too hard` over false precision.
