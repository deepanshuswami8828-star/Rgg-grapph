"""
Strategy 2, version 2 — Weekly RRG only, early exit at RS-Momentum < 101.

At each COMPLETED week's close:
  SELL (open):  Weekly == Leading and RS-Momentum < 101   (early exit)
                or Weekly in {Weakening, Lagging}          (safety net)
  BUY  (flat):  Weekly in {Leading, Improving}; after an early exit only once the weekly
                has been in Weakening/Lagging and comes back up (fresh entry).
The Daily RRG is never used. Internal registry key 3, shown as "Strategy 2 · Version 2".
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

UP = {"Leading", "Improving"}
DOWN = {"Weakening", "Lagging"}


def weeks(rows, daily_q=None):
    """rows: [(quadrant, rs_momentum)] per week; 5 sessions per week, Fridays are week closes."""
    days = pd.bdate_range("2024-01-01", periods=5 * len(rows))
    asof = pd.DataFrame({"Quadrant": np.repeat([q for q, _ in rows], 5),
                         "RS_Momentum": np.repeat([m for _, m in rows], 5)}, index=days)
    dq = daily_q if daily_q is not None else ["Lagging"] * len(days)
    daily = pd.DataFrame({"Quadrant": dq, "Close": 100.0}, index=days)
    return daily, asof, days, days[days.weekday == 4]


def run(rows, daily_q=None):
    daily, asof, days, fri = weeks(rows, daily_q)
    trades, _ = strat.gen_strat_2_v2(daily, asof, days[0])
    return [(list(fri).index(t["buy"]), list(fri).index(t["sell"]) if t["sell"] is not None else None,
             t["exit_reason"]) for t in trades]


def test_early_exit_in_leading_below_101():
    out = run([("Improving", 100.5), ("Leading", 102.0), ("Leading", 100.9)])
    assert [(b, s) for b, s, _ in out] == [(0, 2)]
    assert out[0][2] == "Weekly Leading, RS-Momentum 100.90 < 101"


def test_no_early_exit_at_or_above_101_or_outside_leading():
    # Leading at exactly 101 holds; Improving below 101 is not an early exit
    out = run([("Leading", 103.0), ("Leading", 101.0), ("Improving", 100.2), ("Leading", 101.5)])
    assert out == [(0, None, "Open Position")]


@pytest.mark.parametrize("q", sorted(DOWN))
def test_safety_net_exit(q):
    out = run([("Improving", 100.4), (q, 99.0)])
    assert [(b, s) for b, s, _ in out] == [(0, 1)] and out[0][2] == f"Weekly → {q}"


def test_fresh_entry_after_early_exit():
    rows = [("Leading", 103.0), ("Leading", 100.5),          # buy w0, early exit w1
            ("Leading", 102.0), ("Improving", 101.0),         # still up: no re-buy
            ("Weakening", 99.5),                               # down: re-armed
            ("Improving", 100.3)]                              # fresh entry: buy w5
    assert [(b, s) for b, s, _ in run(rows)] == [(0, 1), (5, None)]


def test_reentry_right_after_safety_net_exit():
    rows = [("Improving", 100.5), ("Lagging", 98.0), ("Improving", 100.2)]
    assert [(b, s) for b, s, _ in run(rows)] == [(0, 1), (2, None)]


def test_daily_is_ignored():
    rows = [("Improving", 100.5), ("Leading", 102.0), ("Leading", 100.9), ("Lagging", 98.0),
            ("Improving", 100.1)]
    base = run(rows)
    rng = np.random.default_rng(11)
    for _ in range(5):
        dq = list(rng.choice(["Leading", "Improving", "Weakening", "Lagging"], 5 * len(rows)))
        assert run(rows, dq) == base


@pytest.fixture(scope="module")
def stocks():
    bench = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    return {t: (m["name"], dp.align_stock_with_benchmark(dp.load_clean_data(t), bench, m["name"],
                                                          cfg.BENCHMARK_NAME))
            for t, m in cfg.STOCKS.items()}


def test_matches_weekly_chart_on_every_stock(stocks):
    """Independent path: the Weekly page's weekly candles, rules replayed by hand."""
    start = pd.Timestamp("2023-01-01")
    for ticker, (name, al) in stocks.items():
        daily, _ = strat.compute_rrg(al, name, "Daily")
        asof = strat.weekly_asof(al, name)
        if daily.empty or asof.empty:
            continue
        trades, _ = strat.gen_strat_2_v2(daily, asof, start)
        wk, _ = strat.compute_rrg(al, name, "Weekly")
        if wk.index[-1] == daily.index[-1] and wk.index[-1].weekday() != 4:
            wk = wk.iloc[:-1]
        mine, held, can_buy = [], None, True
        for d, r in wk.iterrows():
            if d < start:
                continue
            q, mom = r["Quadrant"], r["RS_Momentum"]
            if held is not None:
                early = q == "Leading" and mom < 101
                if early or q in DOWN:
                    mine.append((held, d))
                    held, can_buy = None, not early
            elif q in DOWN:
                can_buy = True
            elif can_buy and q in UP:
                held = d
        assert [(t["buy"], t["sell"]) for t in trades if not t["open"]] == mine, ticker
        assert (trades[-1]["buy"] if trades and trades[-1]["open"] else None) == held, ticker


def test_registry_entry():
    meta = strat.STRATEGY_REGISTRY[3]
    assert meta["label"] == "Strategy 2 · Version 2" and meta["weekly_only"]
    assert strat.SIGNALS[3] is strat.gen_strat_2_v2
    assert strat.STRATEGY_REGISTRY[2]["label"] == "Strategy 2 · Version 1"
    assert strat.STRATEGY_REGISTRY[1]["label"] == "Strategy 1"
