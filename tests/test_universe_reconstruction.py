import pandas as pd

from finesse_portfolio.universe_reconstruction import reconstruct_month_end_universe


def _base_snapshot() -> pd.DataFrame:
    rows = []
    for universe, prefix in [("NIFTY_100", "A"), ("NIFTY_MIDCAP_100", "B"), ("NIFTY_SMALLCAP_100", "C")]:
        rows.extend(
            {"effective_date": "2022-03-31", "universe": universe, "ticker": f"{prefix}{number}.NS"}
            for number in range(100)
        )
    return pd.DataFrame(rows)


def test_reconstruction_applies_changes_and_keeps_complete_indices() -> None:
    changes = pd.DataFrame(
        [
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "action": "REMOVE", "ticker": "A0.NS", "source_url": "https://official.example/a"},
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "action": "ADD", "ticker": "NEW.NS", "source_url": "https://official.example/a"},
        ]
    )
    result = reconstruct_month_end_universe(_base_snapshot(), changes, "2022-03-31", "2022-05-31")
    april = result.loc[(result["effective_date"] == "2022-04-30") & (result["universe"] == "NIFTY_100")]
    assert len(result) == 3 * 3 * 100
    assert set(april["ticker"]) >= {"NEW.NS"}
    assert "A0.NS" not in set(april["ticker"])


def test_reconstruction_allows_a_same_day_index_migration() -> None:
    changes = pd.DataFrame(
        [
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "action": "REMOVE", "ticker": "A0.NS", "source_url": "https://official.example/a"},
            {"effective_date": "2022-04-15", "universe": "NIFTY_MIDCAP_100", "action": "REMOVE", "ticker": "B0.NS", "source_url": "https://official.example/a"},
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "action": "ADD", "ticker": "B0.NS", "source_url": "https://official.example/a"},
            {"effective_date": "2022-04-15", "universe": "NIFTY_MIDCAP_100", "action": "ADD", "ticker": "A0.NS", "source_url": "https://official.example/a"},
        ]
    )
    result = reconstruct_month_end_universe(_base_snapshot(), changes, "2022-03-31", "2022-04-30")
    april = result.loc[result["effective_date"] == "2022-04-30"]
    assert "B0.NS" in set(april.loc[april["universe"] == "NIFTY_100", "ticker"])
    assert "A0.NS" in set(april.loc[april["universe"] == "NIFTY_MIDCAP_100", "ticker"])


def test_reconstruction_does_not_create_a_month_end_before_its_requested_start() -> None:
    changes = pd.DataFrame(
        [
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "action": "REMOVE", "ticker": "A0.NS", "source_url": "https://official.example/a"},
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "action": "ADD", "ticker": "NEW.NS", "source_url": "https://official.example/a"},
        ]
    )
    result = reconstruct_month_end_universe(_base_snapshot(), changes, "2022-04-01", "2022-05-31")
    assert set(result["effective_date"]) == {"2022-04-30", "2022-05-31"}


def test_reconstruction_allows_an_explicit_official_count_exception() -> None:
    changes = pd.DataFrame(
        [
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "action": "ADD", "ticker": "EXTRA.NS", "source_url": "https://official.example/a"},
        ]
    )
    exceptions = pd.DataFrame(
        [
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "expected_constituent_count": 101, "source_url": "https://official.example/a"},
        ]
    )
    result = reconstruct_month_end_universe(
        _base_snapshot(), changes, "2022-04-01", "2022-04-30", exceptions
    )
    assert len(result.loc[result["universe"] == "NIFTY_100"]) == 101


def test_count_exception_persists_until_a_later_official_count_is_recorded() -> None:
    changes = pd.DataFrame(
        [
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "action": "ADD", "ticker": "EXTRA.NS", "source_url": "https://official.example/a"},
        ]
    )
    exceptions = pd.DataFrame(
        [
            {"effective_date": "2022-04-15", "universe": "NIFTY_100", "expected_constituent_count": 101, "source_url": "https://official.example/a"},
        ]
    )
    result = reconstruct_month_end_universe(
        _base_snapshot(), changes, "2022-04-01", "2022-05-31", exceptions
    )
    may = result.loc[(result["effective_date"] == "2022-05-31") & (result["universe"] == "NIFTY_100")]
    assert len(may) == 101
