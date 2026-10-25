"""
Tags analysis tab: profitability of Strategy 2 version 3 for every stock in a tag, over two periods.
Runs as its own page (top navigation in rrg_app.py), separate from the RRG chart pages.
"""
import pandas as pd
import streamlit as st

import config as cfg
import data_pipeline as dp
import strategies as strat


@st.cache_data(show_spinner=False)
def tag_trades(ticker: str, manifest_version: str):
    """(first data date, Strategy 2 v3 trades run from the start of Period 1) for one ticker."""
    stock_df = dp.load_clean_data(ticker)
    bench_df = dp.load_clean_data(cfg.BENCHMARK_TICKER)
    if stock_df is None or bench_df is None or len(stock_df) == 0:
        return None, []
    name = cfg.STOCKS[ticker]["name"]
    aligned = dp.align_stock_with_benchmark(stock_df, bench_df, name, cfg.BENCHMARK_NAME)
    if aligned is None or len(aligned) == 0:
        return None, []
    daily, _ = strat.compute_rrg(aligned, name, tf="Daily")
    asof = strat.weekly_asof(aligned, name)
    if len(daily) < 2 or asof.empty:
        return aligned.index[0], []
    start = max(strat.TAG_PERIODS[0][1], daily.index[1], asof.index[0])
    trades, _ = strat.gen_strat_2_v3(daily, asof, start, strat.TAG_COST_PCT)
    return aligned.index[0], trades


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
    data = {t: tag_trades(t, m_ver) for t in cfg.stocks_for_tag(tag)}
qualified = [t for t, (first, _) in data.items() if first is not None and first <= strat.TAG_DATA_FROM]
left_out = [t for t in data if t not in qualified]
if left_out:
    st.caption("Not included (data starts after April 2022): " + ", ".join(
        f"{t.replace('.NS', '')} (from {data[t][0]:%d %b %Y})" if data[t][0] is not None else t.replace(".NS", "")
        for t in left_out))

for label, p_start, p_end in strat.TAG_PERIODS:
    rows = []
    for t in qualified:
        s = strat.ticker_period_summary(strat.period_trades(data[t][1], p_start, p_end))
        rows.append({
            "Ticker": t.replace(".NS", ""),
            "Number of trades": s["trades"],
            "Profit % per trade": ", ".join(f"{p:.2f}" for p in s["profits"]) or "—",
            "Days held per trade": ", ".join(str(x) for x in s["days"]) or "—",
            "Sum of profit %": round(s["profit_sum"], 2),
            "Sum of days held": s["days_sum"],
            "Daily profit %": round(s["daily_profit"], 4) if s["daily_profit"] is not None else None,
        })
    daily_vals = [r["Daily profit %"] for r in rows if r["Daily profit %"] is not None]
    avg = sum(daily_vals) / len(daily_vals) if daily_vals else None

    st.markdown(f"#### {label}: {p_start:%b %Y} to {p_end:%b %Y}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tickers in period", len(qualified))
    c2.metric("Closed trades in period", sum(r["Number of trades"] for r in rows))
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
    if len(daily_vals) < len(rows):
        st.caption(f"{len(rows) - len(daily_vals)} ticker(s) had no closed trade in this period, "
                   f"so they have no daily profit % and are left out of the average.")
