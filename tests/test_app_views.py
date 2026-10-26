"""
App Views & Offline Resilience Tests (Tests 12, 13, 14).
Tests:
- All 6 stocks x 5 pages via AppTest with 0 exceptions.
- App restart loading saved data and timestamps.
- Offline resilience when network/yfinance is disconnected.
"""
import os
import sys
from unittest.mock import patch

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import data_pipeline as dp

APP_PATH = os.path.join(cfg.ROOT_DIR, "rrg_app.py")


def test_apptest_all_stocks_all_pages():
    """Test 12: every configured stock x 5 pages with 0 exceptions."""
    pages = ["Daily", "Weekly", "Both", "All stocks", "Strategy"]
    for ticker in cfg.STOCKS.keys():
        for page in pages:
            at = AppTest.from_file(APP_PATH)
            at.run(timeout=120)
            at.sidebar.selectbox(key="stock").set_value(ticker)
            at.sidebar.radio(key="page").set_value(page)
            at.run(timeout=120)

            if page == "Strategy":
                at.sidebar.button[1].click()
                at.run(timeout=120)

            assert len(at.exception) == 0, f"Exception on {ticker} - {page}: {[e.message for e in at.exception]}"


def test_app_restart_loads_saved_data_and_status():
    """Test 13: Restarting app loads saved data and status panel shows timestamps."""
    manifest = dp.load_manifest()
    updated_at = manifest.get("updated_at")
    assert updated_at is not None

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=120)
    assert len(at.exception) == 0

    # Verify metrics are loaded
    assert len(at.metric) >= 3
    # Check that status panel displays correctly
    assert len(at.expander) >= 1


def test_offline_mode_resilient_when_internet_disconnected():
    """Test 14: Offline mode when yfinance raises NetworkError."""
    with patch("yfinance.download", side_effect=ConnectionError("No internet connection")):
        for ticker in cfg.STOCKS.keys():
            at = AppTest.from_file(APP_PATH)
            at.run(timeout=120)
            at.sidebar.selectbox(key="stock").set_value(ticker)
            at.run(timeout=120)
            assert len(at.exception) == 0
            # Data still loaded from data/ clean CSVs
            clean_df = dp.load_clean_data(ticker)
            assert clean_df is not None and len(clean_df) > 0
