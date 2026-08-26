#!/usr/bin/env python3
"""Build a conservatively lagged annual ROE and debt-to-equity research file.

This uses the public, consolidated financial-statement tables on Screener.in as a
secondary structured view of listed-company results.  It does not use any value
published after the simulated decision date: fiscal-year values are made
available on the following 30 June.  The source page and every extraction result
are recorded in the accompanying coverage file for review.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

import pandas as pd
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (research; FinesseXCitadel competition backtest)"}
FY_RE = re.compile(r"Mar\s+(20\d{2})")


def number(value: str) -> float | None:
    cleaned = value.replace(",", "").replace("%", "").replace("+", "").strip()
    if cleaned in {"", "-", "–"}:
        return None
    match = re.search(r"-?[\d.]+", cleaned)
    return float(match.group()) if match else None


def annual_table(soup: BeautifulSoup, section_id: str) -> dict[int, dict[str, float | None]]:
    table = soup.select_one(f"#{section_id} table")
    if table is None:
        raise ValueError(f"Missing {section_id} table")
    years = []
    for header in table.select("thead th")[1:]:
        match = FY_RE.search(header.get_text(" ", strip=True))
        years.append(int(match.group(1)) if match else None)
    result: dict[int, dict[str, float | None]] = {}
    for row in table.select("tbody tr"):
        cells = row.select("td")
        if not cells:
            continue
        label = re.sub(r"\s+", " ", cells[0].get_text(" ", strip=True)).rstrip(" +")
        for year, cell in zip(years, cells[1:]):
            if year is not None:
                result.setdefault(year, {})[label] = number(cell.get_text(" ", strip=True))
    return result


def fetch(url: str) -> str:
    """Use curl because it honours the desktop network proxy reliably."""
    result = subprocess.run(
        ["curl", "-L", "--fail", "--silent", "--show-error", "--max-time", "30", "-A", HEADERS["User-Agent"], url],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def company_page(symbol: str) -> tuple[str, BeautifulSoup]:
    direct = f"https://www.screener.in/company/{quote(symbol, safe='')}/consolidated/"
    page = fetch(direct)
    if "Balance Sheet" not in page:
        raise ValueError(f"No consolidated financial statements found for {symbol}")
    return direct, BeautifulSoup(page, "html.parser")


def build_rows(ticker: str, page_url: str, soup: BeautifulSoup) -> list[dict[str, object]]:
    balance = annual_table(soup, "balance-sheet")
    profit = annual_table(soup, "profit-loss")
    page_text = soup.get_text(" ", strip=True).lower()
    is_financial = any(word in page_text for word in ("financial services", "banks", "insurance"))
    rows: list[dict[str, object]] = []
    for year in range(2020, 2026):
        equity_capital = balance.get(year, {}).get("Equity Capital")
        reserves = balance.get(year, {}).get("Reserves")
        previous_capital = balance.get(year - 1, {}).get("Equity Capital")
        previous_reserves = balance.get(year - 1, {}).get("Reserves")
        net_profit = profit.get(year, {}).get("Net Profit")
        debt = balance.get(year, {}).get("Borrowings")
        equity = None if equity_capital is None or reserves is None else equity_capital + reserves
        prior_equity = (
            None
            if previous_capital is None or previous_reserves is None
            else previous_capital + previous_reserves
        )
        average_equity = None if equity is None or prior_equity is None else (equity + prior_equity) / 2
        if net_profit is None or average_equity in {None, 0}:
            continue
        # Deposits and policy liabilities are structural for regulated financials;
        # treating them as corporate debt would make the cross-sector signal invalid.
        debt_to_equity = 0.0 if is_financial else (None if debt is None or equity in {None, 0} else debt / equity)
        if debt_to_equity is None:
            continue
        rows.append(
            {
                "reported_date": f"{year}-06-30",
                "ticker": ticker,
                "roe": 100 * net_profit / average_equity,
                "debt_to_equity": debt_to_equity,
                "fiscal_year": year,
                "source_url": page_url,
                "financial_sector_treatment": is_financial,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", default="data/universe_fixed.csv")
    parser.add_argument("--output", default="data/raw/fundamentals.csv")
    parser.add_argument("--coverage-output", default="data/raw/fundamentals_coverage.csv")
    parser.add_argument("--pause-seconds", type=float, default=0.15)
    parser.add_argument("--start", type=int, default=0, help="Zero-based universe position to begin")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of symbols to fetch")
    args = parser.parse_args()

    universe = pd.read_csv(args.universe)
    all_tickers = sorted(universe["ticker"].astype(str).str.upper().unique())
    tickers = all_tickers[args.start : None if args.limit is None else args.start + args.limit]
    rows: list[dict[str, object]] = []
    coverage: list[dict[str, object]] = []
    for position, ticker in enumerate(tickers, start=args.start + 1):
        symbol = ticker.removesuffix(".NS")
        try:
            page_url, soup = company_page(symbol)
            company_rows = build_rows(ticker, page_url, soup)
            rows.extend(company_rows)
            coverage.append({"ticker": ticker, "status": "ok", "records": len(company_rows), "source_url": page_url})
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            # Keep a complete audit of gaps rather than silently omitting them.
            coverage.append({"ticker": ticker, "status": "failed", "records": 0, "source_url": "", "detail": str(error)})
        if position % 25 == 0 or position == args.start + len(tickers):
            print(f"[{position}/{len(all_tickers)}] completed; {sum(item['status'] == 'ok' for item in coverage)} pages retrieved", flush=True)
        time.sleep(args.pause_seconds)

    output = Path(args.output)
    coverage_output = Path(args.coverage_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    coverage_output.parent.mkdir(parents=True, exist_ok=True)
    existing_rows = pd.read_csv(output) if output.exists() else pd.DataFrame()
    existing_coverage = pd.read_csv(coverage_output) if coverage_output.exists() else pd.DataFrame()
    combined_rows = pd.concat([existing_rows, pd.DataFrame(rows)], ignore_index=True)
    combined_rows = combined_rows.drop_duplicates(["reported_date", "ticker"], keep="last")
    combined_coverage = pd.concat([existing_coverage, pd.DataFrame(coverage)], ignore_index=True)
    combined_coverage = combined_coverage.drop_duplicates(["ticker"], keep="last")
    combined_rows.sort_values(["reported_date", "ticker"]).to_csv(output, index=False)
    combined_coverage.sort_values("ticker").to_csv(coverage_output, index=False)


if __name__ == "__main__":
    main()
