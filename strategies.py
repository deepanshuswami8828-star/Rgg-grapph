"""
strategies.py — Comprehensive RRG Trading Strategy Engine.

Provides signal generators, realistic backtesting simulation (₹10k default,
whole shares, 0.12% charges, mark-to-market daily values, no lookahead bias),
comprehensive metrics calculation, multi-strategy comparison, and cross-sectional
portfolio rotation for all 6 configured stocks against NIFTY 50.

Zero Streamlit dependencies for ultra-fast, sub-second headless execution & testing.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd

import config as cfg
from make_rrg_pvrinox import (
    calc_rs_ratio, calc_rs_momentum, quadrant,
    RS_PRESMOOTH, RS_SHORT, RS_LONG, MOM_SHORT, MOM_LONG
)

UP = {"Improving", "Leading"}
DOWN = {"Weakening", "Lagging"}
WARMUP_DAILY = 30
WARMUP_WEEKLY = 15

# Strategy Registry Metadata
STRATEGY_REGISTRY = {
    1: {
        "id": 1,
        "name": "Basic Quadrant Rotation",
        "tag": "Single Timeframe",
        "short_desc": "Buy on Daily entering Improving/Leading; Sell on Weakening/Lagging (no weekly filter).",
        "full_desc": "Pure single-timeframe RRG rotation. Buys whenever the daily quadrant rotates clockwise from Lagging/Weakening into Improving or Leading. Sells as soon as daily drops into Weakening or Lagging. High trade frequency.",
    },
    2: {
        "id": 2,
        "name": "Leading Profit Booking",
        "tag": "Profit Target",
        "short_desc": "Buy on Improving-to-Leading; Exit on profit target (+8%), trailing stop (5%), or Weakening.",
        "full_desc": "Enters exclusively on high-momentum rotation into the Leading quadrant. Protects capital by locking in profits when target (+8%) is reached, cutting losses with a 5% trailing stop from peak close, or exiting if the quadrant drops into Weakening.",
    },
    3: {
        "id": 3,
        "name": "Daily + Weekly Confirmation",
        "tag": "Multi-Timeframe",
        "short_desc": "Baseline strategy: Buy on Daily Improving/Leading confirmed by Weekly Improving/Leading.",
        "full_desc": "The primary multi-timeframe baseline strategy. Requires higher-timeframe alignment: buys when Daily moves into Improving or Leading ONLY if the Weekly RRG is also in Improving or Leading. Sells when Daily drops into Weakening or Lagging.",
    },
    4: {
        "id": 4,
        "name": "Early Rotation Catcher",
        "tag": "Early Entry",
        "short_desc": "Catch bottoming rotation: Buy on Lagging-to-Improving with RS-Mom >= 100 and price recovery.",
        "full_desc": "Identifies early bottoms before the market realizes the turn. Buys at the exact transition from Lagging to Improving when RS-Momentum >= 100 and daily price is rising. Exits on momentum failure (< 100) or tight 5% stop-loss.",
    },
    5: {
        "id": 5,
        "name": "Leading-Only Momentum",
        "tag": "Trend Following",
        "short_desc": "Strongest trend filter: Both Daily & Weekly Leading + Price > 50-day SMA.",
        "full_desc": "Maximum confluence strategy. Requires Daily in Leading, Weekly in Leading, AND Close above 50-day SMA. Exits when RS-Momentum drops below 100, price breaks below 50-SMA, or 7% protective stop is hit.",
    },
    6: {
        "id": 6,
        "name": "Partial Profit Booking",
        "tag": "Partial Exits",
        "short_desc": "Buy on confirmed RRG; Sell 50% at +8% target, trail remainder to breakeven stop / RRG exit.",
        "full_desc": "Disciplined scaling: Enters on confirmed Daily+Weekly RRG signal. When price reaches +8%, sells half the position to bank gains and moves stop-loss on remaining shares to breakeven. Remaining half runs until RRG exit.",
    },
    7: {
        "id": 7,
        "name": "Improving-to-Leading Crossover",
        "tag": "Sweet Spot",
        "short_desc": "Classic sweet spot: Enter when RS-Ratio crosses above 100 with RS-Momentum >= 100.",
        "full_desc": "Classic JdK RRG entry. Triggers at the exact session RS-Ratio crosses above 100 while RS-Momentum is >= 100 (crossing vertical axis into Leading). Exits on RS-Momentum falling below 100 or 6% stop-loss.",
    },
    8: {
        "id": 8,
        "name": "Leading Pullback Entry",
        "tag": "Buy Dip in Trend",
        "short_desc": "Weekly Leading primary trend; buy when temporary Daily pullback into Weakening turns back up.",
        "full_desc": "Trend pullback strategy. When Weekly is firmly in Leading, waits for Daily to pull back into Weakening or Lagging, then buys the moment Daily resumes upward momentum into Improving/Leading. Exits if Weekly leaves Leading or 6% stop-loss.",
    },
    9: {
        "id": 9,
        "name": "Weakening Early Exit",
        "tag": "Early Exit",
        "short_desc": "Standard entry, but exit immediately when Daily touches Weakening (ahead of Lagging).",
        "full_desc": "Capital preservation focus. Uses confirmed Daily+Weekly entry, but exits on the very first session Daily enters Weakening without waiting for Lagging. Locks in trend gains before deep deceleration occurs.",
    },
    10: {
        "id": 10,
        "name": "Price + RRG Confirmation",
        "tag": "Price Filtered",
        "short_desc": "Confirmed RRG entry + Close > 50-day SMA + 20-day SMA upward sloping.",
        "full_desc": "Hybrid technical strategy. Combines confirmed RRG quadrant status with traditional trend filters: Price must exceed 50-day SMA and 20-day SMA must be sloping upward. Exits on RRG breakdown or Close < 50-SMA.",
    },
    11: {
        "id": 11,
        "name": "RS-Momentum Reversal",
        "tag": "Momentum Oscillator",
        "short_desc": "Pure oscillator: Buy when RS-Momentum crosses above 100; Sell when it crosses below 100.",
        "full_desc": "Fastest reacting strategy. Treats RS-Momentum as a pure zero-line oscillator. Buys whenever RS-Momentum crosses above 100 regardless of quadrant (even in Lagging). Sells whenever RS-Momentum crosses below 100.",
    },
    12: {
        "id": 12,
        "name": "Portfolio Rotation (Multi-Stock)",
        "tag": "Multi-Stock Portfolio",
        "short_desc": "Cross-sectional portfolio: Dynamically allocate single ₹10k pool to top 2 stocks across all 6.",
        "full_desc": "Actual multi-stock portfolio simulation. Starting capital is ₹10,000 for the entire portfolio. Every session, all 6 stocks are ranked by composite RRG relative strength. Capital is allocated to the top eligible stocks in Leading/Improving, rotating out of weakening stocks with realistic whole-share accounting.",
    },
}


# ---- RRG & Weekly As-Of Calculations -----------------------------------------
def compute_rrg(df_aligned: pd.DataFrame, stock_name: str, tf: str = "Daily") -> Tuple[pd.DataFrame, bool]:
    """Computes RRG daily or weekly series from aligned closes."""
    bench_name = cfg.BENCHMARK_NAME
    closes = df_aligned.copy()
    if tf == "Weekly":
        closes = closes.groupby(closes.index.to_period("W-FRI")).tail(1)

    raw_len = len(closes)
    warmup_val = WARMUP_WEEKLY if tf == "Weekly" else WARMUP_DAILY
    warmup = min(warmup_val, raw_len // 3)
    if raw_len < warmup + 10:
        return pd.DataFrame(), False

    rr = calc_rs_ratio(closes[stock_name], closes[bench_name])
    rm = calc_rs_momentum(rr)
    df = pd.DataFrame({"RS_Ratio": rr, "RS_Momentum": rm, "Close": closes[stock_name]}).dropna()
    df = df.iloc[warmup:]
    df["Quadrant"] = [quadrant(a, b) for a, b in zip(df["RS_Ratio"], df["RS_Momentum"])]

    is_sufficient = len(df) >= 60 if tf == "Weekly" else len(df) >= 30
    return df, is_sufficient


def weekly_asof(closes: pd.DataFrame, stock_name: str, bench_name: str = cfg.BENCHMARK_NAME) -> pd.DataFrame:
    """
    Weekly RS-Ratio / RS-Momentum as they stood on each trading day (no look-ahead).
    """
    week = closes.index.to_period("W-FRI")
    wk = closes.groupby(week).tail(1)
    if len(wk) < 15:
        return pd.DataFrame()

    rs_w = pd.Series((wk[stock_name] / wk[bench_name]).to_numpy())
    sm = rs_w.rolling(RS_PRESMOOTH, min_periods=1).mean()
    e_fast = sm.ewm(span=RS_SHORT, adjust=False).mean().to_numpy()
    e_slow = sm.ewm(span=RS_LONG, adjust=False).mean().to_numpy()
    rr_w = pd.Series(100.0 * e_fast / e_slow)
    m_fast = rr_w.ewm(span=MOM_SHORT, adjust=False).mean().to_numpy()
    m_slow = rr_w.ewm(span=MOM_LONG, adjust=False).mean().to_numpy()
    prior = rs_w.rolling(RS_PRESMOOTH - 1, min_periods=1).sum().to_numpy()

    pos = pd.Index(wk.index.to_period("W-FRI")).get_indexer(week)
    prev = pos - 1
    warmup = min(WARMUP_WEEKLY, len(wk) // 3)
    ok = prev >= warmup
    if not ok.any():
        return pd.DataFrame()

    prev_ok = prev[ok]
    d_idx = closes.index[ok]
    rs_d = (closes[stock_name] / closes[bench_name]).to_numpy()[ok]

    def step(x, state, span):
        a = 2.0 / (span + 1.0)
        return a * x + (1 - a) * state

    sm_d = (prior[prev_ok] + rs_d) / RS_PRESMOOTH
    rr_d = 100.0 * step(sm_d, e_fast[prev_ok], RS_SHORT) / step(sm_d, e_slow[prev_ok], RS_LONG)
    rm_d = 100.0 * step(rr_d, m_fast[prev_ok], MOM_SHORT) / step(rr_d, m_slow[prev_ok], MOM_LONG)
    out = pd.DataFrame({"RS_Ratio": rr_d, "RS_Momentum": rm_d, "Close": closes[stock_name].loc[d_idx]}, index=d_idx)
    out["Quadrant"] = [quadrant(r, m) for r, m in zip(rr_d, rm_d)]
    return out


# ---- Signal Generators (Strategies 1 to 11) ----------------------------------
def gen_strat_1(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12) -> List[Dict]:
    """Strategy 1: Basic Quadrant Rotation (No weekly filter)."""
    q = daily["Quadrant"]
    up = q.isin(UP)
    prev_q = q.shift(1)
    prev_up = prev_q.isin(UP)
    close = daily["Close"]
    c = cost_pct / 100.0

    trades, pos = [], None
    for d in daily.index[daily.index >= start]:
        if pos is None and up[d] and not prev_up[d] and pd.notna(prev_q[d]):
            pos = dict(buy=d, buy_px=close[d], weekly="", frm=prev_q[d], into=q[d])
        elif pos is not None and not up[d] and prev_up[d]:
            trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                               exit_reason="Daily Drop to Weakening/Lagging"))
            pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades


def gen_strat_2(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12,
                profit_target: float = 8.0, trail_stop: float = 5.0) -> List[Dict]:
    """Strategy 2: Leading Profit Booking (+8% Target, 5% Trailing Stop, or Weakening exit)."""
    q = daily["Quadrant"]
    prev_q = q.shift(1)
    close = daily["Close"]
    c = cost_pct / 100.0

    trades, pos = [], None
    peak_px = 0.0
    for d in daily.index[daily.index >= start]:
        if pos is None and q[d] == "Leading" and prev_q[d] != "Leading" and pd.notna(prev_q[d]):
            pos = dict(buy=d, buy_px=close[d], weekly="", frm=prev_q[d], into=q[d])
            peak_px = close[d]
        elif pos is not None:
            peak_px = max(peak_px, close[d])
            gain_pct = 100.0 * (close[d] / pos["buy_px"] - 1.0)
            drop_from_peak = 100.0 * (peak_px - close[d]) / peak_px
            if gain_pct >= profit_target:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason=f"Profit Target (+{profit_target:.1f}%)"))
                pos = None
            elif drop_from_peak >= trail_stop and peak_px > pos["buy_px"] * 1.02:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason=f"Trailing Stop (-{trail_stop:.1f}% from peak)"))
                pos = None
            elif q[d] in DOWN:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="Daily Drop to Weakening/Lagging"))
                pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades


def gen_strat_3(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12) -> Tuple[List[Dict], List[Dict]]:
    """Strategy 3: Daily + Weekly RRG Confirmation (Baseline strategy)."""
    q = daily["Quadrant"]
    up = q.isin(UP)
    prev_q = q.shift(1)
    prev_up = prev_q.isin(UP)
    w_q = asof["Quadrant"].reindex(daily.index)
    w_up = w_q.isin(UP)
    close = daily["Close"]
    c = cost_pct / 100.0

    trades, skipped, pos = [], [], None
    for d in daily.index[daily.index >= start]:
        if pos is None and up[d] and not prev_up[d] and pd.notna(prev_q[d]):
            if w_up[d]:
                pos = dict(buy=d, buy_px=close[d], weekly=w_q[d], frm=prev_q[d], into=q[d])
            else:
                skipped.append(dict(date=d, weekly=w_q[d], frm=prev_q[d], into=q[d]))
        elif pos is not None and not up[d] and prev_up[d]:
            trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                               exit_reason="Daily Drop to Weakening/Lagging"))
            pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades, skipped


def gen_strat_4(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12,
                stop_loss_pct: float = 5.0) -> List[Dict]:
    """Strategy 4: Early Rotation Catcher (Lagging to Improving)."""
    q = daily["Quadrant"]
    prev_q = q.shift(1)
    rm = daily["RS_Momentum"]
    close = daily["Close"]
    prev_close = close.shift(1)
    c = cost_pct / 100.0

    trades, pos = [], None
    for d in daily.index[daily.index >= start]:
        is_lag_to_imp = (prev_q[d] == "Lagging" and q[d] == "Improving")
        price_recovering = close[d] >= prev_close[d]
        if pos is None and is_lag_to_imp and rm[d] >= 100.0 and price_recovering:
            pos = dict(buy=d, buy_px=close[d], weekly="", frm=prev_q[d], into=q[d])
        elif pos is not None:
            loss_pct = 100.0 * (1.0 - close[d] / pos["buy_px"])
            if rm[d] < 100.0:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="RS-Momentum Failure (<100)"))
                pos = None
            elif loss_pct >= stop_loss_pct:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason=f"Stop Loss (-{stop_loss_pct:.1f}%)"))
                pos = None
            elif q[d] in DOWN:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="Daily Drop to Weakening/Lagging"))
                pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades


def gen_strat_5(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12,
                stop_loss_pct: float = 7.0) -> List[Dict]:
    """Strategy 5: Leading-Only Momentum (Daily Leading + Weekly Leading + Close > SMA50)."""
    q = daily["Quadrant"]
    w_q = asof["Quadrant"].reindex(daily.index)
    close = daily["Close"]
    sma50 = close.rolling(50, min_periods=20).mean()
    rm = daily["RS_Momentum"]
    c = cost_pct / 100.0

    in_zone = (q == "Leading") & (w_q == "Leading") & (close > sma50)
    prev_zone = in_zone.shift(1).fillna(False)

    trades, pos = [], None
    for d in daily.index[daily.index >= start]:
        if pos is None and in_zone[d] and not prev_zone[d]:
            pos = dict(buy=d, buy_px=close[d], weekly=w_q[d], frm=q.shift(1)[d], into=q[d])
        elif pos is not None:
            loss_pct = 100.0 * (1.0 - close[d] / pos["buy_px"])
            if rm[d] < 100.0:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="RS-Momentum Drop (<100)"))
                pos = None
            elif close[d] < sma50[d]:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="Close Below 50-SMA"))
                pos = None
            elif loss_pct >= stop_loss_pct:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason=f"Stop Loss (-{stop_loss_pct:.1f}%)"))
                pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades


def gen_strat_7(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12,
                stop_loss_pct: float = 6.0) -> List[Dict]:
    """Strategy 7: Improving-to-Leading Crossover (RS_Ratio crosses 100 with RS_Mom >= 100)."""
    rr = daily["RS_Ratio"]
    prev_rr = rr.shift(1)
    rm = daily["RS_Momentum"]
    close = daily["Close"]
    q = daily["Quadrant"]
    c = cost_pct / 100.0

    crossover = (prev_rr < 100.0) & (rr >= 100.0) & (rm >= 100.0)
    trades, pos = [], None
    for d in daily.index[daily.index >= start]:
        if pos is None and crossover[d]:
            pos = dict(buy=d, buy_px=close[d], weekly="", frm="Improving", into="Leading")
        elif pos is not None:
            loss_pct = 100.0 * (1.0 - close[d] / pos["buy_px"])
            if rm[d] < 100.0:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="RS-Momentum Loss (<100)"))
                pos = None
            elif loss_pct >= stop_loss_pct:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason=f"Stop Loss (-{stop_loss_pct:.1f}%)"))
                pos = None
            elif q[d] == "Lagging":
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="Drop to Lagging"))
                pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades


def gen_strat_8(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12,
                stop_loss_pct: float = 6.0) -> List[Dict]:
    """Strategy 8: Leading Pullback Entry (Weekly Leading, Daily pullback turns back up)."""
    q = daily["Quadrant"]
    w_q = asof["Quadrant"].reindex(daily.index)
    close = daily["Close"]
    c = cost_pct / 100.0

    trades, pos = [], None
    pullback_active = False
    for d in daily.index[daily.index >= start]:
        if w_q[d] == "Leading":
            if q[d] in ["Weakening", "Lagging"]:
                pullback_active = True
            elif pullback_active and q[d] in ["Leading", "Improving"]:
                if pos is None:
                    pos = dict(buy=d, buy_px=close[d], weekly="Leading", frm="Pullback", into=q[d])
                    pullback_active = False
        else:
            pullback_active = False

        if pos is not None:
            loss_pct = 100.0 * (1.0 - close[d] / pos["buy_px"])
            if w_q[d] != "Leading":
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="Weekly Left Leading"))
                pos = None
            elif q[d] == "Lagging":
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="Daily Drop to Lagging"))
                pos = None
            elif loss_pct >= stop_loss_pct:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason=f"Stop Loss (-{stop_loss_pct:.1f}%)"))
                pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades


def gen_strat_9(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12) -> List[Dict]:
    """Strategy 9: Weakening Early Exit (Exits immediately when Daily touches Weakening)."""
    q = daily["Quadrant"]
    up = q.isin(UP)
    prev_q = q.shift(1)
    prev_up = prev_q.isin(UP)
    w_q = asof["Quadrant"].reindex(daily.index)
    w_up = w_q.isin(UP)
    close = daily["Close"]
    c = cost_pct / 100.0

    trades, pos = [], None
    for d in daily.index[daily.index >= start]:
        if pos is None and up[d] and not prev_up[d] and pd.notna(prev_q[d]):
            if w_up[d]:
                pos = dict(buy=d, buy_px=close[d], weekly=w_q[d], frm=prev_q[d], into=q[d])
        elif pos is not None and q[d] in DOWN:
            reason = "Early Exit: Daily Weakening" if q[d] == "Weakening" else "Drop to Lagging"
            trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False, exit_reason=reason))
            pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades


def gen_strat_10(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12,
                 stop_loss_pct: float = 6.0) -> List[Dict]:
    """Strategy 10: Price + RRG Confirmation (RRG UP + Close > SMA50 + SMA20 slope up)."""
    q = daily["Quadrant"]
    w_q = asof["Quadrant"].reindex(daily.index)
    close = daily["Close"]
    sma50 = close.rolling(50, min_periods=20).mean()
    sma20 = close.rolling(20, min_periods=10).mean()
    sma20_slope_up = sma20 > sma20.shift(1)
    c = cost_pct / 100.0

    cond = q.isin(UP) & w_q.isin(UP) & (close > sma50) & sma20_slope_up
    prev_cond = cond.shift(1).fillna(False)

    trades, pos = [], None
    for d in daily.index[daily.index >= start]:
        if pos is None and cond[d] and not prev_cond[d]:
            pos = dict(buy=d, buy_px=close[d], weekly=w_q[d], frm=q.shift(1)[d], into=q[d])
        elif pos is not None:
            loss_pct = 100.0 * (1.0 - close[d] / pos["buy_px"])
            if q[d] in DOWN:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="RRG Drop to Weakening/Lagging"))
                pos = None
            elif close[d] < sma50[d]:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason="Close Below 50-SMA"))
                pos = None
            elif loss_pct >= stop_loss_pct:
                trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                                   exit_reason=f"Stop Loss (-{stop_loss_pct:.1f}%)"))
                pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades


def gen_strat_11(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp, cost_pct: float = 0.12) -> List[Dict]:
    """Strategy 11: RS-Momentum Reversal (Pure oscillator crossover)."""
    rm = daily["RS_Momentum"]
    prev_rm = rm.shift(1)
    close = daily["Close"]
    q = daily["Quadrant"]
    c = cost_pct / 100.0

    cross_up = (prev_rm < 100.0) & (rm >= 100.0)
    cross_down = (prev_rm >= 100.0) & (rm < 100.0)

    trades, pos = [], None
    for d in daily.index[daily.index >= start]:
        if pos is None and cross_up[d]:
            pos = dict(buy=d, buy_px=close[d], weekly="", frm="RM<100", into="RM>=100")
        elif pos is not None and cross_down[d]:
            trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False,
                               exit_reason="RS-Momentum Cross Below 100"))
            pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True,
                           exit_reason="Open Position"))
    for t in trades:
        t["ret"] = 100.0 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())
    return trades


# ---- Execution Simulators ----------------------------------------------------
def simulate_single_strategy(daily: pd.DataFrame, raw_trades: List[Dict], start: pd.Timestamp,
                             capital: float = 10000.0, cost_pct: float = 0.12) -> Tuple[List[Dict], float, pd.Series, pd.Series, int]:
    """
    Simulates realistic cash and share execution for standard single-exit strategies.
    Ensures whole shares, transaction costs, mark-to-market daily portfolio value.
    """
    c = cost_pct / 100.0
    close = daily["Close"][daily.index >= start]
    cash = float(capital)
    book = []
    shares_by_day = pd.Series(0, index=close.index)

    for t in raw_trades:
        px_in = t["buy_px"]
        shares = int(cash // (px_in * (1 + c)))
        paid = shares * px_in * (1 + c)
        px_out = t["sell_px"]
        got = shares * px_out * (1 - c)
        charges = (shares * px_in * c) + (shares * px_out * c)
        cash_before = cash
        cash = cash - paid + got
        end = t["sell"] if t["sell"] is not None else close.index[-1]
        shares_by_day[(close.index >= t["buy"]) & (close.index < end)] = shares
        if t["sell"] is None:
            shares_by_day[close.index == end] = shares

        entry_dict = dict(t)
        entry_dict.update({
            "shares": shares,
            "paid": paid,
            "got": got,
            "pnl": got - paid,
            "pnl_pct": 100.0 * (got - paid) / paid if paid > 0 else 0.0,
            "charges": charges,
            "cash_before": cash_before,
            "cash_after": cash,
        })
        book.append(entry_dict)

    cash_by_day = pd.Series(float(capital), index=close.index)
    for b in book:
        end = b["sell"] if b["sell"] is not None else close.index[-1]
        inside = (close.index >= b["buy"]) & (close.index < end)
        cash_by_day[inside] = b["cash_before"] - b["paid"]
        cash_by_day[close.index >= end] = b["cash_after"]
        if b["sell"] is None:
            cash_by_day[close.index == end] = b["cash_before"] - b["paid"]

    value = cash_by_day + shares_by_day * close * (1 - c)
    if book and book[-1]["sell"] is None:
        value.iloc[-1] = book[-1]["cash_after"]

    # Buy & Hold Benchmark
    bh_shares = int(capital // (close.iloc[0] * (1 + c)))
    bh_left = capital - bh_shares * close.iloc[0] * (1 + c)
    bh_value = bh_left + bh_shares * close * (1 - c)

    return book, cash, value, bh_value, bh_shares


def simulate_partial_strategy(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp,
                              capital: float = 10000.0, cost_pct: float = 0.12,
                              profit_target: float = 8.0, stop_loss_pct: float = 6.0) -> Tuple[List[Dict], float, pd.Series, pd.Series, int]:
    """
    Simulates Strategy 6 (Partial Profit Booking):
    - Buys whole shares on confirmed Daily+Weekly RRG.
    - Sells 50% of position when Close reaches +8% profit target.
    - Moves stop loss on remaining shares to breakeven.
    - Sells remaining shares when Daily drops into Weakening/Lagging or breakeven stop.
    """
    c = cost_pct / 100.0
    close = daily["Close"][daily.index >= start]
    q = daily["Quadrant"].reindex(close.index)
    w_q = asof["Quadrant"].reindex(close.index)
    up = q.isin(UP)
    prev_up = up.shift(1).fillna(False)

    cash = float(capital)
    book = []
    shares_by_day = pd.Series(0, index=close.index)
    cash_by_day = pd.Series(float(capital), index=close.index)

    in_pos = False
    buy_date, buy_px = None, 0.0
    total_shares = 0
    rem_shares = 0
    target_hit = False

    for d in close.index:
        cur_px = close[d]

        # Check entry
        if not in_pos and up[d] and not prev_up[d] and w_q[d] in UP:
            in_pos = True
            buy_date = d
            buy_px = cur_px
            total_shares = int(cash // (buy_px * (1 + c)))
            rem_shares = total_shares
            paid = total_shares * buy_px * (1 + c)
            charges = total_shares * buy_px * c
            cash -= paid
            target_hit = False
            shares_by_day[d] = rem_shares
            cash_by_day[d] = cash
            continue

        if in_pos:
            gain_pct = 100.0 * (cur_px / buy_px - 1.0)
            loss_pct = 100.0 * (1.0 - cur_px / buy_px)

            # Check 50% partial profit target
            if not target_hit and gain_pct >= profit_target and total_shares >= 2:
                half_shares = total_shares // 2
                got_half = half_shares * cur_px * (1 - c)
                paid_half = half_shares * buy_px * (1 + c)
                charges_half = (half_shares * buy_px * c) + (half_shares * cur_px * c)
                cash += got_half
                rem_shares = total_shares - half_shares
                target_hit = True
                book.append({
                    "buy": buy_date, "buy_px": buy_px, "sell": d, "sell_px": cur_px,
                    "shares": half_shares, "paid": paid_half, "got": got_half,
                    "pnl": got_half - paid_half,
                    "pnl_pct": 100.0 * (got_half - paid_half) / paid_half,
                    "charges": charges_half, "cash_before": cash - got_half, "cash_after": cash,
                    "exit_reason": f"Partial Target (+{profit_target:.1f}%)", "open": False,
                    "weekly": w_q.loc[buy_date] if buy_date in w_q.index else "",
                    "frm": "Improving", "into": "Leading", "exit_into": q[d],
                    "held": int(((daily.index > buy_date) & (daily.index <= d)).sum())
                })

            # Check exit for remaining shares
            do_exit = False
            exit_reason = ""
            if target_hit and cur_px <= buy_px:
                do_exit = True
                exit_reason = "Breakeven Stop (after +8% hit)"
            elif not target_hit and loss_pct >= stop_loss_pct:
                do_exit = True
                exit_reason = f"Stop Loss (-{stop_loss_pct:.1f}%)"
            elif q[d] in DOWN:
                do_exit = True
                exit_reason = "Daily Drop to Weakening/Lagging"

            if do_exit:
                got = rem_shares * cur_px * (1 - c)
                paid_rem = rem_shares * buy_px * (1 + c)
                charges_rem = (rem_shares * buy_px * c) + (rem_shares * cur_px * c)
                cash += got
                book.append({
                    "buy": buy_date, "buy_px": buy_px, "sell": d, "sell_px": cur_px,
                    "shares": rem_shares, "paid": paid_rem, "got": got,
                    "pnl": got - paid_rem,
                    "pnl_pct": 100.0 * (got - paid_rem) / paid_rem if paid_rem > 0 else 0.0,
                    "charges": charges_rem, "cash_before": cash - got, "cash_after": cash,
                    "exit_reason": exit_reason, "open": False,
                    "weekly": w_q.loc[buy_date] if buy_date in w_q.index else "",
                    "frm": "Improving", "into": "Leading", "exit_into": q[d],
                    "held": int(((daily.index > buy_date) & (daily.index <= d)).sum())
                })
                in_pos = False
                rem_shares = 0

        shares_by_day[d] = rem_shares
        cash_by_day[d] = cash

    if in_pos and rem_shares > 0:
        last_px = close.iloc[-1]
        got = rem_shares * last_px * (1 - c)
        paid_rem = rem_shares * buy_px * (1 + c)
        charges_rem = (rem_shares * buy_px * c) + (rem_shares * last_px * c)
        book.append({
            "buy": buy_date, "buy_px": buy_px, "sell": None, "sell_px": last_px,
            "shares": rem_shares, "paid": paid_rem, "got": got,
            "pnl": got - paid_rem,
            "pnl_pct": 100.0 * (got - paid_rem) / paid_rem if paid_rem > 0 else 0.0,
            "charges": charges_rem, "cash_before": cash, "cash_after": cash + got,
            "exit_reason": "Still Holding (Open)", "open": True,
            "weekly": w_q.loc[buy_date] if buy_date in w_q.index else "",
            "frm": "Improving", "into": "Leading", "exit_into": None,
            "held": int(((daily.index > buy_date) & (daily.index <= close.index[-1])).sum())
        })

    value = cash_by_day + shares_by_day * close * (1 - c)
    if book and book[-1]["sell"] is None:
        value.iloc[-1] = book[-1]["cash_after"]

    bh_shares = int(capital // (close.iloc[0] * (1 + c)))
    bh_left = capital - bh_shares * close.iloc[0] * (1 + c)
    bh_value = bh_left + bh_shares * close * (1 - c)

    return book, cash, value, bh_value, bh_shares


def run_portfolio_rotation(stocks_rrg: Dict[str, Dict], bench_clean: pd.DataFrame, start: pd.Timestamp,
                           capital: float = 10000.0, cost_pct: float = 0.12,
                           max_positions: int = 2) -> Tuple[List[Dict], pd.Series, pd.Series, List[Dict]]:
    """
    Simulates Strategy 12 (Multi-Stock Portfolio Rotation):
    - Starting capital is a single ₹10,000 pool across all 6 stocks.
    - Evaluates cross-sectional relative strength daily.
    - Holds top eligible stocks (Leading/Improving).
    - Rotates out of stocks dropping into Weakening/Lagging.
    """
    c = cost_pct / 100.0
    all_dates = sorted(list(set.union(*[set(d["daily"].index[d["daily"].index >= start]) for d in stocks_rrg.values()])))
    date_idx = pd.DatetimeIndex(all_dates)

    cash = float(capital)
    held_positions = {}
    trades = []
    portfolio_equity = pd.Series(index=date_idx, dtype=float)
    holdings_history = []

    for d in date_idx:
        cur_px = {}
        for ticker, data in stocks_rrg.items():
            if d in data["daily"].index:
                cur_px[ticker] = data["daily"].loc[d, "Close"]

        # Check existing positions for exit (drop out of UP)
        to_sell = []
        for ticker, pos in list(held_positions.items()):
            daily = stocks_rrg[ticker]["daily"]
            if d in daily.index:
                q = daily.loc[d, "Quadrant"]
                if q in DOWN:
                    to_sell.append((ticker, f"Daily dropped to {q}"))
            else:
                to_sell.append((ticker, "No data/delisted"))

        for ticker, reason in to_sell:
            pos = held_positions.pop(ticker)
            px_out = cur_px[ticker]
            got = pos["shares"] * px_out * (1 - c)
            charges = (pos["shares"] * pos["buy_px"] * c) + (pos["shares"] * px_out * c)
            pnl = got - pos["paid"]
            cash += got
            trades.append({
                "ticker": ticker,
                "name": pos["name"],
                "buy": pos["buy_date"],
                "buy_px": pos["buy_px"],
                "sell": d,
                "sell_px": px_out,
                "shares": pos["shares"],
                "paid": pos["paid"],
                "got": got,
                "pnl": pnl,
                "pnl_pct": 100.0 * pnl / pos["paid"] if pos["paid"] > 0 else 0.0,
                "charges": charges,
                "exit_reason": reason,
                "open": False,
                "held": int(((stocks_rrg[ticker]["daily"].index > pos["buy_date"]) &
                             (stocks_rrg[ticker]["daily"].index <= d)).sum())
            })

        # Check for entries into open slots
        open_slots = max_positions - len(held_positions)
        if open_slots > 0 and cash > 500.0:
            scores = []
            for ticker, data in stocks_rrg.items():
                if ticker in held_positions:
                    continue
                daily = data["daily"]
                if d in daily.index:
                    q = daily.loc[d, "Quadrant"]
                    rr = daily.loc[d, "RS_Ratio"]
                    rm = daily.loc[d, "RS_Momentum"]
                    if q in UP:
                        score = (100.0 if q == "Leading" else 50.0) + (rr - 100.0) + (rm - 100.0)
                        scores.append((score, ticker))
            scores.sort(key=lambda x: x[0], reverse=True)

            for score, ticker in scores[:open_slots]:
                px = cur_px[ticker]
                slot_budget = cash / open_slots
                shares = int(slot_budget // (px * (1 + c)))
                if shares > 0:
                    paid = shares * px * (1 + c)
                    cash -= paid
                    held_positions[ticker] = {
                        "buy_date": d,
                        "buy_px": px,
                        "shares": shares,
                        "paid": paid,
                        "name": stocks_rrg[ticker]["name"]
                    }
                    open_slots -= 1
                    if open_slots <= 0 or cash < 500.0:
                        break

        invested_val = sum(pos["shares"] * cur_px.get(t, pos["buy_px"]) * (1 - c) for t, pos in held_positions.items())
        total_val = cash + invested_val
        portfolio_equity[d] = total_val
        holdings_history.append({
            "date": d,
            "cash": cash,
            "invested": invested_val,
            "total": total_val,
            "positions": ", ".join([f"{pos['name']} ({pos['shares']} sh)" for pos in held_positions.values()]) or "100% Cash"
        })

    last_d = date_idx[-1]
    for ticker, pos in held_positions.items():
        px_out = cur_px.get(ticker, pos["buy_px"])
        got = pos["shares"] * px_out * (1 - c)
        charges = (pos["shares"] * pos["buy_px"] * c) + (pos["shares"] * px_out * c)
        pnl = got - pos["paid"]
        trades.append({
            "ticker": ticker,
            "name": pos["name"],
            "buy": pos["buy_date"],
            "buy_px": pos["buy_px"],
            "sell": None,
            "sell_px": px_out,
            "shares": pos["shares"],
            "paid": pos["paid"],
            "got": got,
            "pnl": pnl,
            "pnl_pct": 100.0 * pnl / pos["paid"] if pos["paid"] > 0 else 0.0,
            "charges": charges,
            "exit_reason": "Still Holding (Open)",
            "open": True,
            "held": int(((stocks_rrg[ticker]["daily"].index > pos["buy_date"]) &
                         (stocks_rrg[ticker]["daily"].index <= last_d)).sum())
        })

    bench_close = bench_clean["Close"][bench_clean.index >= start] if "Close" in bench_clean.columns else bench_clean[bench_clean.index >= start]
    bh_shares = int(capital // (bench_close.iloc[0] * (1 + c)))
    bh_left = capital - bh_shares * bench_close.iloc[0] * (1 + c)
    bh_val = bh_left + bh_shares * bench_close * (1 - c)
    bh_val = bh_val.reindex(date_idx).ffill()

    return trades, portfolio_equity, bh_val, holdings_history


# ---- Metrics Calculation -----------------------------------------------------
def compute_metrics(book: List[Dict], value: pd.Series, bh_value: pd.Series,
                    capital: float, start: pd.Timestamp) -> Dict[str, Any]:
    """Calculates full quantitative performance metrics for a strategy."""
    final_val = float(value.iloc[-1])
    net_pnl = final_val - capital
    return_pct = 100.0 * net_pnl / capital

    days = max(1, (value.index[-1] - start).days)
    years = days / 365.25
    if final_val > 0 and years > 0:
        cagr = 100.0 * ((final_val / capital) ** (1.0 / years) - 1.0)
    else:
        cagr = -100.0 if final_val <= 0 else 0.0

    peak = value.cummax()
    dd_rupees = peak - value
    max_dd_rupees = float(dd_rupees.max())
    dd_pct = 100.0 * dd_rupees / peak
    max_dd_pct = float(dd_pct.max())

    closed = [b for b in book if b.get("sell") is not None]
    wins = [b for b in closed if b.get("pnl", 0.0) > 0]
    losses = [b for b in closed if b.get("pnl", 0.0) <= 0]
    win_rate = (100.0 * len(wins) / len(closed)) if closed else 0.0

    gross_profit = sum(b.get("pnl", 0.0) for b in wins)
    gross_loss = abs(sum(b.get("pnl", 0.0) for b in losses))
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        profit_factor = 999.0
    else:
        profit_factor = 0.0

    avg_return = float(np.mean([b["pnl_pct"] for b in closed])) if closed else 0.0
    avg_hold = float(np.mean([b["held"] for b in closed if "held" in b])) if closed else 0.0
    total_charges = sum(b.get("charges", 0.0) for b in book)

    bh_final = float(bh_value.iloc[-1])
    bh_pnl = bh_final - capital
    bh_return_pct = 100.0 * bh_pnl / capital
    alpha = return_pct - bh_return_pct

    return {
        "capital": capital,
        "final_value": final_val,
        "net_pnl": net_pnl,
        "return_pct": return_pct,
        "cagr_pct": cagr,
        "max_dd_rupees": max_dd_rupees,
        "max_dd_pct": max_dd_pct,
        "total_trades": len(closed) + (1 if book and book[-1].get("sell") is None else 0),
        "closed_trades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_trade_pct": avg_return,
        "avg_holding_days": avg_hold,
        "total_charges": total_charges,
        "bh_final": bh_final,
        "bh_return_pct": bh_return_pct,
        "alpha_pct": alpha,
    }


# ---- Strategy Runner & Comparison Engine -------------------------------------
def run_strategy(strat_id: int, daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp,
                 capital: float = 10000.0, cost_pct: float = 0.12,
                 stocks_rrg: Optional[Dict] = None, bench_clean: Optional[pd.DataFrame] = None) -> Tuple[List[Dict], float, pd.Series, pd.Series, int, Dict]:
    """Runs a single strategy by ID and returns (book, cash, value, bh_value, bh_shares, metrics)."""
    if strat_id == 1:
        raw = gen_strat_1(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 2:
        raw = gen_strat_2(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 3:
        raw, _ = gen_strat_3(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 4:
        raw = gen_strat_4(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 5:
        raw = gen_strat_5(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 6:
        book, cash, val, bh_val, bh_sh = simulate_partial_strategy(daily, asof, start, capital, cost_pct)
    elif strat_id == 7:
        raw = gen_strat_7(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 8:
        raw = gen_strat_8(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 9:
        raw = gen_strat_9(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 10:
        raw = gen_strat_10(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 11:
        raw = gen_strat_11(daily, asof, start, cost_pct)
        book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    elif strat_id == 12:
        if stocks_rrg is not None and bench_clean is not None:
            trades, val, bh_val, _ = run_portfolio_rotation(stocks_rrg, bench_clean, start, capital, cost_pct)
            book = trades
            cash = float(val.iloc[-1])
            bh_sh = 1
        else:
            raw, _ = gen_strat_3(daily, asof, start, cost_pct)
            book, cash, val, bh_val, bh_sh = simulate_single_strategy(daily, raw, start, capital, cost_pct)
    else:
        raise ValueError(f"Unknown strategy ID: {strat_id}")

    metrics = compute_metrics(book, val, bh_val, capital, start)
    return book, cash, val, bh_val, bh_sh, metrics


def compare_all_strategies(daily: pd.DataFrame, asof: pd.DataFrame, start: pd.Timestamp,
                           capital: float = 10000.0, cost_pct: float = 0.12,
                           stocks_rrg: Optional[Dict] = None, bench_clean: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
    """
    Executes all 12 strategies side-by-side and produces:
    - Summary DataFrame with key metrics
    - Synchronized Equity Curves DataFrame
    - Drawdown Curves DataFrame
    - Winner Highlights dictionary
    """
    rows = []
    equity_dict = {}
    drawdown_dict = {}

    for s_id in range(1, 13):
        meta = STRATEGY_REGISTRY[s_id]
        book, cash, val, bh_val, bh_sh, m = run_strategy(
            s_id, daily, asof, start, capital, cost_pct, stocks_rrg, bench_clean
        )
        s_name = f"S{s_id}: {meta['name']}"
        equity_dict[s_name] = val
        peak = val.cummax()
        dd = 100.0 * (peak - val) / peak
        drawdown_dict[s_name] = dd

        rows.append({
            "ID": s_id,
            "Strategy": meta["name"],
            "Tag": meta["tag"],
            "Final Value (₹)": m["final_value"],
            "Net PnL (₹)": m["net_pnl"],
            "Return (%)": m["return_pct"],
            "CAGR (%)": m["cagr_pct"],
            "Max Drawdown (%)": m["max_dd_pct"],
            "Max DD (₹)": m["max_dd_rupees"],
            "Win Rate (%)": m["win_rate"],
            "Total Trades": m["total_trades"],
            "Profit Factor": m["profit_factor"],
            "Avg Trade (%)": m["avg_trade_pct"],
            "Avg Hold (Days)": m["avg_holding_days"],
            "Charges (₹)": m["total_charges"],
            "Alpha vs B&H (%p)": m["alpha_pct"],
        })

    # Add Buy & Hold baseline to equity curve
    equity_dict["Buy & Hold"] = bh_val
    peak_bh = bh_val.cummax()
    drawdown_dict["Buy & Hold"] = 100.0 * (peak_bh - bh_val) / peak_bh

    summary_df = pd.DataFrame(rows)
    equity_df = pd.DataFrame(equity_dict).ffill().bfill()
    drawdown_df = pd.DataFrame(drawdown_dict).ffill().bfill()

    # Winners
    best_return = summary_df.loc[summary_df["Return (%)"].idxmax()]
    best_dd = summary_df.loc[summary_df["Max Drawdown (%)"].idxmin()]
    calmar_scores = summary_df["Return (%)"] / summary_df["Max Drawdown (%)"].replace(0, 0.01)
    best_calmar = summary_df.loc[calmar_scores.idxmax()]
    best_winrate = summary_df.loc[summary_df["Win Rate (%)"].idxmax()]

    highlights = {
        "highest_return": {
            "strategy": best_return["Strategy"],
            "return_pct": float(best_return["Return (%)"]),
            "pnl": float(best_return["Net PnL (₹)"]),
            "id": int(best_return["ID"])
        },
        "lowest_drawdown": {
            "strategy": best_dd["Strategy"],
            "max_dd_pct": float(best_dd["Max Drawdown (%)"]),
            "id": int(best_dd["ID"])
        },
        "best_risk_adjusted": {
            "strategy": best_calmar["Strategy"],
            "score": float(calmar_scores.max()),
            "id": int(best_calmar["ID"])
        },
        "highest_win_rate": {
            "strategy": best_winrate["Strategy"],
            "win_rate": float(best_winrate["Win Rate (%)"]),
            "id": int(best_winrate["ID"])
        }
    }

    return summary_df, equity_df, drawdown_df, highlights
