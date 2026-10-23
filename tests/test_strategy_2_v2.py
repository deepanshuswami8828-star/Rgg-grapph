"""
Strategy 2, version 2 — Weekly RRG only, sell when RS-Momentum falls below 101.

Each day, on the weekly reading as it stands at that day's close (week so far):
  SELL (open):  the trade has been Leading with RS-Momentum >= 101 and RS-Momentum is now
                < 101, in any quadrant (early exit: a downward cross)
                or Weekly in {Weakening, Lagging} (safety net)
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


def run(rows, daily_q=None):
    """rows: [(weekly quadrant, weekly RS-Momentum)] - one per trading day."""
    idx = pd.bdate_range("2024-01-01", periods=len(rows))
    asof = pd.DataFrame({"Quadrant": [q for q, _ in rows], "RS_Momentum": [m for _, m in rows]}, index=idx)
    daily = pd.DataFrame({"Quadrant": daily_q or ["Lagging"] * len(idx), "Close": 100.0}, index=idx)
    trades, _ = strat.gen_strat_2_v2(daily, asof, idx[0])
    pos = list(idx)
    return [(pos.index(t["buy"]), pos.index(t["sell"]) if t["sell"] is not None else None, t["exit_reason"])
            for t in trades]


def test_early_exit_when_momentum_falls_below_101_in_leading():
    out = run([("Improving", 100.5), ("Leading", 102.0), ("Leading", 100.9)])
    assert [(b, s) for b, s, _ in out] == [(0, 2)]
    assert out[0][2] == "Weekly RS-Momentum fell below 101 (100.90, Leading)"


def test_early_exit_when_leading_slips_into_improving_below_101():
    out = run([("Improving", 100.3), ("Leading", 101.21), ("Improving", 100.51), ("Lagging", 99.7)])
    assert [(b, s) for b, s, _ in out] == [(0, 2)]
    assert out[0][2] == "Weekly RS-Momentum fell below 101 (100.51, Improving)"


def test_no_sell_while_momentum_still_rising_below_101():
    out = run([("Weakening", 99.6), ("Leading", 100.2), ("Leading", 100.6), ("Leading", 100.9)])
    assert out == [(1, None, "Open Position")]


def test_no_early_exit_at_exactly_101_or_before_reaching_leading_101():
    assert run([("Leading", 103.0), ("Leading", 101.0), ("Leading", 101.5)]) == [(0, None, "Open Position")]
    assert run([("Improving", 101.5), ("Improving", 100.5), ("Improving", 100.2)]) == [(0, None, "Open Position")]


@pytest.mark.parametrize("q", sorted(DOWN))
def test_safety_net_exit(q):
    out = run([("Improving", 100.4), (q, 99.0)])
    assert [(b, s) for b, s, _ in out] == [(0, 1)] and out[0][2] == f"Weekly → {q}"


def test_fresh_entry_after_early_exit():
    rows = [("Leading", 103.0), ("Leading", 100.5),          # buy d0 (Leading 101+), early exit d1
            ("Leading", 102.0), ("Improving", 101.0),         # still up: no re-buy
            ("Weakening", 99.5),                               # down: re-armed
            ("Improving", 100.3)]                              # fresh entry: buy d5
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
        dq = list(rng.choice(["Leading", "Improving", "Weakening", "Lagging"], len(rows)))
        assert run(rows, dq) == base


@pytest.fixture(scope="module")
def stocks():
    bench = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    return {t: (m["name"], dp.align_stock_with_benchmark(dp.load_clean_data(t), bench, m["name"],
                                                          cfg.BENCHMARK_NAME))
            for t, m in cfg.STOCKS.items()}


def test_every_stock_matches_a_plain_replay(stocks):
    start = pd.Timestamp("2023-01-01")
    for ticker, (name, al) in stocks.items():
        daily, _ = strat.compute_rrg(al, name, "Daily")
        asof = strat.weekly_asof(al, name)
        if daily.empty or asof.empty:
            continue
        trades, _ = strat.gen_strat_2_v2(daily, asof, start)
        mine, held, can_buy, hit101 = [], None, True, False
        for d in daily.index[daily.index >= start]:
            if d not in asof.index:
                continue
            q, mom = asof.at[d, "Quadrant"], asof.at[d, "RS_Momentum"]
            if held is not None:
                if q in DOWN or (hit101 and mom < 101):
                    mine.append((held, d))
                    held, can_buy = None, q in DOWN
                elif q == "Leading" and mom >= 101:
                    hit101 = True
            elif q in DOWN:
                can_buy = True
            elif can_buy and q in UP:
                held, hit101 = d, (q == "Leading" and mom >= 101)
        assert [(t["buy"], t["sell"]) for t in trades if not t["open"]] == mine, ticker
        assert (trades[-1]["buy"] if trades and trades[-1]["open"] else None) == held, ticker


def test_pvr_examples(stocks):
    """PVR INOX: buys the day the weekly turns up, sells the day momentum falls below 101."""
    name, al = stocks["PVRINOX.NS"]
    al = al[al.index <= "2026-10-16"]
    daily, _ = strat.compute_rrg(al, name, "Daily")
    trades, _ = strat.gen_strat_2_v2(daily, strat.weekly_asof(al, name), pd.Timestamp("2024-01-01"))
    got = [(t["buy"].strftime("%Y-%m-%d"), t["sell"].strftime("%Y-%m-%d") if t["sell"] is not None else None)
           for t in trades]
    assert got == [("2024-05-13", "2024-12-02"), ("2025-05-26", "2025-12-01"),
                   ("2026-03-09", "2026-06-15"), ("2026-07-27", None)]
    assert round(trades[0]["sell_px"], 2) == 1572.50


def test_registry_entry():
    meta = strat.STRATEGY_REGISTRY[3]
    assert meta["label"] == "Strategy 2 · Version 2" and meta["weekly_only"]
    assert strat.SIGNALS[3] is strat.gen_strat_2_v2
    assert strat.STRATEGY_REGISTRY[2]["label"] == "Strategy 2 · Version 1"
    assert strat.STRATEGY_REGISTRY[1]["label"] == "Strategy 1"
