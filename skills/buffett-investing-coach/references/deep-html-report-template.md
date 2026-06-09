# Deep Single-Company HTML Report Template

Use this reference for durable HTML reports that teach a user how to understand one public company from an investor's perspective. This is deeper than a normal memo. It is a research file designed to be read once end-to-end and revisited later.

## Default Report Contract

- Output: one UTF-8 HTML file plus one screenshot artifact.
- Reading model: long document with side navigation.
- Audience: ordinary but serious long-term investor learning the company.
- Default history: 5 years, extended only when a shorter window is misleading.
- Evidence density: narrative and evidence balanced. Cite every material number and qualitative claim.
- Fixed add-ons: peer comparison, investor action panel, source audit, update log.
- Tone: clear Chinese by default unless the user requests another language.

## Required HTML Structure

Use these sections in this order unless the user explicitly asks for a different report shape:

1. **Report header**
   - Company name, ticker, exchange, reporting currency, fiscal year end.
   - Report date, data cutoff date, price quote date/time/source.
   - One-line report status: `deep research file`, `watchlist update`, or `re-underwriting file`.

2. **Investor safety box**
   - What the report can support.
   - What it cannot support.
   - Biggest unknowns.
   - Easiest novice mistake.
   - Portfolio-fit warning if the user asks about position sizing or concentration.

3. **One-page company map**
   - What the company does in one paragraph.
   - How it makes money.
   - Why the business may matter.
   - Business-quality label separate from price-status label.
   - Top 3 reasons to study it.
   - Top 3 reasons to be skeptical.

4. **Business from zero**
   - Explain the business in plain language before using finance jargon.
   - Map customers, suppliers, distribution, pricing model, regulation, and technology exposure.
   - Identify whether the listed security cleanly represents the business.

5. **Industry structure and profit pool**
   - Use `industry-report-templates.md` for the selected industry.
   - Explain who captures profits, who takes risk, and what changes bargaining power.
   - State whether the company is a price taker, price setter, regulated return asset, platform, brand owner, supplier, or balance-sheet business.

6. **How this company wins or loses**
   - Moat evidence: pricing power, cost advantage, switching cost, scarcity, brand, network, regulation, or ecosystem.
   - Separate proven evidence from management claims.
   - Explain where the moat could weaken.

7. **Five-year financial quality**
   - Revenue and per-share growth.
   - Margins, returns on capital, and cash conversion.
   - Capex intensity and maintenance-capex uncertainty.
   - Balance sheet, debt maturity, hidden liabilities, and dilution.
   - Owner earnings or why owner earnings cannot be estimated reliably.

8. **Management and capital allocation**
   - Tenure, incentives, ownership, candor, and consistency.
   - Reinvestment, M&A, buybacks, dividends, leverage, and issuance.
   - Whether management behavior matches owner orientation.

9. **Peer comparison**
   - Include 3-5 peers, substitutes, or adjacent companies.
   - Compare role in value chain, moat, financial quality, management, valuation risk, and main unknown.
   - State why the chosen peers are imperfect if they are not direct competitors.

10. **Valuation scenario tree**
   - Current price and market data source.
   - Conservative owner-earnings or normalized earnings range.
   - Downside/no-growth case, base case, and optimistic case.
   - Margin-of-safety discussion in ranges, not a precise target price.
   - Keep a great business on the watchlist if price is not attractive.

11. **Risks and anti-thesis**
   - Permanent capital impairment risks.
   - Smart bear case.
   - Accounting/cash-flow concerns.
   - Industry-specific risks from the selected industry template.
   - What would prove the bullish view wrong.

12. **Investor action panel**
   - Current status: `study candidate`, `watchlist`, `too hard`, `quality insufficient`, or `potentially attractive only if`.
   - What to verify next.
   - Price/evidence triggers that improve margin of safety.
   - Thesis-breaking signals.
   - Next review trigger: earnings date, filing, contract event, regulatory event, valuation move, or management action.

13. **Lesson for the user**
   - Buffett-style principle being trained.
   - Evidence that illustrates the principle.
   - Novice mistake avoided.
   - How to apply the lesson to another company.

14. **Source audit**
   - Table with source, publisher, date, used-for, and link.
   - Include primary sources for filings, presentations, press releases, proxy/governance, and price/valuation.
   - Mark secondary sources as industry context or discovery only.

15. **Update log**
   - Version, date, data cutoff, what changed, and what should be refreshed next.

## Visual And Layout Requirements

- Use a restrained research-file layout: side navigation, readable content width, dense tables, and clear section anchors.
- Avoid a thin landing-page feel. The first screen should show company identity, data cutoff, status, and what the report is for.
- Use cards only for repeated items or compact panels. Do not put every section in a decorative card.
- Include at least one comparison table and one investor action table.
- Include a print-friendly style if the report is likely to be archived.
- Every HTML report must pass the HTML Report Verification Gate in `SKILL.md`.

## Common Failure Modes

- Opening with a buy/sell verdict before the user understands the business.
- Treating a great company as unattractive only because it is expensive today.
- Treating a cheap company as attractive without normalizing owner earnings.
- Using peer multiples without explaining why the peer group is comparable.
- Leaving out management incentives or capital allocation.
- Providing a long report without a clear action panel for future tracking.
