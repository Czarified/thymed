"""Regression tests for TimeCard hour calculations."""

import datetime as dt
import json

import pytest

import thymed


@pytest.fixture
def card_with_open_punch(tmp_path, monkeypatch):
    """A ChargeCode with closed punches plus one still-open punch."""
    t0 = dt.datetime(2026, 11, 10, 8, 0)
    times = [
        [t0.isoformat(), (t0 + dt.timedelta(hours=1, minutes=30)).isoformat()],
        # A 25-hour entry: the old formula dropped the whole day.
        [
            (t0 + dt.timedelta(days=1)).isoformat(),
            (t0 + dt.timedelta(days=2, hours=1)).isoformat(),
        ],
        [(t0 + dt.timedelta(days=3)).isoformat()],  # still clocked in
    ]
    data = tmp_path / "data.dat"
    charges = tmp_path / "charges.json"
    data.write_text(json.dumps({"42": times}))
    charges.write_text(
        json.dumps(
            {
                "42": {
                    "name": "Open",
                    "description": "D",
                    "id": 42,
                    "__type__": "ChargeCode",
                }
            }
        )
    )
    monkeypatch.setattr(thymed, "_DATA", data)
    monkeypatch.setattr(thymed, "_CHARGES", charges)
    return thymed.TimeCard(42)


def test_general_report_with_open_punch(card_with_open_punch):
    """An open punch must not crash reporting, and doesn't count hours."""
    df = card_with_open_punch.general_report(
        dt.datetime(2026, 11, 1), dt.datetime(2026, 12, 1)
    )

    assert len(df) == 3
    assert df["hours"].iloc[0] == 1.5
    assert df["hours"].iloc[1] == 25.0
    assert df["hours"].isna().iloc[2]
    assert df["hours"].groupby(df["date"]).sum().sum() == 26.5
