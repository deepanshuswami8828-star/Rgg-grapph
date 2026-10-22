"""
Configuration settings for Multi-Stock RRG Application.
"""
import os
from datetime import time, timedelta, timezone

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backup")
PROVISIONAL_DIR = os.path.join(DATA_DIR, "provisional")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
MANIFEST_PATH = os.path.join(DATA_DIR, "manifest.json")
REFRESH_LOG_PATH = os.path.join(LOGS_DIR, "refresh.log")
LOCK_FILE_PATH = os.path.join(DATA_DIR, ".refresh.lock")

IST = timezone(timedelta(hours=5, minutes=30))

BENCHMARK_TICKER = "^NSEI"
BENCHMARK_NAME = "NIFTY 50"

# All configured stocks: key is ticker
STOCKS = {
    "PVRINOX.NS": {
        "name": "PVR INOX",
        "sector": "Media & entertainment",
        "notes": "long history",
    },
    "BEL.NS": {
        "name": "Bharat Electronics (BEL)",
        "sector": "Defence",
        "notes": "long history",
    },
    "SUZLON.NS": {
        "name": "Suzlon Energy",
        "sector": "Energy - wind",
        "notes": "long history",
    },
    "WAAREEENER.NS": {
        "name": "Waaree Energies",
        "sector": "Energy - solar",
        "notes": "listed 28 Oct 2024; show its real first date, never invent pre-listing data",
    },
    "BHARTIARTL.NS": {
        "name": "Bharti Airtel",
        "sector": "Telecom",
        "notes": "long history",
    },
    "RELIANCE.NS": {
        "name": "Reliance Industries",
        "sector": "Energy / conglomerate",
        "notes": "1:1 bonus Oct 2024 must NOT appear as a crash",
    },
}

DATA_START_DISPLAY = "2023-01-01"
MARKET_OPEN_IST = time(9, 15)
MARKET_CLOSE_IST = time(15, 30)
REFRESH_AFTER_CLOSE_IST = time(15, 45)

MIN_REFRESH_INTERVAL_MINUTES = 15
MAX_POST_CLOSE_ATTEMPTS_PER_DAY = 4
POST_CLOSE_RETRY_INTERVAL_MINUTES = 30
SUSPICIOUS_MOVE_PCT = 25.0
MIN_HISTORY_ROWS = 60
PROVIDER = "Yahoo Finance (yfinance)"

# RRG Calculation Parameters (calibrated method, unchanged)
RS_PRESMOOTH = 5     # SMA window on raw RS before the double EMA
RS_SHORT = 5         # fast EMA for RS-Ratio
RS_LONG = 30         # slow EMA for RS-Ratio (baseline)
MOM_SHORT = 3        # fast EMA for RS-Momentum
MOM_LONG = 14        # slow EMA for RS-Momentum
TAIL_DAYS_DAILY = 25 # trading days of trajectory drawn
TAIL_WEEKS = 12      # weekly trail length
WARMUP_DAILY = 200   # daily warm-up bars
WARMUP_WEEKLY = 100  # weekly warm-up bars


def sanitize_ticker(ticker: str) -> str:
    """Removes ^ and special chars for clean file naming."""
    return ticker.replace("^", "")


def get_clean_csv_path(ticker: str) -> str:
    """Returns absolute path to <sanitized_ticker>_clean.csv in data/."""
    return os.path.join(DATA_DIR, f"{sanitize_ticker(ticker)}_clean.csv")
