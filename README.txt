Multi-Stock Relative Rotation Graph (RRG) App
NSE Stocks against NIFTY 50 (^NSEI) — Daily, Weekly, Both, All Stocks, Strategy
================================================================================

1. START THE APP
----------------
- Double-click "Start RRG App.bat" (or run in terminal: streamlit run rrg_app.py).
- The app opens in your browser at http://localhost:8501.
- NOTE: The app runs completely standalone. It performs in-app validation, auto-refresh,
  and local cached fallbacks. Windows Task Scheduler is completely optional.

2. CONFIGURED STOCKS
--------------------
All stocks are benchmarked against ^NSEI (NIFTY 50):
  - PVR INOX (PVRINOX.NS)              · Media & entertainment (long history)
  - Bharat Electronics (BEL.NS)        · Defence (long history)
  - Suzlon Energy (SUZLON.NS)          · Energy - wind (long history)
  - Waaree Energies (WAAREEENER.NS)    · Energy - solar (listed 28 Oct 2024; genuine listing date)
  - Bharti Airtel (BHARTIARTL.NS)      · Telecom (long history)
  - Reliance Industries (RELIANCE.NS)  · Energy / conglomerate (1:1 bonus Oct 2024 auto-adjusted)

Adding a new stock:
  Add one line to the STOCKS dictionary in config.py. The pipeline and UI will
  automatically include it in downloads, validation, selectors, and All-Stocks views.

3. DATA & VALIDATION ARCHITECTURE
---------------------------------
Data pipeline (data_pipeline.py) operates with zero Streamlit dependencies:
  - Download: Yahoo Finance (yfinance) auto-adjusted daily closes, max history.
  - Cleaning: Timezone-naive dates, drops non-positive/NaN values, filters weekend dates,
    removes duplicate dates keeping the last.
  - Alignment: Strict inner join between stock and NIFTY 50 on dates where both traded.
    No forward-fill, no back-fill, no interpolation anywhere.
  - Storage:
      data/<ticker>_clean.csv    · Verified clean prices (completed sessions only)
      data/NSEI_clean.csv        · Verified clean NIFTY 50 benchmark prices
      data/backup/               · Rotated backup copy of previous valid CSVs
      data/manifest.json         · Dataset version ID, rows, dates, SHA-256 hashes, warnings
      data/provisional/          · Intraday/partial bars during market hours (never in clean CSVs)
      logs/refresh.log           · Rotating log file tracking syncs, retries, and errors
  - Validation Rules before publication:
      1. Schema integrity (DatetimeIndex, positive numeric prices).
      2. No price shrinkage below stored historical length.
      3. Dates monotonic, no weekend dates, latest date not in future.
      4. Overlapping history adjustment check (detects splits vs discontinuities).
      5. Flagging suspicious one-day price moves (> ±25%).
      6. NIFTY gate: All stocks and benchmark must pass validation; if benchmark fails,
         no files are published and previous valid files remain untouched.
      7. Atomic write: Writes to temp files, validates, then uses atomic os.replace.
      8. File locking: data/.refresh.lock prevents concurrent write conflicts.

4. AUTOMATIC REFRESH
--------------------
In-App (Streamlit):
  - On app start, reads manifest and clean CSVs.
  - Checks if a new completed session is due (past 15:45 IST on weekdays).
  - Skips redundant downloads if data is already up to date or checked within 15 minutes.
  - "Refresh All Data" button in sidebar forces an immediate re-download and validation.
  - During market hours (09:15-15:30 IST), partial bars are flagged as PROVISIONAL.
    Final daily bars are published only after market close buffer (15:45 IST).

Unattended Scheduled Refresh (Windows Task Scheduler):
  - tools/refresh_data.py is an idempotent CLI script that calls data_pipeline directly.
  - tools/refresh_data.bat wraps the Python execution and forwards exit codes.
  - tools/install_scheduler.bat registers 4 weekday tasks (Mon-Fri) via schtasks:
      * 15:45 IST (Market close + 15 min buffer)
      * 16:15 IST (Retry 1)
      * 17:00 IST (Retry 2)
      * 18:30 IST (Retry 3)
  - To verify scheduled tasks:
      schtasks /Query /TN "RRG_Data_Refresh_1545" /V /FO LIST
  - To uninstall scheduled tasks:
      tools\uninstall_scheduler.bat
  - Timezone note: If your PC is outside IST (UTC+05:30), edit the /ST parameters in
    tools/install_scheduler.bat to match your local equivalent time.

5. DATA STATUS PANEL
--------------------
Located at the top of the app in an expandable section:
  - Ticker, Sector, and Benchmark identifier.
  - Last Valid Sync timestamp (IST) and Data Provider.
  - Last Attempt Result (SUCCESS / NO_NEW_SESSION / FAILED).
  - Status Badges:
      * LIVE: Current day post-close completed data.
      * CACHED: Valid stored data within expected refresh interval.
      * OFFLINE / STALE: Displayed with warning when network is down or data is older
        than the latest completed trading session.
  - Flagged moves table showing dates with price movements exceeding ±25%.
  - Full table showing coverage (first date, latest date, row count) for all stocks.

6. RRG FORMULA (Calibrated JdK RRG Method)
------------------------------------------
  - RS = Stock Close / NIFTY 50 Close
  - RS-Ratio = 100 × EMA(SMA(RS, 5), 5) / EMA(SMA(RS, 5), 30)   (adjust=False)
  - RS-Momentum = 100 × EMA(RS-Ratio, 3) / EMA(RS-Ratio, 14)     (adjust=False)
  - Quadrants:
      * Leading:   RS-Ratio >= 100 and RS-Momentum >= 100
      * Weakening: RS-Ratio >= 100 and RS-Momentum < 100
      * Lagging:   RS-Ratio < 100 and RS-Momentum < 100
      * Improving: RS-Ratio < 100 and RS-Momentum >= 100
  - Weekly RRG: Uses last trading day of each week (to_period("W-FRI")).
  - Weekly As-Of: Computes weekly reading day-by-day with zero look-ahead.

7. SHORT HISTORIES & WAAREE ENERGIES
------------------------------------
  - For stocks with shorter histories (Waaree Energies listed on 28 Oct 2024), warmup
    uses min(warmup, len // 3).
  - If weekly history has fewer than 60 weekly bars, Weekly, Both, and Strategy display
    a clear notice: "Weekly RRG needs more history - <stock> listed on <date>".
  - Daily RRG continues to operate fully. No page crashes.

8. THE 12 RRG TRADING STRATEGIES & COMPARISON DASHBOARD
---------------------------------------------------------
The app features 12 comprehensive RRG trading strategies, real historical backtesting
with default ₹10,000 starting capital, whole-share enforcement, 0.12% charges/taxes
per side, daily mark-to-market portfolio accounting, and zero lookahead bias:

  1. Basic Quadrant Rotation Strategy:
     - Single-timeframe rotation (Daily). Buys on entry into Improving/Leading; exits on Weakening/Lagging.
  2. Leading Profit Booking Strategy:
     - Enters on Leading. Exits on profit target (+8%), trailing stop (5% from peak), or Weakening.
  3. Daily + Weekly Confirmation Strategy (Baseline):
     - BUY when BOTH Daily and Weekly are Improving/Leading; SELL when EITHER enters Weakening/Lagging.
     - One position at a time; re-entry only when both qualify again. Weekly = as-of reading (no look-ahead).
     - PVR INOX baseline (data to 16 Oct 2026, Rs 1,00,000 from 1 Jan 2024): 14 trades, first buy
       24 May 2024 (Rs 1339.05), open position from 12 Oct 2026 (Rs 1401.30). Tests: tests/test_strategy_3_rules.py
  4. Early Rotation Catcher (Lagging to Improving):
     - Early bottoming rotation: Buys on Lagging-to-Improving with RS-Mom >= 100 & price recovery. 5% stop-loss.
  5. Leading-Only Momentum Strategy:
     - Trend-following confluence: Daily Leading + Weekly Leading + Close > 50-day SMA.
  6. Partial Profit Booking Strategy:
     - Scales out: Sells 50% at +8% profit target; trails remainder to breakeven stop or RRG exit.
  7. Improving-to-Leading Crossover Strategy:
     - Classic sweet spot: Buys at the exact vertical boundary crossing (RS-Ratio >= 100 with RS-Mom >= 100).
  8. Leading Pullback Entry Strategy:
     - Buy the dip: Weekly Leading primary trend; buys when temporary Daily pullback turns back up.
  9. Weakening Early Exit Strategy:
     - Capital preservation: Exits on the very first session Daily enters Weakening without waiting for Lagging.
  10. Price + RRG Confirmation Strategy:
     - Triple confluence: Daily+Weekly RRG UP + Close > 50-SMA + 20-day SMA sloping upward.
  11. RS-Momentum Reversal Strategy:
     - Pure oscillator: Buys when RS-Momentum crosses above 100; exits when it crosses below 100.
  12. Portfolio Rotation Strategy (Multi-Stock):
     - Cross-sectional allocation across all 6 stocks from a single ₹10,000 capital pool.
     - Ranks all stocks daily by relative strength; dynamically rotates into leaders and out of laggards.

Strategy View Modes:
  - Single Strategy View: Deep dive into any selected strategy with live signals (BUY/HOLD/SELL/WAIT),
    key metrics, interactive 3-row charts, and complete trade ledger with CSV export.
  - Strategy Comparison Dashboard: Overlaid equity curves, drawdown curves, sortable scorecard table,
    and winner callouts (Highest Return, Lowest Drawdown, Best Risk-Adjusted, Highest Win Rate).
  - Portfolio Rotation View: Dedicated Strategy 12 multi-stock tracker with current allocations,
    equity vs NIFTY 50, and full multi-stock transaction log.

9. AUTOMATED TESTING
--------------------
Run test suite:
  python -m pytest tests/ -v -p no:cacheprovider

Test coverage (23 automated tests):
  - tests/test_12_strategies.py           · 7 tests: all 12 strategies, ₹10k execution, whole shares,
                                            PVR INOX baseline, Strategy 6 scaling, Strategy 12 portfolio,
                                            and multi-stock comparison engine across all 6 stocks.
  - tests/test_pvrinox_baseline.py        · Baseline regression checks (108.75/101.71, 11 trades)
  - tests/test_independent_rrg.py         · Independent pandas formula verification (1e-6 tol)
  - tests/test_reliance_bonus.py          · Reliance 1:1 bonus split sanity check (no fake crash)
  - tests/test_waaree_history.py          · Waaree listing date and graceful weekly handling
  - tests/test_pipeline_validation.py     · Failure rejection, byte-identical backup, idempotency
  - tests/test_app_views.py               · 30 combinations (6 stocks x 5 pages) via AppTest
  - tests/test_scheduler_integration.py   · CLI runner exit codes and schtasks registration

10. KNOWN LIMITATIONS
---------------------
  - Yahoo Finance quotes may occasionally lag exchange trading by 5 to 15 minutes.
  - Historical prices retroactively adjust on corporate actions (dividends/splits);
    the pipeline detects and records these re-adjustments in manifest warnings.
  - Task Scheduler requires user account permissions to register tasks on Windows.

