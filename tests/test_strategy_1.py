"""
tests/test_strategy_1.py

Strategy 1 (Daily + Weekly RRG Confirmation) — the app's only strategy:
- registered once, with entry / exit / market / risk text
- runs on every configured stock with Rs 10,000 and 0.12 % charges, whole shares only
- PVR INOX baseline on data to 16 Oct 2026
- P&L explanation and per-trade reasons
Rule-by-rule coverage (all 16 quadrant combinations) is in test_strategy_1_rules.py.
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
def stocks():
    bench = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    out = {}
    for ticker, meta in cfg.STOCKS.items():
        al = dp.align_stock_with_benchmark(dp.load_clean_data(ticker), bench, meta["name"],
                                           cfg.BENCHMARK_NAME)
        daily, _ = strat.compute_rrg(al, meta["name"], "Daily")
        out[ticker] = {"name": meta["name"], "daily": daily, "aligned": al}
    return out


def test_only_strategy_1_registered():
    assert list(strat.STRATEGY_REGISTRY) == [1]
    meta = strat.STRATEGY_REGISTRY[1]
    assert meta["id"] == 1
    for field in ("name", "tag", "short_desc", "full_desc", "entry_rule", "exit_rule",
                  "best_market", "risk_watch"):
        assert len(meta[field]) > 0, field


def test_runs_on_every_stock(stocks):
    start = pd.Timestamp("2024-01-01")
    for ticker, s in stocks.items():
        asof = strat.weekly_asof(s["aligned"], s["name"])
        if s["daily"].empty or asof.empty:
            continue
        book, cash, val, bh_val, bh_sh, m = strat.run_strategy(1, s["daily"], asof, start, 10000.0, 0.12)
        assert len(val) > 0, ticker
        assert cash >= 0.0, ticker
        assert m["capital"] == 10000.0
        assert m["max_dd_pct"] >= 0.0 and 0.0 <= m["win_rate"] <= 100.0
        for b in book:
            assert isinstance(b["shares"], int) and b["shares"] >= 0
            assert b["daily_at_buy"] in strat.UP and b["weekly_at_buy"] in strat.UP


def test_pvr_baseline(stocks):
    s = stocks["PVRINOX.NS"]
    daily = s["daily"][s["daily"].index <= "2026-10-16"]
    asof = strat.weekly_asof(s["aligned"][s["aligned"].index <= "2026-10-16"], "PVR INOX")
    start = pd.Timestamp("2024-01-01")
    raw, _ = strat.gen_strat_1(daily, asof, start, cost_pct=0.12)
    book, cash, val, bh_val, bh_sh = strat.simulate_single_strategy(daily, raw, start, 100000.0, 0.12)
    assert len(book) == 14
    assert (book[0]["buy"].strftime("%Y-%m-%d"), round(book[0]["buy_px"], 2)) == ("2024-05-24", 1339.05)
    assert (book[0]["sell"].strftime("%Y-%m-%d"), round(book[0]["sell_px"], 2)) == ("2024-07-11", 1460.20)
    assert (book[-1]["buy"].strftime("%Y-%m-%d"), round(book[-1]["buy_px"], 2)) == ("2026-10-12", 1401.30)
    assert round(float(val.iloc[-1]), 2) == 98784.96


def test_explain_pnl_and_trade_outcome_reason(stocks):
    s = stocks["PVRINOX.NS"]
    asof = strat.weekly_asof(s["aligned"], "PVR INOX")
    book, cash, val, bh_val, bh_sh, _ = strat.run_strategy(1, s["daily"], asof,
                                                           pd.Timestamp("2024-01-01"), 10000.0, 0.12)
    info = strat.explain_pnl(book, 10000.0, float(val.iloc[-1]), 0.12, "PVR INOX",
                             strat.STRATEGY_REGISTRY[1]["name"])
    for key in ("is_profit", "headline", "summary_en", "summary_hi", "profit_factor", "win_rate"):
        assert key in info
    assert len(info["bullets_en"]) == len(info["bullets_hi"]) > 0
    for b in book:
        assert len(strat.trade_outcome_reason(b, 0.12)) > 0
