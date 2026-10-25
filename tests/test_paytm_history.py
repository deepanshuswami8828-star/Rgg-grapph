"""
Test: Paytm Listing Date & Page Loading.
Verifies:
1. Paytm (PAYTM.NS) first date equals real listing date (2021-11-18).
2. No fabricated or pre-listing dates exist.
3. Every page (Daily, Weekly, Both, All stocks, Strategy) loads without crashing.
"""
import os
import sys
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import data_pipeline as dp


def test_paytm_first_date_is_listing_date():
    paytm_df = dp.load_clean_data("PAYTM.NS")
    assert paytm_df is not None and len(paytm_df) > 0
    first_date_str = paytm_df.index[0].strftime("%Y-%m-%d")
    assert first_date_str == "2021-11-18", f"Expected listing date 2021-11-18, got {first_date_str}"


def test_paytm_every_page_loads():
    app_path = os.path.join(cfg.ROOT_DIR, "rrg_app.py")
    pages = ["Daily", "Weekly", "Both", "All stocks", "Strategy"]

    for page in pages:
        at = AppTest.from_file(app_path)
        at.run(timeout=60)
        at.sidebar.selectbox[0].set_value("PAYTM.NS")
        at.sidebar.radio[0].set_value(page)
        at.run(timeout=60)

        if page == "Strategy":
            at.sidebar.button[1].click()
            at.run(timeout=60)

        assert len(at.exception) == 0, f"Page {page} threw exception for Paytm: {[e.message for e in at.exception]}"
