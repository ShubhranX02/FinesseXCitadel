import zipfile

import pytest

from finesse_portfolio.nse_constituents import archive_coverage, snapshot_from_archive


def test_archive_rejects_missing_required_pdfs(tmp_path) -> None:
    archive = tmp_path / "empty.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("other.pdf", b"not a report")
    with pytest.raises(ValueError, match="Expected one NIFTY_100 PDF"):
        snapshot_from_archive(archive, "2021-03-31")


def test_archive_coverage_reports_missing_required_pdfs(tmp_path) -> None:
    archive = tmp_path / "partial.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("NIFTY_100_Apr2022.pdf", b"not a report")
    status = archive_coverage(archive)
    assert status["complete"] is False
    assert status["missing_universes"] == "NIFTY_MIDCAP_100;NIFTY_SMALLCAP_100"
