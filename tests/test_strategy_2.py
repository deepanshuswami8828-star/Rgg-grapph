"""
Strategy 2 (version 1) — Weekly RRG only, acted on every trading day.

Each day, on the weekly reading as it stands at that day's close (week so far):
  BUY  (flat):          Weekly in {Leading, Improving}
  SELL (open position): Weekly in {Weakening, Lagging}
The Daily RRG is never used. The signal is acted on the first day it is valid - not at the
end of the week (regression: PVR INOX entered Improving on Mon 13 May 2024 -> buy that day).
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
from make_rrg_pvrinox import calc_rs_ratio, calc_rs_momentum, quadrant

QUADS = ["Leading", "Improving", "Weakening", "Lagging"]
UP = {"Leading", "Improving"}
DOWN = {"Weakening", "Lagging"}


def days_frames(weekly_q, daily_q=None, close=None):
    """One weekly reading per trading DAY (as the week stands that day)."""
    idx = pd.bdate_range("2024-01-01", periods=len(weekly_q))
    asof = pd.DataFrame({"Quadrant": weekly_q, "RS_Momentum": 100.5}, index=idx)
    daily = pd.DataFrame({"Quadrant": daily_q or ["Lagging"] * len(idx),
                          "Close": close or [100.0] * len(idx)}, index=idx)
    return daily, asof, idx


@pytest.mark.parametrize("wq", QUADS)
def test_buy_only_when_weekly_up(wq):
    daily, asof, idx = days_frames(["Lagging", wq])
    trades, _ = strat.gen_strat_2(daily, asof, idx[0], entry="close", rrg_exit="close")
    assert any(t["buy"] == idx[1] for t in trades) == (wq in UP)


@pytest.mark.parametrize("wq", QUADS)
def test_sell_only_when_weekly_down(wq):
    daily, asof, idx = days_frames(["Leading", wq])
    trades, _ = strat.gen_strat_2(daily, asof, idx[0], entry="close", rrg_exit="close")
    assert trades[0]["buy"] == idx[0]
    assert (trades[0]["sell"] == idx[1]) == (wq in DOWN)


def test_acts_on_the_first_valid_day_not_the_week_end():
    # Mon 1 Jan 2024 .. : weekly turns Improving on Wednesday -> buy Wednesday, not Friday
    daily, asof, idx = days_frames(["Lagging", "Lagging", "Improving", "Improving", "Improving"])
    trades, _ = strat.gen_strat_2(daily, asof, idx[0], entry="close", rrg_exit="close")
    assert trades[0]["buy"] == idx[2] and idx[2].weekday() == 2


def test_daily_is_ignored():
    w = ["Lagging", "Improving", "Leading", "Weakening", "Lagging", "Improving"]
    base, _ = strat.gen_strat_2(*days_frames(w)[:2], pd.Timestamp("2024-01-01"), entry="close", rrg_exit="close")
    rng = np.random.default_rng(7)
    for _ in range(5):
        dq = list(rng.choice(QUADS, len(w)))
        other, _ = strat.gen_strat_2(*days_frames(w, dq)[:2], pd.Timestamp("2024-01-01"), entry="close", rrg_exit="close")
        assert [(t["buy"], t["sell"]) for t in other] == [(t["buy"], t["sell"]) for t in base]


@pytest.fixture(scope="module")
def stocks():
    bench = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    return {t: (m["name"], dp.align_stock_with_benchmark(dp.load_clean_data(t), bench, m["name"],
                                                          cfg.BENCHMARK_NAME))
            for t, m in cfg.STOCKS.items()}


def weekly_from_scratch(al, name, day):
    """Weekly quadrant on `day` rebuilt from data up to `day` only (no look-ahead)."""
    c = al.loc[:day]
    w = c.groupby(c.index.to_period("W-FRI")).tail(1)
    rr = calc_rs_ratio(w[name], w[cfg.BENCHMARK_NAME])
    return quadrant(rr.iloc[-1], calc_rs_momentum(rr).iloc[-1])


def test_every_stock_first_valid_day_and_no_lookahead(stocks):
    start = pd.Timestamp("2024-01-01")
    for ticker, (name, al) in stocks.items():
        daily, _ = strat.compute_rrg(al, name, "Daily")
        asof = strat.weekly_asof(al, name)
        if daily.empty or asof.empty:
            continue
        trades, _ = strat.gen_strat_2(daily, asof, start, entry="close", rrg_exit="close")
        w = asof["Quadrant"]
        mine, held = [], None
        for d in daily.index[daily.index >= start]:
            if d not in w.index:
                continue
            if held is None and w[d] in UP:
                held = d
            elif held is not None and w[d] in DOWN:
                mine.append((held, d))
                held = None
        assert [(t["buy"], t["sell"]) for t in trades if not t["open"]] == mine, ticker
        assert (trades[-1]["buy"] if trades and trades[-1]["open"] else None) == held, ticker
        for t in trades:                       # the reading used on each trade day is real
            for d in [t["buy"]] + ([t["sell"]] if t["sell"] is not None else []):
                assert weekly_from_scratch(al, name, d) == w[d], (ticker, d)


def test_pvr_baseline_buys_on_13_may_2024(stocks):
    name, al = stocks["PVRINOX.NS"]
    al = al[al.index <= "2026-10-16"]
    daily, _ = strat.compute_rrg(al, name, "Daily")
    asof = strat.weekly_asof(al, name)
    start = pd.Timestamp("2024-01-01")
    raw, _ = strat.gen_strat_2(daily, asof, start, 0.12, entry="close", rrg_exit="close")
    book, cash, val, bh, _ = strat.simulate_single_strategy(daily, raw, start, 100000.0, 0.12)
    assert [(b["buy"].strftime("%Y-%m-%d"), b["sell"].strftime("%Y-%m-%d") if b["sell"] is not None else None)
            for b in book] == [("2024-05-13", "2024-12-23"), ("2025-05-26", "2025-12-08"),
                               ("2026-03-09", "2026-06-29"), ("2026-07-27", None)]
    assert round(book[0]["buy_px"], 2) == 1315.60
    assert round(float(val.iloc[-1]), 2) == 132488.32


def test_registry_and_runner():
    assert {1, 2} <= set(strat.STRATEGY_REGISTRY)
    assert strat.STRATEGY_REGISTRY[2]["name"] == "Weekly RRG Only (Version 1)"
    assert strat.SIGNALS[2] is strat.gen_strat_2
