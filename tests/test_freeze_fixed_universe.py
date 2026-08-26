import importlib.util
from pathlib import Path

import pandas as pd


SPEC = importlib.util.spec_from_file_location(
    "freeze_fixed_universe", Path("scripts/freeze_fixed_universe.py")
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_fixed_snapshot_requires_exactly_three_disjoint_100_stock_indices() -> None:
    rows = []
    for universe, prefix in [
        ("NIFTY_100", "A"),
        ("NIFTY_MIDCAP_100", "B"),
        ("NIFTY_SMALLCAP_100", "C"),
    ]:
        rows.extend(
            {"effective_date": "2020-12-31", "universe": universe, "ticker": f"{prefix}{number}.NS"}
            for number in range(100)
        )
    snapshot = pd.DataFrame(rows)

    result = MODULE._validate_snapshot(snapshot.assign(effective_date=pd.to_datetime(snapshot.effective_date)), pd.Timestamp("2020-12-31"))

    assert len(result) == 300
    assert result["ticker"].nunique() == 300
