"""
Strategy 1 — Daily + Weekly RRG Confirmation rules.

BUY  (flat):          Daily in {Leading, Improving} AND Weekly in {Leading, Improving}
SELL (open position): Daily in {Weakening, Lagging} OR  Weekly in {Weakening, Lagging}
Otherwise an open position is held; never a second buy while open.
"""
import os
import sys
from itertools import product

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import data_pipeline as dp
import strategies as strat

QUADS = ["Leading", "Improving", "Weakening", "Lagging"]
UP = {"Leading", "Improving"}
DOWN = {"Weakening", "Lagging"}


def frames(daily_q, weekly_q, start="2024-01-01"):
    """Synthetic daily / weekly-as-of frames: one row per session, flat prices."""
    idx = pd.bdate_range(start, periods=len(daily_q))
    daily = pd.DataFrame({"Quadrant": daily_q, "Close": 100.0}, index=idx)
    asof = pd.DataFrame({"Quadrant": weekly_q}, index=idx)
    return daily, asof, idx


@pytest.mark.parametrize("dq,wq", list(product(QUADS, QUADS)))
def test_buy_requires_both(dq, wq):
    # day 0 flat in Lagging/Lagging, day 1 tests the combination
    daily, asof, idx = frames(["Lagging", dq], ["Lagging", wq])
    trades, _ = strat.gen_strat_1(daily, asof, idx[0], entry="close")
    bought = any(t["buy"] == idx[1] for t in trades)
    assert bought == (dq in UP and wq in UP), (dq, wq)


@pytest.mark.parametrize("dq,wq", list(product(QUADS, QUADS)))
def test_sell_on_either_down_else_hold(dq, wq):
    # day 0 opens a position (both Leading), day 1 tests the combination
    daily, asof, idx = frames(["Leading", dq], ["Leading", wq])
    trades, _ = strat.gen_strat_1(daily, asof, idx[0], entry="close")
    assert len(trades) == 1 and trades[0]["buy"] == idx[0]
    sold = trades[0]["sell"] == idx[1]
    assert sold == (dq in DOWN or wq in DOWN), (dq, wq)
    if sold:
        assert trades[0]["daily_at_sell"] == dq and trades[0]["weekly_at_sell"] == wq
        for name, q in (("Daily", dq), ("Weekly", wq)):
            assert (f"{name} → {q}" in trades[0]["exit_reason"]) == (q in DOWN)
    else:
        assert trades[0]["open"] and trades[0]["sell"] is None


def test_examples_from_spec():
    cases = {  # (daily, weekly) -> expected action from flat / while open
        ("Leading", "Leading"): ("BUY", "HOLD"), ("Leading", "Improving"): ("BUY", "HOLD"),
        ("Improving", "Leading"): ("BUY", "HOLD"), ("Improving", "Improving"): ("BUY", "HOLD"),
        ("Leading", "Weakening"): ("NO BUY", "SELL"), ("Improving", "Lagging"): ("NO BUY", "SELL"),
        ("Lagging", "Leading"): ("NO BUY", "SELL"), ("Weakening", "Improving"): ("NO BUY", "SELL"),
        ("Lagging", "Improving"): ("NO BUY", "SELL"), ("Weakening", "Leading"): ("NO BUY", "SELL"),
    }
    for (dq, wq), (flat_action, open_action) in cases.items():
        daily, asof, idx = frames(["Lagging", dq], ["Lagging", wq])
        trades, _ = strat.gen_strat_1(daily, asof, idx[0], entry="close")
        assert ("BUY" if trades else "NO BUY") == flat_action, (dq, wq)
        daily, asof, idx = frames(["Leading", dq], ["Leading", wq])
        trades, _ = strat.gen_strat_1(daily, asof, idx[0], entry="close")
        assert ("SELL" if trades[0]["sell"] is not None else "HOLD") == open_action, (dq, wq)


def test_no_second_buy_while_open_and_reentry_needs_both():
    d = ["Leading", "Leading", "Improving", "Leading", "Leading", "Leading", "Leading"]
    w = ["Leading", "Improving", "Leading", "Weakening", "Weakening", "Improving", "Leading"]
    daily, asof, idx = frames(d, w)
    trades, _ = strat.gen_strat_1(daily, asof, idx[0], entry="close")
    # one buy day 0, held through days 1-2, sold day 3 (weekly down), flat day 4 (weekly still down),
    # re-entry day 5 when both qualify again, held day 6
    assert [(t["buy"], t["sell"]) for t in trades] == [(idx[0], idx[3]), (idx[5], None)]


def test_missing_weekly_reading_does_nothing():
    daily, asof, idx = frames(["Leading", "Leading", "Lagging"], ["Leading", None, None])
    asof = asof.dropna()
    trades, _ = strat.gen_strat_1(daily, asof, idx[0], entry="close")
    assert len(trades) == 1 and trades[0]["open"]   # no weekly reading on days 1-2: no sell


@pytest.fixture(scope="module")
def pvr():
    bench = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    al = dp.align_stock_with_benchmark(dp.load_clean_data("PVRINOX.NS"), bench, "PVR INOX",
                                       cfg.BENCHMARK_NAME)
    return al


def test_no_lookahead(pvr):
    """Trades up to a date must not change when later data is added."""
    start = pd.Timestamp("2024-01-01")
    cut = "2025-12-31"
    full_d, _ = strat.compute_rrg(pvr, "PVR INOX", "Daily")
    full_t, _ = strat.gen_strat_1(full_d, strat.weekly_asof(pvr, "PVR INOX"), start, entry="close")
    part = pvr[pvr.index <= cut]
    part_d, _ = strat.compute_rrg(part, "PVR INOX", "Daily")
    part_t, _ = strat.gen_strat_1(part_d, strat.weekly_asof(part, "PVR INOX"), start, entry="close")
    closed_before = [(t["buy"], t["sell"]) for t in full_t
                     if t["sell"] is not None and t["sell"] <= pd.Timestamp(cut)]
    assert closed_before == [(t["buy"], t["sell"]) for t in part_t if not t["open"]]


def test_pvr_baseline_new_rules(pvr):
    """PVR INOX, data to 16 Oct 2026, Rs 1,00,000 from 1 Jan 2024, 0.12 % per side."""
    al = pvr[pvr.index <= "2026-10-16"]
    daily, _ = strat.compute_rrg(al, "PVR INOX", "Daily")
    asof = strat.weekly_asof(al, "PVR INOX")
    start = pd.Timestamp("2024-01-01")
    raw, _ = strat.gen_strat_1(daily, asof, start, 0.12, entry="close")
    book, cash, val, bh, _ = strat.simulate_single_strategy(daily, raw, start, 100000.0, 0.12)
    assert len(book) == 14
    first, ninth, last = book[0], book[8], book[-1]
    assert (first["buy"].strftime("%Y-%m-%d"), round(first["buy_px"], 2)) == ("2024-05-24", 1339.05)
    assert (first["sell"].strftime("%Y-%m-%d"), round(first["sell_px"], 2)) == ("2024-07-11", 1460.20)
    # weekly-triggered exit: daily still Improving
    assert (ninth["buy"].strftime("%Y-%m-%d"), ninth["sell"].strftime("%Y-%m-%d")) == ("2025-12-05", "2025-12-08")
    assert ninth["exit_reason"].startswith("Weekly → Lagging")
    assert (last["buy"].strftime("%Y-%m-%d"), round(last["buy_px"], 2), last["open"]) == ("2026-10-12", 1401.30, True)
    assert round(float(val.iloc[-1]), 2) == 98784.96
