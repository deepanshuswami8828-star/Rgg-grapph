# Task: turn the PVR INOX RRG app into a multi-stock RRG app

You are working in the folder `C:\Users\Lenovo\Downloads\RRG Graph app` (a git repo).
Work ONLY in this folder. Ignore any copy of `rrg_app.py` in `Downloads\internshipp` — it is old.

## What already exists (read these files first)

- `rrg_app.py` — a Streamlit app (Python 3.12+, Streamlit 1.58, Plotly 6.8, pandas 3, yfinance 1.4).
  Pages chosen in the sidebar: **Daily**, **Weekly**, **Both**, **Strategy**.
- `make_rrg_pvrinox.py` — the RRG formula, imported by the app. Do NOT change the formula:
  - RS = stock close / NIFTY 50 close
  - RS-Ratio = 100 × EMA(SMA(RS,5), 5) / EMA(SMA(RS,5), 30)   (EMAs with `adjust=False`)
  - RS-Momentum = 100 × EMA(RS-Ratio, 3) / EMA(RS-Ratio, 14)
  - Quadrants: Leading (Ratio≥100, Mom≥100), Weakening (≥100, <100), Lagging (<100, <100), Improving (<100, ≥100)
- Data: Yahoo Finance via `yfinance.download(..., period="max", auto_adjust=True)`, daily closes,
  stock `PVRINOX.NS`, benchmark `^NSEI`. The full history is used for the EMAs and the first
  200 daily bars / 100 weekly bars are discarded as warm-up. Weekly bars = last trading day of each
  week (`to_period("W-FRI")`). `weekly_asof()` gives the weekly reading as it stood on each day
  (week so far) — the Both page and the Strategy use it so there is no look-ahead.
- Offline fallback CSVs (used only if Yahoo fails): `pvrinox_ticker_...csv`, `nifty50_dataset_...csv`.
- `Start RRG App.bat` launches it; `.streamlit/config.toml` forces the light theme.

Run the app with `python -m streamlit run rrg_app.py` and look at every page before and after
your changes.

## What to build

### 1. A stock selector
Add a **Stock** selectbox at the top of the sidebar. All four pages (Daily, Weekly, Both, Strategy)
must work for whichever stock is selected, exactly as they work for PVR INOX today.

Stocks (Yahoo tickers, all checked to work):

| Name in the app | Yahoo ticker | Sector label | Data on Yahoo from |
|---|---|---|---|
| PVR INOX | `PVRINOX.NS` | Media & entertainment | long history |
| Bharat Electronics (BEL) | `BEL.NS` | Defence | long history |
| Suzlon Energy | `SUZLON.NS` | Energy – wind | long history |
| Waaree Energies | `WAAREEENER.NS` | Energy – solar | **listed 28 Oct 2024 only** |
| Bharti Airtel | `BHARTIARTL.NS` | Telecom | long history |
| Reliance Industries | `RELIANCE.NS` | Energy / conglomerate | long history |

(If the user wanted BHEL, the power-equipment company, the ticker is `BHEL.NS`.)
Keep the stock list in ONE dict near the top of `rrg_app.py` so more stocks can be added by adding
one line. Benchmark stays NIFTY 50 (`^NSEI`) for every stock. Do not use `^CNXENERGY` (NIFTY Energy):
Yahoo returns only a few days of data for it.

Replace every hard-coded "PVR INOX" text, file name and title with the selected stock's name.

### 2. Clean data from 2023
- Still download the **full** history (`period="max"`) for the calculation — the EMAs need it —
  but show charts, sliders, cycle tables and the strategy **from 1 Jan 2023** by default
  (keep the existing "Slider covers" / "Start date" controls working, default 2023-01-01).
- Cleaning, applied to every stock and to NIFTY 50 before any calculation:
  1. Adjusted closes only (`auto_adjust=True`, so splits/bonuses/dividends are handled —
     e.g. Reliance's 1:1 bonus in Oct 2024 must not show as a 50% crash).
  2. Drop rows with missing, zero or negative prices; drop duplicate dates; sort by date.
  3. Keep only dates where BOTH the stock and NIFTY 50 traded (inner join).
  4. Flag (do not silently delete) any one-day move above ±25 % in a table on the page,
     so the user can see if Yahoo sent a bad price.
- Save each cleaned series as `data/<ticker>_clean.csv` (Date, Close) and use those files as the
  offline fallback for that stock (replace the two PVR-only fallback CSVs with this scheme,
  keeping PVR INOX working offline).

### 3. Short histories (Waaree)
Waaree has about 2 years of data, so:
- Use the same warm-up rule the app already has: discard `min(warmup, len(data)//3)` bars.
- If a stock has fewer than 60 weekly bars after warm-up, show a clear message on the Weekly,
  Both and Strategy pages: "Weekly RRG needs more history — <stock> listed on <date>", and do not
  draw a weekly chart that is mostly warm-up noise. The Daily page must still work.
- Never crash for a stock with short history: test Waaree on every page.

### 4. Optional but wanted: "All stocks" RRG
Add a page **All stocks** that draws one RRG with every stock's trail on it (one colour per stock,
same quadrant background, one shared date slider, daily or weekly toggle), plus a table:
stock, quadrant today (daily and weekly), RS-Ratio, RS-Momentum, days in the current quadrant.

### 5. Keep everything else as it is
Slider-only chart (no play button), chart sized to the window, quadrant colours, the weekly strip
on the Strategy chart (dark green Leading, light green Improving, orange Weakening/Lagging), the
cycle/move tables, the rupee strategy simulator (amount, start date, charges 0.12 % default,
whole shares, "Run strategy" button), the Yahoo retry + fallback warning, caching.

## How to check your work (must pass before you finish)

1. **PVR INOX must not change.** With PVR INOX selected, the values on Fri 16 Oct 2026 must be:
   daily RS-Ratio **108.75**, RS-Momentum **101.71**, Leading; weekly **116.37 / 105.33**, Leading.
   Strategy from 2024-01-01 with ₹1,00,000 and 0.12 %: the first 11 trades must be unchanged,
   from the buy on 24 May 2024 at ₹1339.05 to the buy on 12 Oct 2026 at ₹1401.30
   (later trades may be added as new days arrive).
2. For each new stock, recompute RS-Ratio / RS-Momentum for one date by hand in a separate script
   (plain pandas, not the app's functions) and confirm the app shows the same numbers.
3. Reliance around 28 Oct 2024 must show no fake crash (bonus adjusted).
4. Every page loads with no error for every stock — test with
   `streamlit.testing.v1.AppTest` looping over all stocks × all pages.
5. Turn off the internet (or make `yfinance.download` raise) and confirm every stock still loads
   from `data/<ticker>_clean.csv` with the "saved prices" warning.
6. Update `README.txt` (stock list, data/cleaning rules) and `requirements.txt` if you add a package.
7. Commit to git with a clear message.

Tell me at the end: what you changed, the test results, and anything that did not work.
