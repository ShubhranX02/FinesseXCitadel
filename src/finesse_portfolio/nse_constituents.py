from __future__ import annotations

import re
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path
from time import strptime

import pandas as pd
from pypdf import PdfReader

PDF_PATTERNS = {
    "NIFTY_100": re.compile(r"^NIFTY_100_[A-Za-z]{3}\d{4}\.pdf$"),
    "NIFTY_MIDCAP_100": re.compile(r"^NIFTY_Midcap_100_[A-Za-z]{3}\d{4}\.pdf$"),
    "NIFTY_SMALLCAP_100": re.compile(r"^NIFTY_Smallcap_100_[A-Za-z]{3}\d{4}\.pdf$"),
}
SYMBOL_PATTERN = re.compile(r"^([A-Z0-9&-]+)\s+")
REPORT_DATE_PATTERN = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")
# A footer in the March 2021 Midcap and Smallcap PDFs begins with this all-caps token;
# it is not an NSE security symbol. Explicit filtering keeps the 100-name validation strict.
NON_SYMBOL_TOKENS = {"PUBLICATION"}


def required_pdf_matches(archive_path: str | Path) -> dict[str, list[str]]:
    """Return the required constituent PDF matches in an NSE archive.

    This is deliberately separate from extraction: NSE changed the public archive
    contents in April 2022, so callers need to be able to produce an honest
    coverage report before deciding whether an archive can be used.
    """
    archive = Path(archive_path)
    with zipfile.ZipFile(archive) as zip_file:
        members = zip_file.namelist()
    return {
        universe: [member for member in members if pattern.fullmatch(Path(member).name)]
        for universe, pattern in PDF_PATTERNS.items()
    }


def archive_coverage(archive_path: str | Path) -> dict[str, object]:
    """Describe whether an archive contains all three required constituent PDFs."""
    archive = Path(archive_path)
    matches = required_pdf_matches(archive)
    missing = [universe for universe, files in matches.items() if len(files) != 1]
    return {
        "archive": archive.name,
        "complete": not missing,
        "missing_universes": ";".join(missing),
        "matched_pdfs": ";".join(
            f"{universe}={','.join(files)}" for universe, files in matches.items() if files
        ),
    }


def symbols_from_pdf_bytes(pdf_bytes: bytes) -> list[str]:
    """Extract NSE symbols from an official constituent-table PDF."""
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf_bytes)).pages)
    symbols: list[str] = []
    for line in text.splitlines():
        match = SYMBOL_PATTERN.match(line.strip())
        if match and match.group(1) not in NON_SYMBOL_TOKENS:
            symbols.append(match.group(1))
    return list(dict.fromkeys(symbols))


def report_date_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Read the as-of date printed in an official NSE constituent PDF."""
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf_bytes)).pages)
    match = REPORT_DATE_PATTERN.search(text)
    if not match:
        raise ValueError("Could not find a report date in the constituent PDF.")
    parsed = strptime(match.group(1), "%B %d, %Y")
    return date(parsed.tm_year, parsed.tm_mon, parsed.tm_mday).isoformat()


def snapshot_from_archive(archive_path: str | Path, effective_date: str | None = None) -> pd.DataFrame:
    """Extract the three required 100-stock lists from an NSE monthly report ZIP."""
    archive = Path(archive_path)
    records: list[pd.DataFrame] = []
    report_dates: set[str] = set()
    matches_by_universe = required_pdf_matches(archive)
    with zipfile.ZipFile(archive) as zip_file:
        for universe, matches in matches_by_universe.items():
            if len(matches) != 1:
                raise ValueError(f"Expected one {universe} PDF in {archive.name}; found {matches}")
            pdf_bytes = zip_file.read(matches[0])
            report_dates.add(report_date_from_pdf_bytes(pdf_bytes))
            symbols = symbols_from_pdf_bytes(pdf_bytes)
            if len(symbols) != 100:
                raise ValueError(f"{matches[0]} yielded {len(symbols)} symbols; expected 100.")
            records.append(
                pd.DataFrame(
                    {
                        "effective_date": effective_date,
                        "ticker": pd.Series(symbols) + ".NS",
                        "universe": universe,
                        "source_pdf": matches[0],
                    }
                )
            )
    if len(report_dates) != 1:
        raise ValueError(f"Constituent PDFs disagree on report date: {sorted(report_dates)}")
    archive_date = report_dates.pop()
    if effective_date and effective_date != archive_date:
        raise ValueError(f"Provided effective date {effective_date} differs from report date {archive_date}.")
    snapshot = pd.concat(records, ignore_index=True)
    snapshot["effective_date"] = archive_date
    if snapshot["ticker"].duplicated().any():
        duplicates = sorted(snapshot.loc[snapshot["ticker"].duplicated(), "ticker"].unique())
        raise ValueError(f"A ticker appears in multiple index PDFs: {duplicates}")
    return snapshot.sort_values(["universe", "ticker"]).reset_index(drop=True)
