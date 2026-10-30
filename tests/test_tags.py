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
# Nifty Smallcap 50 stocks that passed all 3 data checks
SMALLCAP = ["REDINGTON", "CUB", "KPITTECH", "TATAELXSI", "IGL", "ATHERENERG", "GLAND", "SAILIFE", "SONACOMS",
            "ACUTAAS", "AFFLE", "AMBER", "ANANDRATHI", "ANGELONE", "APOLLOTYRE", "BANDHANBNK", "CDSL", "CAMS",
            "CROMPTON", "DELHIVERY", "LALPATHLAB", "IIFL", "INOXWIND", "KAYNES", "KFINTECH", "MTARTECH", "MANAPPURAM",
            "NATCOPHARM", "NBCC", "NAVINFLUOR", "ONESOURCE", "PNBHOUSING", "PPLPHARMA", "RBLBANK", "SYNGENE",
            "TATACHEM", "TATATECH", "WOCKPHARMA"]
# Nifty Alpha Quality Value Low-Volatility 30 stocks that passed all 3 data checks
ALPHA_QVLV = ["MARICO", "AUROPHARMA", "FEDERALBNK", "HEROMOTOCO", "LUPIN", "COALINDIA", "NTPC", "ICICIBANK", "ALKEM", "CIPLA",
              "DRREDDY", "EICHERMOT", "GRASIM", "HINDUNILVR", "MARUTI", "NMDC", "PFC", "SBIN", "SUNPHARMA", "HINDALCO", "COLPAL"]
# Hospitals stocks that passed all 3 data checks (DRAGARWQ and 3BBLACKBIO passed too, but Yahoo has under 60 sessions for them)
HOSPITALS = ["LALPATHLAB", "SHALBY", "FORTIS", "RAINBOW", "ASTERDM", "MAXHEALTH", "GKSL", "NEPHROCARE", "SURAKSHA", "KRSNAA",
             "VIJAYA", "THYROCARE", "MEDANTA", "METROPOLIS", "HCG", "AGARWALEYE", "GPTHEALTH", "APOLLOHOSP"]
# Hotels and hospitality stocks that passed all 3 data checks
HOTELS = ["BRIGHOTEL", "CHALET", "ITCHOTELS", "ITDC", "JUNIPER", "LEMONTREE", "MHRIL", "PARKHOTELS", "SAMHI", "THELEELA", "VENTIVE"]
# Nifty India Tourism stocks that passed all 3 data checks
TOURISM = ["BLS", "DEVYANI", "GMRAIRPORT", "INDHOTEL", "INDIGO", "ITCHOTELS", "JUBLFOOD", "LEMONTREE", "TBOTEK"]
# Nifty Private Bank stocks that passed all 3 data checks
PRIVATE_BANK = ["AXISBANK", "BANDHANBNK", "FEDERALBNK", "HDFCBANK", "ICICIBANK", "IDFCFIRSTB", "INDUSINDBK", "KOTAKBANK", "RBLBANK", "YESBANK"]
# Nifty Tata Group 25% Cap stocks that passed all 3 data checks
TATA_GROUP = ["INDHOTEL", "TATACONSUM", "TATAPOWER", "TATASTEEL", "TMCV", "TMPV", "VOLTAS"]
# Nifty Energy stocks (Strike list of 40) that passed all 3 data checks
ENERGY = ["ABB", "ADANIENSOL", "ADANIGREEN", "ADANIPOWER", "ATGL", "BHEL", "BPCL", "CESC", "CGPOWER", "COALINDIA", "ENRIN", "GAIL", "GVT&D", "HINDPETRO", "IGL", "INOXWIND", "IOC", "JSWENERGY", "MGL", "NHPC", "NLCINDIA", "NTPC", "NTPCGREEN", "OIL", "PETRONET", "POWERGRID", "POWERINDIA", "RELIANCE", "RPOWER", "SIEMENS", "SUZLON", "TATAPOWER", "TORNTPOWER"]


def test_tag_membership():
    assert cfg.stocks_for_tag(cfg.TAG_ALL) == list(cfg.STOCKS)
    assert sorted(cfg.stocks_for_tag("Midselect")) == sorted(t + ".NS" for t in MIDSELECT)
    assert sorted(cfg.stocks_for_tag("Smallcap")) == sorted(t + ".NS" for t in SMALLCAP)
    assert sorted(cfg.stocks_for_tag("AlphaQVLowVol")) == sorted(t + ".NS" for t in ALPHA_QVLV)
    assert sorted(cfg.stocks_for_tag("Hospitals")) == sorted(t + ".NS" for t in HOSPITALS)
    assert sorted(cfg.stocks_for_tag("Energy")) == sorted(t + ".NS" for t in ENERGY)
    assert sorted(cfg.stocks_for_tag("TataGroup")) == sorted(t + ".NS" for t in TATA_GROUP)
    assert sorted(cfg.stocks_for_tag("PrivateBank")) == sorted(t + ".NS" for t in PRIVATE_BANK)
    assert sorted(cfg.stocks_for_tag("Tourism")) == sorted(t + ".NS" for t in TOURISM)
    assert sorted(cfg.stocks_for_tag("Hotels")) == sorted(t + ".NS" for t in HOTELS)


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
    at.run(timeout=300)  # 135+ stocks: a cold run of every view takes over 2 minutes
    assert len(at.exception) == 0, [e.message for e in at.exception]
