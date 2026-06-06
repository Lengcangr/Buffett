#!/usr/bin/env python3
"""Evaluate a Buffett-style semiconductor strategy with reproducible inputs.

This is a pragmatic evaluation harness for the local `buffett-investing-coach`
skill. It does not pretend to be a full institutional point-in-time database.
Instead, it combines:

1. SEC annual filings / companyfacts already cached locally
2. Historical prices from the Nasdaq historical API
3. A deterministic rule-set that mirrors the skill's stated priorities:
   business quality first, valuation second, "too hard" penalties for the most
   cyclical or structurally difficult names.

The output is intended to answer:
- Would this style of selection have produced acceptable forward returns?
- Where does the current skill over-emphasize or under-emphasize factors?
- What should be changed to make the skill safer and more useful for an
  ordinary long-term investor?
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import math
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

ANNUAL_FORMS = {"10-K", "20-F", "40-F"}
USER_AGENT = "BuffettSkillEvaluation/1.0 research@example.com"
NASDAQ_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}

UNIVERSE: dict[str, dict[str, Any]] = {
    "QCOM": {"assetclass": "stocks", "role_score": 3.0, "complexity_penalty": 0.0, "note": "wireless IP + mobile chips"},
    "NXPI": {"assetclass": "stocks", "role_score": 2.6, "complexity_penalty": 0.0, "note": "auto + industrial mixed signal"},
    "TXN": {"assetclass": "stocks", "role_score": 2.7, "complexity_penalty": 0.0, "note": "analog + embedded"},
    "ADI": {"assetclass": "stocks", "role_score": 2.5, "complexity_penalty": 0.0, "note": "analog + industrial"},
    "AMAT": {"assetclass": "stocks", "role_score": 2.0, "complexity_penalty": 0.35, "note": "equipment"},
    "LRCX": {"assetclass": "stocks", "role_score": 2.0, "complexity_penalty": 0.35, "note": "equipment"},
    "KLAC": {"assetclass": "stocks", "role_score": 2.2, "complexity_penalty": 0.25, "note": "inspection / metrology"},
    "NVDA": {"assetclass": "stocks", "role_score": 2.3, "complexity_penalty": 0.35, "note": "accelerators + platform"},
    "AVGO": {"assetclass": "stocks", "role_score": 2.4, "complexity_penalty": 0.2, "note": "infra semis + software"},
    "AMD": {"assetclass": "stocks", "role_score": 1.7, "complexity_penalty": 0.5, "note": "cpu/gpu challenger"},
    "SWKS": {"assetclass": "stocks", "role_score": 1.1, "complexity_penalty": 0.6, "note": "rf front-end"},
    "QRVO": {"assetclass": "stocks", "role_score": 1.1, "complexity_penalty": 0.6, "note": "rf front-end"},
    "MCHP": {"assetclass": "stocks", "role_score": 2.2, "complexity_penalty": 0.2, "note": "mcu + embedded"},
    "ON": {"assetclass": "stocks", "role_score": 1.7, "complexity_penalty": 0.45, "note": "power semis + auto"},
    "MU": {"assetclass": "stocks", "role_score": 0.8, "complexity_penalty": 1.1, "note": "memory, highly cyclical"},
    "INTC": {"assetclass": "stocks", "role_score": 1.0, "complexity_penalty": 1.0, "note": "fab + turnaround"},
}

BENCHMARKS = {
    "SPY": "etf",
    "SOXX": "etf",
}

COMMON_SPLIT_FACTORS = (2.0, 3.0, 4.0, 5.0, 10.0, 20.0)

METRICS: dict[str, list[str]] = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "SalesRevenueGoodsNet"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "assets": ["Assets"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "debt": [
        "LongTermDebt",
        "LongTermDebtNoncurrent",
        "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
        "LongTermDebtCurrent",
        "LongTermDebtAndFinanceLeaseObligationsCurrent",
        "ShortTermBorrowings",
    ],
    "shares": ["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding"],
}


@dataclass
class Snapshot:
    ticker: str
    as_of: dt.date
    price_date: dt.date | None
    price: float | None
    market_cap: float | None
    fcf: float | None
    fcf_yield: float | None
    earnings_yield: float | None
    debt_to_equity: float | None
    revenue_cagr_3y: float | None
    cfo_cagr_3y: float | None
    revenue_drawdown: float | None
    positive_ni_years: int
    positive_cfo_years: int
    quality_score: float
    valuation_score: float
    combined_score: float
    quality_bucket: str
    price_status: str
    filing_fy: int | None
    share_adjustment_factor: float
    reasons: list[str]


@dataclass
class ShareAdjustment:
    later_fy: int
    filed: str
    factor: float
    observed_ratio: float


def load_companyfacts(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    return json.loads(data.decode("utf-8"))


def clean_float(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("$", "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def units_for_fact(fact: dict[str, Any], metric: str) -> list[dict[str, Any]]:
    units = fact.get("units", {})
    preferred = ["shares"] if metric == "shares" else ["USD", "USD/shares", "pure"]
    for unit in preferred:
        if unit in units:
            return units[unit]
    return next(iter(units.values()), [])


def collect_annual_series(companyfacts: dict[str, Any], metric: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for taxonomy in ("us-gaap", "ifrs-full"):
        section = companyfacts.get("facts", {}).get(taxonomy, {})
        for key in METRICS[metric]:
            fact = section.get(key)
            if not fact:
                continue
            for entry in units_for_fact(fact, metric):
                form = entry.get("form")
                fy = entry.get("fy")
                val = entry.get("val")
                filed = entry.get("filed")
                if form not in ANNUAL_FORMS or fy is None or val is None or not filed:
                    continue
                fp = entry.get("fp")
                if metric in {"revenue", "net_income", "cfo", "capex"} and fp != "FY":
                    continue
                items.append(
                    {
                        "metric": metric,
                        "key": key,
                        "form": form,
                        "fy": int(fy),
                        "filed": filed,
                        "end": entry.get("end"),
                        "value": float(val),
                    }
                )
    items.sort(key=lambda item: (item["fy"], item["filed"], item.get("end") or ""))
    dedup: dict[tuple[int, str], dict[str, Any]] = {}
    for item in items:
        dedup[(item["fy"], item["metric"])] = item
    return list(dedup.values())


def latest_before(series: list[dict[str, Any]], as_of: dt.date) -> dict[str, Any] | None:
    candidates = [item for item in series if dt.date.fromisoformat(item["filed"]) <= as_of]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item["filed"], item["fy"]))


def history_before(series: list[dict[str, Any]], as_of: dt.date, count: int = 4) -> list[dict[str, Any]]:
    candidates = [item for item in series if dt.date.fromisoformat(item["filed"]) <= as_of]
    by_fy: dict[int, dict[str, Any]] = {}
    for item in candidates:
        by_fy[item["fy"]] = item
    return [by_fy[fy] for fy in sorted(by_fy.keys())[-count:]]


def pct_change(start: float | None, end: float | None, years: int) -> float | None:
    if start is None or end is None or start <= 0 or end <= 0 or years <= 0:
        return None
    return (end / start) ** (1 / years) - 1


def infer_split_adjustments(shares_series: list[dict[str, Any]]) -> list[ShareAdjustment]:
    """Infer stock-split factors from large jumps in annual shares outstanding.

    Nasdaq historical closes are split-adjusted. SEC shares outstanding are not.
    To keep market-cap and yield calculations on the same basis, we adjust older
    share counts forward when later annual filings reveal large split-like jumps.
    """

    adjustments: list[ShareAdjustment] = []
    for earlier, later in zip(shares_series, shares_series[1:]):
        earlier_value = earlier.get("value")
        later_value = later.get("value")
        if not earlier_value or not later_value or earlier_value <= 0:
            continue
        observed_ratio = later_value / earlier_value
        best_factor = None
        best_error = None
        for factor in COMMON_SPLIT_FACTORS:
            tolerance = 0.15 if factor >= 10 else 0.05
            error = abs(observed_ratio / factor - 1.0)
            if error <= tolerance and (best_error is None or error < best_error):
                best_factor = factor
                best_error = error
        if best_factor is None:
            continue
        adjustments.append(
            ShareAdjustment(
                later_fy=int(later["fy"]),
                filed=str(later["filed"]),
                factor=float(best_factor),
                observed_ratio=float(observed_ratio),
            )
        )
    return adjustments


def adjusted_shares_value(
    latest_shares: dict[str, Any], share_adjustments: list[ShareAdjustment]
) -> tuple[float, float]:
    factor = 1.0
    latest_filed = dt.date.fromisoformat(str(latest_shares["filed"]))
    for adjustment in share_adjustments:
        if dt.date.fromisoformat(adjustment.filed) > latest_filed:
            factor *= adjustment.factor
    return float(latest_shares["value"]) * factor, factor


def fetch_price_history(symbol: str, assetclass: str, cache_dir: Path) -> list[dict[str, Any]]:
    cache_path = cache_dir / f"{symbol}_{assetclass}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    url = f"https://api.nasdaq.com/api/quote/{symbol}/historical?assetclass={assetclass}&fromdate=2016-01-01&limit=9999"
    response = requests.get(url, headers=NASDAQ_HEADERS, timeout=30)
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("data", {}).get("tradesTable", {}).get("rows", [])
    out: list[dict[str, Any]] = []
    for row in rows:
        close = clean_float(row.get("close"))
        if close is None:
            continue
        out.append(
            {
                "date": dt.datetime.strptime(row["date"], "%m/%d/%Y").date().isoformat(),
                "close": close,
            }
        )
    out.sort(key=lambda item: item["date"])
    cache_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    time.sleep(0.2)
    return out


def price_on_or_before(history: list[dict[str, Any]], target: dt.date) -> tuple[dt.date | None, float | None]:
    candidates = [item for item in history if dt.date.fromisoformat(item["date"]) <= target]
    if not candidates:
        return None, None
    item = candidates[-1]
    return dt.date.fromisoformat(item["date"]), float(item["close"])


def price_on_or_after(history: list[dict[str, Any]], target: dt.date) -> tuple[dt.date | None, float | None]:
    candidates = [item for item in history if dt.date.fromisoformat(item["date"]) >= target]
    if not candidates:
        return None, None
    item = candidates[0]
    return dt.date.fromisoformat(item["date"]), float(item["close"])


def score_snapshot(
    ticker: str,
    meta: dict[str, Any],
    metric_series: dict[str, list[dict[str, Any]]],
    share_adjustments: list[ShareAdjustment],
    price_history: list[dict[str, Any]],
    as_of: dt.date,
) -> Snapshot | None:
    rev_hist = history_before(metric_series["revenue"], as_of, 4)
    ni_hist = history_before(metric_series["net_income"], as_of, 4)
    cfo_hist = history_before(metric_series["cfo"], as_of, 4)
    capex_hist = history_before(metric_series["capex"], as_of, 4)
    latest_revenue = latest_before(metric_series["revenue"], as_of)
    latest_ni = latest_before(metric_series["net_income"], as_of)
    latest_cfo = latest_before(metric_series["cfo"], as_of)
    latest_capex = latest_before(metric_series["capex"], as_of)
    latest_equity = latest_before(metric_series["equity"], as_of)
    latest_debt = latest_before(metric_series["debt"], as_of)
    latest_shares = latest_before(metric_series["shares"], as_of)
    price_date, price = price_on_or_before(price_history, as_of)
    if latest_revenue is None or latest_cfo is None or latest_capex is None or latest_shares is None or price is None:
        return None

    adjusted_shares, share_adjustment_factor = adjusted_shares_value(latest_shares, share_adjustments)
    market_cap = price * adjusted_shares if adjusted_shares > 0 else None
    fcf = latest_cfo["value"] - abs(latest_capex["value"])
    fcf_yield = (fcf / market_cap) if market_cap and market_cap > 0 else None
    earnings_yield = (latest_ni["value"] / market_cap) if latest_ni and market_cap and market_cap > 0 else None
    debt_to_equity = None
    if latest_debt and latest_equity and latest_equity["value"] > 0:
        debt_to_equity = latest_debt["value"] / latest_equity["value"]

    rev_cagr = None
    cfo_cagr = None
    if len(rev_hist) >= 4:
        rev_cagr = pct_change(rev_hist[0]["value"], rev_hist[-1]["value"], rev_hist[-1]["fy"] - rev_hist[0]["fy"])
    if len(cfo_hist) >= 4:
        cfo_cagr = pct_change(cfo_hist[0]["value"], cfo_hist[-1]["value"], cfo_hist[-1]["fy"] - cfo_hist[0]["fy"])

    revenue_drawdown = None
    if rev_hist:
        peak = max(item["value"] for item in rev_hist)
        revenue_drawdown = (latest_revenue["value"] / peak - 1) if peak > 0 else None

    positive_ni_years = sum(1 for item in ni_hist if item["value"] > 0)
    positive_cfo_years = sum(1 for item in cfo_hist if item["value"] > 0)

    reasons: list[str] = []
    quality_score = 0.0
    quality_score += meta["role_score"]
    reasons.append(f"role score {meta['role_score']:.1f}: {meta['note']}")

    if fcf > 0:
        quality_score += 1.3
        reasons.append("positive owner earnings proxy")
    else:
        quality_score -= 1.0
        reasons.append("negative owner earnings proxy")

    if latest_ni and latest_ni["value"] > 0:
        quality_score += 0.8
        reasons.append("latest net income positive")
    else:
        quality_score -= 0.8
        reasons.append("latest net income weak")

    if positive_ni_years >= 3:
        quality_score += 0.7
        reasons.append("mostly positive net income across recent years")
    elif positive_ni_years <= 1:
        quality_score -= 0.7
        reasons.append("too many loss years")

    if positive_cfo_years >= 3:
        quality_score += 0.8
        reasons.append("cash generation mostly positive")

    if rev_cagr is not None:
        if rev_cagr > 0.07:
            quality_score += 1.0
            reasons.append(f"revenue CAGR healthy at {rev_cagr:.1%}")
        elif rev_cagr > 0.0:
            quality_score += 0.5
            reasons.append(f"revenue CAGR still positive at {rev_cagr:.1%}")
        else:
            quality_score -= 0.7
            reasons.append(f"revenue CAGR negative at {rev_cagr:.1%}")

    if cfo_cagr is not None:
        if cfo_cagr > 0.05:
            quality_score += 0.7
            reasons.append(f"cash flow CAGR healthy at {cfo_cagr:.1%}")
        elif cfo_cagr < -0.05:
            quality_score -= 0.6
            reasons.append(f"cash flow CAGR weak at {cfo_cagr:.1%}")

    if debt_to_equity is not None:
        if debt_to_equity <= 0.6:
            quality_score += 0.7
            reasons.append(f"balance sheet manageable, debt/equity {debt_to_equity:.2f}")
        elif debt_to_equity <= 1.2:
            quality_score += 0.2
            reasons.append(f"balance sheet acceptable, debt/equity {debt_to_equity:.2f}")
        else:
            quality_score -= 0.8
            reasons.append(f"balance sheet strained, debt/equity {debt_to_equity:.2f}")

    if revenue_drawdown is not None:
        if revenue_drawdown >= -0.1:
            quality_score += 0.4
            reasons.append("latest revenue still near recent peak")
        elif revenue_drawdown <= -0.3:
            quality_score -= 0.8
            reasons.append("latest revenue far below recent peak")

    quality_score -= meta["complexity_penalty"]
    if meta["complexity_penalty"] > 0:
        reasons.append(f"complexity penalty {meta['complexity_penalty']:.2f}")
    if share_adjustment_factor > 1.0:
        reasons.append(f"historical shares normalized by {share_adjustment_factor:.1f}x for later stock splits")

    valuation_score = 0.0
    if fcf_yield is not None:
        valuation_score += min(max(fcf_yield * 25.0, -2.0), 3.0)
    if earnings_yield is not None:
        valuation_score += min(max(earnings_yield * 18.0, -2.0), 2.0)
    if fcf_yield is not None and fcf_yield < 0.01:
        valuation_score -= 0.8
        reasons.append("fcf yield too thin")
    elif fcf_yield is not None and fcf_yield > 0.04:
        reasons.append("fcf yield provides visible support")

    combined_score = quality_score * 0.72 + valuation_score * 0.28

    if quality_score >= 5.2:
        quality_bucket = "wonderful compounder"
    elif quality_score >= 3.8:
        quality_bucket = "quality cash generator"
    elif quality_score >= 2.2:
        quality_bucket = "cyclical or commodity"
    elif quality_score >= 1.0:
        quality_bucket = "too hard"
    else:
        quality_bucket = "low quality"

    if quality_bucket in {"too hard", "low quality"}:
        price_status = "too hard to value"
    elif fcf_yield is None:
        price_status = "too hard to value"
    elif fcf_yield >= 0.045 and combined_score >= 3.5:
        price_status = "attractive"
    elif quality_bucket in {"wonderful compounder", "quality cash generator"} and fcf_yield < 0.02:
        price_status = "great business, no visible margin"
    elif combined_score >= 2.5:
        price_status = "fair/watchlist"
    else:
        price_status = "potentially attractive only if cheaper"

    return Snapshot(
        ticker=ticker,
        as_of=as_of,
        price_date=price_date,
        price=price,
        market_cap=market_cap,
        fcf=fcf,
        fcf_yield=fcf_yield,
        earnings_yield=earnings_yield,
        debt_to_equity=debt_to_equity,
        revenue_cagr_3y=rev_cagr,
        cfo_cagr_3y=cfo_cagr,
        revenue_drawdown=revenue_drawdown,
        positive_ni_years=positive_ni_years,
        positive_cfo_years=positive_cfo_years,
        quality_score=quality_score,
        valuation_score=valuation_score,
        combined_score=combined_score,
        quality_bucket=quality_bucket,
        price_status=price_status,
        filing_fy=latest_revenue["fy"],
        share_adjustment_factor=share_adjustment_factor,
        reasons=reasons,
    )


def choose_picks(snapshots: list[Snapshot], count: int = 3) -> list[Snapshot]:
    filtered = [
        item
        for item in snapshots
        if item.price_status in {"attractive", "fair/watchlist", "potentially attractive only if cheaper"}
        and item.quality_bucket not in {"too hard", "low quality"}
    ]
    filtered.sort(
        key=lambda item: (
            item.price_status != "attractive",
            item.quality_bucket != "wonderful compounder",
            -item.combined_score,
            -(item.fcf_yield or -999.0),
        )
    )
    return filtered[:count]


def forward_return(history: list[dict[str, Any]], start_date: dt.date, horizon_years: int) -> dict[str, Any] | None:
    start_actual, start_price = price_on_or_after(history, start_date)
    if start_price is None or start_actual is None:
        return None
    target = dt.date(start_date.year + horizon_years, start_date.month, start_date.day)
    end_actual, end_price = price_on_or_after(history, target)
    if end_price is None or end_actual is None:
        return None
    total_return = end_price / start_price - 1
    annualized = (end_price / start_price) ** (1 / horizon_years) - 1
    return {
        "start_date": start_actual.isoformat(),
        "end_date": end_actual.isoformat(),
        "start_price": start_price,
        "end_price": end_price,
        "total_return": total_return,
        "annualized_return": annualized,
    }


def load_all_metric_series(companyfacts_dir: Path) -> dict[str, dict[str, list[dict[str, Any]]]]:
    out: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for ticker in UNIVERSE:
        matches = list(companyfacts_dir.glob(f"{ticker}_*.json"))
        if not matches:
            continue
        facts = load_companyfacts(matches[0])
        out[ticker] = {metric: collect_annual_series(facts, metric) for metric in METRICS}
    return out


def build_rebalance_dates(start_year: int, end_year: int) -> list[dt.date]:
    return [dt.date(year, 5, 15) for year in range(start_year, end_year + 1)]


def render_markdown(
    rebalance_results: list[dict[str, Any]],
    aggregate: dict[str, Any],
    out_path: Path,
) -> None:
    lines = [
        "# Buffett Skill Evaluation Report",
        "",
        "This report evaluates a deterministic proxy for the local `buffett-investing-coach` skill.",
        "The proxy uses the skill's stated priorities: quality first, valuation second, and explicit penalties for cyclical / too-hard names.",
        "",
        "## Aggregate results",
        "",
        f"- Rebalance dates tested: {aggregate['rebalance_count']}",
        f"- Selection size: {aggregate['selection_size']} names",
        f"- Universe size: {aggregate['universe_size']} names",
        "",
        "| Horizon | Strategy avg annualized | SPY avg annualized | SOXX avg annualized | Strategy hit rate vs SPY | Strategy hit rate vs SOXX |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for horizon in ("1y", "3y", "5y"):
        stats = aggregate["horizons"].get(horizon, {})
        lines.append(
            f"| {horizon} | {fmt_pct(stats.get('strategy_avg'))} | {fmt_pct(stats.get('spy_avg'))} | {fmt_pct(stats.get('soxx_avg'))} | {fmt_pct(stats.get('beat_spy_rate'))} | {fmt_pct(stats.get('beat_soxx_rate'))} |"
        )

    lines.extend(
        [
            "",
            "## Rebalance-by-rebalance picks",
            "",
        ]
    )

    for item in rebalance_results:
        lines.append(f"### {item['rebalance_date']}")
        lines.append("")
        lines.append("| Ticker | Bucket | Price status | Combined score | FCF yield | Notes |")
        lines.append("|---|---|---|---:|---:|---|")
        for pick in item["picks"]:
            lines.append(
                f"| {pick['ticker']} | {pick['quality_bucket']} | {pick['price_status']} | {pick['combined_score']:.2f} | {fmt_pct(pick.get('fcf_yield'))} | {pick['summary']} |"
            )
        lines.append("")
        lines.append("| Horizon | Strategy annualized | SPY annualized | SOXX annualized |")
        lines.append("|---|---:|---:|---:|")
        for horizon in ("1y", "3y", "5y"):
            result = item["forward_returns"].get(horizon, {})
            lines.append(
                f"| {horizon} | {fmt_pct(result.get('strategy_annualized'))} | {fmt_pct(result.get('spy_annualized'))} | {fmt_pct(result.get('soxx_annualized'))} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- The evaluation is point-in-time aware for annual SEC filings, but not a full institutional database.",
            "- Market prices come from Nasdaq historical data, not total-return data. Dividends are not included.",
            "- The goal is not to prove a perfect strategy. The goal is to detect whether the current skill nudges users toward sensible long-term behavior or toward seductive but weak recommendations.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fmt_pct(value: float | None) -> str:
    if value is None or math.isnan(value):
        return "n/a"
    return f"{value * 100:.2f}%"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--companyfacts-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start-year", type=int, default=2018)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--selection-size", type=int, default=3)
    args = parser.parse_args()

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / "price_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    metric_series = load_all_metric_series(args.companyfacts_dir.expanduser().resolve())
    share_adjustments_by_ticker = {
        ticker: infer_split_adjustments(series["shares"])
        for ticker, series in metric_series.items()
    }
    price_histories: dict[str, list[dict[str, Any]]] = {}
    for ticker, meta in UNIVERSE.items():
        price_histories[ticker] = fetch_price_history(ticker, meta["assetclass"], cache_dir)
    benchmark_histories = {
        symbol: fetch_price_history(symbol, assetclass, cache_dir)
        for symbol, assetclass in BENCHMARKS.items()
    }

    rebalance_results: list[dict[str, Any]] = []
    horizon_buckets: dict[str, list[dict[str, float | None]]] = {"1y": [], "3y": [], "5y": []}

    for rebalance_date in build_rebalance_dates(args.start_year, args.end_year):
        snapshots: list[Snapshot] = []
        for ticker, meta in UNIVERSE.items():
            snapshot = score_snapshot(
                ticker,
                meta,
                metric_series[ticker],
                share_adjustments_by_ticker.get(ticker, []),
                price_histories[ticker],
                rebalance_date,
            )
            if snapshot:
                snapshots.append(snapshot)

        picks = choose_picks(snapshots, args.selection_size)
        forward_returns: dict[str, Any] = {}
        for horizon_years, label in ((1, "1y"), (3, "3y"), (5, "5y")):
            strategy_returns = []
            for pick in picks:
                result = forward_return(price_histories[pick.ticker], rebalance_date, horizon_years)
                if result:
                    strategy_returns.append(result["annualized_return"])
            spy = forward_return(benchmark_histories["SPY"], rebalance_date, horizon_years)
            soxx = forward_return(benchmark_histories["SOXX"], rebalance_date, horizon_years)
            forward_returns[label] = {
                "strategy_annualized": statistics.mean(strategy_returns) if strategy_returns else None,
                "spy_annualized": spy["annualized_return"] if spy else None,
                "soxx_annualized": soxx["annualized_return"] if soxx else None,
                "strategy_components": strategy_returns,
            }
            horizon_buckets[label].append(forward_returns[label])

        rebalance_results.append(
            {
                "rebalance_date": rebalance_date.isoformat(),
                "picks": [
                    {
                        "ticker": pick.ticker,
                        "quality_bucket": pick.quality_bucket,
                        "price_status": pick.price_status,
                        "combined_score": pick.combined_score,
                        "fcf_yield": pick.fcf_yield,
                        "share_adjustment_factor": pick.share_adjustment_factor,
                        "summary": "; ".join(pick.reasons[:3]),
                        "filing_fy": pick.filing_fy,
                    }
                    for pick in picks
                ],
                "forward_returns": forward_returns,
                "top_watchlist": [
                    {
                        "ticker": snap.ticker,
                        "combined_score": snap.combined_score,
                        "quality_bucket": snap.quality_bucket,
                        "price_status": snap.price_status,
                    }
                    for snap in sorted(snapshots, key=lambda item: item.combined_score, reverse=True)[:8]
                ],
            }
        )

    aggregate: dict[str, Any] = {
        "rebalance_count": len(rebalance_results),
        "selection_size": args.selection_size,
        "universe_size": len(UNIVERSE),
        "horizons": {},
    }
    for label, bucket in horizon_buckets.items():
        strategy_values = [item["strategy_annualized"] for item in bucket if item["strategy_annualized"] is not None]
        spy_values = [item["spy_annualized"] for item in bucket if item["spy_annualized"] is not None]
        soxx_values = [item["soxx_annualized"] for item in bucket if item["soxx_annualized"] is not None]
        beat_spy = [
            item["strategy_annualized"] > item["spy_annualized"]
            for item in bucket
            if item["strategy_annualized"] is not None and item["spy_annualized"] is not None
        ]
        beat_soxx = [
            item["strategy_annualized"] > item["soxx_annualized"]
            for item in bucket
            if item["strategy_annualized"] is not None and item["soxx_annualized"] is not None
        ]
        aggregate["horizons"][label] = {
            "strategy_avg": statistics.mean(strategy_values) if strategy_values else None,
            "spy_avg": statistics.mean(spy_values) if spy_values else None,
            "soxx_avg": statistics.mean(soxx_values) if soxx_values else None,
            "beat_spy_rate": statistics.mean(beat_spy) if beat_spy else None,
            "beat_soxx_rate": statistics.mean(beat_soxx) if beat_soxx else None,
        }

    results = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "method": "deterministic proxy for buffett-investing-coach",
        "rebalance_results": rebalance_results,
        "aggregate": aggregate,
    }
    json_path = output_dir / "buffett_skill_eval_results.json"
    md_path = output_dir / "buffett_skill_eval_report.md"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    render_markdown(rebalance_results, aggregate, md_path)

    print(f"json={json_path}")
    print(f"markdown={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
