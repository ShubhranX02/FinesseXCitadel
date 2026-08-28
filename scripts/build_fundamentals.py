#!/usr/bin/env python3
"""Build dated annual ROE and debt-to-equity inputs from NSE XBRL filings.

Each output record carries NSE's exchange dissemination timestamp. The backtest
therefore uses only a result disclosed on or before its signal date. The raw
XBRL URL and the filing metadata are retained for auditability.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import date
from datetime import time as daytime
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
from bs4 import BeautifulSoup

NSE_API = "https://www.nseindia.com/api/corporates-financial-results"
USER_AGENT = "Mozilla/5.0 (research; FinesseXCitadel competition backtest)"
MIN_ANNUAL_DAYS = 300


def fetch(url: str) -> str:
    """Fetch a public NSE resource through curl, which handles this host reliably."""
    result = subprocess.run(
        [
            "curl", "--http1.1", "-L", "--fail", "--silent", "--show-error", "--max-time", "30",
            "--retry", "2", "-A", USER_AGENT,
            "-H", "Accept: application/json, text/plain, */*",
            "-H", "Referer: https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
            url,
        ],
        check=True, capture_output=True, text=True,
    )
    return result.stdout


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", maxsplit=1)[-1]


def context_dates(root: ET.Element) -> dict[str, tuple[date | None, date | None, bool]]:
    """Map context ID to (start, end, is_instant)."""
    result: dict[str, tuple[date | None, date | None, bool]] = {}
    for element in root.iter():
        if local_name(element) != "context":
            continue
        identifier = element.attrib.get("id")
        if not identifier:
            continue
        start = end = None
        instant = False
        for child in element.iter():
            name = local_name(child)
            if name == "startDate" and child.text:
                start = date.fromisoformat(child.text.strip())
            elif name in {"endDate", "instant"} and child.text:
                end = date.fromisoformat(child.text.strip())
                instant = name == "instant"
        result[identifier] = (start, end, instant)
    return result


def fact(
    root: ET.Element,
    contexts: dict[str, tuple[date | None, date | None, bool]],
    names: tuple[str, ...],
    period_end: date,
    *,
    instant: bool,
) -> float | None:
    """Return the primary fact matching a stated annual or instant period."""
    candidates: list[tuple[int, int, float]] = []
    for element in root.iter():
        if local_name(element) not in names or not element.text:
            continue
        context_id = element.attrib.get("contextRef", "")
        # NSE annual-result XBRL files conventionally put the full-year income
        # statement in FourD and the closing balance sheet in OneI.  Older files
        # have incomplete context dates, so accept those canonical contexts while
        # still preferring an exact conventional match.
        canonical = context_id == ("OneI" if instant else "FourD")
        context = contexts.get(context_id)
        if context is None:
            if not canonical:
                continue
            start = end = None
            is_instant = instant
        else:
            start, end, is_instant = context
        dated_match = end == period_end and is_instant == instant
        annual_match = not instant and start is not None and (end - start).days >= MIN_ANNUAL_DAYS
        if not canonical and (not dated_match or not instant and not annual_match):
            continue
        try:
            value = float(element.text.strip())
        except ValueError:
            continue
        # XBRL contains dimensional note variants; plain contexts such as OneI
        # and FourD hold the consolidated total.
        candidates.append((0 if canonical else 1, len(context_id), value))
    return min(candidates, default=(0, 0, None), key=lambda item: (item[0], item[1]))[2]


def parse_xbrl(xml_text: str, period_end: date) -> dict[str, float | None]:
    root = ET.fromstring(xml_text)
    contexts = context_dates(root)
    return {
        "net_profit": fact(root, contexts, ("ProfitLossForPeriod",), period_end, instant=False),
        "equity": fact(root, contexts, ("Equity", "EquityAttributableToOwnersOfParent"), period_end, instant=True),
        "borrowings_noncurrent": fact(root, contexts, ("BorrowingsNoncurrent",), period_end, instant=True),
        "borrowings_current": fact(root, contexts, ("BorrowingsCurrent",), period_end, instant=True),
    }


def screener_balance_sheet(symbol: str) -> dict[int, dict[str, float | None]]:
    """Return historical consolidated equity and borrowings from a public table.

    Older NSE annual XBRL does not carry balance-sheet tags.  This secondary
    structured source fills only that mechanical gap; NSE remains the source of
    profit and dissemination date.
    """
    html = fetch(f"https://www.screener.in/company/{symbol}/consolidated/")
    table = BeautifulSoup(html, "html.parser").select_one("#balance-sheet table")
    if table is None:
        raise ValueError("No consolidated balance-sheet table")
    years: list[int | None] = []
    for header in table.select("thead th")[1:]:
        label = header.get_text(" ", strip=True)
        year = next((int(token) for token in label.split() if token.isdigit() and len(token) == 4), None)
        years.append(year)
    by_year: dict[int, dict[str, float | None]] = {}
    for row in table.select("tbody tr"):
        cells = row.select("td")
        if not cells:
            continue
        label = cells[0].get_text(" ", strip=True).rstrip(" +")
        for year, cell in zip(years, cells[1:]):
            if year is None:
                continue
            value_text = cell.get_text(" ", strip=True).replace(",", "")
            try:
                value = float(value_text) if value_text not in {"", "-", "–"} else None
            except ValueError:
                value = None
            by_year.setdefault(year, {})[label] = value
    return by_year


def fallback_balance(values: dict[str, float | None]) -> tuple[float | None, float | None]:
    capital = values.get("Equity Capital", values.get("Share Capital"))
    reserves = values.get("Reserves")
    equity = capital + reserves if capital is not None and reserves is not None else None
    return equity, values.get("Borrowings")


def select_filings(symbol: str) -> list[dict[str, object]]:
    url = f"{NSE_API}?{urlencode({'index': 'equities', 'symbol': symbol, 'period': 'Annual'})}"
    filings = json.loads(fetch(url))
    selected = []
    for filing in filings:
        xbrl = filing.get("xbrl")
        broadcast = filing.get("exchdisstime") or filing.get("broadCastDate")
        if not xbrl or not broadcast or not filing.get("toDate"):
            continue
        period_end = pd.Timestamp(filing["toDate"]).date()
        if 2020 <= period_end.year <= 2025:
            selected.append(filing)
    # Prefer consolidated accounts over standalone for a same-day period; retain
    # later revisions because each becomes usable only on its own date.
    deduplicated: dict[tuple[str, str], dict[str, object]] = {}
    for filing in selected:
        disclosure_day = pd.to_datetime(
            filing.get("exchdisstime") or filing["broadCastDate"], dayfirst=True
        ).date().isoformat()
        key = (str(filing["toDate"]), disclosure_day)
        prior = deduplicated.get(key)
        if prior is None or filing.get("consolidated") == "Consolidated":
            deduplicated[key] = filing
    return sorted(deduplicated.values(), key=lambda item: (item["toDate"], item.get("exchdisstime") or item["broadCastDate"]))


def process_symbol(ticker: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    symbol = ticker.removesuffix(".NS")
    rows: list[dict[str, object]] = []
    audit: list[dict[str, object]] = []
    balance_sheet = screener_balance_sheet(symbol)
    for filing in select_filings(symbol):
        reported_at = pd.to_datetime(filing.get("exchdisstime") or filing["broadCastDate"], dayfirst=True)
        # Signals use the market close. A filing disseminated after 15:30 cannot
        # influence that day's close and becomes available on the next business day.
        available_date = reported_at.date()
        if reported_at.time() > daytime(15, 30):
            available_date = (pd.Timestamp(available_date) + pd.offsets.BDay(1)).date()
        period_end = pd.Timestamp(filing["toDate"]).date()
        parsed = parse_xbrl(fetch(str(filing["xbrl"])), period_end)
        equity, profit = parsed["equity"], parsed["net_profit"]
        debt = sum(value or 0 for value in (parsed["borrowings_current"], parsed["borrowings_noncurrent"]))
        equity_source = "NSE_XBRL"
        if equity is None:
            equity, fallback_debt = fallback_balance(balance_sheet.get(period_end.year, {}))
            # Screener's public tables are stated in ₹ crore; NSE XBRL is INR.
            equity = None if equity is None else equity * 10_000_000
            debt = None if fallback_debt is None else fallback_debt * 10_000_000
            equity_source = "SCREENER_BALANCE_SHEET"
        complete = profit is not None and equity not in {None, 0}
        # Deposit funding is not comparable to corporate debt, so regulated banks
        # are not scored by this debt-penalised quality factor.
        is_bank = filing.get("bank") == "B"
        roe = None if not complete else 100 * float(profit) / float(equity)
        debt_to_equity = None if not complete or debt is None or is_bank else float(debt) / float(equity)
        audit.append({
            "ticker": ticker, "reported_at": reported_at.isoformat(), "period_end": period_end.isoformat(),
            "consolidated": filing.get("consolidated"), "bank": is_bank, "xbrl_url": filing["xbrl"],
            "net_profit": profit, "equity": equity, "borrowings_current": parsed["borrowings_current"],
            "borrowings_noncurrent": parsed["borrowings_noncurrent"],
            "equity_source": equity_source, "status": "ok" if debt_to_equity is not None else "not_scored",
        })
        if debt_to_equity is not None:
            rows.append({
                "reported_date": available_date.isoformat(), "ticker": ticker, "roe": roe,
                "debt_to_equity": debt_to_equity, "period_end": period_end.isoformat(),
                "consolidated": filing.get("consolidated"), "equity_source": equity_source, "xbrl_url": filing["xbrl"],
            })
    return rows, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", default="data/universe_fixed.csv")
    parser.add_argument("--output", default="data/raw/fundamentals.csv")
    parser.add_argument("--coverage-output", default="data/raw/fundamentals_coverage.csv")
    parser.add_argument("--start", type=int, default=0, help="Zero-based universe position to begin")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of symbols to fetch")
    parser.add_argument("--pause-seconds", type=float, default=0.2)
    args = parser.parse_args()

    all_tickers = sorted(pd.read_csv(args.universe)["ticker"].astype(str).str.upper().unique())
    tickers = all_tickers[args.start : None if args.limit is None else args.start + args.limit]
    output, coverage_output = Path(args.output), Path(args.coverage_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    coverage_output.parent.mkdir(parents=True, exist_ok=True)
    existing_rows = pd.read_csv(output) if output.exists() else pd.DataFrame()
    existing_audit = pd.read_csv(coverage_output) if coverage_output.exists() else pd.DataFrame()
    rows: list[dict[str, object]] = []
    audit: list[dict[str, object]] = []

    def persist() -> None:
        combined_rows = pd.concat([existing_rows, pd.DataFrame(rows)], ignore_index=True)
        if not combined_rows.empty:
            combined_rows = combined_rows.drop_duplicates(["reported_date", "ticker"], keep="last")
            combined_rows.sort_values(["reported_date", "ticker"]).to_csv(output, index=False)
        combined_audit = pd.concat([existing_audit, pd.DataFrame(audit)], ignore_index=True)
        combined_audit.to_csv(coverage_output, index=False)

    for position, ticker in enumerate(tickers, start=args.start + 1):
        try:
            symbol_rows, symbol_audit = process_symbol(ticker)
            rows.extend(symbol_rows)
            audit.extend(symbol_audit or [{"ticker": ticker, "status": "no_usable_annual_xbrl"}])
        except (ET.ParseError, OSError, ValueError, subprocess.CalledProcessError) as error:
            audit.append({"ticker": ticker, "status": "failed", "detail": str(error)})
        if position % 10 == 0 or position == args.start + len(tickers):
            print(f"[{position}/{len(all_tickers)}] processed", flush=True)
            persist()
        time.sleep(args.pause_seconds)
    persist()


if __name__ == "__main__":
    main()
