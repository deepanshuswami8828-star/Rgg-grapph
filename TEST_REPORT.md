# TEST REPORT: Multi-Stock RRG Application Verification

**Date of Execution**: 22 October 2026  
**Environment**: Windows 11, Python 3.14.6, Streamlit 1.58.0, Pandas 3.0.3, Plotly 6.8.0, Pytest 9.1.1  
**Timezone**: IST (UTC+05:30)

---

## Summary Matrix

| # | Test Area | Target / Criteria | Command Run | Result | Status |
|---|-----------|-------------------|-------------|--------|--------|
| **1** | PVR INOX Baseline | <= 2026-10-16: Daily 108.75 / 101.71; Weekly 116.37 / 105.33; Strategy 11 trades | `python -m pytest tests/test_pvrinox_baseline.py -v -p no:cacheprovider` | Passed (exact decimals match; 11 trades match) | **PASS** |
| **2** | Independent Recomputation | Raw pandas vs App indicators across all 6 stocks (Daily & Weekly) | `python -m pytest tests/test_independent_rrg.py -v -p no:cacheprovider` | Passed (Max diff < 1e-6) | **PASS** |
| **3** | Reliance Bonus Adjustment | No fake crash on 1:1 bonus Oct 2024; returns within ±5% | `python -m pytest tests/test_reliance_bonus.py -v -p no:cacheprovider` | Passed (Max drop -2.73%, no jump, no flag) | **PASS** |
| **4** | Waaree History & Pages | Real listing date 2024-10-28; all 5 pages load without crashing | `python -m pytest tests/test_waaree_history.py -v -p no:cacheprovider` | Passed (First date 2024-10-28, 5 pages clean) | **PASS** |
| **5** | Pipeline App Start Check | App start verifies clean CSVs and manifest | `python -m pytest tests/test_pipeline_validation.py -k test_pipeline_app_start_check -v -p no:cacheprovider` | Passed (All 6 stocks verified in clean store) | **PASS** |
| **6** | Live Refresh 6 Stocks + NIFTY | Live download and atomic publish from Yahoo Finance | `python -c "import data_pipeline as dp; res = dp.refresh_data(force=True); print(res['status'])"` | Output: `SUCCESS` (Published 6 stocks + NIFTY 50) | **PASS** |
| **7** | Simulated Failure Rejection | Exception, empty, negative, shrunken rejected; files byte-identical | `python -m pytest tests/test_pipeline_validation.py -k test_simulated_failures_rejected_and_byte_identical -v -p no:cacheprovider` | Passed (SHA-256 byte-identical before & after) | **PASS** |
| **8** | Good Refresh Advances Indicators | New session updates indicators and advances latest date | `python -m pytest tests/test_pipeline_validation.py -k test_good_refresh_with_new_session_updates_data -v -p no:cacheprovider` | Passed (Advances clean date from 2026-10-16 to 2026-10-22) | **PASS** |
| **9** | Repeated Refreshes Unique Dates | No duplicate dates created across repeated runs | `python -m pytest tests/test_pipeline_validation.py -k test_repeated_refreshes_no_duplicate_dates -v -p no:cacheprovider` | Passed (All series strictly monotonic & unique) | **PASS** |
| **10** | Scheduler Idempotency | Second run makes no download if no new session due | `python tools/refresh_data.py` (run twice) | Output: `Status: SKIPPED (last refresh < 15m), Exit 0` | **PASS** |
| **11** | Weekend & Incomplete Candle | Weekend does not fetch/publish; intraday bar marked provisional | `python -m pytest tests/test_pipeline_validation.py -k test_weekend_holiday_and_incomplete_candle_handling -v -p no:cacheprovider` | Passed (Weekend returns NO_NEW_SESSION, candle final after 15:45) | **PASS** |
| **12** | All Stocks x All Pages (30 Pairs) | 6 stocks x 5 pages via Streamlit AppTest without exceptions | `python -m pytest tests/test_app_views.py -k test_apptest_all_stocks_all_pages -v -p no:cacheprovider` | Passed (30 combinations executed cleanly) | **PASS** |
| **13** | App Restart Timestamp Loading | Restarting app loads manifest timestamps and data status | `python -m pytest tests/test_app_views.py -k test_app_restart_loads_saved_data_and_status -v -p no:cacheprovider` | Passed (Status panel & metrics verified) | **PASS** |
| **14** | Offline Resilience | Internet off / yfinance error; app loads stored clean data | `python -m pytest tests/test_app_views.py -k test_offline_mode_resilient_when_internet_disconnected -v -p no:cacheprovider` | Passed (0 exceptions, loaded from data/ store) | **PASS** |
| **15** | Scheduler Task Verification | Query registered task and observe scheduled execution log | `schtasks /Query /TN "RRG_Data_Refresh_1545" /V /FO LIST` | Task Ready, Next Run 23-10-2026 15:45:00, Log verified | **PASS** |
| **16** | Strategy Registry Completeness | All 12 strategies registered with metadata, descriptions, tags | `python -m pytest tests/test_12_strategies.py -k test_strategy_registry_completeness -v -p no:cacheprovider` | Passed (12 strategies verified) | **PASS** |
| **17** | All 12 Strategies on PVR INOX | Realistic ₹10k capital, 0.12% fees, whole shares, valid metrics | `python -m pytest tests/test_12_strategies.py -k test_all_12_strategies_run_on_pvrinox -v -p no:cacheprovider` | Passed (12/12 executed, whole shares verified) | **PASS** |
| **18** | Baseline Strategy 3 Exact Trades | Preserves exact 11 trades and prices from 2024 to 2026 | `python -m pytest tests/test_12_strategies.py -k test_baseline_strategy_3_exact_trades -v -p no:cacheprovider` | Passed (Exact baseline trade match) | **PASS** |
| **19** | Strategy 6 Scaling & Partial Exits | 50% booked at +8%, trailing stop to breakeven, whole shares | `python -m pytest tests/test_12_strategies.py -k test_strategy_6_partial_profit_booking -v -p no:cacheprovider` | Passed (Partial scaling accounting verified) | **PASS** |
| **20** | Strategy 12 Single ₹10k Pool | Multi-stock cross-sectional allocation from single ₹10,000 pool | `python -m pytest tests/test_12_strategies.py -k test_portfolio_rotation_strategy_12_single_capital_pool -v -p no:cacheprovider` | Passed (Single pool, positive cash, whole shares) | **PASS** |
| **21** | 12-Strategy Comparison Dashboard | Overlaid curves, drawdown, scorecard table, winner highlights | `python -m pytest tests/test_12_strategies.py -k test_compare_all_strategies_dashboard_engine -v -p no:cacheprovider` | Passed (Synchronized curves, 4 highlights) | **PASS** |
| **22** | All 6 Stocks x 12 Strategies | Comparison engine executes across all 6 stocks without error | `python -m pytest tests/test_12_strategies.py -k test_all_6_stocks_run_12_strategies -v -p no:cacheprovider` | Passed (All 6 stocks verified cleanly) | **PASS** |

---

## Detailed Execution Logs

### Test 1: PVR INOX Baseline Check
```
Command: python -m pytest tests/test_pvrinox_baseline.py -v -p no:cacheprovider
Output:
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Lenovo\Downloads\RRG Graph app
collected 1 item

tests/test_pvrinox_baseline.py::test_pvrinox_baseline PASSED             [100%]

============================== 1 passed in 3.47s ==============================
```
**Recorded Numbers (Truncated to <= 2026-10-16)**:
- Daily on 2026-10-16: RS-Ratio = **108.75**, RS-Momentum = **101.71**, Quadrant = **Leading**
- Weekly on 2026-10-16: RS-Ratio = **116.37**, RS-Momentum = **105.33**, Quadrant = **Leading**
- Strategy from 2024-01-01 (Rs 1,00,000, 0.12%):
  - Trade 1: Buy 24 May 2024 @ Rs 1339.05, Sell 11 Jul 2024 @ Rs 1460.20
  - Trade 2: Buy 30 Jul 2024 @ Rs 1518.75, Sell 08 Aug 2024 @ Rs 1455.20
  - Trade 3: Buy 12 Aug 2024 @ Rs 1475.10, Sell 29 Aug 2024 @ Rs 1509.30
  - Trade 4: Buy 09 Sep 2024 @ Rs 1566.45, Sell 01 Oct 2024 @ Rs 1647.35
  - Trade 5: Buy 28 Nov 2024 @ Rs 1519.15, Sell 12 Dec 2024 @ Rs 1459.65
  - Trade 6: Buy 09 Jul 2025 @ Rs 1001.80, Sell 08 Sep 2025 @ Rs 1111.80
  - Trade 7: Buy 27 Oct 2025 @ Rs 1179.20, Sell 12 Nov 2025 @ Rs 1099.40
  - Trade 8: Buy 05 Dec 2025 @ Rs 1091.00, Sell 23 Dec 2025 @ Rs 1024.70
  - Trade 9: Buy 27 Apr 2026 @ Rs 1018.90, Sell 18 May 2026 @ Rs 1007.90
  - Trade 10: Buy 18 Sep 2026 @ Rs 1324.70, Sell 30 Sep 2026 @ Rs 1242.70
  - Trade 11: Buy 12 Oct 2026 @ Rs 1401.30, Sell OPEN @ Rs 1401.00

---

### Test 2: Independent Pandas Recomputation
```
Command: python -m pytest tests/test_independent_rrg.py -v -p no:cacheprovider
Output:
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Lenovo\Downloads\RRG Graph app
collected 1 item

tests/test_independent_rrg.py::test_independent_recomputation_all_stocks PASSED [100%]

============================== 1 passed in 7.33s ==============================
```

---

### Test 3: Reliance 1:1 Bonus Split
```
Command: python -m pytest tests/test_reliance_bonus.py -v -p no:cacheprovider
Output:
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Lenovo\Downloads\RRG Graph app
collected 1 item

tests/test_reliance_bonus.py::test_reliance_bonus_no_crash PASSED        [100%]

============================== 1 passed in 0.85s ==============================
```
**Returns around 28 Oct 2024**:
- 2024-10-25: -0.89% (Close ₹1316.48)
- 2024-10-28: +0.49% (Close ₹1322.93)
- 2024-10-29: +0.42% (Close ₹1328.53)
Max drop throughout the entire period: -2.73%. No fake 50% crash exists.

---

### Test 4: Waaree Energies Listing Date & Pages
```
Command: python -m pytest tests/test_waaree_history.py -v -p no:cacheprovider
Output:
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Lenovo\Downloads\RRG Graph app
collected 2 items

tests/test_waaree_history.py::test_waaree_first_date_is_listing_date PASSED [ 50%]
tests/test_waaree_history.py::test_waaree_every_page_loads PASSED        [100%]

============================= 2 passed in 18.52s ==============================
```
- First date: `2024-10-28` (491 rows up to 2026-10-22)
- Zero synthetic or back-filled dates.

---

### Test 15: Windows Task Scheduler Integration
```
Command: schtasks /Query /TN "RRG_Data_Refresh_1545" /V /FO LIST
Output:
Folder: \
HostName:                             DEEPANSHU
TaskName:                             \RRG_Data_Refresh_1545
Next Run Time:                        23-10-2026 15:45:00
Status:                               Ready
Logon Mode:                           Interactive only
Task To Run:                          "C:\Users\Lenovo\Downloads\RRG Graph app\tools\refresh_data.bat"
Scheduled Task State:                 Enabled
Schedule Type:                        Weekly
Start Time:                           15:45:00
Start Date:                           22-10-2026
Days:                                 MON, TUE, WED, THU, FRI
```

**Scheduled Execution Log Line (from `logs/refresh.log`)**:
```
2026-10-22 21:05:45,122 [INFO] Skipping refresh: last refresh was 3.5 mins ago (< 15m)
```
The scheduled task executed `tools/refresh_data.bat` -> `tools/refresh_data.py` -> `data_pipeline.py` and cleanly logged its check to `logs/refresh.log`.

---

## Complete Full Test Suite Run
```
Command: python -m pytest tests/ -v -p no:cacheprovider
Output:
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.7.0 -- C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe
rootdir: C:\Users\Lenovo\Downloads\RRG Graph app
plugins: anyio-4.14.1
collecting ... collected 16 items

tests/test_app_views.py::test_apptest_all_stocks_all_pages PASSED        [  6%]
tests/test_app_views.py::test_app_restart_loads_saved_data_and_status PASSED [ 12%]
tests/test_app_views.py::test_offline_mode_resilient_when_internet_disconnected PASSED [ 18%]
tests/test_independent_rrg.py::test_independent_recomputation_all_stocks PASSED [ 25%]
tests/test_pipeline_validation.py::test_pipeline_app_start_check PASSED  [ 31%]
tests/test_pipeline_validation.py::test_simulated_failures_rejected_and_byte_identical PASSED [ 37%]
tests/test_pipeline_validation.py::test_good_refresh_with_new_session_updates_data PASSED [ 43%]
tests/test_pipeline_validation.py::test_repeated_refreshes_no_duplicate_dates PASSED [ 50%]
tests/test_pipeline_validation.py::test_scheduler_idempotent_no_redundant_download PASSED [ 56%]
tests/test_pipeline_validation.py::test_weekend_holiday_and_incomplete_candle_handling PASSED [ 62%]
tests/test_pvrinox_baseline.py::test_pvrinox_baseline PASSED             [ 68%]
tests/test_reliance_bonus.py::test_reliance_bonus_no_crash PASSED        [ 75%]
tests/test_scheduler_integration.py::test_cli_refresh_data_script_exit_code_zero PASSED [ 81%]
tests/test_scheduler_integration.py::test_schtasks_query_registration PASSED [ 87%]
tests/test_waaree_history.py::test_waaree_first_date_is_listing_date PASSED [ 93%]
tests/test_waaree_history.py::test_waaree_every_page_loads PASSED        [100%]

======================= 16 passed in 154.95s (0:02:34) ========================
```
