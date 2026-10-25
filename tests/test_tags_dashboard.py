"""
Test: Tags dashboard (Strategy 2 version 3 profitability per tag and period).
Verifies:
1. A trade counts in a period only if bought and sold inside it; spanning or open trades are left out.
2. Profit % assumes a fixed Rs 1,00,000 per trade; days held are calendar days; daily profit = sum % / sum days.
3. The Tags page loads for every tag and its numbers match a direct calculation.
"""
import os
import sys
import pandas as pd
from streamlit.testing.v1 import AppTest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import strategies as strat

APP_PATH = os.path.join(cfg.ROOT_DIR, "rrg_app.py")
TAGS_PATH = os.path.join(cfg.ROOT_DIR, "tags_analysis.py")
T = pd.Timestamp


def trade(buy, sell, buy_px, sell_px):
    return {"buy": T(buy), "sell": T(sell) if sell else None, "buy_px": buy_px, "sell_px": sell_px}


def test_period_trades_excludes_spanning_and_open_trades():
    trades = [
        trade("2022-11-01", "2023-01-10", 100, 110),   # inside period 1
        trade("2024-09-02", "2024-10-15", 100, 90),    # spans both periods
        trade("2024-10-01", "2025-02-03", 100, 120),   # inside period 2 (first day)
        trade("2026-09-01", None, 100, 105),           # still open
    ]
    (_, p1s, p1e), (_, p2s, p2e) = strat.TAG_PERIODS
    assert strat.period_trades(trades, p1s, p1e) == [trades[0]]
    assert strat.period_trades(trades, p2s, p2e) == [trades[2]]


def test_profit_days_and_daily_profit():
    trades = [trade("2023-01-02", "2023-01-12", 200.0, 220.0),   # +10%, 10 days
              trade("2023-03-01", "2023-03-31", 400.0, 360.0)]   # -10%, 30 days
    s = strat.ticker_period_summary(trades)
    assert s["trades"] == 2
    assert [round(p, 6) for p in s["profits"]] == [10.0, -10.0]
    assert s["days"] == [10, 30]
    assert s["profit_sum"] == 0 and s["days_sum"] == 40 and s["daily_profit"] == 0
    assert strat.ticker_period_summary([])["daily_profit"] is None


def test_profit_uses_whole_shares_of_one_lakh():
    # 100000 / 300 -> 333 shares; 333 * 330 - 333 * 300 = 9990 on 99900 paid = 10%
    assert round(strat.trade_profit_pct(trade("2023-01-02", "2023-02-01", 300.0, 330.0)), 6) == 10.0


def test_rrg_tab_has_no_tags_analysis_mixed_in():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=60)
    assert len(at.exception) == 0
    assert "Tags" not in at.sidebar.radio(key="page").options
    assert not any("Daily profit %" in df.value.columns for df in at.dataframe)


def test_tags_page_loads_and_matches_direct_calculation():
    for tag in cfg.TAGS:
        at = AppTest.from_file(TAGS_PATH)          # the Tags analysis tab is its own page script
        at.run(timeout=300)
        at.selectbox(key="tags_page_tag").set_value(tag)
        at.run(timeout=300)
        assert len(at.exception) == 0, f"Tags page failed for {tag}: {[e.message for e in at.exception]}"
        assert any(f"Tag: {tag}" in m.value for m in at.markdown)
        assert len(at.sidebar.radio) == 0          # the RRG sidebar is not shown on this tab
        period_tables = [df.value for df in at.dataframe if "Daily profit %" in df.value.columns]
        assert len(period_tables) == 2

        for table in period_tables:
            assert len(table) <= strat.TAG_MAX_ROWS
            check_rows(table)


def check_rows(table):
    """Each row's lists add up to its sums, and daily profit % = sum of profit % / sum of days held."""
    for _, r in table.iterrows():
        if r["Number of trades"]:
            profits = [float(x) for x in r["Profit % per trade"].split(", ")]
            days = [int(x) for x in r["Days held per trade"].split(", ")]
            assert len(profits) == len(days) == r["Number of trades"]
            assert abs(sum(profits) - r["Sum of profit %"]) < 0.05
            assert sum(days) == r["Sum of days held"]
            assert abs(r["Sum of profit %"] / r["Sum of days held"] - r["Daily profit %"]) < 1e-3


def _toy_market(highs_after_buy):
    """Daily closes / weekly readings: weekly Leading for 6 days, Weakening day 7, Leading again from day 9."""
    idx = pd.bdate_range("2023-01-02", periods=12)
    daily = pd.DataFrame({"Close": [100, 101, 102, 103, 104, 105, 104, 103, 102, 103, 104, 105.0]}, index=idx)
    quads = ["Leading"] * 6 + ["Weakening", "Weakening", "Leading", "Leading", "Leading", "Leading"]
    asof = pd.DataFrame({"Quadrant": quads, "RS_Momentum": 101.0}, index=idx)
    highs = daily["Close"] + 0.5
    for day, h in highs_after_buy.items():
        highs.iloc[day] = h
    return daily, asof, highs


def test_take_profit_sells_at_target_on_the_first_day_the_high_reaches_it():
    daily, asof, highs = _toy_market({0: 200.0, 3: 105.5})   # day 0 is the buy day: its high is ignored
    trades, _ = strat.gen_strat_2_v3(daily, asof, daily.index[0], 0.0, take_profit_pct=5.0, highs=highs)
    first = trades[0]
    assert first["buy"] == daily.index[0] and first["sell"] == daily.index[3]
    assert first["sell_px"] == 105.0 and first["exit_reason"].startswith("Take-profit 5%")
    # no re-buy while the weekly stays Leading after the take-profit; next buy only after Weakening -> Leading
    assert trades[1]["buy"] == daily.index[8]


def test_take_profit_never_reached_matches_base_strategy():
    daily, asof, highs = _toy_market({})
    base, _ = strat.gen_strat_2_v3(daily, asof, daily.index[0], 0.0)
    huge, _ = strat.gen_strat_2_v3(daily, asof, daily.index[0], 0.0, take_profit_pct=1000.0, highs=highs)
    assert [(t["buy"], t["sell"], t["sell_px"]) for t in base] == [(t["buy"], t["sell"], t["sell_px"]) for t in huge]


def test_thresholds_and_period_report():
    assert strat.TAKE_PROFIT_THRESHOLDS == list(range(1, 21)) + list(range(25, 101, 5))
    (_, p1s, p1e), _ = strat.TAG_PERIODS
    rep = strat.period_report({"A": [trade("2023-01-02", "2023-01-12", 100, 110)],          # +10% in 10 days
                               "B": [trade("2023-02-01", "2023-03-03", 100, 95)],           # -5% in 30 days
                               "C": []}, p1s, p1e)                                          # no trade
    assert rep["tickers"] == 3 and rep["trades"] == 2 and rep["tickers_with_trades"] == 2
    assert abs(rep["avg_daily_profit"] - (1.0 + (-5 / 30)) / 2) < 1e-9


def test_tags_page_shows_take_profit_charts():
    at = AppTest.from_file(TAGS_PATH)
    at.run(timeout=600)
    assert len(at.exception) == 0
    numbers = [df.value for df in at.dataframe if "Take-profit threshold" in df.value.columns]
    assert len(numbers) == 1 and len(numbers[0]) == 1 + len(strat.TAKE_PROFIT_THRESHOLDS)
    assert len(at.get("plotly_chart")) == len(strat.TAG_PERIODS)
