"""Tests for the SQL analysis - run with: python3 test_analysis.py

Every SQL answer is recomputed independently in pandas from the same
generated data and the two must agree. The generator is also checked to be
deterministic, so results are stable run to run.
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from generate_data import generate, DB  # noqa: E402
from run_queries import run  # noqa: E402


def to_frame(cols, rows):
    return pd.DataFrame(rows, columns=cols)


def test_generator_deterministic():
    p1, a1 = generate()
    p2, a2 = generate()
    assert p1.equals(p2) and a1.equals(a2), "same seed must give identical data"
    assert len(p1) == 200 and len(a1) == 1200
    print("PASS generator is deterministic (200 patients, 1200 appointments)")


def test_database_matches_generator():
    assert DB.exists(), "run generate_data.py first"
    p, a = generate()
    with sqlite3.connect(DB) as con:
        pa = pd.read_sql("SELECT COUNT(*) AS n FROM appointments", con).iloc[0, 0]
        pp = pd.read_sql("SELECT COUNT(*) AS n FROM patients", con).iloc[0, 0]
    assert pa == len(a) and pp == len(p)
    print("PASS database contents match the generator")


def test_attendance_by_clinic():
    _, a = generate()
    expected = (a.groupby("clinic")["attended"]
                  .agg(["count", "sum"])
                  .assign(pct=lambda d: (100 * d["sum"] / d["count"]).round(1))
                  .sort_values("pct", ascending=False))
    got = to_frame(*run()["attendance_by_clinic"])
    assert list(got["clinic"]) == list(expected.index)
    assert list(got["attendance_pct"]) == list(expected["pct"])
    print("PASS attendance_by_clinic matches independent pandas calculation")


def test_wait_by_reason():
    _, a = generate()
    expected = a.groupby("reason")["days_waited"].mean().round(1).sort_values(ascending=False)
    got = to_frame(*run()["wait_by_reason"])
    assert list(got["reason"]) == list(expected.index)
    assert list(got["avg_days_waited"]) == list(expected.values)
    print("PASS wait_by_reason matches independent pandas calculation")


def test_monthly_volume_rolling_average():
    _, a = generate()
    monthly = a.assign(month=a["appointment_date"].str[:7]).groupby("month").size()
    got = to_frame(*run()["monthly_volume"])
    assert list(got["month"]) == list(monthly.index) and len(got) == 6
    assert list(got["appointments"]) == list(monthly.values)
    # rolling 3-month mean of the last month, computed independently
    expected_last = round(monthly.values[-3:].mean(), 1)
    assert got["rolling_3mo_avg"].iloc[-1] == expected_last
    print("PASS monthly_volume including window-function rolling average")


def test_no_show_by_age_band():
    p, a = generate()
    merged = a.merge(p, on="patient_id")
    expected = (merged.groupby("age_band")["attended"]
                      .agg(["count", "sum"])
                      .assign(pct=lambda d: (100 * (d["count"] - d["sum"]) / d["count"]).round(1)))
    got = to_frame(*run()["no_show_by_age_band"])
    assert list(got["age_band"]) == list(expected.index)
    assert list(got["no_show_pct"]) == list(expected["pct"])
    print("PASS no_show_by_age_band (join) matches independent pandas calculation")


def test_top_no_shows():
    p, a = generate()
    missed = a[a["attended"] == 0].groupby("patient_id").size().sort_values(ascending=False)
    got = to_frame(*run()["top_no_shows"])
    assert len(got) <= 10
    for _, row in got.iterrows():
        assert missed.loc[row["patient_id"]] == row["missed"]
    assert got["missed"].iloc[0] == missed.iloc[0]
    print("PASS top_no_shows returns the true most-missed patients")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception:
            failed += 1
            import traceback
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    sys.exit(1 if failed else 0)
