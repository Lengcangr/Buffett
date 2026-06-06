# Research Playbook

Use this when the user gives a company, ticker, exchange, sector, basket, or security. The user may be an outsider; do not require them to provide materials unless the company is private, obscure, or blocked by paywalls.

## Intent And Safety First

Before gathering sources, classify the request:

- **Advanced underwriting**: the user wants a deep company file and understands the difference between business quality and price.
- **Ordinary-user teaching**: the user sounds new, wants a binary buy/sell call, asks about a concentrated position, or already owns the security and is reacting to price.
- **Instrument mismatch**: the user mixes operating companies with ETFs, options, crypto, SPACs, or similar wrappers.

If the request is ordinary-user teaching, load `09-ordinary-user-discipline.md` and default to teaching-first output. If the request is an instrument mismatch, classify instruments before doing any Buffett-style business memo.

## Standard Due Diligence Depth

Default to a standard 3-5 year review:

- Latest annual report or 10-K.
- Prior 3-5 annual reports when available.
- Latest quarterly/interim report.
- Investor presentation only as secondary management framing.
- Proxy/circular or governance disclosure when management, compensation, or related-party risk matters.
- Current price/market capitalization if discussing valuation or margin of safety.
- Industry source or competitor filings when moat claims need context.

Use a deeper 10-year history when the company is cyclical, acquisitive, highly levered, in semiconductors, or when the user asks for a deep file.

## Source Priority

1. Regulatory filings and exchange announcements.
2. Company investor relations and annual reports.
3. Audited financial statements.
4. Reputable secondary sources for industry context.
5. Databases and aggregators for discovery and cross-checking only.

## Company Identification

Before analysis, establish:

- Legal name and common name.
- Ticker(s), exchange(s), ISIN if useful.
- Reporting currency and fiscal year end.
- Share classes, ADR ratio, holding-company structure, or VIE structure if applicable.
- Main operating segments and geography.

If multiple candidates exist, state the ambiguity. If the ambiguity changes legal rights, ADR economics, governance, taxes, listing liquidity, or valuation inputs, ask for clarification before any price-status or instrument-level conclusion. Until clarified, only provide business-level analysis.

## Evidence Extraction

Extract the facts needed for Buffett-style judgment:

- Revenue by segment and geography.
- Gross margin, operating margin, net margin, and cash conversion trend.
- Return on equity, return on invested capital, and return on tangible capital when calculable.
- Debt, interest coverage, lease obligations, maturities, pension or guarantee exposures.
- Capex, depreciation/amortization, working capital, and maintenance versus growth investment clues.
- Share count, buybacks, dividends, issuance, acquisitions, divestitures.
- Customer concentration, suppliers, regulation, litigation, and key-person risks.
- Management tenure, ownership, compensation, and capital-allocation history.

Prefer per-share trends over aggregate growth because owners receive per-share outcomes.

## Screening Multiple Companies

When ranking an industry or watchlist:

1. Define the candidate universe and source date.
2. Exclude obvious too-hard or low-quality businesses with reasons.
3. Score business quality separately from current price.
4. Identify best businesses even if expensive; put them in watchlist status.
5. Identify apparently cheap names only if normalized owner earnings are credible.
6. Explain the learning principle behind the ranking.

Quick screens are preliminary triage only. They are allowed to answer:

- `worth deeper underwriting`
- `watchlist quality`
- `too hard`
- `likely weak / value-trap risk`

Quick screens are not allowed to answer:

- `best buy now`
- `top pick to purchase`
- `attractive` without a deeper memo
- direct comparisons driven mainly by low multiples or recent drawdowns

Suggested output columns:

- Company/ticker.
- Business role and circle-of-competence status.
- Moat evidence.
- Financial quality.
- Management/capital allocation.
- Triage status.
- Watchlist trigger.
- Main risk.
- What must be verified next.

## Handling Valuation

When valuation is requested:

- Obtain current market price and date/time of quote from a current source.
- Use conservative owner earnings or normalized free cash flow.
- State assumptions behind any valuation range.
- Include at least one downside or no-growth case.
- Conclude in principle-level terms: adequate margin, thin margin, no visible margin, watchlist only, or insufficient evidence.
- For high-quality but expensive companies, write a watchlist note: what price, earnings growth, cash-flow evidence, capital-allocation proof, or risk reduction would justify re-evaluation.
- Avoid ranking by valuation alone. A cheap weak business is not automatically better than a great business waiting for a fair price.
- In ordinary-user or screen contexts, present valuation labels tentatively. Explain what deeper work is still missing before the label can support action.

Do not issue individualized buy/sell/hold advice.

## Sector Notes

Load `08-industry-playbooks.md` for industry-specific checks. For semiconductors, always normalize cycles, check capex intensity, customer concentration, export controls, and whether the moat is structural rather than merely hot demand. For banks and insurers, do not proceed to a confident conclusion without sector-specific balance-sheet and underwriting metrics.

## Failure Modes

- **Insufficient sources**: say what is missing and stop short of a conclusion.
- **Unclear business**: place it in the too-hard pile rather than forcing a thesis.
- **Conflicting facts**: identify the conflict and prefer the more authoritative source.
- **Paywalled or inaccessible source**: use accessible primary alternatives or ask the user to provide the document.
- **Stale market data**: avoid valuation conclusions until current price data is verified.
- **Great but expensive**: do not discard automatically. Mark as watchlist only and state the evidence or price change needed for a visible margin of safety.
- **Ambiguous security**: stop at business-only analysis until the instrument is clarified.
- **Complex financials without key metrics**: default to `too hard` or `insufficient evidence`.
- **Wrapper or derivative instrument**: redirect instead of forcing an owner-earnings memo.
