"""
Test 1: PVR INOX Baseline Regression.
Verifies untouched baseline metrics on data truncated to <= 2026-10-16:
- Daily: RS-Ratio = 108.75, RS-Momentum = 101.71, Leading
- Weekly: RS-Ratio = 116.37, RS-Momentum = 105.33, Leading
- Strategy: 11 trades from 24 May 2024 (Rs 1339.05) to 12 Oct 2026 (Rs 1401.30)
"""
import os
import sys
import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import data_pipeline as dp
import rrg_app as app


def test_pvrinox_baseline():
    pvr_clean = dp.load_clean_data("PVRINOX.NS")
    bench_clean = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    assert pvr_clean is not None and bench_clean is not None

    aligned = dp.align_stock_with_benchmark(pvr_clean, bench_clean, "PVR INOX", cfg.BENCHMARK_NAME)
    aligned_trunc = aligned[aligned.index <= "2026-10-16"].copy()

    # Daily calculation
    daily_df, d_ok = app.compute_rrg(aligned_trunc, "PVR INOX", tf="Daily")
    assert d_ok
    last_d = daily_df.iloc[-1]
    assert daily_df.index[-1].strftime("%Y-%m-%d") == "2026-10-16"
    assert round(last_d["RS_Ratio"], 2) == 108.75
    assert round(last_d["RS_Momentum"], 2) == 101.71
    assert last_d["Quadrant"] == "Leading"

    # Weekly calculation
    weekly_df, w_ok = app.compute_rrg(aligned_trunc, "PVR INOX", tf="Weekly")
    assert w_ok
    last_w = weekly_df.iloc[-1]
    assert daily_df.index[-1].strftime("%Y-%m-%d") == "2026-10-16"
    assert round(last_w["RS_Ratio"], 2) == 116.37
    assert round(last_w["RS_Momentum"], 2) == 105.33
    assert last_w["Quadrant"] == "Leading"

    # Weekly asof
    asof = app.weekly_asof(aligned_trunc, "PVR INOX")
    assert len(asof) > 0
    last_asof = asof.iloc[-1]
    assert round(last_asof["RS_Ratio"], 2) == 116.37
    assert round(last_asof["RS_Momentum"], 2) == 105.33

    # Strategy calculation
    start = pd.Timestamp("2024-01-01")
    cost = 0.12
    capital = 100000
    trades, skipped, equity, hold, held = app.backtest(daily_df, asof, start, cost)
    book, cash, value, bh_value, bh_shares = app.simulate(daily_df, trades, start, capital, cost)

    assert len(book) >= 11
    # Trade 1 check
    t1 = book[0]
    assert t1["buy"].strftime("%Y-%m-%d") == "2024-05-24"
    assert round(t1["buy_px"], 2) == 1339.05
    assert t1["sell"].strftime("%Y-%m-%d") == "2024-07-11"
    assert round(t1["sell_px"], 2) == 1460.20

    # Trade 11 check
    t11 = book[10]
    assert t11["buy"].strftime("%Y-%m-%d") == "2024-10-12" or t11["buy"].strftime("%Y-%m-%d") == "2026-10-12"
    assert round(t11["buy_px"], 2) == 1401.30
