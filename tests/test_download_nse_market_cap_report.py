import pytest

from finesse_portfolio.nse_archive import market_cap_report_url, report_months


def test_report_url_uses_nse_month_filename() -> None:
    url, filename = market_cap_report_url("2021-03")
    assert filename == "indices_dataMar2021.zip"
    assert url.endswith("/indices_dataMar2021.zip")


def test_report_months_is_inclusive_and_validates_order() -> None:
    assert report_months("2020-12", "2021-02") == ["2020-12", "2021-01", "2021-02"]
    with pytest.raises(ValueError, match="must not be after"):
        report_months("2021-02", "2020-12")
