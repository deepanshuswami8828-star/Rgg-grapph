"""
Test: realistic entry and RRG-exit fills for every strategy.
A buy signal appears at a day's close; the buy happens on the NEXT trading day at the average of
that day's open and close. Exits are checked from the day after the buy (stop-loss / take-profit
measured from the new buy price). An exit triggered by the RRG (weekly quadrant / momentum, or
Strategy 1's daily quadrant) also sells on the next trading day at the average of open and close;
the stop-loss still sells at that day's close and the take-profit at its target. Signal rules are unchanged.
Verifies:
1. Toy data: next-day fill, price = (open + close) / 2, close used when the open is missing.
2. Toy data: no exit on the fill day; stop-loss measured from the fill price; signal on the last day -> no trade.
3. Real data, all strategies and stocks: every trade is bought on the trading day after its signal, at the
   average of that day's open and close, and the signals are the ones the original rule produces.
4. RRG exits sell the next day at the average of open and close; stop-loss stays a same-day close sale.
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


def frames(weekly, closes, opens=None, daily_q=None):
    idx = pd.bdate_range("2024-01-01", periods=len(weekly))
    asof = pd.DataFrame({"Quadrant": weekly, "RS_Momentum": 100.5}, index=idx)
    daily = pd.DataFrame({"Quadrant": daily_q or ["Leading"] * len(idx), "Close": closes}, index=idx)
    return idx, daily, asof, (pd.Series(opens, index=idx) if opens is not None else None)


def test_default_entry_is_next_day_average():
    assert strat.DEFAULT_ENTRY == strat.ENTRY_NEXT_AVG


@pytest.mark.parametrize("fn", [strat.gen_strat_1, strat.gen_strat_2, strat.gen_strat_2_v2, strat.gen_strat_2_v3])
def test_buy_next_day_at_average_of_open_and_close(fn):
    idx, daily, asof, opens = frames(["Leading"] * 4, [100.0, 104.0, 105.0, 106.0], opens=[99.0, 102.0, 104.0, 105.0])
    trades, _ = fn(daily, asof, idx[0], 0.0, opens=opens)
    assert trades[0]["signal"] == idx[0] and trades[0]["buy"] == idx[1]
    assert trades[0]["buy_px"] == (102.0 + 104.0) / 2


def test_missing_open_falls_back_to_close():
    idx, daily, asof, opens = frames(["Leading"] * 3, [100.0, 104.0, 105.0], opens=[99.0, np.nan, 104.0])
    trades, _ = strat.gen_strat_2_v3(daily, asof, idx[0], 0.0, opens=opens)
    assert trades[0]["buy"] == idx[1] and trades[0]["buy_px"] == 104.0


def test_no_exit_on_fill_day_and_stop_measured_from_fill_price():
    # signal d0; fill d1 at (100+90)/2 = 95 even though d1 closes in Weakening; stop 10% = 85.5
    idx, daily, asof, opens = frames(["Leading", "Weakening", "Leading", "Leading"], [100.0, 90.0, 86.0, 85.0],
                                     opens=[100.0, 100.0, 90.0, 86.0])
    trades, _ = strat.gen_strat_2_v3(daily, asof, idx[0], 0.0, opens=opens)
    t = trades[0]
    assert t["buy"] == idx[1] and t["buy_px"] == 95.0
    assert t["sell"] == idx[3] and t["exit_reason"].startswith("Stop-loss 10%")   # 86 > 85.5 holds, 85 <= 85.5 sells


def test_take_profit_measured_from_fill_price_and_not_on_fill_day():
    idx, daily, asof, opens = frames(["Leading"] * 4, [100.0, 104.0, 105.0, 106.0], opens=[99.0, 102.0, 104.0, 105.0])
    highs = pd.Series([101.0, 200.0, 108.2, 109.0], index=idx)      # fill day high (200) is ignored
    trades, _ = strat.gen_strat_2_v3(daily, asof, idx[0], 0.0, take_profit_pct=5.0, highs=highs, opens=opens)
    t = trades[0]
    assert t["buy"] == idx[1] and t["buy_px"] == 103.0
    assert t["sell"] == idx[2] and abs(t["sell_px"] - 108.15) < 1e-9          # 103 * 1.05


def test_signal_on_last_day_gives_no_trade():
    idx, daily, asof, opens = frames(["Lagging", "Lagging", "Leading"], [100.0, 101.0, 102.0], opens=[100.0, 101.0, 102.0])
    assert strat.gen_strat_2(daily, asof, idx[0], 0.0, opens=opens)[0] == []


def _stock_inputs():
    for t in cfg.STOCKS:
        name = cfg.STOCKS[t]["name"]
        al = dp.align_stock_with_benchmark(dp.load_clean_data(t), dp.load_clean_data(cfg.BENCHMARK_TICKER), name)
        daily, _ = strat.compute_rrg(al, name, tf="Daily")
        asof = strat.weekly_asof(al, name)
        if len(daily) < 2 or asof.empty:
            continue
        yield t, daily, asof, dp.load_open_data(t), max(pd.Timestamp("2022-10-01"), daily.index[1], asof.index[0])


def test_every_stock_and_strategy_buys_the_day_after_its_signal():
    checked = 0
    for t, daily, asof, opens, start in _stock_inputs():
        for sid, fn in strat.SIGNALS.items():
            trades, _ = fn(daily, asof, start, 0.0, opens=opens)
            for x in trades:
                nxt = daily.index[daily.index.get_loc(x["signal"]) + 1]
                assert x["buy"] == nxt, (t, sid, x["signal"], x["buy"])
                o, c = opens.get(nxt, np.nan), daily.at[nxt, "Close"]
                assert abs(x["buy_px"] - ((o + c) / 2 if o == o else c)) < 1e-9, (t, sid, x["buy"])
                assert x["sell"] is None or x["sell"] > x["buy"]
                checked += 1
    assert checked > 100


def test_first_signal_matches_the_original_rule():
    # the first signal is the same day the original (same-day close) rule bought
    for t, daily, asof, opens, start in _stock_inputs():
        for sid, fn in strat.SIGNALS.items():
            new, _ = fn(daily, asof, start, 0.0, opens=opens)
            old, _ = fn(daily, asof, start, 0.0, entry=strat.ENTRY_CLOSE)
            if old and new and old[0]["buy"] < daily.index[-1]:
                assert new[0]["signal"] == old[0]["buy"], (t, sid)


# ---- RRG exits on the next day ------------------------------------------------------------------
def test_default_rrg_exit_is_next_day_average():
    assert strat.DEFAULT_RRG_EXIT == strat.ENTRY_NEXT_AVG


@pytest.mark.parametrize("fn", [strat.gen_strat_2, strat.gen_strat_2_v2, strat.gen_strat_2_v3])
def test_weekly_exit_sells_next_day_at_average(fn):
    # signal d0 -> buy d1 at (100+102)/2 = 101; weekly turns Lagging d3 -> sell d4 at (103+105)/2 = 104
    idx, daily, asof, opens = frames(["Leading", "Leading", "Leading", "Lagging", "Lagging"],
                                     [100.0, 102.0, 104.0, 104.0, 105.0], opens=[99.0, 100.0, 103.0, 104.0, 103.0])
    t = fn(daily, asof, idx[0], 0.0, opens=opens)[0][0]
    assert t["buy"] == idx[1] and t["buy_px"] == 101.0
    assert t["exit_signal"] == idx[3] and t["sell"] == idx[4] and t["sell_px"] == 104.0
    assert t["exit_reason"].startswith("Weekly")


def test_strategy_1_rrg_exit_sells_next_day():
    idx, daily, asof, opens = frames(["Leading"] * 5, [100.0, 102.0, 104.0, 103.0, 101.0],
                                     opens=[99.0, 100.0, 103.0, 104.0, 99.0],
                                     daily_q=["Leading", "Leading", "Leading", "Weakening", "Weakening"])
    t = strat.gen_strat_1(daily, asof, idx[0], 0.0, opens=opens)[0][0]
    assert t["exit_signal"] == idx[3] and t["sell"] == idx[4] and t["sell_px"] == 100.0


def test_stop_loss_still_sells_the_same_day_at_the_close():
    idx, daily, asof, opens = frames(["Leading", "Leading", "Leading", "Lagging"], [100.0, 100.0, 89.0, 88.0],
                                     opens=[100.0, 100.0, 95.0, 88.0])
    t = strat.gen_strat_2_v3(daily, asof, idx[0], 0.0, opens=opens)[0][0]
    assert t["buy_px"] == 100.0 and t["sell"] == idx[2] and t["sell_px"] == 89.0
    assert t["exit_reason"].startswith("Stop-loss")


def test_stop_loss_on_the_weekly_signal_day_wins_over_the_next_day_exit():
    # d2: weekly Lagging AND close 85 <= 90 stop -> stop-loss sells d2 at the close
    idx, daily, asof, opens = frames(["Leading", "Leading", "Lagging", "Lagging"], [100.0, 100.0, 85.0, 84.0],
                                     opens=[100.0, 100.0, 95.0, 84.0])
    t = strat.gen_strat_2_v3(daily, asof, idx[0], 0.0, opens=opens)[0][0]
    assert t["sell"] == idx[2] and t["exit_reason"].startswith("Stop-loss")


def test_weekly_exit_on_last_day_leaves_trade_open_with_exit_due():
    idx, daily, asof, opens = frames(["Leading", "Leading", "Leading", "Weakening"], [100.0, 102.0, 104.0, 103.0],
                                     opens=[99.0, 100.0, 103.0, 104.0])
    t = strat.gen_strat_2(daily, asof, idx[0], 0.0, opens=opens)[0][-1]
    assert t["sell"] is None and t["exit_signal_pending"] == idx[3]


def test_v2_early_exit_next_day_still_waits_for_a_weekly_down_and_up():
    # Leading 101+ then momentum < 101 while still Leading -> early exit next day; no re-buy until weekly dips
    idx = pd.bdate_range("2024-01-01", periods=7)
    asof = pd.DataFrame({"Quadrant": ["Leading", "Leading", "Leading", "Leading", "Leading", "Lagging", "Leading"],
                         "RS_Momentum": [101.5, 101.5, 101.2, 100.5, 100.4, 99.0, 100.2]}, index=idx)
    daily = pd.DataFrame({"Quadrant": "Leading", "Close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0]}, index=idx)
    opens = pd.Series([100.0, 101.0, 102.0, 103.0, 102.0, 105.0, 106.0], index=idx)
    trades = strat.gen_strat_2_v2(daily, asof, idx[0], 0.0, opens=opens)[0]
    assert trades[0]["exit_signal"] == idx[3] and trades[0]["sell"] == idx[4] and trades[0]["sell_px"] == 103.0
    assert len(trades) == 1                     # d5 Lagging re-arms, d6 Leading signals, fill would be d7 (no data)


def test_every_stock_weekly_exits_sell_next_day_at_average():
    checked = 0
    for t, daily, asof, opens, start in _stock_inputs():
        for sid, fn in strat.SIGNALS.items():
            for x in fn(daily, asof, start, 0.0, opens=opens)[0]:
                if x["sell"] is None or x["exit_reason"].startswith("Stop-loss"):
                    continue
                nxt = daily.index[daily.index.get_loc(x["exit_signal"]) + 1]
                assert x["sell"] == nxt, (t, sid, x["exit_signal"], x["sell"])
                o, c = opens.get(nxt, np.nan), daily.at[nxt, "Close"]
                assert abs(x["sell_px"] - ((o + c) / 2 if o == o else c)) < 1e-9, (t, sid, x["sell"])
                checked += 1
    assert checked > 100
