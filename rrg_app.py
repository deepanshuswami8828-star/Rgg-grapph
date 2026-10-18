"""
Live RRG app: PVR INOX against NIFTY 50, daily or weekly.

Drag the slider under the chart (or click the chart and use the arrow keys) to move
through the sessions: the trail redraws for each date and the title states that
date's quadrant. Every dot is coloured by the quadrant it sat in on its own date.

The calculation is imported from make_rrg_pvrinox.py (not duplicated):

    RS-Ratio    = 100 * EMA(SMA(RS,5),5) / EMA(SMA(RS,5),30)
    RS-Momentum = 100 * EMA(RS-Ratio,3) / EMA(RS-Ratio,14)

Daily uses daily closes. Weekly applies the same formula to weekly closes (the last
trading day of each week), which is how weekly RRGs are built - the periods are
counted in weeks, not days.

Accuracy: the EMAs are run over the full Yahoo history (from 2007) and the first
WARMUP bars are discarded, so no shown value depends on where the download starts.

Run:  streamlit run rrg_app.py
"""
import os
import sys
import warnings
from datetime import datetime, time, timedelta, timezone

# the formula lives next to this file; find it however the app is started
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

warnings.filterwarnings("ignore")

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from plotly.subplots import make_subplots

from make_rrg_pvrinox import (
    STOCK, STOCK_TICKER, BENCH, BENCH_TICKER, TAIL_DAYS, SURFACE, INK_1, INK_2, INK_3,
    GRID, SERIES, QUAD_BG, QUAD_FG, RS_PRESMOOTH, RS_SHORT, RS_LONG, MOM_SHORT, MOM_LONG,
    calc_rs_ratio, calc_rs_momentum, quadrant, load_closes,
)

ORDER = ["Leading", "Weakening", "Lagging", "Improving"]
IST = timezone(timedelta(hours=5, minutes=30))

# everything that differs between the two timeframes
TF = {
    "Daily": dict(unit="session", units="sessions", warmup=200, tail=TAIL_DAYS,
                  windows=[60, 125, 250, 500, 750], window=250, slider="Session: ",
                  head="%a %d %b %Y"),
    "Weekly": dict(unit="week", units="weeks", warmup=100, tail=12,
                   windows=[26, 52, 104, 156, 260], window=52, slider="Week ending: ",
                   head="Week ending %a %d %b %Y"),
}

st.set_page_config(page_title="PVR INOX Live RRG", page_icon="📈", layout="wide")

# Tight page, and the RRG iframe sized to the browser window so the slider is
# always on screen without scrolling.
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 1rem;}
iframe[data-testid="stIFrame"] {height: calc(100vh - 245px) !important; min-height: 430px;}
div[data-testid="stMetric"] {padding: 0;}
div[data-testid="stMetricValue"] {font-size: 1.5rem;}
</style>
""", unsafe_allow_html=True)


def market_open(now):
    return now.weekday() < 5 and time(9, 15) <= now.time() <= time(15, 30)


# ---- data -------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner="Downloading closes...")
def get_closes():
    try:
        import yfinance as yf
        raw = yf.download([STOCK_TICKER, BENCH_TICKER], period="max", interval="1d",
                          auto_adjust=True, progress=False)
        closes = raw["Close"][[STOCK_TICKER, BENCH_TICKER]].dropna()
        if len(closes) < 1000:
            raise ValueError("insufficient rows returned")
        closes.columns = [STOCK, BENCH]
        source = "Yahoo Finance (auto-adjusted closes, full history)"
    except Exception:
        closes, source = load_closes()
        source += " - offline fallback, live download failed"
    return closes, source, datetime.now(IST)


def get_rrg(tf):
    closes, source, fetched = get_closes()
    if tf == "Weekly":
        # last trading day of each week, dated on that day (a holiday Friday
        # leaves the week dated Thursday rather than a day with no trade)
        closes = closes.groupby(closes.index.to_period("W-FRI")).tail(1)
    rr = calc_rs_ratio(closes[STOCK], closes[BENCH])
    rm = calc_rs_momentum(rr)
    df = pd.DataFrame({"RS_Ratio": rr, "RS_Momentum": rm, "Close": closes[STOCK]}).dropna()
    df = df.iloc[min(TF[tf]["warmup"], len(df) // 3):]
    df["Quadrant"] = [quadrant(a, b) for a, b in zip(df["RS_Ratio"], df["RS_Momentum"])]
    return df, source, fetched


def latest_is_provisional(df, tf, now):
    """True while the newest bar can still change (market day/week not finished)."""
    last = df.index[-1]
    if tf == "Daily":
        return market_open(now) and last.date() == now.date()
    same_week = last.to_period("W-FRI") == pd.Timestamp(now.date()).to_period("W-FRI")
    week_done = now.weekday() > 4 or (now.weekday() == 4 and now.time() > time(15, 30))
    return same_week and not week_done


def periods(df):
    """Consecutive runs of the same quadrant -> one row per run, newest first."""
    run_id = (df["Quadrant"] != df["Quadrant"].shift()).cumsum()
    rows = [{"Quadrant": g["Quadrant"].iloc[0], "From": g.index[0], "To": g.index[-1],
             "Bars": len(g)} for _, g in df.groupby(run_id)]
    return pd.DataFrame(rows).iloc[::-1].reset_index(drop=True)


def frame_range(xs, ys):
    """Axis limits for one trail: frame it, but always keep the 100/100 cross in view."""
    spread = max(xs.max() - xs.min(), ys.max() - ys.min())
    pad, margin = max(0.35, 0.20 * spread), max(0.45, 0.25 * spread)
    return ([min(xs.min() - pad, 100 - margin), max(xs.max() + pad, 100 + margin)],
            [min(ys.min() - pad, 100 - margin), max(ys.max() + pad, 100 + margin)])


# Fills the iframe, and ← / → step one bar; the slider follows because each step
# is a named frame.
FIT_AND_KEYS = """
var gd = document.getElementById('{plot_id}');
document.documentElement.style.height = '100%';
document.body.style.height = '100%';
document.body.style.margin = '0';
gd.parentElement.style.height = '100%';
gd.style.height = '100%';
Plotly.Plots.resize(gd);
var names = gd._transitionData._frames.map(function (f) { return f.name; });
var at = names.length - 1;
function go(i) {
    at = Math.max(0, Math.min(names.length - 1, i));
    Plotly.animate(gd, [names[at]], {mode: 'immediate', frame: {duration: 0, redraw: true},
                                     transition: {duration: 0}});
}
gd.on('plotly_sliderchange', function (e) { at = names.indexOf(e.step.label); });
gd.on('plotly_animatingframe', function (e) { at = names.indexOf(e.name); });
document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') { go(at - 1); e.preventDefault(); }
    if (e.key === 'ArrowRight') { go(at + 1); e.preventDefault(); }
});
"""


def sparse_labels(xs, ys, xr, yr, gap=0.06, aspect=0.6):
    """Bar numbers only where they fit: newest first, then any dot at least `gap`
    (share of the plot) away from every label already placed. The first and last
    bars are always numbered; hover still gives every dot's date."""
    n = len(xs)
    px = [(x - xr[0]) / (xr[1] - xr[0]) for x in xs]
    py = [(y - yr[0]) / (yr[1] - yr[0]) * aspect for y in ys]   # height / width of plot
    keep = [n - 1, 0]
    for i in range(n - 2, 0, -1):
        if all((px[i] - px[j]) ** 2 + (py[i] - py[j]) ** 2 > gap ** 2 for j in keep):
            keep.append(i)
    return [str(i + 1) if i in keep else "" for i in range(n)]


# ---- weekly RRG as it stood on any day --------------------------------------
def weekly_asof(closes):
    """Weekly RS-Ratio / RS-Momentum as they read on each trading day.

    On day d the current week is unfinished, so its weekly close is d's close.
    The EMAs are recursive, so this is one EMA step from the previous week's final
    state - exactly what a live weekly chart shows that day. On the last trading
    day of a week it equals that week's final weekly value."""
    week = closes.index.to_period("W-FRI")
    wk = closes.groupby(week).tail(1)
    rs_w = pd.Series((wk[STOCK] / wk[BENCH]).to_numpy())
    sm = rs_w.rolling(RS_PRESMOOTH, min_periods=1).mean()
    e_fast = sm.ewm(span=RS_SHORT, adjust=False).mean().to_numpy()
    e_slow = sm.ewm(span=RS_LONG, adjust=False).mean().to_numpy()
    rr_w = pd.Series(100.0 * e_fast / e_slow)
    m_fast = rr_w.ewm(span=MOM_SHORT, adjust=False).mean().to_numpy()
    m_slow = rr_w.ewm(span=MOM_LONG, adjust=False).mean().to_numpy()
    # sum of the (RS_PRESMOOTH - 1) completed weeks up to each week, for the SMA
    prior = rs_w.rolling(RS_PRESMOOTH - 1, min_periods=1).sum().to_numpy()

    pos = pd.Index(wk.index.to_period("W-FRI")).get_indexer(week)
    prev = pos - 1
    ok = prev >= min(TF["Weekly"]["warmup"], len(wk) // 3)   # same rule as get_rrg
    prev, d_idx = prev[ok], closes.index[ok]
    rs_d = (closes[STOCK] / closes[BENCH]).to_numpy()[ok]

    def step(x, state, span):
        a = 2.0 / (span + 1.0)
        return a * x + (1 - a) * state

    sm_d = (prior[prev] + rs_d) / RS_PRESMOOTH
    rr_d = 100.0 * step(sm_d, e_fast[prev], RS_SHORT) / step(sm_d, e_slow[prev], RS_LONG)
    rm_d = 100.0 * step(rr_d, m_fast[prev], MOM_SHORT) / step(rr_d, m_slow[prev], MOM_LONG)
    out = pd.DataFrame({"RS_Ratio": rr_d, "RS_Momentum": rm_d,
                        "Close": closes[STOCK].to_numpy()[ok]}, index=d_idx)
    out["Quadrant"] = [quadrant(a, b) for a, b in zip(out["RS_Ratio"], out["RS_Momentum"])]
    return out


# ---- the RRG with its date slider -------------------------------------------
def quad_corners(xr, yr, s, size):
    corner = {"Improving": (xr[0], yr[1], "left", "top"),
              "Leading": (xr[1], yr[1], "right", "top"),
              "Lagging": (xr[0], yr[0], "left", "bottom"),
              "Weakening": (xr[1], yr[0], "right", "bottom")}
    return [dict(x=x, y=y, xref="x" + s, yref="y" + s, xanchor=xa, yanchor=ya,
                 showarrow=False, xshift=8 if xa == "left" else -8,
                 yshift=-6 if ya == "top" else 6, text="<b>%s</b>" % q.upper(),
                 font=dict(color=QUAD_FG[q], size=size))
            for q, (x, y, xa, ya) in corner.items()]


def r3(values):
    """Plain floats rounded to 3 decimals: far smaller page, no visible change."""
    return [round(float(v), 3) for v in values]


def panel_parts(view, s, xr, yr, aspect, small):
    """Traces (plain dicts, no plotly validation - hundreds of frames are built)
    and annotations for one trail drawn on axes x{s}/y{s}."""
    tail, dates, last_text = view["tail"], view["dates"], view["last_text"]
    xs, ys = tail["RS_Ratio"].to_numpy(), tail["RS_Momentum"].to_numpy()
    quads = list(tail["Quadrant"])
    n = len(tail)
    fade = [round(0.3 + 0.7 * i / max(n - 1, 1), 2) for i in range(n)]
    hover = ["<b>#%d  %s</b><br>%s<br>RS-Ratio %.2f<br>RS-Momentum %.2f<br>Close ₹%.2f"
             % (i + 1, d, q, r, m, c)
             for i, (d, r, m, q, c) in enumerate(zip(dates, xs, ys, quads, tail["Close"]))]
    x, y = r3(xs), r3(ys)
    ax = dict(type="scatter", xaxis="x" + s, yaxis="y" + s)
    traces = [
        dict(x=x, y=y, mode="lines", line=dict(color=SERIES, width=2),
             opacity=0.55, hoverinfo="skip", **ax),
        dict(x=x, y=y, mode="markers+text",
             text=sparse_labels(xs, ys, xr, yr, aspect=aspect), textposition="top center",
             textfont=dict(color=INK_2, size=10 if small else 11),
             marker=dict(size=10 if small else 11, color=[QUAD_FG[q] for q in quads],
                         opacity=fade, line=dict(color=SURFACE, width=1.2)),
             hovertext=hover, hoverinfo="text", **ax),
        dict(x=x[-1:], y=y[-1:], mode="markers",
             marker=dict(size=19 if small else 22, color=QUAD_FG[quads[-1]],
                         line=dict(color=SURFACE, width=2.5)),
             hovertext=hover[-1:], hoverinfo="text", **ax),
    ]
    ref = dict(xref="x" + s, yref="y" + s, showarrow=False)
    notes = quad_corners(xr, yr, s, 11 if small else 13) + [
        dict(x=x[0], y=y[0], yshift=-18, text=tail.index[0].strftime("%d %b"),
             font=dict(color=INK_3, size=10 if small else 11), **ref),
        dict(x=x[-1], y=y[-1], yshift=-22, text="<b>%s</b>" % last_text,
             font=dict(color=INK_1, size=11 if small else 12), **ref),
    ]
    heading = ("<b>%s</b>%s<span style='color:%s'><b>%s</b></span>  ·  RS-Ratio %.2f  ·  "
               "RS-Momentum %.2f" % (view["heading"], "<br>" if small else "  ·  ",
                                      QUAD_FG[quads[-1]], quads[-1].upper(), xs[-1], ys[-1]))
    return traces, notes, heading


def rrg_figure(panels, names, slider_prefix):
    """One date slider driving one or two RRG panels. Returns a plain figure dict.

    panels: list of {"name", "views": [one view per slider step], "fixed": range or None}
    where a view is {"tail": frame, "dates": hover dates, "last_text", "heading"}."""
    two = len(panels) == 2
    suffix = ["", "2"][:len(panels)]
    domains = [[0, 0.47], [0.53, 1]] if two else [[0, 1]]
    aspect = 0.95 if two else 0.6

    def frame_parts(j):
        data, notes, layout = [], [], {}
        for p, s, dom in zip(panels, suffix, domains):
            v = p["views"][j]
            xr, yr = p["fixed"] or frame_range(v["tail"]["RS_Ratio"].to_numpy(),
                                               v["tail"]["RS_Momentum"].to_numpy())
            xr, yr = r3(xr), r3(yr)
            traces, ann, heading = panel_parts(v, s, xr, yr, aspect, two)
            data += traces
            notes += ann
            layout["xaxis" + s] = dict(range=xr)
            layout["yaxis" + s] = dict(range=yr)
            if two:
                notes.append(dict(x=(dom[0] + dom[1]) / 2, y=1.0, xref="paper", yref="paper",
                                  xanchor="center", yanchor="bottom", yshift=6,
                                  showarrow=False, align="center",
                                  text="<span style='font-size:15px'><b>%s</b></span>  %s"
                                       % (p["name"].upper(), heading),
                                  font=dict(size=12, color=INK_2)))
            else:
                layout["title"] = dict(text=heading, y=0.985, yanchor="top", font=dict(size=15))
        layout["annotations"] = notes
        return data, layout

    frames = []
    for j, name in enumerate(names):
        data, layout = frame_parts(j)
        frames.append(dict(data=data, layout=layout, name=name))
    data, layout = frame_parts(len(names) - 1)

    big = 1e4  # quadrant fills reach far past any range the axes can take
    shapes = []
    for s in suffix:
        ref = dict(xref="x" + s, yref="y" + s, layer="below")
        for q, (x0, x1, y0, y1) in {"Improving": (-big, 100, 100, big),
                                    "Leading": (100, big, 100, big),
                                    "Lagging": (-big, 100, -big, 100),
                                    "Weakening": (100, big, -big, 100)}.items():
            shapes.append(dict(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                               fillcolor=QUAD_BG[q], line=dict(width=0), **ref))
        shapes.append(dict(type="line", x0=-big, x1=big, y0=100, y1=100,
                           line=dict(color=INK_3, width=1.1), **ref))
        shapes.append(dict(type="line", x0=100, x1=100, y0=-big, y1=big,
                           line=dict(color=INK_3, width=1.1), **ref))

    step = dict(mode="immediate", frame=dict(duration=0, redraw=True),
                transition=dict(duration=0))
    xt = "RS-Ratio (100 = in line with %s)" % BENCH if two else         "JdK RS-Ratio — relative strength level (100 = in line with %s)" % BENCH
    yt = "RS-Momentum" if two else "JdK RS-Momentum — rate of change of relative strength"
    for s, dom in zip(suffix, domains):
        layout["xaxis" + s].update(domain=dom, anchor="y" + s, gridcolor=GRID, zeroline=False,
                                   title=dict(text=xt, standoff=4, font=dict(size=12)))
        layout["yaxis" + s].update(anchor="x" + s, gridcolor=GRID, zeroline=False,
                                   title=dict(text=yt, font=dict(size=12)))
    layout.update(
        shapes=shapes, autosize=True, showlegend=False, hovermode="closest",
        margin=dict(l=65, r=20, t=58 if two else 40, b=85),
        plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, font=dict(color=INK_2),
        sliders=[dict(active=len(frames) - 1, x=0, len=1, y=0, yanchor="top",
                      steps=[dict(method="animate", label=f["name"], args=[[f["name"]], step])
                             for f in frames],
                      pad=dict(t=42, b=0, l=0, r=0),
                      currentvalue=dict(prefix=slider_prefix, xanchor="left",
                                        font=dict(size=13, color=INK_1)),
                      ticklen=0, minorticklen=0, font=dict(size=1, color=SURFACE))],
    )
    return dict(data=data, layout=layout, frames=frames)


def fixed_range(views):
    """One axis range covering every trail the slider can show."""
    every = pd.concat([v["tail"] for v in views])
    return frame_range(every["RS_Ratio"].to_numpy(), every["RS_Momentum"].to_numpy())


def single_views(df, tf, window, tail_n, provisional_last):
    head = TF[tf]["head"]
    start = max(len(df) - window, tail_n - 1)
    views = []
    for k in range(start, len(df)):
        tail = df.iloc[k - tail_n + 1:k + 1]
        day = tail.index[-1]
        tag = "  (provisional)" if provisional_last and k == len(df) - 1 else ""
        views.append(dict(tail=tail, dates=[d.strftime(head) for d in tail.index],
                          last_text=day.strftime("%d %b %Y") + tag,
                          heading=day.strftime(head)))
    return views, [df.index[k].strftime("%Y-%m-%d") for k in range(start, len(df))]


def weekly_views_on(days, wk, asof, tail_w, open_week):
    """Weekly trail as it stood on each day: completed weeks + the week so far."""
    wk_per = wk.index.to_period("W-FRI")
    head = TF["Weekly"]["head"]
    views = []
    for d in days:
        i = wk_per.searchsorted(d.to_period("W-FRI"))
        done = wk.iloc[max(0, i - (tail_w - 1)):i]
        now_row = asof.loc[[d]]
        tail = pd.concat([done[now_row.columns], now_row])
        # the week is complete on its last trading day, unless that week is still open
        week_final = i < len(wk) and wk.index[i] == d and not (open_week and i == len(wk) - 1)
        last = ("Week ending %s" if week_final else "Week to %s") % d.strftime("%a %d %b %Y")
        views.append(dict(tail=tail, dates=[x.strftime(head) for x in done.index] + [last],
                          last_text=d.strftime("%d %b %Y") + ("" if week_final else " (week so far)"),
                          heading=last))
    return views


# ---- the quadrant timeline --------------------------------------------------
def timeline_figure(seg, tf):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2],
                        vertical_spacing=0.04)
    fig.add_hline(y=100, line_color=INK_3, line_width=1, row=1, col=1)
    fig.add_trace(go.Scatter(x=seg.index, y=seg["RS_Ratio"], name="RS-Ratio",
                             line=dict(color=SERIES, width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=seg.index, y=seg["RS_Momentum"], name="RS-Momentum",
                             line=dict(color="#d0782a", width=2)), row=1, col=1)
    head = TF[tf]["head"]
    for q in ORDER:
        part = seg[seg["Quadrant"] == q]
        fig.add_trace(go.Bar(x=part.index, y=[1] * len(part), name=q, marker_color=QUAD_FG[q],
                             marker_line_width=0,
                             customdata=part[["RS_Ratio", "RS_Momentum"]].to_numpy(),
                             hovertemplate="%{x|" + head + "}<br><b>" + q + "</b><br>"
                                           "RS-Ratio %{customdata[0]:.2f}<br>"
                                           "RS-Momentum %{customdata[1]:.2f}<extra></extra>"),
                      row=2, col=1)
    fig.update_layout(height=360, bargap=0, barmode="stack", hovermode="x unified",
                      margin=dict(l=65, r=20, t=10, b=10),
                      plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, font=dict(color=INK_2),
                      legend=dict(orientation="h", y=1.08, x=0, traceorder="normal"))
    if tf == "Daily":
        # hide weekends and exchange holidays so the strip has no gaps
        holidays = pd.bdate_range(seg.index[0], seg.index[-1]).difference(seg.index)
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"]),
                                      dict(values=list(holidays))])
    fig.update_xaxes(gridcolor=GRID)
    fig.update_yaxes(gridcolor=GRID, row=1, col=1)
    fig.update_yaxes(visible=False, row=2, col=1)
    return fig


def quad_style(col):
    return ["background-color: %s; color: %s; font-weight: bold" % (QUAD_BG[q], QUAD_FG[q])
            if q in QUAD_BG else "" for q in col]


# ---- cycles: up = Improving/Leading, down = Weakening/Lagging ---------------
UP = ("Improving", "Leading")
UP_FG, DOWN_FG = QUAD_FG["Leading"], QUAD_FG["Lagging"]


def phases(df):
    """Consecutive runs on the same side of RS-Momentum 100 (up / down)."""
    up = df["Quadrant"].isin(UP)
    run_id = (up != up.shift()).cumsum()
    out = []
    for _, g in df.groupby(run_id):
        route = [q for i, q in enumerate(g["Quadrant"]) if i == 0 or q != g["Quadrant"].iloc[i - 1]]
        out.append(dict(up=bool(g["Quadrant"].iloc[0] in UP), start=g.index[0], last=g.index[-1],
                        bars=len(g), entered=g["Quadrant"].iloc[0], route=route))
    for a, b in zip(out, out[1:]):
        a["next"] = b["start"]
    if out:
        out[-1]["next"] = None
    return out


CYCLES_FROM = pd.Timestamp("2024-01-01")   # the move log always starts here


def moves(df):
    """Every switch between the two sides, oldest first: the date it entered
    Improving/Leading (up) or Weakening/Lagging (down), and how long it stayed."""
    ph = phases(df)
    last_close = df["Close"].iloc[-1]
    out = []
    for prev, p in zip(ph, ph[1:]):
        close = df.loc[p["start"], "Close"]
        end_close = df.loc[p["next"], "Close"] if p["next"] is not None else last_close
        out.append(dict(date=p["start"], up=p["up"], frm=prev["route"][-1], to=p["entered"],
                        route=p["route"], bars=p["bars"], open=p["next"] is None,
                        until=p["next"], close=close,
                        change=100 * (end_close / close - 1)))
    return out


def cycle_strip(items, start):
    """Up/down blocks per timeframe on one date axis."""
    fig = go.Figure()
    names = [n for n, _ in items]
    for row, (name, df) in enumerate(items):
        y0, y1 = row + 0.12, row + 0.88
        end = df.index[-1]
        for p in phases(df):
            x0 = max(p["start"], start)
            x1 = p["next"] or end + pd.Timedelta(days=1)
            if x1 <= start:
                continue
            fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1, opacity=0.85,
                          fillcolor=UP_FG if p["up"] else DOWN_FG, line_width=0)
            fig.add_trace(go.Scatter(
                x=[x0 + (x1 - x0) / 2], y=[row + 0.5], mode="markers",
                marker=dict(size=18, opacity=0), showlegend=False,
                hovertemplate="<b>%s · %s</b><br>%s → %s<br>%d %s<br>%s<extra></extra>"
                              % (name, "UP" if p["up"] else "DOWN",
                                 p["start"].strftime("%d %b %Y"),
                                 p["next"].strftime("%d %b %Y") if p["next"] else "now",
                                 p["bars"], "weeks" if name == "Weekly" else "sessions",
                                 " → ".join(p["route"]))))
    for label, color in (("Up: Improving / Leading", UP_FG),
                         ("Down: Weakening / Lagging", DOWN_FG)):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=label,
                                 marker=dict(size=12, symbol="square", color=color)))
    fig.update_layout(height=90 + 55 * len(items), margin=dict(l=65, r=20, t=30, b=30),
                      plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, font=dict(color=INK_2),
                      legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0),
                      hovermode="closest")
    fig.update_xaxes(range=[start, max(df.index[-1] for _, df in items) + pd.Timedelta(days=3)],
                     gridcolor=GRID, dtick="M3", tickformat="%b %Y")
    fig.update_yaxes(range=[len(items), 0], tickvals=[i + 0.5 for i in range(len(items))],
                     ticktext=["<b>%s</b>" % n for n in names], showgrid=False, zeroline=False)
    return fig


def move_log(df, unit_s, unit_p):
    log = [m for m in moves(df) if m["date"] >= CYCLES_FROM]
    plural = lambda n: "%d %s" % (n, unit_s if n == 1 else unit_p)
    cur = phases(df)[-1]

    ups = [m["bars"] for m in log if m["up"] and not m["open"]]
    downs = [m["bars"] for m in log if not m["up"] and not m["open"]]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Now", "%s · %s" % ("Up" if cur["up"] else "Down", cur["route"][-1]),
              "since %s" % cur["start"].strftime("%d %b %Y"),
              delta_color="normal" if cur["up"] else "inverse")
    c2.metric("Moves up since Jan 2024", sum(m["up"] for m in log))
    c3.metric("Average stay up", "%.1f %s" % (sum(ups) / len(ups), unit_p) if ups else "—")
    c4.metric("Average stay down", "%.1f %s" % (sum(downs) / len(downs), unit_p) if downs else "—")

    if not log:
        st.info("No moves since January 2024.")
        return
    table = pd.DataFrame([{
        "#": i + 1,
        "Date": m["date"].strftime("%a %d %b %Y"),
        "Move": "▲ Up" if m["up"] else "▼ Down",
        "From": m["frm"],
        "Into": m["to"],
        "Stayed": plural(m["bars"]) + (" (still there)" if m["open"] else ""),
        "Until": m["until"].strftime("%d %b %Y") if m["until"] is not None else "now",
        "Close": "₹%.2f" % m["close"],
        "Price till next move": ("%+.1f%%" % m["change"]) if abs(m["change"]) >= 0.05 else "0.0%",
    } for i, m in enumerate(log)])

    def move_style(col):
        return ["color: %s; font-weight: bold" % (UP_FG if v.startswith("▲") else DOWN_FG)
                for v in col]

    def price_style(col):
        return ["color: %s; font-weight: bold" % (UP_FG if v.startswith("+") else
                                                  DOWN_FG if v.startswith("-") else INK_2)
                for v in col]

    # tall enough to show every row: read it top (2024) to bottom (today)
    st.dataframe(table.style.apply(quad_style, subset=["From", "Into"])
                 .apply(move_style, subset=["Move"])
                 .apply(price_style, subset=["Price till next move"]),
                 hide_index=True, width="stretch", height=38 + 35 * len(table),
                 column_config={"#": st.column_config.NumberColumn(width="small"),
                                "Move": st.column_config.TextColumn(width="small"),
                                "Close": st.column_config.TextColumn(width="small")})


def cycle_section(items):
    """items: [(name, df)] - one strip row and one move log per timeframe."""
    st.subheader("Cycles since January 2024")
    st.caption("▲ **Up** = the date it moved into Improving or Leading (RS-Momentum rose above "
               "100).  ▼ **Down** = the date it moved into Weakening or Lagging (RS-Momentum "
               "fell below 100).  Oldest at the top, latest at the bottom.  "
               "*Price till next move* = close on that date to close on the next move "
               "(or the latest close).")
    st.plotly_chart(cycle_strip(items, CYCLES_FROM), width="stretch", theme=None,
                    config={"displaylogo": False, "displayModeBar": False})
    for name, df in items:
        weekly = name == "Weekly"
        st.markdown("##### %s moves" % name)
        move_log(df, "week" if weekly else "session", "weeks" if weekly else "sessions")


SINCE_2024 = "Since Jan 2024"


# ---- sidebar ----------------------------------------------------------------
with st.sidebar:
    st.header("Settings")
    tf = st.radio("Timeframe", ["Daily", "Weekly", "Both", "Strategy"], horizontal=True,
                  help="Both: the daily and weekly RRG side by side, moved by one slider. "
                       "Strategy: buy/sell signals and every past trade.")
    cfg = TF["Daily" if tf in ("Both", "Strategy") else tf]
    if st.button("Refresh data now", width="stretch"):
        get_closes.clear()
    if tf == "Strategy":
        bt_from = st.date_input("Backtest from", value=CYCLES_FROM.date(),
                                min_value=datetime(2010, 1, 1).date(), key="bt_from")
        cost = st.number_input("Cost per buy / sell (%)", min_value=0.0, max_value=2.0,
                               value=0.0, step=0.05, format="%.2f",
                               help="Brokerage + taxes, charged on each side of every trade.")
    else:
        window = st.select_slider("Slider covers", options=[SINCE_2024] + cfg["windows"],
                                  value=SINCE_2024, key="window_" + tf,
                                  format_func=lambda v: v if v == SINCE_2024
                                  else "last %d %s" % (v, cfg["units"]))
        if tf == "Both":
            tail_n = st.slider("Daily trail (sessions)", 5, 60, TF["Daily"]["tail"], key="tail_bd")
            tail_w = st.slider("Weekly trail (weeks)", 5, 60, TF["Weekly"]["tail"], key="tail_bw")
        else:
            tail_n = st.slider("Trail length (%s)" % cfg["units"], 5, 60, cfg["tail"],
                               key="tail_" + tf)
        fixed_axes = st.toggle("Fixed axes while sliding", value=False,
                               help="Off: each date is framed like the static chart. "
                                    "On: one scale for the whole slider, so movement is "
                                    "comparable between dates.")
    auto = st.toggle("Auto-refresh during market hours", value=True,
                     help="Re-downloads every 5 minutes while NSE is open "
                          "(Mon-Fri 09:15-15:30 IST).")


# ---- page -------------------------------------------------------------------
refresh_every = timedelta(minutes=5) if auto and market_open(datetime.now(IST)) else None


@st.cache_data(max_entries=6, show_spinner="Building the chart...")
def chart_html(key, _build):
    """The slider chart as a standalone page, cached on `key` so changing other
    widgets (date lookup, tables) does not rebuild hundreds of frames."""
    return pio.to_html(_build(), validate=False, include_plotlyjs=True, full_html=True,
                       auto_play=False, default_width="100%", default_height="100%",
                       config={"displaylogo": False, "responsive": True},
                       post_script=FIT_AND_KEYS)


def embed(key, build):
    # Embedded as plain Plotly: Streamlit's chart wrapper does not drive the
    # animation slider reliably, a standalone Plotly page does. CSS above sizes it
    # to the window.
    st.iframe(chart_html(key, build), height=700)


def window_size(df, choice):
    """Bars covered by the slider: everything since Jan 2024, or the last N."""
    if choice == SINCE_2024:
        return int((df.index >= CYCLES_FROM).sum())
    return int(choice)


def header(title, source, fetched, now, status_text):
    st.markdown("#### %s against %s — %s" % (STOCK, BENCH, title))
    status = ("🟢 NSE open" if market_open(now) else "⚪ NSE closed") + " — " + status_text
    st.caption("%s  ·  fetched %s IST  ·  %s"
               % (status, fetched.strftime("%d %b %Y %H:%M"), source))


def formula_note(extra):
    st.caption("RS-Ratio = 100 × EMA(SMA(RS,%d),%d) / EMA(SMA(RS,%d),%d)   ·   "
               "RS-Momentum = 100 × EMA(RS-Ratio,%d) / EMA(RS-Ratio,%d)   ·   %s   ·   "
               "computed over the full Yahoo history after an EMA warm-up   ·   "
               "Yahoo quotes may lag the exchange by a few minutes"
               % (RS_PRESMOOTH, RS_SHORT, RS_PRESMOOTH, RS_LONG, MOM_SHORT, MOM_LONG, extra))


def single_page():
    df, source, fetched = get_rrg(tf)
    now = datetime.now(IST)
    provisional = latest_is_provisional(df, tf, now)
    unit, units = cfg["unit"], cfg["units"]

    last, prev = df.iloc[-1], df.iloc[-2]
    streak = periods(df).iloc[0]["Bars"]

    header("%s RRG" % tf.lower(), source, fetched, now,
           "latest %s is %s" % (unit, "provisional" if provisional else "final"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Quadrant on %s" % df.index[-1].strftime("%d %b"), last["Quadrant"],
              "%d %s in a row" % (streak, unit if streak == 1 else units), delta_color="off")
    c2.metric("RS-Ratio", "%.2f" % last["RS_Ratio"],
              "%+.2f" % (last["RS_Ratio"] - prev["RS_Ratio"]))
    c3.metric("RS-Momentum", "%.2f" % last["RS_Momentum"],
              "%+.2f" % (last["RS_Momentum"] - prev["RS_Momentum"]))
    c4.metric("%s close" % STOCK, "₹%.2f" % last["Close"],
              "%+.2f%% vs previous %s" % (100 * (last["Close"] / prev["Close"] - 1), unit))

    win = window_size(df, window)

    def build():
        views, names = single_views(df, tf, win, tail_n, provisional)
        return rrg_figure([dict(name=tf, views=views,
                                fixed=fixed_range(views) if fixed_axes else None)],
                          names, cfg["slider"])
    embed((tf, win, tail_n, fixed_axes, provisional, str(fetched)), build)
    st.caption("Drag the slider, or click the chart and use the ← / → keys to step one %s. "
               "Each dot is coloured by the quadrant it was in on that %s; the large dot is "
               "the selected date. Hover any dot for its date." % (unit, unit))

    seg = df.iloc[-win:]
    cycle_section([(tf, df)])
    runs = periods(seg)

    st.subheader("Which quadrant on which %s" % ("date" if tf == "Daily" else "week"))
    st.plotly_chart(timeline_figure(seg, tf), width="stretch", theme=None,
                    config={"displaylogo": False})

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Look up a date**")
        pick = st.date_input("Date", value=df.index[-1].date(),
                             min_value=seg.index[0].date(), max_value=now.date(),
                             label_visibility="collapsed", key="pick_" + tf)
        ts = pd.Timestamp(pick)
        if tf == "Daily":
            hit = df.loc[:ts]
            row_date = hit.index[-1]
            note = "" if row_date.date() == pick else \
                " (no trading on %s; showing the previous session)" % pick.strftime("%d %b %Y")
        else:
            wk = ts.to_period("W-FRI")
            same = df[df.index.to_period("W-FRI") == wk]
            row_date = same.index[-1] if len(same) else df.loc[:ts].index[-1]
            note = " (the week containing %s)" % pick.strftime("%a %d %b %Y")
        row = df.loc[row_date]
        st.markdown("**%s** — <span style='color:%s;font-weight:700'>%s</span>  ·  "
                    "RS-Ratio %.2f  ·  RS-Momentum %.2f%s"
                    % (row_date.strftime(cfg["head"]), QUAD_FG[row["Quadrant"]],
                       row["Quadrant"].upper(), row["RS_Ratio"], row["RS_Momentum"], note),
                    unsafe_allow_html=True)

        counts = seg["Quadrant"].value_counts().reindex(ORDER, fill_value=0)
        st.markdown("**%s per quadrant (last %d)**" % (units.capitalize(), len(seg)))
        st.dataframe(pd.DataFrame({"Quadrant": counts.index, units.capitalize(): counts.values,
                                   "Share": ["%.0f%%" % (100 * v / len(seg))
                                             for v in counts.values]})
                     .style.apply(quad_style, subset=["Quadrant"]),
                     hide_index=True, width="stretch")
    with right:
        st.markdown("**Quadrant periods (newest first)**")
        show = runs.assign(From=runs["From"].dt.strftime("%d %b %Y"),
                           To=runs["To"].dt.strftime("%d %b %Y")) \
                   .rename(columns={"Bars": units.capitalize()})
        st.dataframe(show.style.apply(quad_style, subset=["Quadrant"]),
                     hide_index=True, width="stretch", height=400)

    with st.expander("Every %s, one by one" % unit):
        rows = seg.iloc[::-1]
        table = pd.DataFrame({"Date": rows.index.strftime(cfg["head"]),
                              "Close": rows["Close"].round(2).to_numpy(),
                              "RS-Ratio": rows["RS_Ratio"].round(2).to_numpy(),
                              "RS-Mom.": rows["RS_Momentum"].round(2).to_numpy(),
                              "Quadrant": rows["Quadrant"].to_numpy()})
        st.dataframe(table.style.apply(quad_style, subset=["Quadrant"])
                     .format({"Close": "%.2f", "RS-Ratio": "%.2f", "RS-Mom.": "%.2f"}),
                     hide_index=True, width="stretch", height=500)
        st.download_button("Download as CSV", seg.to_csv(float_format="%.4f"),
                           file_name="rrg_pvrinox_%s.csv" % tf.lower(), mime="text/csv")

    formula_note("periods are %s" % units)


def both_page():
    daily, source, fetched = get_rrg("Daily")
    weekly, _, _ = get_rrg("Weekly")
    closes, _, _ = get_closes()
    asof = weekly_asof(closes)
    now = datetime.now(IST)
    prov_day = latest_is_provisional(daily, "Daily", now)
    prov_week = latest_is_provisional(weekly, "Weekly", now)

    header("daily + weekly RRG", source, fetched, now,
           "latest session %s, latest week %s" % ("provisional" if prov_day else "final",
                                                  "in progress" if prov_week else "complete"))

    d_last, w_last = daily.iloc[-1], asof.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Daily quadrant on %s" % daily.index[-1].strftime("%d %b"), d_last["Quadrant"],
              "RS-Ratio %.2f · RS-Mom. %.2f" % (d_last["RS_Ratio"], d_last["RS_Momentum"]),
              delta_color="off")
    c2.metric("Weekly quadrant on %s" % asof.index[-1].strftime("%d %b"), w_last["Quadrant"],
              "RS-Ratio %.2f · RS-Mom. %.2f" % (w_last["RS_Ratio"], w_last["RS_Momentum"]),
              delta_color="off")
    prev = daily.iloc[-2]
    c3.metric("%s close" % STOCK, "₹%.2f" % d_last["Close"],
              "%+.2f%% vs previous session" % (100 * (d_last["Close"] / prev["Close"] - 1)))

    # one slider step per trading day; both charts are drawn as they stood that day
    # both charts need a value on every slider day (short offline data can leave
    # the weekly one starting later than the daily one)
    win = min(window_size(daily, window), int((daily.index >= asof.index[0]).sum()))

    def build():
        d_views, names = single_views(daily, "Daily", win, tail_n, prov_day)
        days = [pd.Timestamp(n) for n in names]
        w_views = weekly_views_on(days, weekly, asof, tail_w, prov_week)
        return rrg_figure([dict(name="Daily", views=d_views,
                                fixed=fixed_range(d_views) if fixed_axes else None),
                           dict(name="Weekly", views=w_views,
                                fixed=fixed_range(w_views) if fixed_axes else None)],
                          names, "Session: ")
    embed(("Both", win, tail_n, tail_w, fixed_axes, prov_day, prov_week, str(fetched)), build)
    st.caption("One slider moves both charts: the daily RRG on the selected session, and the "
               "weekly RRG as it stood that same day (completed weeks plus the week so far, "
               "using that day's close). On a week's last trading day the weekly dot is that "
               "week's final value. Click the chart and use ← / → to step one session.")

    seg_d = daily.iloc[-win:]
    cycle_section([("Daily", daily), ("Weekly", weekly)])
    both = pd.DataFrame({"Close": seg_d["Close"],
                         "Daily": seg_d["Quadrant"],
                         "D RS-Ratio": seg_d["RS_Ratio"], "D RS-Mom.": seg_d["RS_Momentum"],
                         "Weekly": asof["Quadrant"].reindex(seg_d.index),
                         "W RS-Ratio": asof["RS_Ratio"].reindex(seg_d.index),
                         "W RS-Mom.": asof["RS_Momentum"].reindex(seg_d.index)})

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Look up a date**")
        pick = st.date_input("Date", value=daily.index[-1].date(),
                             min_value=seg_d.index[0].date(), max_value=now.date(),
                             label_visibility="collapsed", key="pick_both")
        hit = both.loc[:pd.Timestamp(pick)]
        day, row = hit.index[-1], hit.iloc[-1]
        note = "" if day.date() == pick else \
            " (no trading on %s; showing the previous session)" % pick.strftime("%d %b %Y")
        st.markdown("**%s**%s" % (day.strftime("%a %d %b %Y"), note))
        for name, q, r, m in (("Daily", row["Daily"], row["D RS-Ratio"], row["D RS-Mom."]),
                              ("Weekly", row["Weekly"], row["W RS-Ratio"], row["W RS-Mom."])):
            st.markdown("%s — <span style='color:%s;font-weight:700'>%s</span>  ·  "
                        "RS-Ratio %.2f  ·  RS-Momentum %.2f"
                        % (name, QUAD_FG[q], q.upper(), r, m), unsafe_allow_html=True)
    with right:
        agree = (both["Daily"] == both["Weekly"]).mean()
        st.markdown("**Sessions per quadrant (last %d sessions)**" % len(both))
        st.dataframe(pd.DataFrame({
            "Quadrant": ORDER,
            "Daily": both["Daily"].value_counts().reindex(ORDER, fill_value=0).to_numpy(),
            "Weekly": both["Weekly"].value_counts().reindex(ORDER, fill_value=0).to_numpy()})
            .style.apply(quad_style, subset=["Quadrant"]), hide_index=True, width="stretch")
        st.caption("Daily and weekly agree on %.0f%% of these sessions." % (100 * agree))

    with st.expander("Every session: daily and weekly quadrant side by side", expanded=False):
        rows = both.iloc[::-1]
        table = rows.reset_index(drop=True)
        table.insert(0, "Date", rows.index.strftime("%a %d %b %Y"))
        st.dataframe(table.style.apply(quad_style, subset=["Daily", "Weekly"])
                     .format({c: "%.2f" for c in table.columns
                              if c not in ("Date", "Daily", "Weekly")}),
                     hide_index=True, width="stretch", height=500)
        st.download_button("Download as CSV", both.to_csv(float_format="%.4f"),
                           file_name="rrg_pvrinox_daily_weekly.csv", mime="text/csv")

    formula_note("daily periods are sessions, weekly periods are weeks")


# ---- strategy: weekly up + daily turns up -> buy; daily turns down -> sell --
def pct(v):
    """Signed percent, without a misleading "-0.0%" for tiny moves."""
    return "%+.1f%%" % v if abs(v) >= 0.05 else "0.0%"


def backtest(daily, asof, start, cost_pct):
    """Runs the rules day by day from `start`, using only what was known that day.

    Buy  : the daily RRG moves from Weakening/Lagging into Improving/Leading, and the
           weekly RRG (as it stood that day, week so far) is Improving/Leading.
    Sell : the daily RRG moves from Improving/Leading into Weakening/Lagging.
    Fills at that day's close; cost_pct is charged on the buy and on the sell."""
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
            trades.append(dict(pos, sell=d, sell_px=close[d], exit_into=q[d], open=False))
            pos = None
    if pos is not None:
        trades.append(dict(pos, sell=None, sell_px=close.iloc[-1], exit_into=None, open=True))

    for t in trades:
        t["ret"] = 100 * ((t["sell_px"] * (1 - c)) / (t["buy_px"] * (1 + c)) - 1)
        end = t["sell"] if t["sell"] is not None else daily.index[-1]
        t["held"] = int(((daily.index > t["buy"]) & (daily.index <= end)).sum())

    # value of 100 invested: follows the stock only while a trade is open
    seg = close[close.index >= start]
    ret = seg.pct_change().fillna(0.0)
    held = pd.Series(False, index=seg.index)
    for t in trades:
        end = t["sell"] if t["sell"] is not None else seg.index[-1]
        held[(seg.index > t["buy"]) & (seg.index <= end)] = True
    factor = 1 + ret.where(held, 0.0)
    for t in trades:
        factor[t["buy"]] *= 1 / (1 + c)
        if t["sell"] is not None:
            factor[t["sell"]] *= 1 - c
    equity = 100 * factor.cumprod()
    hold = 100 * seg / seg.iloc[0]
    return trades, skipped, equity, hold, held


def strategy_figure(daily, trades, equity, hold, start):
    seg = daily[daily.index >= start]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.62, 0.38],
                        vertical_spacing=0.06,
                        subplot_titles=("PVR INOX close — green bands = in a trade",
                                        "Value of ₹100 — strategy vs buying and holding"))
    for t in trades:
        end = t["sell"] if t["sell"] is not None else seg.index[-1]
        # plain shape: add_vrect does not draw on these date subplots
        fig.add_shape(type="rect", xref="x", yref="y domain", x0=t["buy"], x1=end, y0=0, y1=1,
                      fillcolor=QUAD_FG["Leading"], opacity=0.14, line_width=0, layer="below")
    fig.add_trace(go.Scatter(x=seg.index, y=seg["Close"], name="Close", line=dict(color=INK_2, width=1.4),
                             hovertemplate="%{x|%a %d %b %Y}<br>₹%{y:.2f}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=[t["buy"] for t in trades], y=[t["buy_px"] for t in trades], mode="markers", name="Buy",
        marker=dict(symbol="triangle-up", size=13, color=QUAD_FG["Leading"],
                    line=dict(color=SURFACE, width=1)),
        hovertext=["<b>BUY #%d</b> %s<br>₹%.2f<br>weekly %s, daily %s → %s"
                   % (i + 1, t["buy"].strftime("%a %d %b %Y"), t["buy_px"], t["weekly"], t["frm"], t["into"])
                   for i, t in enumerate(trades)], hoverinfo="text"), row=1, col=1)
    sells = [(i, t) for i, t in enumerate(trades) if t["sell"] is not None]
    fig.add_trace(go.Scatter(
        x=[t["sell"] for _, t in sells], y=[t["sell_px"] for _, t in sells], mode="markers", name="Sell",
        marker=dict(symbol="triangle-down", size=13, color=QUAD_FG["Lagging"],
                    line=dict(color=SURFACE, width=1)),
        hovertext=["<b>SELL #%d</b> %s<br>₹%.2f<br>daily → %s<br>trade %+.1f%%"
                   % (i + 1, t["sell"].strftime("%a %d %b %Y"), t["sell_px"], t["exit_into"], t["ret"])
                   for i, t in sells], hoverinfo="text"), row=1, col=1)
    fig.add_trace(go.Scatter(x=equity.index, y=equity, name="Strategy", line=dict(color=SERIES, width=2),
                             hovertemplate="%{x|%d %b %Y}<br>Strategy ₹%{y:.1f}<extra></extra>"), row=2, col=1)
    fig.add_trace(go.Scatter(x=hold.index, y=hold, name="Buy & hold", line=dict(color=INK_3, width=1.5, dash="dot"),
                             hovertemplate="%{x|%d %b %Y}<br>Buy & hold ₹%{y:.1f}<extra></extra>"), row=2, col=1)
    fig.add_hline(y=100, line_color=GRID, line_width=1, row=2, col=1)
    fig.update_layout(height=640, margin=dict(l=65, r=20, t=75, b=10), hovermode="closest",
                      plot_bgcolor=SURFACE, paper_bgcolor=SURFACE, font=dict(color=INK_2),
                      legend=dict(orientation="h", y=0.995, yanchor="top", yref="container",
                                  x=0))
    fig.update_annotations(font=dict(size=13, color=INK_1), x=0, xanchor="left")
    fig.update_xaxes(gridcolor=GRID, dtick="M3", tickformat="%b %Y")
    fig.update_yaxes(gridcolor=GRID)
    return fig


def status_box(color, title, lines):
    st.markdown(
        "<div style='border-left:6px solid %s;background:%s;padding:14px 18px;border-radius:6px'>"
        "<div style='font-size:1.45rem;font-weight:700;color:%s'>%s</div>"
        "<div style='color:%s;margin-top:4px;line-height:1.6'>%s</div></div>"
        % (color, SURFACE if color == INK_3 else color + "14", color, title, INK_1, "<br>".join(lines)),
        unsafe_allow_html=True)


def strategy_page():
    daily, source, fetched = get_rrg("Daily")
    closes, _, _ = get_closes()
    asof = weekly_asof(closes)
    now = datetime.now(IST)
    prov = latest_is_provisional(daily, "Daily", now)
    start = max(pd.Timestamp(bt_from), daily.index[1], asof.index[0])

    header("strategy", source, fetched, now,
           "today's signal is provisional until the 15:30 close" if prov else "signals are final")
    st.caption("**Buy** when the daily RRG moves from Weakening/Lagging into Improving/Leading "
               "while the weekly RRG is in Improving/Leading.  **Sell** when the daily RRG moves "
               "from Improving/Leading into Weakening/Lagging.  Trades at that day's close.")

    trades, skipped, equity, hold, held = backtest(daily, asof, start, cost)
    last_day = daily.index[-1]
    dq, wq = daily["Quadrant"].iloc[-1], asof["Quadrant"].iloc[-1]
    ok = lambda q: "✅" if q in UP else "❌"
    state_lines = ["Weekly now: %s <b style='color:%s'>%s</b>  ·  Daily now: %s <b style='color:%s'>%s</b>"
                   % (ok(wq), QUAD_FG[wq], wq, ok(dq), QUAD_FG[dq], dq)]
    open_t = trades[-1] if trades and trades[-1]["open"] else None
    sold_today = trades and trades[-1]["sell"] == last_day

    if open_t and open_t["buy"] == last_day:
        status_box(QUAD_FG["Leading"], "▲ BUY signal today — %s" % last_day.strftime("%a %d %b %Y"),
                   ["Daily moved %s → %s with weekly in %s. Buy at about ₹%.2f."
                    % (open_t["frm"], open_t["into"], open_t["weekly"], open_t["buy_px"])] + state_lines)
    elif open_t:
        status_box(QUAD_FG["Leading"], "HOLD — in a trade since %s" % open_t["buy"].strftime("%a %d %b %Y"),
                   ["Bought at ₹%.2f, now ₹%.2f (%s, %d sessions)."
                    % (open_t["buy_px"], open_t["sell_px"], pct(open_t["ret"]), open_t["held"]),
                    "Sell when the daily moves into Weakening or Lagging (daily RS-Momentum %.2f, "
                    "sell below 100)." % daily["RS_Momentum"].iloc[-1]] + state_lines)
    elif sold_today:
        t = trades[-1]
        status_box(QUAD_FG["Lagging"], "▼ SELL signal today — %s" % last_day.strftime("%a %d %b %Y"),
                   ["Daily moved into %s. Sell at about ₹%.2f (trade %+.1f%%)."
                    % (t["exit_into"], t["sell_px"], t["ret"])] + state_lines)
    else:
        need = []
        if wq not in UP:
            need.append("the weekly to be in Improving or Leading")
        need.append("the daily to move from Weakening/Lagging into Improving/Leading"
                    if dq not in UP else
                    "the daily to drop into Weakening/Lagging and then turn back up "
                    "(it is already up, so today is not a fresh entry)")
        status_box(INK_3, "WAIT — no position",
                   ["Next buy needs " + " and ".join(need) + "."] + state_lines)

    closed = [t for t in trades if not t["open"]]
    wins = [t for t in closed if t["ret"] > 0]
    strat, bh = equity.iloc[-1] - 100, hold.iloc[-1] - 100
    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Strategy return", "%+.1f%%" % strat, "%+.1f%% vs buy & hold" % (strat - bh))
    c2.metric("Buy & hold return", "%+.1f%%" % bh, "since %s" % start.strftime("%d %b %Y"),
              delta_color="off")
    c3.metric("Trades", "%d closed%s" % (len(closed), " + 1 open" if open_t else ""),
              "%d wins · %.0f%% win rate" % (len(wins), 100 * len(wins) / len(closed)) if closed else "",
              delta_color="off")
    c4.metric("Time in the market", "%.0f%%" % (100 * held.mean()),
              "avg trade %+.1f%% · %.0f sessions" % (
                  sum(t["ret"] for t in closed) / len(closed), sum(t["held"] for t in closed) / len(closed))
              if closed else "", delta_color="off")

    st.plotly_chart(strategy_figure(daily, trades, equity, hold, start), width="stretch", theme=None,
                    config={"displaylogo": False})

    st.subheader("Every trade, oldest first")
    if trades:
        table = pd.DataFrame([{
            "#": i + 1,
            "Buy date": t["buy"].strftime("%a %d %b %Y"),
            "Buy ₹": "%.2f" % t["buy_px"],
            "Weekly at buy": t["weekly"],
            "Daily moved": "%s → %s" % (t["frm"], t["into"]),
            "Sell date": t["sell"].strftime("%a %d %b %Y") if t["sell"] is not None else "open",
            "Sell ₹": ("%.2f" % t["sell_px"]) + ("" if t["sell"] is not None else " (now)"),
            "Daily exit into": t["exit_into"] or "—",
            "Held": "%d sessions" % t["held"],
            "Return": pct(t["ret"]),
        } for i, t in enumerate(trades)])

        def ret_style(col):
            return ["color: %s; font-weight: bold" % (UP_FG if v.startswith("+") else
                                                      DOWN_FG if v.startswith("-") else INK_2)
                    for v in col]
        st.dataframe(table.style.apply(quad_style, subset=["Weekly at buy", "Daily exit into"])
                     .apply(ret_style, subset=["Return"]),
                     hide_index=True, width="stretch", height=38 + 35 * len(table))
        st.download_button("Download trades as CSV", table.to_csv(index=False),
                           file_name="pvrinox_strategy_trades.csv", mime="text/csv")
    else:
        st.info("No trades since %s." % start.strftime("%d %b %Y"))

    with st.expander("Daily turned up but the weekly was down — no buy (%d times)" % len(skipped)):
        if skipped:
            st.dataframe(pd.DataFrame([{"Date": s["date"].strftime("%a %d %b %Y"),
                                        "Daily moved": "%s → %s" % (s["frm"], s["into"]),
                                        "Weekly that day": s["weekly"]} for s in skipped])
                         .style.apply(quad_style, subset=["Weekly that day"]),
                         hide_index=True, width="stretch")

    formula_note("weekly position on each day is the week so far (no look-ahead)  ·  "
                 "cost per side %.2f%%  ·  past results do not guarantee future returns" % cost)


@st.fragment(run_every=refresh_every)
def page():
    if tf == "Strategy":
        strategy_page()
    elif tf == "Both":
        both_page()
    else:
        single_page()


page()
