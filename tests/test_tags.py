"""
Test: Stock tags (used by the Tags analysis tab).
Verifies:
1. ALL holds every configured stock; Midselect holds exactly the 25 checked stocks.
2. Every tagged stock has clean data.
3. The RRG tab has no tag box: its stock list and All-stocks page show every stock.
"""
import os
import sys
from streamlit.testing.v1 import AppTest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
import data_pipeline as dp

APP_PATH = os.path.join(cfg.ROOT_DIR, "rrg_app.py")
MIDSELECT = ["PAYTM", "MCX", "PERSISTENT", "INDHOTEL", "HEROMOTOCO", "INDIANB", "ASHOKLEY", "INDUSTOWER",
             "NAUKRI", "BHEL", "AUROPHARMA", "DIXON", "FEDERALBNK", "INDUSINDBK", "AUBANK", "MARICO", "LICI",
             "SUZLON", "POLICYBZR", "LUPIN", "YESBANK", "BHARATFORG", "GVT&D", "SRF", "SWIGGY"]


def test_tag_membership():
    assert cfg.stocks_for_tag(cfg.TAG_ALL) == list(cfg.STOCKS)
    assert sorted(cfg.stocks_for_tag("Midselect")) == sorted(t + ".NS" for t in MIDSELECT)


def test_every_tagged_stock_has_data():
    for ticker in cfg.stocks_for_tag(cfg.TAG_ALL):
        df = dp.load_clean_data(ticker)
        assert df is not None and len(df) > 0, f"No clean data for {ticker}"


def test_rrg_sidebar_has_no_tag_box_and_lists_every_stock():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=60)
    assert len(at.exception) == 0
    assert all(r.key != "tag" for r in at.sidebar.radio)          # tag box removed from the RRG tab
    assert list(at.sidebar.selectbox(key="stock").options) == [
        f"{cfg.STOCKS[t]['name']} ({cfg.STOCKS[t]['sector']})" for t in cfg.STOCKS]
    at.sidebar.radio(key="page").set_value("All stocks")
    at.run(timeout=120)
    assert len(at.exception) == 0, [e.message for e in at.exception]
