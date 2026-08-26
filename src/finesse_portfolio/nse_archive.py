from __future__ import annotations

from calendar import month_abbr
from datetime import date
from time import strptime


def market_cap_report_url(month: str) -> tuple[str, str]:
    """Return the official NSE archive URL and filename for a YYYY-MM report month."""
    date = strptime(month, "%Y-%m")
    filename = f"indices_data{month_abbr[date.tm_mon]}{date.tm_year}.zip"
    return (
        "https://www.niftyindices.com/Indices_-_Market_Capitalisation_and_Weightage/"
        + filename,
        filename,
    )


def report_months(start_month: str, end_month: str) -> list[str]:
    """Return inclusive YYYY-MM labels for a monthly archive range."""
    start, end = strptime(start_month, "%Y-%m"), strptime(end_month, "%Y-%m")
    cursor = date(start.tm_year, start.tm_mon, 1)
    final = date(end.tm_year, end.tm_mon, 1)
    if cursor > final:
        raise ValueError("start_month must not be after end_month.")
    months: list[str] = []
    while cursor <= final:
        months.append(cursor.strftime("%Y-%m"))
        cursor = date(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
    return months
