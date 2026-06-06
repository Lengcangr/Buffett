# Source Index

Use this index to find primary materials. Verify current URLs when the task depends on latest filings, prices, market capitalization, management changes, or announcements.

## Buffett And Berkshire Sources

Primary sources:

- Berkshire Hathaway shareholder letters: https://www.berkshirehathaway.com/letters/letters.html
- Berkshire Hathaway annual and interim reports: https://www.berkshirehathaway.com/reports.html
- Berkshire Hathaway shareholder meeting information: https://www.berkshirehathaway.com/sharehold.html
- Berkshire Hathaway SEC filings: search Berkshire Hathaway Inc. or CIK 0001067983 in EDGAR.
- SEC EDGAR company search: https://www.sec.gov/edgar/search-and-access

Media and meeting archives:

- CNBC Warren Buffett Archive: https://buffett.cnbc.com/warren-buffett-archive/
- CNBC Berkshire annual meetings: https://buffett.cnbc.com/annual-meetings/

Local corpus:

- Default root: `C:/Users/64939/.codex/data/buffett-corpus`
- Manifest: `metadata/corpus_manifest.json`
- Public link registry: `metadata/public_source_registry.json`
- Distilled navigation maps: `distilled/`

Use Berkshire materials for Buffett principles and Berkshire-specific facts. Do not copy long passages. Paraphrase and cite the original source.

## Third-Party Skill Or GitHub Material

Third-party repositories can be useful for discovery and structure, but do not copy their content into this skill unless the license clearly allows it. If license is missing or unclear, independently author the framework and rely on primary Berkshire sources.

Known discovery sources:

- `https://github.com/agi-now/buffett-skills`: useful structure inspiration; license should be verified before reuse.
- `https://github.com/ReeceHarding/buffett-letters`: Markdown mirror for discovery; verify against Berkshire official pages because completeness can vary.

## United States

- SEC EDGAR search: https://www.sec.gov/edgar/search-and-access
- SEC company submissions API pattern: `https://data.sec.gov/submissions/CIK##########.json` after confirming the CIK.
- Company investor relations pages: locate through the company website and cross-check with SEC filings.

Key filings: 10-K, 10-Q, 8-K, DEF 14A, S-1/F-1 for recent listings, 20-F/6-K for foreign issuers.

## Hong Kong

- HKEXnews: https://www.hkexnews.hk/index.htm
- Company announcements, annual reports, interim reports, circulars, listing documents, and regulatory notices are usually available through HKEXnews.
- Company IR pages can provide presentation context, but HKEX filings should govern facts.

## Mainland China A-Shares

- CNINFO: https://www.cninfo.com.cn/new/index
- Shanghai Stock Exchange listed-company announcements: https://www.sse.com.cn/disclosure/listedinfo/announcement/
- Shenzhen Stock Exchange listed-company announcements: https://www.szse.cn/disclosure/listed/notice/index.html

Use annual reports, interim reports, quarterly reports, exchange inquiry letters, and company responses. Watch for related-party transactions, pledges, guarantees, government subsidies, and accounting-policy changes.

## Other Global Markets

Start with the company IR page and the local exchange/regulator. Confirm:

- Reporting standard: IFRS, US GAAP, or local GAAP.
- Fiscal year and currency.
- Ordinary shares versus ADRs/GDRs.
- Local governance rules and minority-shareholder protections.

## Market Data

For valuation, current price and market capitalization are time-sensitive. Use a current financial data source available in the environment and record date/time. If no reliable current quote is available, do not make price-sensitive margin-of-safety claims.

## Source Quality Labels

- **Primary**: regulator, exchange, audited filing, company-published report.
- **Management framing**: investor presentation, earnings call, company blog.
- **Secondary context**: reputable media, industry report, analyst summary.
- **Discovery only**: search snippets, aggregators, wiki-style summaries, third-party mirrors.

Final conclusions should rest mainly on primary sources.
