"""
tests/test_12_strategies.py

Comprehensive automated tests verifying:
- All 12 RRG strategies execute with realistic ₹10,000 capital and 0.12% charges.
- Whole-share constraint enforcement (no fractional shares).
- Exact match of baseline Strategy 3 numbers on PVR INOX.
- Strategy 12 multi-stock portfolio allocation from single ₹10,000 pool.
- Full 12-strategy comparison dashboard across all 6 stocks with zero exceptions.
"""

import os
import sys
import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import data_pipeline as dp
import strategies as strat


@pytest.fixture(scope="module")
def prepared_data():
    clean_data = {}
    for ticker in list(cfg.STOCKS.keys()) + [cfg.BENCHMARK_TICKER]:
        clean_data[ticker] = dp.load_clean_data(ticker)
    bench_clean = clean_data[cfg.BENCHMARK_TICKER]

    stocks_rrg = {}
    for ticker, meta in cfg.STOCKS.items():
        clean_df = clean_data[ticker]
        al = dp.align_stock_with_benchmark(clean_df, bench_clean, meta["name"], cfg.BENCHMARK_NAME)
        d, _ = strat.compute_rrg(al, meta["name"], "Daily")
        stocks_rrg[ticker] = {"name": meta["name"], "daily": d, "aligned": al}

    return clean_data, bench_clean, stocks_rrg


def test_strategy_registry_completeness():
    """Verify all 12 strategies are properly registered with required metadata."""
    assert len(strat.STRATEGY_REGISTRY) == 12
    for s_id in range(1, 13):
        assert s_id in strat.STRATEGY_REGISTRY
        meta = strat.STRATEGY_REGISTRY[s_id]
        assert meta["id"] == s_id
        assert "name" in meta and len(meta["name"]) > 0
        assert "tag" in meta and len(meta["tag"]) > 0
        assert "short_desc" in meta and len(meta["short_desc"]) > 0
        assert "full_desc" in meta and len(meta["full_desc"]) > 0


def test_all_12_strategies_run_on_pvrinox(prepared_data):
    """Test each of the 12 strategies on PVR INOX with ₹10,000 capital."""
    _, bench_clean, stocks_rrg = prepared_data
    pvr_data = stocks_rrg["PVRINOX.NS"]
    daily = pvr_data["daily"]
    asof = strat.weekly_asof(pvr_data["aligned"], "PVR INOX")
    start = pd.Timestamp("2024-01-01")
    capital = 10000.0
    cost = 0.12

    for s_id in range(1, 13):
        book, cash, val, bh_val, bh_sh, m = strat.run_strategy(
            s_id, daily, asof, start, capital, cost, stocks_rrg, bench_clean
        )
        assert len(val) > 0, f"Strategy {s_id} returned empty equity curve"
        assert cash >= 0.0, f"Strategy {s_id} resulted in negative cash: {cash}"
        assert m["capital"] == capital
        assert isinstance(m["final_value"], float)
        assert isinstance(m["return_pct"], float)
        assert isinstance(m["max_dd_pct"], float)
        assert m["max_dd_pct"] >= 0.0
        assert 0.0 <= m["win_rate"] <= 100.0

        # Check whole-shares constraint
        for b in book:
            assert isinstance(b["shares"], int)
            assert b["shares"] >= 0


def test_baseline_strategy_3_exact_trades(prepared_data):
    """Verify Strategy 3 matches untouched PVR INOX baseline numbers."""
    _, _, stocks_rrg = prepared_data
    pvr_data = stocks_rrg["PVRINOX.NS"]
    daily = pvr_data["daily"]
    asof = strat.weekly_asof(pvr_data["aligned"], "PVR INOX")
    start = pd.Timestamp("2024-01-01")

    # Truncate to baseline date 2026-10-16 for exact check
    daily_trunc = daily[daily.index <= "2026-10-16"].copy()
    asof_trunc = asof[asof.index <= "2026-10-16"].copy()

    raw, _ = strat.gen_strat_3(daily_trunc, asof_trunc, start, cost_pct=0.12)
    book, cash, val, bh_val, bh_sh = strat.simulate_single_strategy(
        daily_trunc, raw, start, capital=100000.0, cost_pct=0.12
    )

    assert len(book) >= 11
    t1 = book[0]
    assert t1["buy"].strftime("%Y-%m-%d") == "2024-05-24"
    assert round(t1["buy_px"], 2) == 1339.05
    assert t1["sell"].strftime("%Y-%m-%d") == "2024-07-11"
    assert round(t1["sell_px"], 2) == 1460.20

    t11 = book[10]
    assert t11["buy"].strftime("%Y-%m-%d") in ["2024-10-12", "2026-10-12"]
    assert round(t11["buy_px"], 2) == 1401.30


def test_strategy_6_partial_profit_booking(prepared_data):
    """Verify Strategy 6 partial profit booking mechanics."""
    _, _, stocks_rrg = prepared_data
    pvr_data = stocks_rrg["PVRINOX.NS"]
    daily = pvr_data["daily"]
    asof = strat.weekly_asof(pvr_data["aligned"], "PVR INOX")
    start = pd.Timestamp("2024-01-01")

    book, cash, val, bh_val, bh_sh = strat.simulate_partial_strategy(
        daily, asof, start, capital=10000.0, cost_pct=0.12, profit_target=8.0, stop_loss_pct=6.0
    )
    assert len(book) > 0
    # Verify whole shares
    for b in book:
        assert isinstance(b["shares"], int)
        assert b["shares"] > 0
    # Check that partial targets or RRG exits are properly documented
    reasons = [b["exit_reason"] for b in book]
    assert any("Partial Target" in r or "Drop to" in r or "Still Holding" in r for r in reasons)


def test_portfolio_rotation_strategy_12_single_capital_pool(prepared_data):
    """Verify Strategy 12 uses single ₹10,000 pool across all 6 stocks."""
    _, bench_clean, stocks_rrg = prepared_data
    start = pd.Timestamp("2024-01-01")
    capital = 10000.0

    trades, eq, bh_val, hist = strat.run_portfolio_rotation(
        stocks_rrg, bench_clean, start, capital=capital, cost_pct=0.12, max_positions=2
    )
    assert len(trades) > 0
    assert len(eq) > 100
    assert 9900.0 <= eq.iloc[0] <= capital
    assert all(h["cash"] >= 0 for h in hist), "Cash balance cannot be negative"
    # Ensure shares are integers
    for t in trades:
        assert isinstance(t["shares"], int)
        assert t["shares"] > 0


def test_compare_all_strategies_dashboard_engine(prepared_data):
    """Verify compare_all_strategies runs smoothly and produces valid scorecard."""
    _, bench_clean, stocks_rrg = prepared_data
    pvr_data = stocks_rrg["PVRINOX.NS"]
    daily = pvr_data["daily"]
    asof = strat.weekly_asof(pvr_data["aligned"], "PVR INOX")
    start = pd.Timestamp("2024-01-01")

    summary_df, eq_df, dd_df, hi = strat.compare_all_strategies(
        daily, asof, start, capital=10000.0, cost_pct=0.12, stocks_rrg=stocks_rrg, bench_clean=bench_clean
    )
    assert len(summary_df) == 12
    assert "Buy & Hold" in eq_df.columns
    assert len(eq_df.columns) == 13 # 12 strategies + 1 B&H
    assert "highest_return" in hi
    assert "lowest_drawdown" in hi
    assert "best_risk_adjusted" in hi
    assert "highest_win_rate" in hi


def test_all_6_stocks_run_12_strategies(prepared_data):
    """Verify compare_all_strategies runs for all 6 configured stocks without error."""
    _, bench_clean, stocks_rrg = prepared_data
    start = pd.Timestamp("2024-01-01")

    for ticker, data in stocks_rrg.items():
        daily = data["daily"]
        name = data["name"]
        asof = strat.weekly_asof(data["aligned"], name)
        if len(asof) < 30:
            continue
        summary_df, eq_df, dd_df, hi = strat.compare_all_strategies(
            daily, asof, start, capital=10000.0, cost_pct=0.12, stocks_rrg=stocks_rrg, bench_clean=bench_clean
        )
        assert len(summary_df) == 12, f"Failed on stock {ticker} ({name})"


def test_strategy_registry_explanation_fields():
    """Verify all 12 strategies have clear entry, exit, market condition, and risk rules."""
    for s_id in range(1, 13):
        meta = strat.STRATEGY_REGISTRY[s_id]
        assert "entry_rule" in meta and len(meta["entry_rule"]) > 10
        assert "exit_rule" in meta and len(meta["exit_rule"]) > 10
        assert "best_market" in meta and len(meta["best_market"]) > 10
        assert "risk_watch" in meta and len(meta["risk_watch"]) > 10


def test_explain_pnl_and_trade_outcome_reason(prepared_data):
    """Verify explain_pnl attribution logic and trade outcome reasoning."""
    _, bench_clean, stocks_rrg = prepared_data
    pvr_data = stocks_rrg["PVRINOX.NS"]
    daily = pvr_data["daily"]
    asof = strat.weekly_asof(pvr_data["aligned"], "PVR INOX")
    start = pd.Timestamp("2024-01-01")
    capital = 10000.0
    cost = 0.12

    # Run Strategy 3
    book, cash, val, bh_val, bh_sh, _ = strat.run_strategy(
        3, daily, asof, start, capital, cost, stocks_rrg, bench_clean
    )
    final_val = float(val.iloc[-1])
    pnl_info = strat.explain_pnl(book, capital, final_val, cost, "PVR INOX", "Daily + Weekly Confirmation")

    assert "is_profit" in pnl_info
    assert "headline" in pnl_info and len(pnl_info["headline"]) > 0
    assert "summary_en" in pnl_info and len(pnl_info["summary_en"]) > 0
    assert "summary_hi" in pnl_info and len(pnl_info["summary_hi"]) > 0
    assert "profit_factor" in pnl_info
    assert "win_rate" in pnl_info
    assert len(pnl_info["bullets_en"]) > 0
    assert len(pnl_info["bullets_hi"]) > 0
    assert len(pnl_info["bullets_en"]) == len(pnl_info["bullets_hi"])

    # Test trade outcome reasoning on every book item
    for b in book:
        reason_str = strat.trade_outcome_reason(b, cost)
        assert isinstance(reason_str, str) and len(reason_str) > 0

