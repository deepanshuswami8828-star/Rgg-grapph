"""
Tags analysis tab: profitability of Strategy 2 version 3 for every stock in a tag, over two periods,
and how it changes when a take-profit threshold is added.
Runs as its own page (top navigation in rrg_app.py), separate from the RRG chart pages.
Everything is driven by config.TAGS / config.stocks_for_tag, so new tags appear here automatically.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config as cfg
import data_pipeline as dp
import strategies as strat

BASE_COLOR, CURVE_COLOR = "#c62828", "#2a78d6"


# ---- data (cached per data version) ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def ticker_inputs(ticker: str, manifest_version: str):
    """(first data date, daily RRG frame, weekly as-of frame, daily highs, strategy start) for one ticker."""
    stock_df = dp.load_clean_data(ticker)
    bench_df = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    if stock_df is None or bench_df is None or len(stock_df) == 0:
        return None
    name = cfg.STOCKS[ticker]["name"]
    aligned = dp.align_stock_with_benchmark(stock_df, bench_df, name, cfg.BENCHMARK_NAME)
    if aligned is None or len(aligned) == 0:
        return None
    daily, _ = strat.compute_rrg(aligned, name, tf="Daily")
    asof = strat.weekly_asof(aligned, name)
    start = max(strat.TAG_PERIODS[0][1], daily.index[1], asof.index[0]) if len(daily) >= 2 and not asof.empty else None
    return aligned.index[0], daily, asof, dp.load_high_data(ticker), start


@st.cache_data(show_spinner=False)
def ticker_trades(ticker: str, manifest_version: str, take_profit_pct=None):
    """Strategy 2 v3 trades from the start of Period 1 (optionally with a take-profit threshold)."""
    inputs = ticker_inputs(ticker, manifest_version)
    if inputs is None or inputs[4] is None:
        return []
    _, daily, asof, highs, start = inputs
    trades, _ = strat.gen_strat_2_v3(daily, asof, start, strat.TAG_COST_PCT,
                                     take_profit_pct=take_profit_pct, highs=highs)
    return trades


def tag_members(tag: str, manifest_version: str):
    """(qualifying tickers, left-out tickers with their first date) for a tag."""
    firsts = {}
    for t in cfg.stocks_for_tag(tag):
        inputs = ticker_inputs(t, manifest_version)
        firsts[t] = inputs[0] if inputs is not None else None
    qualified = [t for t, f in firsts.items() if f is not None and f <= strat.TAG_DATA_FROM]
    return qualified, {t: f for t, f in firsts.items() if t not in qualified}


@st.cache_data(show_spinner=False)
def tag_reports(tag: str, manifest_version: str, take_profit_pct=None):
    """{period label: strat.period_report} for a tag, base strategy or with a take-profit threshold."""
    qualified, _ = tag_members(tag, manifest_version)
    trades = {t: ticker_trades(t, manifest_version, take_profit_pct) for t in qualified}
    return {label: strat.period_report(trades, p_start, p_end) for label, p_start, p_end in strat.TAG_PERIODS}


# ---- page ------------------------------------------------------------------------------------
st.title("🏷️ Tags analysis")
st.caption("Profitability of Strategy 2 · Version 3 (weekly RRG, 10% stop-loss) for every stock in a tag.")

tag = st.selectbox("Tag", cfg.TAGS, key="tags_page_tag",
                   format_func=lambda g: f"{g} ({len(cfg.stocks_for_tag(g))} stocks)")
st.markdown(f"### Tag: {tag}")
st.caption(f"Strategy run from {strat.TAG_PERIODS[0][1]:%d %b %Y}. Each trade assumes ₹{strat.TAG_TRADE_AMOUNT:,.0f} invested, "
           f"charges {strat.TAG_COST_PCT:g}% per side. A trade counts in a period only if it was bought and sold inside it "
           f"(a trade spanning both periods, or still open, is left out). A ticker counts only if its data starts by April 2022.")

m_ver = dp.load_manifest().get("version_id", "none")
with st.spinner("Running the strategy for every stock in the tag..."):
    qualified, left_out = tag_members(tag, m_ver)
    base = tag_reports(tag, m_ver)
if left_out:
    st.caption("Not included (data starts after April 2022): " + ", ".join(
        f"{t.replace('.NS', '')} (from {f:%d %b %Y})" if f is not None else t.replace(".NS", "") for t, f in left_out.items()))

for label, p_start, p_end in strat.TAG_PERIODS:
    rep = base[label]
    rows = [{
        "Ticker": t.replace(".NS", ""),
        "Number of trades": s["trades"],
        "Profit % per trade": ", ".join(f"{p:.2f}" for p in s["profits"]) or "—",
        "Days held per trade": ", ".join(str(x) for x in s["days"]) or "—",
        "Sum of profit %": round(s["profit_sum"], 2),
        "Sum of days held": s["days_sum"],
        "Daily profit %": round(s["daily_profit"], 4) if s["daily_profit"] is not None else None,
    } for t, s in rep["rows"].items()]
    avg = rep["avg_daily_profit"]

    st.markdown(f"#### {label}: {p_start:%b %Y} to {p_end:%b %Y}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tickers in period", rep["tickers"])
    c2.metric("Closed trades in period", rep["trades"])
    c3.metric("Average daily profit % (simple)", f"{avg:.4f}%" if avg is not None else "—",
              help="Simple average of 'Daily profit %' over the tickers that had at least one closed trade.")
    if len(rows) > strat.TAG_MAX_ROWS:
        st.caption(f"Showing {strat.TAG_MAX_ROWS} of {len(rows)} tickers.")
    shown = rows[:strat.TAG_MAX_ROWS]
    st.dataframe(pd.DataFrame(shown), hide_index=True, width="stretch", height=38 + 35 * max(1, len(shown)),
                 column_config={"Profit % per trade": st.column_config.TextColumn(width="large"),
                                "Days held per trade": st.column_config.TextColumn(width="medium"),
                                "Daily profit %": st.column_config.NumberColumn(format="%.4f"),
                                "Sum of profit %": st.column_config.NumberColumn(format="%.2f")})
    if rep["tickers_with_trades"] < rep["tickers"]:
        st.caption(f"{rep['tickers'] - rep['tickers_with_trades']} ticker(s) had no closed trade in this period, "
                   f"so they have no daily profit % and are left out of the average.")

# ---- take-profit threshold analysis -------------------------------------------------------------
st.markdown("---")
st.markdown("### Take-profit threshold analysis")
st.caption("Modified Strategy 2 · Version 3: on any day after the buy, if the day's high reaches the buy price + x%, "
           "the stock is sold that day at exactly buy price + x% (x% profit booked). After such an exit it is bought again "
           "only once the weekly has dropped into Weakening/Lagging and come back up, as after a stop-loss. "
           "Everything else (weekly exits, 10% stop-loss, periods, ₹1,00,000 per trade) is unchanged. "
           "The red dashed line is the base strategy without take-profit.")

with st.spinner(f"Testing {len(strat.TAKE_PROFIT_THRESHOLDS)} take-profit thresholds for every stock in the tag..."):
    curve = {x: tag_reports(tag, m_ver, float(x)) for x in strat.TAKE_PROFIT_THRESHOLDS}

chart_cols = st.columns(len(strat.TAG_PERIODS))
for col, (label, p_start, p_end) in zip(chart_cols, strat.TAG_PERIODS):
    pts = [(curve[x][label]["avg_daily_profit"], x) for x in strat.TAKE_PROFIT_THRESHOLDS
           if curve[x][label]["avg_daily_profit"] is not None]
    base_avg = base[label]["avg_daily_profit"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines+markers",
                             name="With take-profit x%", line=dict(color=CURVE_COLOR, width=2), marker=dict(size=6),
                             hovertemplate="Take-profit %{y}%<br>Avg daily profit %{x:.4f}%<extra></extra>"))
    if base_avg is not None:
        fig.add_trace(go.Scatter(x=[base_avg, base_avg], y=[0, 100], mode="lines",
                                 name=f"Base strategy (no take-profit): {base_avg:.4f}%",
                                 line=dict(color=BASE_COLOR, width=2, dash="dash"), hoverinfo="name"))
    fig.update_layout(title=f"{label}: {p_start:%b %Y} to {p_end:%b %Y}", height=520, margin=dict(l=10, r=10, t=50, b=10),
                      xaxis_title="Simple average of daily profit % (all tickers)",
                      yaxis_title="Take-profit threshold x (% over buy price)",
                      yaxis=dict(range=[0, 102], dtick=10), legend=dict(orientation="h", y=-0.18),
                      plot_bgcolor="#fcfcfb", paper_bgcolor="#fcfcfb")
    col.plotly_chart(fig, width="stretch", key=f"tp_chart_{label}")

with st.expander("Numbers behind the charts"):
    table = []
    for x in [None] + strat.TAKE_PROFIT_THRESHOLDS:
        reps = base if x is None else curve[x]
        row = {"Take-profit threshold": "Base (none)" if x is None else f"{x}%"}
        for label, _, _ in strat.TAG_PERIODS:
            a = reps[label]["avg_daily_profit"]
            row[f"{label}: avg daily profit %"] = round(a, 4) if a is not None else None
            row[f"{label}: closed trades"] = reps[label]["trades"]
        table.append(row)
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
