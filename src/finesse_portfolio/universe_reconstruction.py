"""Rebuild monthly point-in-time membership from a full snapshot and NSE notices."""
from __future__ import annotations

import pandas as pd

INDEXES = ("NIFTY_100", "NIFTY_MIDCAP_100", "NIFTY_SMALLCAP_100")
REQUIRED_CHANGE_COLUMNS = {"effective_date", "universe", "action", "ticker", "source_url"}


def read_change_ledger(path: str) -> pd.DataFrame:
    """Load and validate an auditable official-index-change ledger."""
    changes = pd.read_csv(path, parse_dates=["effective_date"])
    missing = REQUIRED_CHANGE_COLUMNS.difference(changes.columns)
    if missing:
        raise ValueError(f"Change ledger is missing columns: {sorted(missing)}")
    if changes.empty:
        raise ValueError("Change ledger is empty; refusing to carry an old universe forward.")
    changes = changes.copy()
    changes["universe"] = changes["universe"].astype(str).str.upper().str.strip()
    changes["action"] = changes["action"].astype(str).str.upper().str.strip()
    changes["ticker"] = changes["ticker"].astype(str).str.upper().str.strip()
    changes["ticker"] = changes["ticker"].where(changes["ticker"].str.endswith(".NS"), changes["ticker"] + ".NS")
    if set(changes["universe"]).difference(INDEXES):
        raise ValueError("Change ledger has an unexpected universe label.")
    if set(changes["action"]).difference({"ADD", "REMOVE"}):
        raise ValueError("Change ledger action must be ADD or REMOVE.")
    if changes[["effective_date", "universe", "action", "ticker"]].duplicated().any():
        raise ValueError("Change ledger has duplicate effective-date, index, action and ticker rows.")
    if changes["source_url"].isna().any() or (changes["source_url"].str.strip() == "").any():
        raise ValueError("Every change-ledger row must include its official source URL.")
    return changes.sort_values(["effective_date", "action", "universe", "ticker"]).reset_index(drop=True)


def _validated_state(base_universe: pd.DataFrame, base_date: pd.Timestamp) -> dict[str, set[str]]:
    snapshot = base_universe.loc[base_universe["effective_date"] == base_date, ["universe", "ticker"]].copy()
    counts = snapshot.groupby("universe")["ticker"].nunique().to_dict()
    if counts != {index: 100 for index in INDEXES}:
        raise ValueError(f"Base snapshot {base_date.date()} is not three complete 100-stock indices: {counts}")
    if snapshot["ticker"].duplicated().any():
        raise ValueError("Base snapshot contains a ticker in more than one index.")
    return {index: set(snapshot.loc[snapshot["universe"] == index, "ticker"]) for index in INDEXES}


def reconstruct_month_end_universe(
    base_universe: pd.DataFrame,
    changes: pd.DataFrame,
    start: str,
    end: str,
) -> pd.DataFrame:
    """Apply official adds/removes and emit a complete snapshot at each month end."""
    base = base_universe.copy()
    base["effective_date"] = pd.to_datetime(base["effective_date"])
    changes = changes.copy()
    changes["effective_date"] = pd.to_datetime(changes["effective_date"])
    start_date, end_date = pd.Timestamp(start), pd.Timestamp(end)
    eligible_dates = base.loc[base["effective_date"] <= start_date, "effective_date"]
    if eligible_dates.empty:
        raise ValueError("No complete base snapshot exists on or before the requested start date.")
    base_date = eligible_dates.max()
    state = _validated_state(base, base_date)
    changes = changes.loc[(changes["effective_date"] > base_date) & (changes["effective_date"] <= end_date)].copy()
    month_ends = pd.date_range(start_date, end_date, freq="ME")
    if month_ends.empty:
        raise ValueError("Requested reconstruction period has no month end.")

    records: list[dict[str, str]] = []
    change_cursor = 0
    change_dates = list(changes["effective_date"].drop_duplicates())
    for month_end in month_ends:
        while change_cursor < len(change_dates) and change_dates[change_cursor] <= month_end:
            effective_date = change_dates[change_cursor]
            batch = changes.loc[changes["effective_date"] == effective_date].copy()
            # Process removals first, allowing an official index migration on one date.
            batch["_action_order"] = batch["action"].map({"REMOVE": 0, "ADD": 1})
            batch = batch.sort_values(["_action_order", "universe", "ticker"])
            for row in batch.itertuples(index=False):
                if row.action == "REMOVE":
                    if row.ticker not in state[row.universe]:
                        raise ValueError(
                            f"{row.ticker} cannot be removed from {row.universe} on "
                            f"{effective_date.date()}: it is absent from the reconstructed state."
                        )
                    state[row.universe].remove(row.ticker)
                else:
                    if any(row.ticker in members for members in state.values()):
                        raise ValueError(
                            f"{row.ticker} cannot be added to {row.universe} on "
                            f"{effective_date.date()}: it already belongs to an index."
                        )
                    state[row.universe].add(row.ticker)
            counts = {index: len(state[index]) for index in INDEXES}
            if counts != {index: 100 for index in INDEXES}:
                raise ValueError(
                    f"Official changes on {effective_date.date()} do not leave three 100-stock indices: {counts}"
                )
            change_cursor += 1
        for universe in INDEXES:
            records.extend(
                {
                    "effective_date": month_end.date().isoformat(),
                    "ticker": ticker,
                    "universe": universe,
                    "derivation": "official_change_ledger",
                }
                for ticker in sorted(state[universe])
            )
    return pd.DataFrame(records).sort_values(["effective_date", "universe", "ticker"]).reset_index(drop=True)
