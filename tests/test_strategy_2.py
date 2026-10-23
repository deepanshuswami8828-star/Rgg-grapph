"""
Strategy 2 (version 1) — Weekly RRG only.

At each COMPLETED week's close:
  BUY  (flat):          Weekly in {Leading, Improving}
  SELL (open position): Weekly in {Weakening, Lagging}
The Daily RRG is never used; the unfinished current week is ignored.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import data_pipeline as dp
import strategies as strat

QUADS = ["Leading", "Improving", "Weakening", "Lagging"]
UP = {"Leading", "Improving"}
DOWN = {"Weakening", "Lagging"}


def weeks(weekly_q, daily_q=None):
    """Synthetic data: 5 sessions per week, weekly quadrant set on every day of its week."""
    days = pd.bdate_range("2024-01-01", periods=5 * len(weekly_q))       # Mon..Fri blocks
    asof = pd.DataFrame({"Quadrant": np.repeat(weekly_q, 5)}, index=days)
    dq = daily_q if daily_q is not None else ["Lagging"] * len(days)
    daily = pd.DataFrame({"Quadrant": dq, "Close": 100.0}, index=days)
    fridays = days[days.weekday == 4]
    return daily, asof, days, fridays


@pytest.mark.parametrize("wq", QUADS)
def test_buy_only_when_weekly_up(wq):
    daily, asof, days, fri = weeks(["Lagging", wq])
    trades, _ = strat.gen_strat_2(daily, asof, days[0])
    assert any(t["buy"] == fri[1] for t in trades) == (wq in UP)


@pytest.mark.parametrize("wq", QUADS)
def test_sell_only_when_weekly_down(wq):
    daily, asof, days, fri = weeks(["Leading", wq])
    trades, _ = strat.gen_strat_2(daily, asof, days[0])
    assert trades[0]["buy"] == fri[0]
    sold = trades[0]["sell"] == fri[1]
    assert sold == (wq in DOWN)
    if sold:
        assert trades[0]["exit_reason"] == f"Weekly → {wq}"


def test_trades_only_at_week_close_and_reentry():
    daily, asof, days, fri = weeks(["Improving", "Leading", "Weakening", "Lagging", "Improving"])
    trades, _ = strat.gen_strat_2(daily, asof, days[0])
    assert [(t["buy"], t["sell"]) for t in trades] == [(fri[0], fri[2]), (fri[4], None)]
    assert all(t["buy"].weekday() == 4 for t in trades)


def test_daily_is_ignored():
    w = ["Improving", "Leading", "Weakening", "Lagging", "Improving"]
    base, _ = strat.gen_strat_2(*weeks(w)[:2], pd.Timestamp("2024-01-01"))
    rng = np.random.default_rng(7)
    for _ in range(5):
        dq = list(rng.choice(QUADS, 5 * len(w)))
        other, _ = strat.gen_strat_2(*weeks(w, dq)[:2], pd.Timestamp("2024-01-01"))
        assert [(t["buy"], t["sell"]) for t in other] == [(t["buy"], t["sell"]) for t in base]


def test_unfinished_week_is_ignored():
    daily, asof, days, fri = weeks(["Lagging", "Leading"])
    cut = days[days <= days[7]]                  # data stops on Wednesday of week 2
    trades, _ = strat.gen_strat_2(daily.loc[cut], asof.loc[cut], days[0])
    assert trades == []                          # week 2 not closed yet -> no buy


@pytest.fixture(scope="module")
def stocks():
    bench = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    out = {}
    for ticker, meta in cfg.STOCKS.items():
        al = dp.align_stock_with_benchmark(dp.load_clean_data(ticker), bench, meta["name"],
                                           cfg.BENCHMARK_NAME)
        out[ticker] = (meta["name"], al)
    return out


def test_matches_weekly_chart_on_every_stock(stocks):
    """Independent path: the Weekly page's weekly candles, rules replayed by hand."""
    start = pd.Timestamp("2023-01-01")
    for ticker, (name, al) in stocks.items():
        daily, _ = strat.compute_rrg(al, name, "Daily")
        asof = strat.weekly_asof(al, name)
        if daily.empty or asof.empty:
            continue
        trades, _ = strat.gen_strat_2(daily, asof, start)
        wk, _ = strat.compute_rrg(al, name, "Weekly")
        if wk.index[-1] == daily.index[-1] and wk.index[-1].weekday() != 4:
            wk = wk.iloc[:-1]
        mine, held = [], None
        for d, q in wk["Quadrant"].items():
            if d < start:
                continue
            if held is None and q in UP:
                held = d
            elif held is not None and q in DOWN:
                mine.append((held, d))
                held = None
        assert [(t["buy"], t["sell"]) for t in trades if not t["open"]] == mine, ticker
        assert (trades[-1]["buy"] if trades and trades[-1]["open"] else None) == held, ticker


def test_pvr_baseline(stocks):
    name, al = stocks["PVRINOX.NS"]
    al = al[al.index <= "2026-10-16"]
    daily, _ = strat.compute_rrg(al, name, "Daily")
    asof = strat.weekly_asof(al, name)
    start = pd.Timestamp("2024-01-01")
    raw, _ = strat.gen_strat_2(daily, asof, start, 0.12)
    book, cash, val, bh, _ = strat.simulate_single_strategy(daily, raw, start, 100000.0, 0.12)
    assert [(b["buy"].strftime("%Y-%m-%d"), b["sell"].strftime("%Y-%m-%d") if b["sell"] is not None else None)
            for b in book] == [("2024-05-17", "2024-12-27"), ("2025-05-30", "2025-12-12"),
                               ("2026-03-13", "2026-07-03"), ("2026-07-31", None)]
    assert round(book[0]["buy_px"], 2) == 1324.95
    assert round(float(val.iloc[-1]), 2) == 136018.64


def test_registry_and_runner():
    assert {1, 2} <= set(strat.STRATEGY_REGISTRY)
    assert strat.STRATEGY_REGISTRY[2]["name"] == "Weekly RRG Only (Version 1)"
    assert strat.SIGNALS[2] is strat.gen_strat_2
