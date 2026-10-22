"""
Test 3: Reliance 1:1 Bonus Adjustment Around 28 Oct 2024.
Confirms no fake crash exists in Reliance Industries (RELIANCE.NS) around
the 1:1 bonus date (late October 2024). All daily percentage changes remain
normal (< 5%), proving proper auto-adjustment.
"""
import os
import sys
import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import data_pipeline as dp


def test_reliance_bonus_no_crash():
    rel_clean = dp.load_clean_data("RELIANCE.NS")
    assert rel_clean is not None and len(rel_clean) > 0

    # Window around bonus date 28 Oct 2024
    window = rel_clean.loc["2024-10-15":"2024-11-15"]
    assert len(window) >= 15

    pct_changes = window["Close"].pct_change() * 100.0
    pct_changes = pct_changes.dropna()

    # Verify that maximum drop is modest and nowhere near a 50% split crash
    max_drop = pct_changes.min()
    max_gain = pct_changes.max()

    assert max_drop > -5.0, f"Suspicious drop detected: {max_drop:.2f}%"
    assert max_gain < 5.0, f"Suspicious jump detected: {max_gain:.2f}%"

    # Also check manifest warnings for Reliance around this date
    manifest = dp.load_manifest()
    rel_info = manifest.get("tickers", {}).get("RELIANCE.NS", {})
    flagged = rel_info.get("flagged_moves", [])
    flagged_dates = [f["date"] for f in flagged]
    assert "2024-10-28" not in flagged_dates
    assert "2024-10-29" not in flagged_dates
