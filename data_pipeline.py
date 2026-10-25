"""
Data Pipeline for Multi-Stock RRG Application.
Zero Streamlit imports. Handles download, strict validation, atomic storage,
backup rotation, manifest updates, and file locking.
"""
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import shutil
import tempfile
import time as pytime
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

from config import (
    DATA_DIR, BACKUP_DIR, PROVISIONAL_DIR, LOGS_DIR, MANIFEST_PATH,
    REFRESH_LOG_PATH, LOCK_FILE_PATH, IST, BENCHMARK_TICKER, BENCHMARK_NAME,
    STOCKS, MARKET_OPEN_IST, MARKET_CLOSE_IST, REFRESH_AFTER_CLOSE_IST,
    MIN_REFRESH_INTERVAL_MINUTES, SUSPICIOUS_MOVE_PCT, MIN_HISTORY_ROWS,
    PROVIDER, get_clean_csv_path, sanitize_ticker
)

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(PROVISIONAL_DIR, exist_ok=True)

logger = logging.getLogger("rrg_data_pipeline")
logger.setLevel(logging.INFO)
if not logger.handlers:
    rf_handler = RotatingFileHandler(
        REFRESH_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    rf_handler.setFormatter(formatter)
    logger.addHandler(rf_handler)


class FileLock:
    """File lock to prevent concurrent refresh processes."""
    def __init__(self, lock_path: str = LOCK_FILE_PATH, timeout_sec: float = 15.0):
        self.lock_path = lock_path
        self.timeout_sec = timeout_sec
        self.acquired = False

    def __enter__(self):
        start_time = pytime.time()
        while pytime.time() - start_time < self.timeout_sec:
            try:
                self.fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self.fd, str(os.getpid()).encode("utf-8"))
                self.acquired = True
                return self
            except FileExistsError:
                pytime.sleep(0.2)
        # Check for stale lock (> 2 mins old)
        try:
            mtime = os.path.getmtime(self.lock_path)
            if pytime.time() - mtime > 120:
                logger.warning("Breaking stale lock file %s", self.lock_path)
                os.remove(self.lock_path)
                return self.__enter__()
        except Exception:
            pass
        raise TimeoutError(f"Could not acquire file lock on {self.lock_path}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            try:
                os.close(self.fd)
                if os.path.exists(self.lock_path):
                    os.remove(self.lock_path)
            except Exception as e:
                logger.error("Error releasing lock: %s", e)
            self.acquired = False


def calculate_sha256(filepath: str) -> str:
    """Calculates SHA-256 hash of a file."""
    if not os.path.exists(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_manifest() -> dict:
    """Loads manifest.json or returns default empty manifest structure."""
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to parse manifest: %s", e)
    return {
        "version_id": "none",
        "updated_at": None,
        "status": "INITIAL",
        "provider": PROVIDER,
        "tickers": {},
        "last_attempt": {
            "time": None,
            "result": "NONE",
            "message": "No refresh attempt recorded yet"
        }
    }


def save_manifest(manifest: dict) -> None:
    """Atomically writes manifest.json via temp file."""
    temp_dir = os.path.dirname(MANIFEST_PATH)
    with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
        json.dump(manifest, tf, indent=2)
        temp_name = tf.name
    os.replace(temp_name, MANIFEST_PATH)


def load_clean_data(ticker: str) -> Optional[pd.DataFrame]:
    """Loads <ticker>_clean.csv as a DataFrame with DatetimeIndex and Close column."""
    csv_path = get_clean_csv_path(ticker)
    if not os.path.exists(csv_path):
        return None
    try:
        df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
        df.index = pd.to_datetime(df.index).tz_localize(None)
        if "Close" not in df.columns:
            return None
        return df[["Close"]].sort_index()
    except Exception as e:
        logger.error("Error loading clean CSV for %s: %s", ticker, e)
        return None


def clean_price_series(series: pd.Series, ticker: str) -> pd.Series:
    """
    Cleans raw price series:
    - timezone-naive DatetimeIndex
    - drop NaNs, non-finite, and prices <= 0
    - filter weekend dates (weekdays 0-4 only)
    - deduplicate dates (keep last)
    - sort ascending
    """
    s = series.copy()
    if s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    s = s.dropna()
    s = s[pd.to_numeric(s, errors="coerce").notnull()]
    s = s.astype(float)
    s = s[s > 0.0]
    # Filter weekend dates
    s = s[s.index.weekday < 5]
    # Remove duplicate dates keeping the last entry
    s = s[~s.index.duplicated(keep="last")]
    s = s.sort_index()
    s.name = "Close"
    return s


def validate_series(
    ticker: str,
    new_s: pd.Series,
    stored_s: Optional[pd.Series],
    is_benchmark: bool = False
) -> Tuple[bool, List[str], List[dict]]:
    """
    Executes validation checks:
    1. Schema: DatetimeIndex, numeric prices
    2. Minimum rows, no non-positive prices
    3. Monotonic dates, no weekend dates
    4. Row count cannot shrink below stored count
    5. Latest date cannot be older than stored latest date or in the future
    6. Overlapping history adjustment check
    7. Flag moves > +/-25%
    Returns: (is_valid, warnings, flagged_moves)
    """
    warnings: List[str] = []
    flagged_moves: List[dict] = []

    # Check 1: DatetimeIndex and not empty
    if not isinstance(new_s.index, pd.DatetimeIndex) or len(new_s) == 0:
        return False, ["Invalid schema or empty series"], []

    # Check 2: Minimum history
    min_rows = MIN_HISTORY_ROWS if not is_benchmark else 100
    if len(new_s) < min_rows:
        return False, [f"History length {len(new_s)} below minimum threshold {min_rows}"], []

    # Check 3: Check for non-positive or non-finite prices
    if (new_s <= 0).any() or new_s.isna().any():
        return False, ["Non-positive or NaN prices detected"], []

    # Check 4: Monotonic index
    if not new_s.index.is_monotonic_increasing:
        return False, ["Date index is not monotonically increasing"], []

    # Check 5: No weekend dates
    weekend_mask = new_s.index.weekday >= 5
    if weekend_mask.any():
        weekend_dates = new_s.index[weekend_mask].strftime("%Y-%m-%d").tolist()
        return False, [f"Weekend dates detected: {weekend_dates}"], []

    now_ist = datetime.now(IST)
    today_date = now_ist.date()

    # Check 6: Latest date cannot be in future
    if new_s.index[-1].date() > today_date:
        return False, [f"Latest date {new_s.index[-1].date()} is in the future"], []

    # Check 7: History must not shrink compared to stored version
    if stored_s is not None and len(stored_s) > 0:
        if len(new_s) < len(stored_s):
            return False, [f"Series row count shrunk: new={len(new_s)}, stored={len(stored_s)}"], []
        if new_s.index[-1] < stored_s.index[-1]:
            return False, [f"Latest date regressed: new={new_s.index[-1]}, stored={stored_s.index[-1]}"], []

        # Check 8: Overlapping history adjustment check
        overlap_dates = new_s.index.intersection(stored_s.index)
        if len(overlap_dates) > 10:
            ratio = (new_s.loc[overlap_dates] / stored_s.loc[overlap_dates]).dropna()
            ratio_std = ratio.std()
            ratio_mean = ratio.mean()
            if ratio_std < 1e-4 and abs(ratio_mean - 1.0) > 1e-4:
                warnings.append(
                    f"Harmless historical price adjustment detected (factor {ratio_mean:.4f})"
                )
            elif ratio_std >= 0.05:
                warnings.append(
                    f"Non-uniform historical price shift detected (std={ratio_std:.4f})"
                )

    # Check 9: Flag moves > +/-25%
    pct_changes = new_s.pct_change() * 100.0
    large_moves = pct_changes[pct_changes.abs() >= SUSPICIOUS_MOVE_PCT]
    for d, pct_val in large_moves.items():
        flagged_moves.append({
            "date": d.strftime("%Y-%m-%d"),
            "pct_change": round(float(pct_val), 2),
            "close": round(float(new_s[d]), 2)
        })
        warnings.append(f"Flagged move of {pct_val:+.1f}% on {d.strftime('%Y-%m-%d')}")

    return True, warnings, flagged_moves


def is_market_open(now_dt: datetime) -> bool:
    """True if currently during NSE trading hours (Mon-Fri 09:15-15:30 IST)."""
    return now_dt.weekday() < 5 and (MARKET_OPEN_IST <= now_dt.time() <= MARKET_CLOSE_IST)


def is_session_final(candle_date: date, now_dt: datetime) -> bool:
    """
    A bar is final only if fetched after 15:45 IST on its own date, or on a later date.
    """
    if candle_date < now_dt.date():
        return True
    if candle_date == now_dt.date() and now_dt.time() >= REFRESH_AFTER_CLOSE_IST:
        return True
    return False


def get_expected_latest_session(now_dt: datetime) -> date:
    """
    Returns the expected latest completed session date.
    If today is Mon-Fri and time >= 15:45 IST, today is candidate.
    Otherwise, the last weekday prior to today.
    """
    current_date = now_dt.date()
    if now_dt.weekday() < 5 and now_dt.time() >= REFRESH_AFTER_CLOSE_IST:
        return current_date
    d = current_date - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def align_stock_with_benchmark(
    stock_df: pd.DataFrame,
    bench_df: pd.DataFrame,
    stock_name: str,
    bench_name: str = BENCHMARK_NAME
) -> pd.DataFrame:
    """
    Strict INNER JOIN between stock and benchmark on Date.
    No forward fill, no back fill, no interpolation anywhere.
    """
    aligned = pd.concat([
        stock_df["Close"].rename(stock_name),
        bench_df["Close"].rename(bench_name)
    ], axis=1, join="inner").dropna()
    aligned = aligned.sort_index()
    return aligned


def fetch_ticker_series(ticker: str, retries: int = 3, backoff: float = 2.0) -> pd.Series:
    """Fetches full historical daily series for a single ticker with retries."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            raw = yf.download(
                ticker,
                period="max",
                interval="1d",
                auto_adjust=True,
                progress=False
            )
            if raw is not None and not raw.empty and "Close" in raw:
                close_obj = raw["Close"]
                if isinstance(close_obj, pd.DataFrame):
                    s = close_obj.iloc[:, 0]
                else:
                    s = close_obj
                cleaned = clean_price_series(s, ticker)
                if len(cleaned) > 0:
                    return cleaned
        except Exception as e:
            last_err = e
            logger.warning("Download error for %s (attempt %d/%d): %s", ticker, attempt, retries, e)
        if attempt < retries:
            pytime.sleep(backoff * attempt)
    raise ValueError(f"Failed downloading {ticker}: {last_err}")


# ---- Daily highs (used by take-profit analysis) -------------------------------
# Kept apart from the verified close files so the close pipeline, its manifest and checks stay unchanged.
HIGHS_DIR = os.path.join(DATA_DIR, "highs")


def get_high_csv_path(ticker: str) -> str:
    return os.path.join(HIGHS_DIR, f"{sanitize_ticker(ticker)}_high.csv")


def load_high_data(ticker: str) -> Optional[pd.Series]:
    """Daily high (same Yahoo adjustment as the close files) as a Series, or None if not stored."""
    path = get_high_csv_path(ticker)
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df["High"].sort_index()
    except Exception as e:
        logger.error("Error loading highs for %s: %s", ticker, e)
        return None


def refresh_highs(tickers=None, retries: int = 3, backoff: float = 2.0) -> Dict[str, str]:
    """Download and store daily highs for every stock (auto-adjusted like the close files). Returns status per ticker."""
    os.makedirs(HIGHS_DIR, exist_ok=True)
    status = {}
    for ticker in (tickers or list(STOCKS.keys())):
        for attempt in range(1, retries + 1):
            try:
                raw = yf.download(ticker, period="max", interval="1d", auto_adjust=True, progress=False)
                high = raw["High"]
                high = high.iloc[:, 0] if isinstance(high, pd.DataFrame) else high
                s = clean_price_series(high, ticker).rename("High")
                if len(s) == 0:
                    raise ValueError("no highs")
                s.to_csv(get_high_csv_path(ticker), index_label="Date", date_format="%Y-%m-%d")
                status[ticker] = f"OK {len(s)} rows"
                break
            except Exception as e:
                status[ticker] = f"FAILED: {e}"
                if attempt < retries:
                    pytime.sleep(backoff * attempt)
    return status


def fetch_and_clean_all(
    retry_count: int = 3,
    backoff_sec: float = 2.0
) -> Tuple[Optional[Dict[str, pd.Series]], Optional[str]]:
    """
    Downloads all 6 stocks + NIFTY from Yahoo Finance with retries.
    Uses resilient per-ticker downloads to avoid batch failure on any single stock.
    Returns: (cleaned_dict, error_message)
    """
    all_tickers = list(STOCKS.keys()) + [BENCHMARK_TICKER]
    cleaned: Dict[str, pd.Series] = {}
    for ticker in all_tickers:
        try:
            s = fetch_ticker_series(ticker, retries=retry_count, backoff=backoff_sec)
            cleaned[ticker] = s
        except Exception as e:
            return None, f"Failed fetching {ticker}: {e}"
    return cleaned, None


def refresh_data(force: bool = False, include_provisional: bool = False) -> dict:
    """
    Main refresh workflow:
    1. Acquire lock.
    2. Check if weekend / holiday / already up to date.
    3. Download all tickers with retries.
    4. Separate final vs provisional candles.
    5. Validate benchmark and all stocks.
    6. Backup previous files, atomically write clean CSVs, update manifest.
    7. Release lock and return status summary.
    """
    now_ist = datetime.now(IST)
    manifest = load_manifest()

    # Rule 11: Weekend run does not fetch/publish unless force=True
    if not force and now_ist.weekday() >= 5:
        msg = "Weekend: NSE closed; skipping fetch/publish."
        logger.info(msg)
        manifest["last_attempt"] = {
            "time": now_ist.isoformat(),
            "result": "NO_NEW_SESSION",
            "message": msg
        }
        save_manifest(manifest)
        return {"status": "NO_NEW_SESSION", "message": msg, "manifest": manifest}

    expected_session = get_expected_latest_session(now_ist)
    bench_clean = load_clean_data(BENCHMARK_TICKER)
    latest_stored_date = (
        bench_clean.index[-1].date() if bench_clean is not None and len(bench_clean) > 0 else None
    )

    # Check minimum refresh interval
    last_fetched_str = manifest.get("updated_at")
    if not force and last_fetched_str:
        try:
            last_fetched_dt = datetime.fromisoformat(last_fetched_str)
            elapsed_sec = (now_ist - last_fetched_dt).total_seconds()
            if elapsed_sec < MIN_REFRESH_INTERVAL_MINUTES * 60:
                msg = f"Skipping refresh: last refresh was {elapsed_sec / 60:.1f} mins ago (< {MIN_REFRESH_INTERVAL_MINUTES}m)"
                logger.info(msg)
                return {"status": "SKIPPED", "message": msg, "manifest": manifest}
        except Exception:
            pass

    # If already up to expected session and not forced, check if live bar requested
    if not force and latest_stored_date and latest_stored_date >= expected_session:
        if not (include_provisional and is_market_open(now_ist)):
            msg = f"Data already up to date ({latest_stored_date}). No new completed session due."
            logger.info(msg)
            manifest["last_attempt"] = {
                "time": now_ist.isoformat(),
                "result": "NO_NEW_SESSION",
                "message": msg
            }
            save_manifest(manifest)
            return {"status": "NO_NEW_SESSION", "message": msg, "manifest": manifest}

    try:
        with FileLock():
            cleaned_data, error_msg = fetch_and_clean_all()
            if error_msg or not cleaned_data:
                fail_msg = f"Refresh failed: {error_msg}"
                logger.error(fail_msg)
                manifest["last_attempt"] = {
                    "time": now_ist.isoformat(),
                    "result": "FAILED",
                    "message": fail_msg
                }
                save_manifest(manifest)
                return {"status": "FAILED", "message": fail_msg, "manifest": manifest}

            # Handle provisional vs final candle:
            # If the newest bar is today and now < 15:45 IST, it is provisional.
            # It must NOT be written to *_clean.csv.
            final_data: Dict[str, pd.Series] = {}
            provisional_data: Dict[str, dict] = {}

            for t, s in cleaned_data.items():
                if len(s) == 0:
                    continue
                last_bar_date = s.index[-1].date()
                if not is_session_final(last_bar_date, now_ist):
                    # Save provisional reading separately
                    provisional_data[t] = {
                        "date": last_bar_date.strftime("%Y-%m-%d"),
                        "close": float(s.iloc[-1]),
                        "fetched_at": now_ist.isoformat()
                    }
                    # Clean data gets only completed sessions
                    final_s = s.iloc[:-1]
                else:
                    final_s = s
                final_data[t] = final_s

            # Write provisional data to provisional directory
            if provisional_data:
                for t, p_info in provisional_data.items():
                    p_path = os.path.join(PROVISIONAL_DIR, f"{sanitize_ticker(t)}_provisional.json")
                    with open(p_path, "w", encoding="utf-8") as pf:
                        json.dump(p_info, pf, indent=2)

            # Step 1: Validate benchmark
            bench_s = final_data.get(BENCHMARK_TICKER)
            stored_bench = bench_clean["Close"] if bench_clean is not None else None
            b_valid, b_warnings, b_flags = validate_series(
                BENCHMARK_TICKER, bench_s, stored_bench, is_benchmark=True
            )
            if not b_valid:
                fail_msg = f"Benchmark {BENCHMARK_TICKER} validation failed: {b_warnings}"
                logger.error(fail_msg)
                manifest["last_attempt"] = {
                    "time": now_ist.isoformat(),
                    "result": "FAILED",
                    "message": fail_msg
                }
                save_manifest(manifest)
                return {"status": "FAILED", "message": fail_msg, "manifest": manifest}

            # Step 2: Validate all stocks
            validated_stocks: Dict[str, Tuple[pd.Series, List[str], List[dict]]] = {}
            for ticker in STOCKS.keys():
                stock_s = final_data.get(ticker)
                if stock_s is None:
                    fail_msg = f"Stock {ticker} missing from downloaded data"
                    logger.error(fail_msg)
                    manifest["last_attempt"] = {
                        "time": now_ist.isoformat(),
                        "result": "FAILED",
                        "message": fail_msg
                    }
                    save_manifest(manifest)
                    return {"status": "FAILED", "message": fail_msg, "manifest": manifest}

                stored_stock_df = load_clean_data(ticker)
                stored_stock_s = stored_stock_df["Close"] if stored_stock_df is not None else None
                s_valid, s_warnings, s_flags = validate_series(
                    ticker, stock_s, stored_stock_s, is_benchmark=False
                )
                if not s_valid:
                    fail_msg = f"Stock {ticker} validation failed: {s_warnings}"
                    logger.error(fail_msg)
                    manifest["last_attempt"] = {
                        "time": now_ist.isoformat(),
                        "result": "FAILED",
                        "message": fail_msg
                    }
                    save_manifest(manifest)
                    return {"status": "FAILED", "message": fail_msg, "manifest": manifest}

                # Check alignment with benchmark
                aligned_dates = stock_s.index.intersection(bench_s.index)
                if len(aligned_dates) < MIN_HISTORY_ROWS:
                    fail_msg = f"Stock {ticker} has insufficient aligned dates with NIFTY ({len(aligned_dates)})"
                    logger.error(fail_msg)
                    manifest["last_attempt"] = {
                        "time": now_ist.isoformat(),
                        "result": "FAILED",
                        "message": fail_msg
                    }
                    save_manifest(manifest)
                    return {"status": "FAILED", "message": fail_msg, "manifest": manifest}

                validated_stocks[ticker] = (stock_s, s_warnings, s_flags)

            # Step 3: All passed! Rotate backups and atomically write clean CSVs
            version_id = now_ist.strftime("v%Y%m%d_%H%M%S")

            # Backup existing clean CSVs
            for t in list(STOCKS.keys()) + [BENCHMARK_TICKER]:
                existing_path = get_clean_csv_path(t)
                if os.path.exists(existing_path):
                    backup_path = os.path.join(BACKUP_DIR, f"{sanitize_ticker(t)}_clean.csv")
                    shutil.copy2(existing_path, backup_path)

            # Atomically publish benchmark
            bench_target = get_clean_csv_path(BENCHMARK_TICKER)
            with tempfile.NamedTemporaryFile("w", dir=DATA_DIR, delete=False, encoding="utf-8", newline="") as tf:
                bench_s.to_frame(name="Close").to_csv(tf, index_label="Date", date_format="%Y-%m-%d")
                temp_bench = tf.name
            os.replace(temp_bench, bench_target)
            bench_sha = calculate_sha256(bench_target)

            # Atomically publish each stock
            new_manifest_tickers = {}
            for ticker, (s_series, s_warn, s_flg) in validated_stocks.items():
                target_path = get_clean_csv_path(ticker)
                with tempfile.NamedTemporaryFile("w", dir=DATA_DIR, delete=False, encoding="utf-8", newline="") as tf:
                    s_series.to_frame(name="Close").to_csv(tf, index_label="Date", date_format="%Y-%m-%d")
                    temp_stock = tf.name
                os.replace(temp_stock, target_path)
                stock_sha = calculate_sha256(target_path)

                new_manifest_tickers[ticker] = {
                    "first_date": s_series.index[0].strftime("%Y-%m-%d"),
                    "last_date": s_series.index[-1].strftime("%Y-%m-%d"),
                    "rows": int(len(s_series)),
                    "sha256": stock_sha,
                    "fetched_at": now_ist.isoformat(),
                    "status": "VALID",
                    "benchmark_version": bench_sha,
                    "warnings": s_warn,
                    "flagged_moves": s_flg
                }

            new_manifest_tickers[BENCHMARK_TICKER] = {
                "first_date": bench_s.index[0].strftime("%Y-%m-%d"),
                "last_date": bench_s.index[-1].strftime("%Y-%m-%d"),
                "rows": int(len(bench_s)),
                "sha256": bench_sha,
                "fetched_at": now_ist.isoformat(),
                "status": "VALID",
                "benchmark_version": bench_sha,
                "warnings": b_warnings,
                "flagged_moves": b_flags
            }

            manifest["version_id"] = version_id
            manifest["updated_at"] = now_ist.isoformat()
            manifest["status"] = "SUCCESS"
            manifest["provider"] = PROVIDER
            manifest["tickers"] = new_manifest_tickers
            manifest["last_attempt"] = {
                "time": now_ist.isoformat(),
                "result": "SUCCESS",
                "message": f"Successfully published {len(validated_stocks)} stocks and {BENCHMARK_TICKER}"
            }
            save_manifest(manifest)
            logger.info("Successfully published version %s with %d stocks and %s", version_id, len(validated_stocks), BENCHMARK_TICKER)

            return {
                "status": "SUCCESS",
                "version_id": version_id,
                "message": f"Published {len(validated_stocks)} stocks + NIFTY 50",
                "manifest": manifest
            }

    except TimeoutError as te:
        fail_msg = f"Refresh skipped: lock busy ({te})"
        logger.warning(fail_msg)
        return {"status": "LOCKED", "message": fail_msg, "manifest": manifest}
    except Exception as exc:
        fail_msg = f"Unexpected error in refresh: {exc}"
        logger.exception(fail_msg)
        manifest["last_attempt"] = {
            "time": now_ist.isoformat(),
            "result": "FAILED",
            "message": fail_msg
        }
        save_manifest(manifest)
        return {"status": "FAILED", "message": fail_msg, "manifest": manifest}


def migrate_initial_offline_csvs() -> None:
    """
    Migrates the existing legacy offline CSV files into data/ so PVR INOX and NIFTY
    work offline immediately even if Yahoo Finance is unreachable on first run.
    """
    pvr_legacy = os.path.join(os.path.dirname(DATA_DIR), "pvrinox_ticker_2022-04-01_to_2026-08-13.csv")
    nifty_legacy = os.path.join(os.path.dirname(DATA_DIR), "nifty50_dataset_2024-04-01_to_2026-08-13.csv")
    pvr_target = get_clean_csv_path("PVRINOX.NS")
    nifty_target = get_clean_csv_path(BENCHMARK_TICKER)

    if not os.path.exists(pvr_target) and os.path.exists(pvr_legacy):
        try:
            df = pd.read_csv(pvr_legacy, parse_dates=["Date"], index_col="Date")
            col = "Adj Close" if "Adj Close" in df.columns else "Close"
            s = clean_price_series(df[col], "PVRINOX.NS")
            s.to_frame(name="Close").to_csv(pvr_target, index_label="Date", date_format="%Y-%m-%d")
            logger.info("Migrated legacy PVR INOX CSV to %s", pvr_target)
        except Exception as e:
            logger.error("Failed migrating legacy PVR INOX CSV: %s", e)

    if not os.path.exists(nifty_target) and os.path.exists(nifty_legacy):
        try:
            df = pd.read_csv(nifty_legacy, parse_dates=["Date"], index_col="Date")
            s = clean_price_series(df["Close"], BENCHMARK_TICKER)
            s.to_frame(name="Close").to_csv(nifty_target, index_label="Date", date_format="%Y-%m-%d")
            logger.info("Migrated legacy NIFTY 50 CSV to %s", nifty_target)
        except Exception as e:
            logger.error("Failed migrating legacy NIFTY CSV: %s", e)
