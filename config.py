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
        "tags": [],
    },
    "BEL.NS": {
        "name": "Bharat Electronics (BEL)",
        "sector": "Defence",
        "notes": "long history",
        "tags": [],
    },
    "SUZLON.NS": {
        "name": "Suzlon Energy",
        "sector": "Energy - wind",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "WAAREEENER.NS": {
        "name": "Waaree Energies",
        "sector": "Energy - solar",
        "notes": "listed 28 Oct 2024; show its real first date, never invent pre-listing data",
        "tags": [],
    },
    "BHARTIARTL.NS": {
        "name": "Bharti Airtel",
        "sector": "Telecom",
        "notes": "long history",
        "tags": [],
    },
    "RELIANCE.NS": {
        "name": "Reliance Industries",
        "sector": "Energy / conglomerate",
        "notes": "1:1 bonus Oct 2024 must NOT appear as a crash",
        "tags": [],
    },
    "PAYTM.NS": {
        "name": "Paytm (One 97 Communications)",
        "sector": "Fintech / Payments",
        "notes": "listed 18 Nov 2021; show its real first date, never invent pre-listing data",
        "tags": ["Midselect"],
    },
    "MCX.NS": {
        "name": "Multi Commodity Exchange (MCX)",
        "sector": "Financial Services - Commodity Exchange",
        "notes": "listed 9 Mar 2012; 5-for-1 split Jan 2026 must NOT appear as a crash",
        "tags": ["Midselect"],
    },
    "PERSISTENT.NS": {
        "name": "Persistent Systems",
        "sector": "IT Services",
        "notes": "listed 6 Apr 2010; bonus 2015 and split 2024 must NOT appear as crashes",
        "tags": ["Midselect"],
    },
    "INDHOTEL.NS": {
        "name": "Indian Hotels (IHCL)",
        "sector": "Hotels & Tourism",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "HEROMOTOCO.NS": {
        "name": "Hero MotoCorp",
        "sector": "Automobile - Two Wheelers",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "INDIANB.NS": {
        "name": "Indian Bank",
        "sector": "Banking - PSU Bank",
        "notes": "listed 1 Mar 2007",
        "tags": ["Midselect"],
    },
    "ASHOKLEY.NS": {
        "name": "Ashok Leyland",
        "sector": "Automobile - Commercial Vehicles",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "INDUSTOWER.NS": {
        "name": "Indus Towers",
        "sector": "Telecom - Tower Infrastructure",
        "notes": "listed 28 Dec 2012 (as Bharti Infratel)",
        "tags": ["Midselect"],
    },
    "NAUKRI.NS": {
        "name": "Info Edge (Naukri)",
        "sector": "Internet - Online Classifieds",
        "notes": "listed 21 Nov 2006",
        "tags": ["Midselect"],
    },
    "BHEL.NS": {
        "name": "Bharat Heavy Electricals (BHEL)",
        "sector": "Capital Goods - Heavy Electrical Equipment",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "AUROPHARMA.NS": {
        "name": "Aurobindo Pharma",
        "sector": "Pharmaceuticals",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "DIXON.NS": {
        "name": "Dixon Technologies",
        "sector": "Consumer Electronics - Manufacturing",
        "notes": "listed 18 Sep 2017",
        "tags": ["Midselect"],
    },
    "FEDERALBNK.NS": {
        "name": "Federal Bank",
        "sector": "Banking - Private Bank",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "INDUSINDBK.NS": {
        "name": "IndusInd Bank",
        "sector": "Banking - Private Bank",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "AUBANK.NS": {
        "name": "AU Small Finance Bank",
        "sector": "Banking - Small Finance Bank",
        "notes": "listed 10 Jul 2017",
        "tags": ["Midselect"],
    },
    "MARICO.NS": {
        "name": "Marico",
        "sector": "FMCG",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "LICI.NS": {
        "name": "Life Insurance Corporation (LIC)",
        "sector": "Insurance - Life Insurance",
        "notes": "listed 17 May 2022; show its real first date, never invent pre-listing data",
        "tags": ["Midselect"],
    },
    "POLICYBZR.NS": {
        "name": "PB Fintech (Policybazaar)",
        "sector": "Financial Services - Insurtech",
        "notes": "listed 15 Nov 2021; show its real first date, never invent pre-listing data",
        "tags": ["Midselect"],
    },
    "LUPIN.NS": {
        "name": "Lupin",
        "sector": "Pharmaceuticals",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "YESBANK.NS": {
        "name": "Yes Bank",
        "sector": "Banking - Private Bank",
        "notes": "listed 12 Jul 2005",
        "tags": ["Midselect"],
    },
    "BHARATFORG.NS": {
        "name": "Bharat Forge",
        "sector": "Auto Components - Forgings",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "GVT&D.NS": {
        "name": "GE Vernova T&D India",
        "sector": "Capital Goods - Power Transmission Equipment",
        "notes": "continuous NSE trading from 30 Jun 2008",
        "tags": ["Midselect"],
    },
    "SRF.NS": {
        "name": "SRF",
        "sector": "Chemicals - Specialty Chemicals",
        "notes": "long history",
        "tags": ["Midselect"],
    },
    "SWIGGY.NS": {
        "name": "Swiggy",
        "sector": "Internet - Food & Quick-commerce Delivery",
        "notes": "listed 13 Nov 2024; show its real first date, never invent pre-listing data",
        "tags": ["Midselect"],
    },
}


# Stock tags: the sidebar Tag option shows "ALL" (every stock above) or one tag's stocks.
# A stock belongs to a tag when the tag's name is in its "tags" list.
TAG_ALL = "ALL"
TAGS = [TAG_ALL, "Midselect"]


def stocks_for_tag(tag: str) -> list:
    """Tickers shown for a tag, in the order of STOCKS."""
    if tag == TAG_ALL:
        return list(STOCKS)
    return [t for t, info in STOCKS.items() if tag in info.get("tags", [])]

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
