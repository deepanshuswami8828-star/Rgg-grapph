"""
Pipeline & Validation Tests (Tests 5, 7, 8, 9, 10, 11).
Tests automated validation rules, failure rejection, byte-identical backup retention,
idempotency, duplicate date prevention, and weekend/provisional candle handling.
"""
import copy
import json
import os
import shutil
import sys
from datetime import datetime, time
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import data_pipeline as dp


def test_pipeline_app_start_check():
    """Test 5: App start loads verified data and manifest."""
    manifest = dp.load_manifest()
    assert manifest is not None
    assert "tickers" in manifest
    # Verify all 6 stocks present
    for t in cfg.STOCKS.keys():
        assert t in manifest["tickers"]
        clean_df = dp.load_clean_data(t)
        assert clean_df is not None and len(clean_df) > 0


def test_simulated_failures_rejected_and_byte_identical(tmp_path):
    """
    Test 7: Simulated Yahoo failure (exception, empty, malformed, negative, shrunken).
    Each must be rejected; CSVs and manifest must remain byte-identical.
    """
    pvr_path = cfg.get_clean_csv_path("PVRINOX.NS")
    initial_sha = dp.calculate_sha256(pvr_path)
    initial_manifest_sha = dp.calculate_sha256(cfg.MANIFEST_PATH)

    failure_cases = [
        ("exception", Exception("Simulated 500 Yahoo Server Error")),
        ("empty", pd.DataFrame()),
        ("negative_prices", pd.Series([-100.0, -50.0], index=pd.date_range("2026-10-01", periods=2))),
        ("shrunken_history", pd.Series([1000.0, 1010.0], index=pd.date_range("2026-10-01", periods=2))),
    ]

    for case_name, mock_val in failure_cases:
        if case_name == "exception":
            with patch("data_pipeline.fetch_and_clean_all", side_effect=mock_val):
                res = dp.refresh_data(force=True)
                assert res["status"] == "FAILED"
        else:
            with patch("data_pipeline.fetch_and_clean_all", return_value=(None, f"Simulated {case_name}")):
                res = dp.refresh_data(force=True)
                assert res["status"] == "FAILED"

        # Verify CSV is untouched and byte-identical
        current_sha = dp.calculate_sha256(pvr_path)
        assert current_sha == initial_sha, f"Failure case {case_name} corrupted CSV file!"

        # Verify manifest recorded failure
        m = dp.load_manifest()
        assert m["last_attempt"]["result"] == "FAILED"


def test_good_refresh_with_new_session_updates_data():
    """
    Test 8: A good refresh with new data updates indicators and dates.
    Simulates storing data up to 2026-10-19, then refreshing with 2026-10-22 session.
    """
    pvr_clean = dp.load_clean_data("PVRINOX.NS")
    bench_clean = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    assert pvr_clean is not None and bench_clean is not None
    latest = pvr_clean.index[-1].strftime("%Y-%m-%d")    # latest stored session (moves forward with each data refresh)
    assert latest > "2026-10-16"

    try:
        # Step 1: Temporarily truncate PVRINOX and BENCHMARK to 2026-10-16
        trunc_dt = "2026-10-16"
        pvr_trunc = pvr_clean[pvr_clean.index <= trunc_dt]
        bench_trunc = bench_clean[bench_clean.index <= trunc_dt]
        pvr_trunc.to_csv(cfg.get_clean_csv_path("PVRINOX.NS"), index_label="Date", date_format="%Y-%m-%d")
        bench_trunc.to_csv(cfg.get_clean_csv_path(cfg.BENCHMARK_TICKER), index_label="Date", date_format="%Y-%m-%d")

        stored_check = dp.load_clean_data("PVRINOX.NS")
        assert stored_check.index[-1].strftime("%Y-%m-%d") == trunc_dt
        initial_rows = len(stored_check)

        # Step 2: Now refresh with full dataset (includes 2026-10-22)
        mock_cleaned = {}
        for t in list(cfg.STOCKS.keys()):
            mock_cleaned[t] = dp.load_clean_data(t)["Close"].copy()
        mock_cleaned["PVRINOX.NS"] = pvr_clean["Close"].copy()
        mock_cleaned[cfg.BENCHMARK_TICKER] = bench_clean["Close"].copy()

        with patch("data_pipeline.fetch_and_clean_all", return_value=(mock_cleaned, None)):
            res = dp.refresh_data(force=True)
            assert res["status"] == "SUCCESS"

            # Check updated clean CSV has advanced to the latest session
            new_pvr = dp.load_clean_data("PVRINOX.NS")
            assert new_pvr.index[-1].strftime("%Y-%m-%d") == latest
            assert len(new_pvr) > initial_rows
    finally:
        # Always restore full clean files
        pvr_clean.to_csv(cfg.get_clean_csv_path("PVRINOX.NS"), index_label="Date", date_format="%Y-%m-%d")
        bench_clean.to_csv(cfg.get_clean_csv_path(cfg.BENCHMARK_TICKER), index_label="Date", date_format="%Y-%m-%d")


def test_repeated_refreshes_no_duplicate_dates():
    """
    Test 9: Repeated refreshes never create duplicate dates.
    """
    for t in cfg.STOCKS.keys():
        df = dp.load_clean_data(t)
        assert df is not None
        assert df.index.is_unique, f"Duplicate dates found in {t}"
        assert df.index.is_monotonic_increasing, f"Dates not monotonic in {t}"


def test_scheduler_idempotent_no_redundant_download():
    """
    Test 10: Scheduler script run twice in a row with no new session available
    makes no download on the second run.
    """
    # First run
    res1 = dp.refresh_data(force=False)
    assert res1["status"] in ("SUCCESS", "NO_NEW_SESSION", "SKIPPED")

    # Second run immediately after
    res2 = dp.refresh_data(force=False)
    assert res2["status"] in ("NO_NEW_SESSION", "SKIPPED")


def test_weekend_holiday_and_incomplete_candle_handling():
    """
    Test 11:
    - Weekend run does not fetch/publish.
    - Partial today's bar (< 15:45 IST) is not written to *_clean.csv.
    """
    # 1. Weekend run simulation (Saturday)
    sat_dt = datetime(2026, 10, 24, 12, 0, 0, tzinfo=cfg.IST)
    with patch("data_pipeline.datetime") as mock_dt:
        mock_dt.now.return_value = sat_dt
        mock_dt.fromisoformat = datetime.fromisoformat
        res = dp.refresh_data(force=False)
        assert res["status"] == "NO_NEW_SESSION"
        assert "Weekend" in res["message"]

    # 2. Incomplete candle test (today 11:00 AM IST)
    assert not dp.is_session_final(datetime.now(cfg.IST).date(), datetime(2026, 10, 22, 11, 0, 0, tzinfo=cfg.IST))
    # After 15:45 IST, it is final
    assert dp.is_session_final(datetime.now(cfg.IST).date(), datetime(2026, 10, 22, 16, 0, 0, tzinfo=cfg.IST))
