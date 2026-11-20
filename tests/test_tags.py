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
# Hospitals stocks that passed all 3 data checks (DRAGARWQ and 3BBLACKBIO added on 12 Nov 2026, once Yahoo had 60 sessions)
HOSPITALS = ["LALPATHLAB", "SHALBY", "FORTIS", "RAINBOW", "ASTERDM", "MAXHEALTH", "GKSL", "NEPHROCARE", "SURAKSHA", "KRSNAA",
             "VIJAYA", "THYROCARE", "MEDANTA", "METROPOLIS", "HCG", "AGARWALEYE", "GPTHEALTH", "APOLLOHOSP",
             "DRAGARWQ", "3BBLACKBIO"]
# Hotels and hospitality stocks that passed all 3 data checks
HOTELS = ["BRIGHOTEL", "CHALET", "ITCHOTELS", "ITDC", "JUNIPER", "LEMONTREE", "MHRIL", "PARKHOTELS", "SAMHI", "THELEELA", "VENTIVE"]
# Nifty India Tourism stocks that passed all 3 data checks
TOURISM = ["BLS", "DEVYANI", "GMRAIRPORT", "INDHOTEL", "INDIGO", "ITCHOTELS", "JUBLFOOD", "LEMONTREE", "TBOTEK"]
# Nifty Metal stocks that passed all 3 data checks (HINDZINC, JSWSTEEL, VEDL, NATIONALUM, JINDALSTEL, SAIL, APLAPOLLO failed)
METAL = ["ADANIENT", "HINDALCO", "HINDCOPPER", "JSL", "LLOYDSME", "NMDC", "TATASTEEL", "VAML"]
# Nifty Next 50 stocks that passed all 3 data checks (ZYDUSLIFE, HINDZINC, VEDL, CHOLAFIN, TORNTPHARM, JINDALSTEL,
# AMBUJACEM, SOLARINDS, BRITANNIA, MOTHERSON failed)
NIFTY_NEXT_50 = ["ABB", "ADANIENSOL", "ADANIGREEN", "ADANIPOWER", "BAJAJHLDNG", "BANKBARODA", "BOSCHLTD", "BPCL", "CANBK",
                 "CGPOWER", "CUMMINSIND", "DIVISLAB", "DLF", "DMART", "ENRIN", "GAIL", "GODREJCP", "HAL", "HDFCAMC", "HYUNDAI",
                 "IDEA", "IOC", "IRFC", "LTM", "MAZDOCK", "MUTHOOTFIN", "PFC", "PIDILITIND", "PNB", "POLYCAB", "POWERINDIA",
                 "SIEMENS", "TATACAP", "TATAPOWER", "TMCV", "TVSMOTOR", "UNIONBANK", "VAML", "VBL", "WIPRO"]
# Nifty Non-Cyclical Consumer stocks that passed all 3 data checks (TITAN, TRENT, NESTLEIND, PAGEIND, HAVELLS,
# BRITANNIA, ITC failed)
NON_CYCLICAL = ["ASIANPAINT", "BHARTIARTL", "COLPAL", "DABUR", "DIXON", "DMART", "ETERNAL", "GODREJCP", "HINDUNILVR", "IDEA",
                "INDHOTEL", "INDIGO", "LENSKART", "MARICO", "NAUKRI", "NYKAA", "SWIGGY", "TATACOMM", "TATACONSUM", "UNITDSPR",
                "VBL", "VMM", "VOLTAS"]
# Nifty Oil & Gas stocks that passed all 3 data checks (CASTROLIND, ONGC, AEGISLOG failed)
OIL_GAS = ["AEGISVOPAK", "ATGL", "BPCL", "CHENNPETRO", "GAIL", "HINDPETRO", "IGL", "IOC", "MGL", "OIL", "PETRONET", "RELIANCE"]
# Nifty Capital Market stocks that passed all 3 data checks (360ONE failed)
CAPITAL_MARKET = ["ABSLAMC", "ANANDRATHI", "ANGELONE", "BSE", "CAMS", "CDSL", "GROWW", "HDFCAMC", "ICICIAMC", "IEX", "KFINTECH",
                  "MCX", "MOTILALOFS", "NAM-INDIA", "NUVAMA", "UTIAMC"]
# Shipping list stocks that passed all 3 data checks (GESHIP, TRANSWORLD, DOLPHIN, SWANDEF, MARINE, KIRLOSENG failed;
# GLOBOFFS has no Yahoo data; CHOWGULSTM, SHAHISHIP trade on BSE only)
SHIPPING = ["ABSMARINE", "BEL", "BHEL", "COCHINSHIP", "ESSARSHPNG", "GRSE", "KIRLPNU", "MAZDOCK", "SADHAV", "SCI", "SEAMECLTD",
            "SHREEJISPG"]
# Infra list stocks that passed all 3 data checks (LT, NCC, CEMPRO, HGINFRA, KNRCON, JKIL, ASHOKA, KPIL, KEC failed); HUDCO, IRFC, PFS, TFCILTD, IFCI added 12 Nov 2026
INFRA = ["ADANIPORTS", "AFCONS", "DBL", "GMRAIRPORT", "GPPL", "GRINFRA", "HCC", "IRB", "IRCON", "JSWINFRA", "NBCC", "PNCINFRA",
         "RITES", "RVNL", "HUDCO", "IRFC", "PFS", "TFCILTD", "IFCI"]
# Cement list stocks that passed all 3 data checks (ULTRACEMCO, AMBUJACEM, DALBHARAT, RAMCOCEM, SAGCEM, DECCANCE failed)
CEMENT = ["ACC", "BIRLACORPN", "HEIDELBERG", "INDIACEM", "JKCEMENT", "JKLAKSHMI", "JSWCEMENT", "NUVOCO", "ORIENTCEM",
          "PRSMJOHNSN", "SHREECEM", "STARCEMENT"]
# Spirits list stocks that passed all 3 data checks (RADICO, GMBREW, IFBAGRO, UBL failed; JAGAJITIND trades on BSE only;
# IGLSPIRITS listed 4 Nov 2026, too short a history for now)
SPIRITS = ["ABDL", "ASALCBR", "GLOBUSSPR", "PICCADIL", "SDBL", "SULA", "TI", "UNITDSPR"]
# Luxury list stocks that passed all 3 data checks (EIHOTEL, EIHAHOTELS, TAJGVK, ORIENTHOT, ASIANHOTNR, KDDL, TITAN, RADICO
# failed; BENARAS added on 12 Nov 2026, once Yahoo had 60 sessions)
LUXURY = ["ADVENTHTL", "BLUESTONE", "CARYSIL", "CHALET", "CORDELIA", "ETHOSLTD", "INDHOTEL", "ITCHOTELS", "JUNIPER", "KAYA",
          "LANDMARK", "LODHA", "MANYAVAR", "OBEROIRLTY", "PNGSREVA", "SOBHA", "STANLEY", "SULA", "SUNTECK", "TBZ", "THELEELA",
          "TMPV", "UNITDSPR", "VENTIVE", "BENARAS"]
# Lifestyle and Fashion list stocks that passed all 3 data checks (VHLTD, SHOPERSTOP, CERA, PHOENIXLTD, TRENT, BATAINDIA,
# KKCL, VIPIND, ICIL failed)
LIFESTYLE_FASHION = ["ABFRL", "ABLBL", "ARVINDFASN", "BRIGHOTEL", "CAMPUS", "EICHERMOT", "GREENLAM", "HINDWAREAP", "KAJARIACER",
                     "KALYANKJIL", "METROBRAND", "MHRIL", "NYKAA", "PICCADIL", "PNGJL", "PVRINOX", "RAYMONDLSL", "REDTAPE",
                     "SAFARI", "SENCO", "SFL", "SPECIALITY", "WELSPUNLIV"]
# Automation and Robotics list stocks that passed all 3 data checks (SCHAEFFLER, TIMKEN, SHANTIGEAR, HONAUT, NIBL failed)
AUTOMATION_ROBOTICS = ["BBL", "BHARATFORG", "ELECON", "MTARTECH", "NRBBEARING", "SIEMENS", "SONACOMS"]
# Gold Lending list stocks that passed all 3 data checks (CGCL, KARURVYSYA failed)
GOLD_LENDING = ["CSBBANK", "CUB", "DHANBANK", "FEDERALBNK", "FEDFINA", "FINKURVE", "IIFL", "MANAPPURAM", "MUTHOOTFIN", "SOUTHBANK"]
# Consumer loans list stocks that passed all 3 data checks (BAJFINANCE, POONAWALLA, CHOLAFIN, SUNDARMFIN failed)
CONSUMER_LOANS = ["HDBFS", "INDOSTAR", "LTF", "M&MFIN", "MANBA", "MUTHOOTCAP", "SBICARD", "SHRIRAMFIN", "TATACAP"]
# Housing and large ticket finance list stocks that passed all 3 data checks (GICHSGFIN failed)
HOUSING_LARGE_TICKET = ["AADHARHFC", "AAVAS", "ABCAPITAL", "APTUS", "BAJAJHFL", "CANFINHOME", "HDBFS", "HOMEFIRST", "IIFL",
                        "INDIASHLTR", "JIOFIN", "LICHSGFIN", "PIRAMALFIN", "PNBHOUSING", "REPCOHOME", "SAMMAANCAP", "TATACAP"]
# MSME and Microfinance list stocks that passed all 3 data checks (CGCL, PAISALO failed)
MSME_MICROFINANCE = ["ARMANFIN", "CREDITACC", "FIVESTAR", "FUSION", "MASFIN", "MUTHOOTMF", "NORTHARC", "SATIN", "SBFC", "SPANDANA",
                     "UGROCAP"]
# Consumer Finance list = Consumer loans + Housing and large ticket finance + MSME and Microfinance
CONSUMER_FINANCE = sorted(set(CONSUMER_LOANS + HOUSING_LARGE_TICKET + MSME_MICROFINANCE))
# Nifty Private Bank stocks that passed all 3 data checks
PRIVATE_BANK = ["AXISBANK", "BANDHANBNK", "FEDERALBNK", "HDFCBANK", "ICICIBANK", "IDFCFIRSTB", "INDUSINDBK", "KOTAKBANK", "RBLBANK", "YESBANK"]
# Nifty Tata Group 25% Cap stocks that passed all 3 data checks
TATA_GROUP = ["INDHOTEL", "TATACONSUM", "TATAPOWER", "TATASTEEL", "TMCV", "TMPV", "VOLTAS"]
# Nifty Energy stocks (Strike list of 40) that passed all 3 data checks, plus PFC, RECLTD, IREDA (added 12 Nov 2026)
ENERGY = ["ABB", "ADANIENSOL", "ADANIGREEN", "ADANIPOWER", "ATGL", "BHEL", "BPCL", "CESC", "CGPOWER", "COALINDIA", "ENRIN", "GAIL", "GVT&D", "HINDPETRO", "IGL", "INOXWIND", "IOC", "JSWENERGY", "MGL", "NHPC", "NLCINDIA", "NTPC", "NTPCGREEN", "OIL", "PETRONET", "POWERGRID", "POWERINDIA", "RELIANCE", "RPOWER", "SIEMENS", "SUZLON", "TATAPOWER", "TORNTPOWER", "PFC", "RECLTD", "IREDA"]
# Nifty Midcap 50 stocks that passed all 3 data checks (17 Nov 2026; GLENMARK, MFSL, UPL failed, and PHOENIXLTD,
# HAVELLS, NATIONALUM, APLAPOLLO had failed earlier)
NIFTY_MIDCAP_50 = ["ASHOKLEY", "AUBANK", "AUROPHARMA", "BHARATFORG", "BHEL", "DABUR", "DIXON", "FEDERALBNK",
                   "FORTIS", "GMRAIRPORT", "GODREJPROP", "GVT&D", "HEROMOTOCO", "HINDPETRO", "ICICIGI", "IDFCFIRSTB",
                   "INDHOTEL", "INDUSINDBK", "INDUSTOWER", "JSWENERGY", "LAURUSLABS", "LUPIN", "MANKIND", "MARICO", "MCX",
                   "NAUKRI", "NHPC", "NMDC", "NYKAA", "OIL", "PAYTM", "PERSISTENT", "POLICYBZR", "PRESTIGE", "RECLTD",
                   "SRF", "SUZLON", "SWIGGY", "TIINDIA", "UNITDSPR", "VMM", "WAAREEENER", "YESBANK"]

# Nifty FMCG / Media / EV and New Age Automotive / Housing lists (17 Nov 2026): stocks that passed all 3 data checks
NIFTY_FMCG = ["COLPAL", "DABUR", "GODFRYPHLP", "GODREJCP", "HINDUNILVR", "MARICO", "TATACONSUM", "UNITDSPR", "VBL"]
NIFTY_MEDIA = ["BALAJITELE", "DBCORP", "DEN", "DISHTV", "GTPL", "HATHWAY", "NDTV", "PVRINOX", "SHEMAROO", "TVTODAY", "UFO", "ZEEL"]
NIFTY_EV_AUTOMOTIVE = ["ASHOKLEY", "ATHERENERG", "BHARATFORG", "BOSCHLTD", "CGPOWER", "EICHERMOT", "FLUOROCHEM",
                       "HEROMOTOCO", "HYUNDAI", "JWL", "KPITTECH", "M&M", "MARUTI", "MSUMI", "OLAELEC", "RELIANCE",
                       "SANSERA", "SONACOMS", "TATACHEM", "TATAELXSI", "TATATECH", "TIINDIA", "TMCV", "TMPV",
                       "TVSMOTOR"]
NIFTY_HOUSING = ["AADHARHFC", "AAVAS", "ACC", "AMBER", "APOLLOPIPE", "APTUS", "ASIANPAINT", "BAJAJHFL", "BIRLACORPN",
                 "BLUESTARCO", "CANFINHOME", "CROMPTON", "DIXON", "FINCABLES", "GRASIM", "GREENLAM", "GREENPANEL",
                 "HEIDELBERG", "HINDWAREAP", "HOMEFIRST", "HUDCO", "INDIASHLTR", "INDIGOPNTS", "JKCEMENT",
                 "JKLAKSHMI", "KAJARIACER", "LGEINDIA", "LICHSGFIN", "NUVOCO", "ORIENTELEC", "PIDILITIND",
                 "PNBHOUSING", "POLYCAB", "PRINCEPIPE", "REPCOHOME", "RRKABEL", "SAMMAANCAP", "SHREECEM",
                 "STARCEMENT", "STYLAMIND", "VOLTAS"]

# Nifty PSE and Nifty CPSE (one tag, 17 Nov 2026): stocks that passed all 3 data checks (ONGC, SAIL, NATIONALUM failed)
NIFTY_PSE_CPSE = ["BEL", "BHEL", "BPCL", "COALINDIA", "COCHINSHIP", "CONCOR", "GAIL", "HAL", "HINDPETRO", "IOC", "IRFC", "NBCC", "NHPC", "NLCINDIA", "NMDC", "NTPC", "OIL", "PFC", "POWERGRID", "RECLTD", "SJVN"]

# MidSmall IT and Telecom list (20 Nov 2026): stocks that passed all 3 data checks
MIDSMALL_IT_TELECOM = ["AFFLE", "BHARTIHEXA", "BSOFT", "COFORGE", "E2E", "FSL", "HAPPSTMNDS", "HATHWAY", "HEXT", "IDEA", "IKS", "INDUSTOWER", "INTELLECT", "ITI", "KPITTECH", "LATENTVIEW", "LTTS", "MAPMYINDIA", "MPHASIS", "NETWEB", "NEWGEN", "NUCLEUS", "OFSS", "ONMOBILE", "OPTIEMUS", "PERSISTENT", "QUICKHEAL", "RAILTEL", "RATEGAIN", "ROUTE", "SAGILITY", "SONATSOFTW", "TATACOMM", "TATAELXSI", "TATATECH", "TEJASNET", "ZAGGLE"]

# Pharma list (20 Nov 2026): stocks that passed all 3 data checks
PHARMA = ["AARTIPHARM", "AJANTPHARM", "AKUMS", "ALIVUS", "ALKEM", "ANTHEM", "APLLTD", "AUROPHARMA", "BIOCON", "BLUEJET", "CAPLIPOINT", "CIPLA", "COHANCE", "CONCORDBIO", "CORONA", "DIVISLAB", "DRREDDY", "EMCURE", "ERIS", "GLAND", "GLAXO", "GRANULES", "JUBLPHARMA", "LAURUSLABS", "LUPIN", "MANKIND", "NATCOPHARM", "ONESOURCE", "PFIZER", "PPLPHARMA", "RUBICON", "SAILIFE", "SHILPAMED", "SUNPHARMA", "SYNGENE", "VIYASH", "WOCKPHARMA"]


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
    assert sorted(cfg.stocks_for_tag("Metal")) == sorted(t + ".NS" for t in METAL)
    assert sorted(cfg.stocks_for_tag("NiftyNext50")) == sorted(t + ".NS" for t in NIFTY_NEXT_50)
    assert sorted(cfg.stocks_for_tag("NonCyclicalConsumer")) == sorted(t + ".NS" for t in NON_CYCLICAL)
    assert sorted(cfg.stocks_for_tag("OilGas")) == sorted(t + ".NS" for t in OIL_GAS)
    assert sorted(cfg.stocks_for_tag("CapitalMarket")) == sorted(t + ".NS" for t in CAPITAL_MARKET)
    assert sorted(cfg.stocks_for_tag("Shipping")) == sorted(t + ".NS" for t in SHIPPING)
    assert sorted(cfg.stocks_for_tag("Infra")) == sorted(t + ".NS" for t in INFRA)
    assert sorted(cfg.stocks_for_tag("Cement")) == sorted(t + ".NS" for t in CEMENT)
    assert sorted(cfg.stocks_for_tag("Spirits")) == sorted(t + ".NS" for t in SPIRITS)
    assert sorted(cfg.stocks_for_tag("Luxury")) == sorted(t + ".NS" for t in LUXURY)
    assert sorted(cfg.stocks_for_tag("LifestyleFashion")) == sorted(t + ".NS" for t in LIFESTYLE_FASHION)
    assert sorted(cfg.stocks_for_tag("AutomationRobotics")) == sorted(t + ".NS" for t in AUTOMATION_ROBOTICS)
    assert sorted(cfg.stocks_for_tag("GoldLending")) == sorted(t + ".NS" for t in GOLD_LENDING)
    assert sorted(cfg.stocks_for_tag("ConsumerLoans")) == sorted(t + ".NS" for t in CONSUMER_LOANS)
    assert sorted(cfg.stocks_for_tag("HousingLargeTicketFinance")) == sorted(t + ".NS" for t in HOUSING_LARGE_TICKET)
    assert sorted(cfg.stocks_for_tag("MSMEMicrofinance")) == sorted(t + ".NS" for t in MSME_MICROFINANCE)
    assert sorted(cfg.stocks_for_tag("ConsumerFinance")) == sorted(t + ".NS" for t in CONSUMER_FINANCE)
    assert len(CONSUMER_FINANCE) == 35
    assert sorted(cfg.stocks_for_tag("NiftyMidcap50")) == sorted(t + ".NS" for t in NIFTY_MIDCAP_50)
    assert len(NIFTY_MIDCAP_50) == 43
    assert sorted(cfg.stocks_for_tag("NiftyFMCG")) == sorted(t + ".NS" for t in NIFTY_FMCG)
    assert sorted(cfg.stocks_for_tag("NiftyMedia")) == sorted(t + ".NS" for t in NIFTY_MEDIA)
    assert sorted(cfg.stocks_for_tag("NiftyEVAutomotive")) == sorted(t + ".NS" for t in NIFTY_EV_AUTOMOTIVE)
    assert sorted(cfg.stocks_for_tag("NiftyHousing")) == sorted(t + ".NS" for t in NIFTY_HOUSING)
    assert [len(NIFTY_FMCG), len(NIFTY_MEDIA), len(NIFTY_EV_AUTOMOTIVE), len(NIFTY_HOUSING)] == [9, 12, 25, 41]
    assert sorted(cfg.stocks_for_tag("NiftyPSEandCPSE")) == sorted(t + ".NS" for t in NIFTY_PSE_CPSE)
    assert len(NIFTY_PSE_CPSE) == 21
    assert sorted(cfg.stocks_for_tag("MidSmallITTelecom")) == sorted(t + ".NS" for t in MIDSMALL_IT_TELECOM)
    assert len(MIDSMALL_IT_TELECOM) == 37
    assert sorted(cfg.stocks_for_tag("Pharma")) == sorted(t + ".NS" for t in PHARMA)
    assert len(PHARMA) == 37


def test_every_tagged_stock_has_data():
    for ticker in cfg.stocks_for_tag(cfg.TAG_ALL):
        df = dp.load_clean_data(ticker)
        assert df is not None and len(df) > 0, f"No clean data for {ticker}"


def test_rrg_sidebar_has_no_tag_box_and_lists_every_stock():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=60)
    assert len(at.exception) == 0
    assert all(r.key != "tag" for r in at.sidebar.radio)          # tag box removed from the RRG tab
    # every stock, symbols A to Z, shown as "SYMBOL · name (sector)" (since the search box, 12 Nov 2026)
    assert list(at.sidebar.selectbox(key="stock").options) == [
        f"{t.replace('.NS', '')} · {cfg.STOCKS[t]['name']} ({cfg.STOCKS[t]['sector']})"
        for t in sorted(cfg.STOCKS, key=lambda t: t.replace(".NS", "").upper())]
    at.sidebar.radio(key="page").set_value("All stocks")
    at.run(timeout=300)  # 135+ stocks: a cold run of every view takes over 2 minutes
    assert len(at.exception) == 0, [e.message for e in at.exception]
