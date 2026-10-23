"""
Strategy 2, version 3 — Weekly RRG only (version 1) plus a 10% stop-loss on price.

Every trading day's close:
  SELL (open):  close <= 90% of the buy price  (stop-loss, loss booked)
                or Weekly (as of that day) in {Weakening, Lagging}
  BUY  (flat):  Weekly (as of that day) in {Leading, Improving}; after a stop-loss only once
                the weekly has been in Weakening/Lagging and comes back up (fresh entry).
The Daily RRG is never used. Internal registry key 4, shown as "Strategy 2 · Version 3".
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
    """rows: [(weekly quadrant as of that day, close)] - one per trading day."""
    idx = pd.bdate_range("2024-01-01", periods=len(rows))
    asof = pd.DataFrame({"Quadrant": [q for q, _ in rows], "RS_Momentum": 100.5}, index=idx)
    daily = pd.DataFrame({"Quadrant": daily_q or ["Lagging"] * len(idx),
                          "Close": [p for _, p in rows]}, index=idx)
    trades, _ = strat.gen_strat_2_v3(daily, asof, idx[0])
    pos = list(idx)
    return [(pos.index(t["buy"]), pos.index(t["sell"]) if t["sell"] is not None else None, t["exit_reason"])
            for t in trades]


def test_stop_loss_at_10_percent():
    out = run([("Leading", 100.0), ("Leading", 95.0), ("Leading", 90.0)])
    assert [(b, s) for b, s, _ in out] == [(0, 2)]
    assert out[0][2].startswith("Stop-loss 10%")


def test_just_above_stop_holds():
    assert run([("Leading", 100.0), ("Leading", 90.01), ("Improving", 91.0)]) == [(0, None, "Open Position")]


def test_stop_triggers_on_any_day():
    # Wednesday close 89 is below the stop even though the week recovers by Friday
    out = run([("Leading", 100.0), ("Leading", 99.0), ("Leading", 89.0), ("Leading", 97.0), ("Leading", 98.0)])
    assert [(b, s) for b, s, _ in out] == [(0, 2)]


@pytest.mark.parametrize("q", sorted(DOWN))
def test_weekly_exit_on_the_first_down_day(q):
    out = run([("Improving", 100.0), (q, 97.0)])
    assert [(b, s) for b, s, _ in out] == [(0, 1)] and out[0][2] == f"Weekly → {q}"


def test_stop_loss_wins_when_both_hit():
    assert run([("Leading", 100.0), ("Weakening", 85.0)])[0][2].startswith("Stop-loss 10%")


def test_fresh_entry_after_stop_loss():
    rows = [("Leading", 100.0), ("Leading", 88.0),         # buy d0, stop d1 (weekly still up)
            ("Leading", 87.0), ("Improving", 86.0),        # still up: no re-buy
            ("Lagging", 84.0),                              # down: re-armed
            ("Improving", 85.0)]                            # fresh entry: buy d5
    assert [(b, s) for b, s, _ in run(rows)] == [(0, 1), (5, None)]


def test_rebuy_after_weekly_exit_needs_no_extra_cycle():
    assert [(b, s) for b, s, _ in run([("Improving", 100.0), ("Lagging", 98.0), ("Improving", 99.0)])] == \
        [(0, 1), (2, None)]


def test_daily_rrg_is_ignored():
    rows = [("Leading", 100.0), ("Leading", 88.0), ("Lagging", 84.0), ("Improving", 85.0), ("Weakening", 80.0)]
    base = run(rows)
    rng = np.random.default_rng(13)
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
        trades, _ = strat.gen_strat_2_v3(daily, asof, start)
        mine, held, held_px, can_buy = [], None, None, True
        for d in daily.index[daily.index >= start]:
            if d not in asof.index:
                continue
            q, px = asof.at[d, "Quadrant"], daily.at[d, "Close"]
            if held is not None:
                if px <= held_px * 0.9 or q in DOWN:
                    mine.append((held, d))
                    held, can_buy = None, q in DOWN
            elif q in DOWN:
                can_buy = True
            elif can_buy and q in UP:
                held, held_px = d, px
        assert [(t["buy"], t["sell"]) for t in trades if not t["open"]] == mine, ticker
        assert (trades[-1]["buy"] if trades and trades[-1]["open"] else None) == held, ticker


def test_suzlon_stop_loss_example(stocks):
    name, al = stocks["SUZLON.NS"]
    al = al[al.index <= "2026-10-16"]
    daily, _ = strat.compute_rrg(al, name, "Daily")
    trades, _ = strat.gen_strat_2_v3(daily, strat.weekly_asof(al, name), pd.Timestamp("2024-01-01"))
    stops = [t for t in trades if t["exit_reason"].startswith("Stop-loss")]
    assert [(t["buy"].strftime("%Y-%m-%d"), t["sell"].strftime("%Y-%m-%d")) for t in stops] == \
        [("2025-05-27", "2025-08-18")]
    for t in stops:
        assert t["sell_px"] <= t["buy_px"] * 0.9
        prev_close = daily["Close"][daily.index < t["sell"]].iloc[-1]
        assert prev_close > t["buy_px"] * 0.9          # sold on the first close below the stop


def test_registry_entry():
    meta = strat.STRATEGY_REGISTRY[4]
    assert meta["label"] == "Strategy 2 · Version 3" and meta["weekly_only"]
    assert strat.SIGNALS[4] is strat.gen_strat_2_v3
