"""
Strategy 2, version 3 — Weekly RRG only (version 1) plus a 10% stop-loss.

At each COMPLETED week's close:
  SELL (open):  close <= 90% of the buy price  (stop-loss, loss booked)
                or Weekly in {Weakening, Lagging}
  BUY  (flat):  Weekly in {Leading, Improving}; after a stop-loss only once the weekly has
                been in Weakening/Lagging and comes back up (fresh entry).
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


def weeks(rows, daily_q=None, midweek_px=None):
    """rows: [(weekly quadrant, Friday close)]; 5 sessions per week. Mon-Thu closes are
    midweek_px (default: same as Friday) - they must never trigger anything."""
    days = pd.bdate_range("2024-01-01", periods=5 * len(rows))
    asof = pd.DataFrame({"Quadrant": np.repeat([q for q, _ in rows], 5),
                         "RS_Momentum": 100.5}, index=days)
    px = []
    for _, p in rows:
        mid = p if midweek_px is None else midweek_px
        px += [mid, mid, mid, mid, p]
    dq = daily_q if daily_q is not None else ["Lagging"] * len(days)
    daily = pd.DataFrame({"Quadrant": dq, "Close": px}, index=days)
    return daily, asof, days, days[days.weekday == 4]


def run(rows, **kw):
    daily, asof, days, fri = weeks(rows, **kw)
    trades, _ = strat.gen_strat_2_v3(daily, asof, days[0])
    f = list(fri)
    return [(f.index(t["buy"]), f.index(t["sell"]) if t["sell"] is not None else None, t["exit_reason"])
            for t in trades]


def test_stop_loss_at_10_percent():
    out = run([("Leading", 100.0), ("Leading", 95.0), ("Leading", 90.0)])
    assert [(b, s) for b, s, _ in out] == [(0, 2)]
    assert out[0][2].startswith("Stop-loss 10%")


def test_just_above_stop_holds():
    out = run([("Leading", 100.0), ("Leading", 90.01), ("Improving", 91.0)])
    assert out == [(0, None, "Open Position")]


def test_stop_checked_only_at_week_close():
    # Mon-Thu closes far below the stop, Friday closes fine -> no stop
    out = run([("Leading", 100.0), ("Leading", 98.0)], midweek_px=70.0)
    assert out == [(0, None, "Open Position")]


@pytest.mark.parametrize("q", sorted(DOWN))
def test_weekly_exit_still_works(q):
    out = run([("Improving", 100.0), (q, 97.0)])
    assert [(b, s) for b, s, _ in out] == [(0, 1)] and out[0][2] == f"Weekly → {q}"


def test_stop_loss_wins_when_both_hit():
    out = run([("Leading", 100.0), ("Weakening", 85.0)])
    assert out[0][2].startswith("Stop-loss 10%")


def test_fresh_entry_after_stop_loss():
    rows = [("Leading", 100.0), ("Leading", 88.0),         # buy w0, stop w1 (weekly still up)
            ("Leading", 87.0), ("Improving", 86.0),        # still up: no re-buy
            ("Lagging", 84.0),                              # down: re-armed
            ("Improving", 85.0)]                            # fresh entry: buy w5
    assert [(b, s) for b, s, _ in run(rows)] == [(0, 1), (5, None)]


def test_rebuy_after_weekly_exit_needs_no_extra_cycle():
    rows = [("Improving", 100.0), ("Lagging", 98.0), ("Improving", 99.0)]
    assert [(b, s) for b, s, _ in run(rows)] == [(0, 1), (2, None)]


def test_daily_is_ignored():
    rows = [("Leading", 100.0), ("Leading", 88.0), ("Lagging", 84.0), ("Improving", 85.0),
            ("Weakening", 80.0)]
    base = run(rows)
    rng = np.random.default_rng(13)
    for _ in range(5):
        dq = list(rng.choice(["Leading", "Improving", "Weakening", "Lagging"], 5 * len(rows)))
        assert run(rows, daily_q=dq) == base


@pytest.fixture(scope="module")
def stocks():
    bench = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    return {t: (m["name"], dp.align_stock_with_benchmark(dp.load_clean_data(t), bench, m["name"],
                                                          cfg.BENCHMARK_NAME))
            for t, m in cfg.STOCKS.items()}


def test_matches_weekly_chart_on_every_stock(stocks):
    """Independent path: the Weekly page's candles + week-close prices, rules replayed by hand."""
    start = pd.Timestamp("2023-01-01")
    for ticker, (name, al) in stocks.items():
        daily, _ = strat.compute_rrg(al, name, "Daily")
        asof = strat.weekly_asof(al, name)
        if daily.empty or asof.empty:
            continue
        trades, _ = strat.gen_strat_2_v3(daily, asof, start)
        wk, _ = strat.compute_rrg(al, name, "Weekly")
        if wk.index[-1] == daily.index[-1] and wk.index[-1].weekday() != 4:
            wk = wk.iloc[:-1]
        mine, held, held_px, can_buy = [], None, None, True
        for d, r in wk.iterrows():
            if d < start:
                continue
            q, px = r["Quadrant"], daily.loc[d, "Close"]
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
    stop = [t for t in trades if t["exit_reason"].startswith("Stop-loss")]
    assert len(stop) == 1
    assert (stop[0]["buy"].strftime("%Y-%m-%d"), stop[0]["sell"].strftime("%Y-%m-%d")) == ("2025-05-30", "2025-06-20")
    assert stop[0]["sell_px"] <= stop[0]["buy_px"] * 0.9


def test_registry_entry():
    meta = strat.STRATEGY_REGISTRY[4]
    assert meta["label"] == "Strategy 2 · Version 3" and meta["weekly_only"]
    assert strat.SIGNALS[4] is strat.gen_strat_2_v3
