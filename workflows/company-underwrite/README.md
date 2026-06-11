# Company Underwrite Workflow

This workflow turns one public-company question into a repeatable investment research packet.

It is designed for ordinary but serious long-term investors who want to understand a company from zero, learn the Buffett-style reasoning, and preserve the work for future updates.

## Inputs

- Company name and ticker
- Exchange and reporting currency
- Industry or value-chain lens
- Report depth: quick, full memo, or deep HTML
- Data cutoff date
- Peer set if known

## Outputs

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

## Phase Checklist

1. Plan the research before collecting evidence.
2. Build a source audit from primary sources first.
3. Draft the memo using business quality before valuation.
4. Run an adversarial review.
5. Fix critical issues or preserve open questions.
6. Render HTML only after the memo is stable.
7. Verify UTF-8 and screenshot output.
8. Persist the durable lessons into `wiki/`.

## Command Prompt Example

```text
Use $investment-research-pipeline and $buffett-investing-coach in company-underwrite mode for CEG.
Create the research plan, source audit, adversarial review, final memo, HTML report, screenshot, and wiki update.
```

## Quality Bar

- Every material number has a source.
- Management claims are labeled as claims until verified.
- Business quality and price status are separate.
- The investor action panel includes price/evidence triggers and thesis-breaking signals.
- The final report teaches a reusable principle.

