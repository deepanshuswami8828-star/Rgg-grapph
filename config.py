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
        "tags": ["Midselect", "Energy"],
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
        "tags": ["NonCyclicalConsumer"],
    },
    "RELIANCE.NS": {
        "name": "Reliance Industries",
        "sector": "Energy / conglomerate",
        "notes": "1:1 bonus Oct 2024 must NOT appear as a crash",
        "tags": ["Energy", "OilGas"],
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
        "tags": ["Midselect", "CapitalMarket"],
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
        "tags": ["Midselect", "TataGroup", "Tourism", "NonCyclicalConsumer"],
    },
    "HEROMOTOCO.NS": {
        "name": "Hero MotoCorp",
        "sector": "Automobile - Two Wheelers",
        "notes": "long history",
        "tags": ["Midselect", "AlphaQVLowVol"],
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
        "tags": ["Midselect", "NonCyclicalConsumer"],
    },
    "BHEL.NS": {
        "name": "Bharat Heavy Electricals (BHEL)",
        "sector": "Capital Goods - Heavy Electrical Equipment",
        "notes": "long history",
        "tags": ["Midselect", "Energy"],
    },
    "AUROPHARMA.NS": {
        "name": "Aurobindo Pharma",
        "sector": "Pharmaceuticals",
        "notes": "long history",
        "tags": ["Midselect", "AlphaQVLowVol"],
    },
    "DIXON.NS": {
        "name": "Dixon Technologies",
        "sector": "Consumer Electronics - Manufacturing",
        "notes": "listed 18 Sep 2017",
        "tags": ["Midselect", "NonCyclicalConsumer"],
    },
    "FEDERALBNK.NS": {
        "name": "Federal Bank",
        "sector": "Banking - Private Bank",
        "notes": "long history",
        "tags": ["Midselect", "AlphaQVLowVol", "PrivateBank"],
    },
    "INDUSINDBK.NS": {
        "name": "IndusInd Bank",
        "sector": "Banking - Private Bank",
        "notes": "long history",
        "tags": ["Midselect", "PrivateBank"],
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
        "tags": ["Midselect", "AlphaQVLowVol", "NonCyclicalConsumer"],
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
        "tags": ["Midselect", "AlphaQVLowVol"],
    },
    "YESBANK.NS": {
        "name": "Yes Bank",
        "sector": "Banking - Private Bank",
        "notes": "listed 12 Jul 2005",
        "tags": ["Midselect", "PrivateBank"],
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
        "tags": ["Midselect", "Energy"],
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
        "tags": ["Midselect", "NonCyclicalConsumer"],
    },
    # Nifty Smallcap 50 stocks that passed all 3 data checks (price break, repricing, missing data) on 28 Oct 2026
    "REDINGTON.NS": {
        "name": "Redington",
        "sector": "IT hardware distribution",
        "notes": "listed 15 Feb 2007",
        "tags": ["Smallcap"],
    },
    "CUB.NS": {
        "name": "City Union Bank",
        "sector": "Banking - private",
        "notes": "long history",
        "tags": ["Smallcap"],
    },
    "KPITTECH.NS": {
        "name": "KPIT Technologies",
        "sector": "IT - automotive software",
        "notes": "listed 22 Apr 2019",
        "tags": ["Smallcap"],
    },
    "TATAELXSI.NS": {
        "name": "Tata Elxsi",
        "sector": "IT - design & technology services",
        "notes": "long history",
        "tags": ["Smallcap"],
    },
    "IGL.NS": {
        "name": "Indraprastha Gas (IGL)",
        "sector": "City gas distribution",
        "notes": "listed 26 Dec 2003",
        "tags": ["Smallcap", "Energy", "OilGas"],
    },
    "ATHERENERG.NS": {
        "name": "Ather Energy",
        "sector": "Automobile - electric two-wheelers",
        "notes": "listed 6 May 2025; show its real first date, never invent pre-listing data",
        "tags": ["Smallcap"],
    },
    "GLAND.NS": {
        "name": "Gland Pharma",
        "sector": "Pharmaceuticals - injectables",
        "notes": "listed 20 Nov 2020",
        "tags": ["Smallcap"],
    },
    "SAILIFE.NS": {
        "name": "Sai Life Sciences",
        "sector": "Pharmaceuticals - CRDMO",
        "notes": "listed 18 Dec 2024; show its real first date, never invent pre-listing data",
        "tags": ["Smallcap"],
    },
    "SONACOMS.NS": {
        "name": "Sona BLW Precision Forgings",
        "sector": "Auto components",
        "notes": "listed 24 Jun 2021",
        "tags": ["Smallcap"],
    },
    "ACUTAAS.NS": {
        "name": "Acutaas Chemicals",
        "sector": "Healthcare",
        "notes": "listed 14 Sep 2021",
        "tags": ["Smallcap"],
    },
    "AFFLE.NS": {
        "name": "Affle 3i",
        "sector": "Information Technology",
        "notes": "listed 8 Aug 2019",
        "tags": ["Smallcap"],
    },
    "AMBER.NS": {
        "name": "Amber Enterprises India",
        "sector": "Consumer Durables",
        "notes": "listed 30 Jan 2018",
        "tags": ["Smallcap"],
    },
    "ANANDRATHI.NS": {
        "name": "Anand Rathi Wealth",
        "sector": "Financial Services",
        "notes": "listed 14 Dec 2021",
        "tags": ["Smallcap", "CapitalMarket"],
    },
    "ANGELONE.NS": {
        "name": "Angel One",
        "sector": "Financial Services",
        "notes": "listed 5 Oct 2020",
        "tags": ["Smallcap", "CapitalMarket"],
    },
    "APOLLOTYRE.NS": {
        "name": "Apollo Tyres",
        "sector": "Automobile and Auto Components",
        "notes": "long history",
        "tags": ["Smallcap"],
    },
    "BANDHANBNK.NS": {
        "name": "Bandhan Bank",
        "sector": "Financial Services",
        "notes": "listed 27 Mar 2018",
        "tags": ["Smallcap", "PrivateBank"],
    },
    "CDSL.NS": {
        "name": "Central Depository Services (CDSL)",
        "sector": "Financial Services",
        "notes": "listed 30 Jun 2017",
        "tags": ["Smallcap", "CapitalMarket"],
    },
    "CAMS.NS": {
        "name": "Computer Age Management Services (CAMS)",
        "sector": "Financial Services",
        "notes": "listed 5 Oct 2020",
        "tags": ["Smallcap", "CapitalMarket"],
    },
    "CROMPTON.NS": {
        "name": "Crompton Greaves Consumer Electricals",
        "sector": "Consumer Durables",
        "notes": "listed 13 May 2016",
        "tags": ["Smallcap"],
    },
    "DELHIVERY.NS": {
        "name": "Delhivery",
        "sector": "Services",
        "notes": "listed 24 May 2022; show its real first date, never invent pre-listing data",
        "tags": ["Smallcap"],
    },
    "LALPATHLAB.NS": {
        "name": "Dr. Lal PathLabs",
        "sector": "Healthcare",
        "notes": "listed 23 Dec 2015",
        "tags": ["Smallcap", "Hospitals"],
    },
    "IIFL.NS": {
        "name": "IIFL Finance",
        "sector": "Financial Services",
        "notes": "listed 17 May 2005",
        "tags": ["Smallcap"],
    },
    "INOXWIND.NS": {
        "name": "Inox Wind",
        "sector": "Capital Goods",
        "notes": "listed 9 Apr 2015",
        "tags": ["Smallcap", "Energy"],
    },
    "KAYNES.NS": {
        "name": "Kaynes Technology India",
        "sector": "Capital Goods",
        "notes": "listed 22 Nov 2022; show its real first date, never invent pre-listing data",
        "tags": ["Smallcap"],
    },
    "KFINTECH.NS": {
        "name": "KFin Technologies",
        "sector": "Financial Services",
        "notes": "listed 29 Dec 2022; show its real first date, never invent pre-listing data",
        "tags": ["Smallcap", "CapitalMarket"],
    },
    "MTARTECH.NS": {
        "name": "MTAR Technologies",
        "sector": "Capital Goods",
        "notes": "listed 15 Mar 2021",
        "tags": ["Smallcap"],
    },
    "MANAPPURAM.NS": {
        "name": "Manappuram Finance",
        "sector": "Financial Services",
        "notes": "listed 30 Jun 2010",
        "tags": ["Smallcap"],
    },
    "NATCOPHARM.NS": {
        "name": "NATCO Pharma",
        "sector": "Healthcare",
        "notes": "long history",
        "tags": ["Smallcap"],
    },
    "NBCC.NS": {
        "name": "NBCC (India)",
        "sector": "Construction",
        "notes": "listed 12 Apr 2012",
        "tags": ["Smallcap"],
    },
    "NAVINFLUOR.NS": {
        "name": "Navin Fluorine International",
        "sector": "Chemicals",
        "notes": "listed 1 Jun 2007",
        "tags": ["Smallcap"],
    },
    "ONESOURCE.NS": {
        "name": "Onesource Specialty Pharma",
        "sector": "Healthcare",
        "notes": "listed 24 Jan 2025; show its real first date, never invent pre-listing data",
        "tags": ["Smallcap"],
    },
    "PNBHOUSING.NS": {
        "name": "PNB Housing Finance",
        "sector": "Financial Services",
        "notes": "listed 7 Nov 2016",
        "tags": ["Smallcap"],
    },
    "PPLPHARMA.NS": {
        "name": "Piramal Pharma",
        "sector": "Healthcare",
        "notes": "listed 19 Oct 2022; show its real first date, never invent pre-listing data",
        "tags": ["Smallcap"],
    },
    "RBLBANK.NS": {
        "name": "RBL Bank",
        "sector": "Financial Services",
        "notes": "listed 31 Aug 2016",
        "tags": ["Smallcap", "PrivateBank"],
    },
    "SYNGENE.NS": {
        "name": "Syngene International",
        "sector": "Healthcare",
        "notes": "listed 11 Aug 2015",
        "tags": ["Smallcap"],
    },
    "TATACHEM.NS": {
        "name": "Tata Chemicals",
        "sector": "Chemicals",
        "notes": "long history",
        "tags": ["Smallcap"],
    },
    "TATATECH.NS": {
        "name": "Tata Technologies",
        "sector": "Information Technology",
        "notes": "listed 30 Nov 2023; show its real first date, never invent pre-listing data",
        "tags": ["Smallcap"],
    },
    "WOCKPHARMA.NS": {
        "name": "Wockhardt",
        "sector": "Healthcare",
        "notes": "long history",
        "tags": ["Smallcap"],
    },
    "COALINDIA.NS": {
        "name": "Coal India",
        "sector": "Oil Gas & Consumable Fuels",
        "notes": "listed 4 Nov 2010",
        "tags": ["AlphaQVLowVol", "Energy"],
    },
    "NTPC.NS": {
        "name": "NTPC",
        "sector": "Power",
        "notes": "listed 5 Nov 2004",
        "tags": ["AlphaQVLowVol", "Energy"],
    },
    "ICICIBANK.NS": {
        "name": "ICICI Bank",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["AlphaQVLowVol", "PrivateBank"],
    },
    "ALKEM.NS": {
        "name": "Alkem Laboratories",
        "sector": "Healthcare",
        "notes": "listed 23 Dec 2015",
        "tags": ["AlphaQVLowVol"],
    },
    "CIPLA.NS": {
        "name": "Cipla",
        "sector": "Healthcare",
        "notes": "long history",
        "tags": ["AlphaQVLowVol"],
    },
    "DRREDDY.NS": {
        "name": "Dr. Reddy's Laboratories",
        "sector": "Healthcare",
        "notes": "long history",
        "tags": ["AlphaQVLowVol"],
    },
    "EICHERMOT.NS": {
        "name": "Eicher Motors",
        "sector": "Automobile and Auto Components",
        "notes": "long history",
        "tags": ["AlphaQVLowVol"],
    },
    "GRASIM.NS": {
        "name": "Grasim Industries",
        "sector": "Construction Materials",
        "notes": "long history",
        "tags": ["AlphaQVLowVol"],
    },
    "HINDUNILVR.NS": {
        "name": "Hindustan Unilever",
        "sector": "Fast Moving Consumer Goods",
        "notes": "long history; former NSE symbol HINDLEVER",
        "tags": ["AlphaQVLowVol", "NonCyclicalConsumer"],
    },
    "MARUTI.NS": {
        "name": "Maruti Suzuki India",
        "sector": "Automobile and Auto Components",
        "notes": "listed 9 Jul 2003",
        "tags": ["AlphaQVLowVol"],
    },
    "NMDC.NS": {
        "name": "NMDC",
        "sector": "Metals & Mining",
        "notes": "long history",
        "tags": ["AlphaQVLowVol", "Metal"],
    },
    "PFC.NS": {
        "name": "Power Finance Corporation",
        "sector": "Financial Services",
        "notes": "listed 23 Feb 2007",
        "tags": ["AlphaQVLowVol", "NiftyNext50"],
    },
    "SBIN.NS": {
        "name": "State Bank of India",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["AlphaQVLowVol"],
    },
    "SUNPHARMA.NS": {
        "name": "Sun Pharmaceutical Industries",
        "sector": "Healthcare",
        "notes": "long history",
        "tags": ["AlphaQVLowVol"],
    },
    "HINDALCO.NS": {
        "name": "Hindalco Industries",
        "sector": "Metals & Mining",
        "notes": "long history; former NSE symbol HINDALC0",
        "tags": ["AlphaQVLowVol", "Metal"],
    },
    "COLPAL.NS": {
        "name": "Colgate Palmolive (India)",
        "sector": "Fast Moving Consumer Goods",
        "notes": "long history; former NSE symbol COLGATE",
        "tags": ["AlphaQVLowVol", "NonCyclicalConsumer"],
    },
    "SHALBY.NS": {
        "name": "Shalby",
        "sector": "Healthcare",
        "notes": "listed 15 Dec 2017",
        "tags": ["Hospitals"],
    },
    "FORTIS.NS": {
        "name": "Fortis Healthcare",
        "sector": "Healthcare",
        "notes": "listed 9 May 2007",
        "tags": ["Hospitals"],
    },
    "RAINBOW.NS": {
        "name": "Rainbow Children's Medicare",
        "sector": "Healthcare",
        "notes": "listed 10 May 2022; show its real first date, never invent pre-listing data",
        "tags": ["Hospitals"],
    },
    "ASTERDM.NS": {
        "name": "Aster DM Healthcare",
        "sector": "Healthcare",
        "notes": "listed 26 Feb 2018",
        "tags": ["Hospitals"],
    },
    "MAXHEALTH.NS": {
        "name": "Max Healthcare Institute",
        "sector": "Healthcare",
        "notes": "listed 21 Aug 2020",
        "tags": ["Hospitals"],
    },
    "GKSL.NS": {
        "name": "Gujarat Kidney and Super Speciality",
        "sector": "Healthcare",
        "notes": "listed 30 Dec 2025; show its real first date, never invent pre-listing data",
        "tags": ["Hospitals"],
    },
    "NEPHROCARE.NS": {
        "name": "Nephro Care India",
        "sector": "Healthcare",
        "notes": "listed 5 Jul 2024; NSE SME (series SM); show its real first date, never invent pre-listing data",
        "tags": ["Hospitals"],
    },
    "SURAKSHA.NS": {
        "name": "Suraksha Diagnostic",
        "sector": "Healthcare",
        "notes": "listed 6 Dec 2024; show its real first date, never invent pre-listing data",
        "tags": ["Hospitals"],
    },
    "KRSNAA.NS": {
        "name": "Krsnaa Diagnostics",
        "sector": "Healthcare",
        "notes": "listed 16 Aug 2021",
        "tags": ["Hospitals"],
    },
    "VIJAYA.NS": {
        "name": "Vijaya Diagnostic Centre",
        "sector": "Healthcare",
        "notes": "listed 14 Sep 2021",
        "tags": ["Hospitals"],
    },
    "THYROCARE.NS": {
        "name": "Thyrocare Technologies",
        "sector": "Healthcare",
        "notes": "listed 9 May 2016",
        "tags": ["Hospitals"],
    },
    "MEDANTA.NS": {
        "name": "Global Health (Medanta)",
        "sector": "Healthcare",
        "notes": "listed 16 Nov 2022; show its real first date, never invent pre-listing data",
        "tags": ["Hospitals"],
    },
    "METROPOLIS.NS": {
        "name": "Metropolis Healthcare",
        "sector": "Healthcare",
        "notes": "listed 15 Apr 2019",
        "tags": ["Hospitals"],
    },
    "HCG.NS": {
        "name": "HealthCare Global Enterprises",
        "sector": "Healthcare",
        "notes": "listed 30 Mar 2016",
        "tags": ["Hospitals"],
    },
    "AGARWALEYE.NS": {
        "name": "Dr. Agarwal's Health Care",
        "sector": "Healthcare",
        "notes": "listed 4 Feb 2025; show its real first date, never invent pre-listing data",
        "tags": ["Hospitals"],
    },
    "GPTHEALTH.NS": {
        "name": "GPT Healthcare",
        "sector": "Healthcare",
        "notes": "listed 29 Feb 2024; show its real first date, never invent pre-listing data",
        "tags": ["Hospitals"],
    },
    "APOLLOHOSP.NS": {
        "name": "Apollo Hospitals Enterprise",
        "sector": "Healthcare",
        "notes": "long history",
        "tags": ["Hospitals"],
    },
    "PETRONET.NS": {
        "name": "Petronet LNG",
        "sector": "Energy",
        "notes": "listed 26 Mar 2004",
        "tags": ["Energy", "OilGas"],
    },
    "OIL.NS": {
        "name": "Oil India",
        "sector": "Energy",
        "notes": "listed 30 Sep 2009",
        "tags": ["Energy", "OilGas"],
    },
    "POWERGRID.NS": {
        "name": "Power Grid Corporation of India",
        "sector": "Utilities",
        "notes": "listed 5 Oct 2007",
        "tags": ["Energy"],
    },
    "TATAPOWER.NS": {
        "name": "Tata Power Company",
        "sector": "Utilities",
        "notes": "long history",
        "tags": ["Energy", "TataGroup", "NiftyNext50"],
    },
    "NTPCGREEN.NS": {
        "name": "NTPC Green Energy",
        "sector": "Utilities",
        "notes": "listed 27 Nov 2024; show its real first date, never invent pre-listing data",
        "tags": ["Energy"],
    },
    "IOC.NS": {
        "name": "Indian Oil Corporation",
        "sector": "Energy",
        "notes": "long history",
        "tags": ["Energy", "NiftyNext50", "OilGas"],
    },
    "NHPC.NS": {
        "name": "NHPC",
        "sector": "Utilities",
        "notes": "listed 1 Sep 2009",
        "tags": ["Energy"],
    },
    "SIEMENS.NS": {
        "name": "Siemens",
        "sector": "Industrials",
        "notes": "long history",
        "tags": ["Energy", "NiftyNext50"],
    },
    "GAIL.NS": {
        "name": "GAIL (India)",
        "sector": "Utilities",
        "notes": "long history",
        "tags": ["Energy", "NiftyNext50", "OilGas"],
    },
    "ABB.NS": {
        "name": "ABB India",
        "sector": "Industrials",
        "notes": "long history",
        "tags": ["Energy", "NiftyNext50"],
    },
    "CGPOWER.NS": {
        "name": "CG Power and Industrial Solutions",
        "sector": "Industrials",
        "notes": "long history",
        "tags": ["Energy", "NiftyNext50"],
    },
    "BPCL.NS": {
        "name": "Bharat Petroleum Corporation",
        "sector": "Energy",
        "notes": "long history",
        "tags": ["Energy", "NiftyNext50", "OilGas"],
    },
    "RPOWER.NS": {
        "name": "Reliance Power",
        "sector": "Utilities",
        "notes": "listed 11 Feb 2008",
        "tags": ["Energy"],
    },
    "CESC.NS": {
        "name": "CESC",
        "sector": "Utilities",
        "notes": "long history",
        "tags": ["Energy"],
    },
    "NLCINDIA.NS": {
        "name": "NLC India",
        "sector": "Utilities",
        "notes": "long history",
        "tags": ["Energy"],
    },
    "ADANIENSOL.NS": {
        "name": "Adani Energy Solutions",
        "sector": "Utilities",
        "notes": "listed 31 Jul 2015",
        "tags": ["Energy", "NiftyNext50"],
    },
    "TORNTPOWER.NS": {
        "name": "Torrent Power",
        "sector": "Utilities",
        "notes": "listed 28 Nov 2006",
        "tags": ["Energy"],
    },
    "ATGL.NS": {
        "name": "Adani Total Gas",
        "sector": "Utilities",
        "notes": "listed 5 Nov 2018",
        "tags": ["Energy", "OilGas"],
    },
    "ENRIN.NS": {
        "name": "Siemens Energy India",
        "sector": "Utilities",
        "notes": "listed 19 Jun 2025; show its real first date, never invent pre-listing data",
        "tags": ["Energy", "NiftyNext50"],
    },
    "ADANIGREEN.NS": {
        "name": "Adani Green Energy",
        "sector": "Utilities",
        "notes": "listed 18 Jun 2018",
        "tags": ["Energy", "NiftyNext50"],
    },
    "POWERINDIA.NS": {
        "name": "Hitachi Energy India",
        "sector": "Industrials",
        "notes": "listed 30 Mar 2020",
        "tags": ["Energy", "NiftyNext50"],
    },
    "ADANIPOWER.NS": {
        "name": "Adani Power",
        "sector": "Utilities",
        "notes": "listed 20 Aug 2009",
        "tags": ["Energy", "NiftyNext50"],
    },
    "JSWENERGY.NS": {
        "name": "JSW Energy",
        "sector": "Utilities",
        "notes": "listed 4 Jan 2010",
        "tags": ["Energy"],
    },
    "HINDPETRO.NS": {
        "name": "Hindustan Petroleum Corporation",
        "sector": "Energy",
        "notes": "long history",
        "tags": ["Energy", "OilGas"],
    },
    "MGL.NS": {
        "name": "Mahanagar Gas",
        "sector": "Utilities",
        "notes": "listed 1 Jul 2016",
        "tags": ["Energy", "OilGas"],
    },
    "TATASTEEL.NS": {
        "name": "Tata Steel",
        "sector": "Basic Materials",
        "notes": "long history",
        "tags": ["TataGroup", "Metal"],
    },
    "TMCV.NS": {
        "name": "Tata Motors (Commercial Vehicles)",
        "sector": "Automobile and Auto Components",
        "notes": "listed 12 Nov 2025; show its real first date, never invent pre-listing data",
        "tags": ["TataGroup", "NiftyNext50"],
    },
    "TMPV.NS": {
        "name": "Tata Motors Passenger Vehicles",
        "sector": "Consumer Cyclical",
        "notes": "long history",
        "tags": ["TataGroup"],
    },
    "VOLTAS.NS": {
        "name": "Voltas",
        "sector": "Consumer Cyclical",
        "notes": "long history",
        "tags": ["TataGroup", "NonCyclicalConsumer"],
    },
    "TATACONSUM.NS": {
        "name": "Tata Consumer Products",
        "sector": "Consumer Defensive",
        "notes": "long history",
        "tags": ["TataGroup", "NonCyclicalConsumer"],
    },
    "KOTAKBANK.NS": {
        "name": "Kotak Mahindra Bank",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["PrivateBank"],
    },
    "IDFCFIRSTB.NS": {
        "name": "IDFC First Bank",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["PrivateBank"],
    },
    "HDFCBANK.NS": {
        "name": "HDFC Bank",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["PrivateBank"],
    },
    "AXISBANK.NS": {
        "name": "Axis Bank",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["PrivateBank"],
    },
    "LEMONTREE.NS": {
        "name": "Lemon Tree Hotels",
        "sector": "Consumer Cyclical",
        "notes": "listed 9 Apr 2018",
        "tags": ["Tourism", "Hotels"],
    },
    "TBOTEK.NS": {
        "name": "TBO Tek",
        "sector": "Consumer Cyclical",
        "notes": "listed 15 May 2024; show its real first date, never invent pre-listing data",
        "tags": ["Tourism"],
    },
    "DEVYANI.NS": {
        "name": "Devyani International",
        "sector": "Consumer Cyclical",
        "notes": "listed 16 Aug 2021",
        "tags": ["Tourism"],
    },
    "INDIGO.NS": {
        "name": "InterGlobe Aviation",
        "sector": "Industrials",
        "notes": "listed 10 Nov 2015",
        "tags": ["Tourism", "NonCyclicalConsumer"],
    },
    "JUBLFOOD.NS": {
        "name": "Jubilant Foodworks",
        "sector": "Consumer Cyclical",
        "notes": "listed 8 Feb 2010",
        "tags": ["Tourism"],
    },
    "ITCHOTELS.NS": {
        "name": "ITC Hotels",
        "sector": "Consumer Cyclical",
        "notes": "listed 29 Jan 2025; show its real first date, never invent pre-listing data",
        "tags": ["Tourism", "Hotels"],
    },
    "BLS.NS": {
        "name": "BLS International Services",
        "sector": "Industrials",
        "notes": "listed 15 Jun 2016",
        "tags": ["Tourism"],
    },
    "GMRAIRPORT.NS": {
        "name": "GMR Airports",
        "sector": "Industrials",
        "notes": "listed 21 Aug 2006",
        "tags": ["Tourism"],
    },
    "JUNIPER.NS": {
        "name": "Juniper Hotels",
        "sector": "Consumer Cyclical",
        "notes": "listed 28 Feb 2024; show its real first date, never invent pre-listing data",
        "tags": ["Hotels"],
    },
    "THELEELA.NS": {
        "name": "The Leela (Schloss Bangalore)",
        "sector": "Consumer Cyclical",
        "notes": "listed 2 Jun 2025; show its real first date, never invent pre-listing data",
        "tags": ["Hotels"],
    },
    "CHALET.NS": {
        "name": "Chalet Hotels",
        "sector": "Consumer Cyclical",
        "notes": "listed 7 Feb 2019",
        "tags": ["Hotels"],
    },
    "VENTIVE.NS": {
        "name": "Ventive Hospitality",
        "sector": "Consumer Cyclical",
        "notes": "listed 30 Dec 2024; show its real first date, never invent pre-listing data",
        "tags": ["Hotels"],
    },
    "ITDC.NS": {
        "name": "India Tourism Development Corporation",
        "sector": "Consumer Cyclical",
        "notes": "listed 30 Dec 2016",
        "tags": ["Hotels"],
    },
    "MHRIL.NS": {
        "name": "Mahindra Holidays & Resorts India",
        "sector": "Consumer Cyclical",
        "notes": "listed 16 Jul 2009",
        "tags": ["Hotels"],
    },
    "PARKHOTELS.NS": {
        "name": "Apeejay Surrendra Park Hotels",
        "sector": "Consumer Cyclical",
        "notes": "listed 12 Feb 2024; show its real first date, never invent pre-listing data",
        "tags": ["Hotels"],
    },
    "BRIGHOTEL.NS": {
        "name": "Brigade Hotel Ventures",
        "sector": "Consumer Cyclical",
        "notes": "listed 31 Jul 2025; show its real first date, never invent pre-listing data",
        "tags": ["Hotels"],
    },
    "SAMHI.NS": {
        "name": "SAMHI Hotels",
        "sector": "Consumer Cyclical",
        "notes": "listed 22 Sep 2023; show its real first date, never invent pre-listing data",
        "tags": ["Hotels"],
    },
    "VAML.NS": {
        "name": "Vedanta Aluminium Metal",
        "sector": "Basic Materials",
        "notes": "listed 15 Jun 2026 (demerged from Vedanta); show its real first date, never invent pre-listing data",
        "tags": ["Metal", "NiftyNext50"],
    },
    "HINDCOPPER.NS": {
        "name": "Hindustan Copper",
        "sector": "Basic Materials",
        "notes": "NSE listing 8 Jan 2010",
        "tags": ["Metal"],
    },
    "LLOYDSME.NS": {
        "name": "Lloyds Metals and Energy",
        "sector": "Basic Materials",
        "notes": "NSE listing 17 Jul 2023; show its real first date, never invent pre-listing data",
        "tags": ["Metal"],
    },
    "ADANIENT.NS": {
        "name": "Adani Enterprises",
        "sector": "Energy",
        "notes": "long history (former NSE symbol ADANIEXPO)",
        "tags": ["Metal"],
    },
    "JSL.NS": {
        "name": "Jindal Stainless",
        "sector": "Basic Materials",
        "notes": "NSE listing 17 Nov 2003 (former NSE symbol JSTAINLESS)",
        "tags": ["Metal"],
    },
    "TVSMOTOR.NS": {
        "name": "TVS Motor Company",
        "sector": "Consumer Cyclical",
        "notes": "long history",
        "tags": ["NiftyNext50"],
    },
    "DIVISLAB.NS": {
        "name": "Divi's Laboratories",
        "sector": "Healthcare",
        "notes": "NSE from 12 Mar 2003",
        "tags": ["NiftyNext50"],
    },
    "DLF.NS": {
        "name": "DLF",
        "sector": "Real Estate",
        "notes": "listed 5 Jul 2007",
        "tags": ["NiftyNext50"],
    },
    "DMART.NS": {
        "name": "Avenue Supermarts (DMart)",
        "sector": "Consumer Defensive",
        "notes": "listed 21 Mar 2017",
        "tags": ["NiftyNext50", "NonCyclicalConsumer"],
    },
    "IDEA.NS": {
        "name": "Vodafone Idea",
        "sector": "Communication Services",
        "notes": "listed 9 Mar 2007",
        "tags": ["NiftyNext50", "NonCyclicalConsumer"],
    },
    "MUTHOOTFIN.NS": {
        "name": "Muthoot Finance",
        "sector": "Financial Services",
        "notes": "listed 6 May 2011",
        "tags": ["NiftyNext50"],
    },
    "HYUNDAI.NS": {
        "name": "Hyundai Motor India",
        "sector": "Consumer Cyclical",
        "notes": "listed 22 Oct 2024; show its real first date, never invent pre-listing data",
        "tags": ["NiftyNext50"],
    },
    "HDFCAMC.NS": {
        "name": "HDFC Asset Management",
        "sector": "Financial Services",
        "notes": "listed 6 Aug 2018",
        "tags": ["NiftyNext50", "CapitalMarket"],
    },
    "WIPRO.NS": {
        "name": "Wipro",
        "sector": "Technology",
        "notes": "long history",
        "tags": ["NiftyNext50"],
    },
    "UNIONBANK.NS": {
        "name": "Union Bank of India",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["NiftyNext50"],
    },
    "PNB.NS": {
        "name": "Punjab National Bank",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["NiftyNext50"],
    },
    "HAL.NS": {
        "name": "Hindustan Aeronautics",
        "sector": "Industrials",
        "notes": "listed 28 Mar 2018",
        "tags": ["NiftyNext50"],
    },
    "BANKBARODA.NS": {
        "name": "Bank of Baroda",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["NiftyNext50"],
    },
    "MAZDOCK.NS": {
        "name": "Mazagon Dock Shipbuilders",
        "sector": "Industrials",
        "notes": "listed 12 Oct 2020",
        "tags": ["NiftyNext50"],
    },
    "VBL.NS": {
        "name": "Varun Beverages",
        "sector": "Consumer Defensive",
        "notes": "listed 8 Nov 2016",
        "tags": ["NiftyNext50", "NonCyclicalConsumer"],
    },
    "POLYCAB.NS": {
        "name": "Polycab India",
        "sector": "Industrials",
        "notes": "listed 16 Apr 2019",
        "tags": ["NiftyNext50"],
    },
    "GODREJCP.NS": {
        "name": "Godrej Consumer Products",
        "sector": "Consumer Defensive",
        "notes": "long history",
        "tags": ["NiftyNext50", "NonCyclicalConsumer"],
    },
    "CANBK.NS": {
        "name": "Canara Bank",
        "sector": "Financial Services",
        "notes": "long history",
        "tags": ["NiftyNext50"],
    },
    "PIDILITIND.NS": {
        "name": "Pidilite Industries",
        "sector": "Basic Materials",
        "notes": "long history",
        "tags": ["NiftyNext50"],
    },
    "BOSCHLTD.NS": {
        "name": "Bosch",
        "sector": "Consumer Cyclical",
        "notes": "long history (former NSE symbol MICO)",
        "tags": ["NiftyNext50"],
    },
    "CUMMINSIND.NS": {
        "name": "Cummins India",
        "sector": "Industrials",
        "notes": "long history (former NSE symbol KIRLOSKCUM)",
        "tags": ["NiftyNext50"],
    },
    "BAJAJHLDNG.NS": {
        "name": "Bajaj Holdings & Investment",
        "sector": "Financial Services",
        "notes": "long history (former NSE symbol BAJAJAUTO)",
        "tags": ["NiftyNext50"],
    },
    "LTM.NS": {
        "name": "LTM (LTIMindtree)",
        "sector": "Technology",
        "notes": "listed 21 Jul 2016 (former NSE symbols LTIM, LTI)",
        "tags": ["NiftyNext50"],
    },
    "TATACAP.NS": {
        "name": "Tata Capital",
        "sector": "Financial Services",
        "notes": "listed 13 Oct 2025; show its real first date, never invent pre-listing data",
        "tags": ["NiftyNext50"],
    },
    "IRFC.NS": {
        "name": "Indian Railway Finance Corporation",
        "sector": "Financial Services",
        "notes": "listed 29 Jan 2021",
        "tags": ["NiftyNext50"],
    },
    "ETERNAL.NS": {
        "name": "Eternal (Zomato)",
        "sector": "Consumer Cyclical",
        "notes": "listed 23 Jul 2021 (former NSE symbol ZOMATO)",
        "tags": ["NonCyclicalConsumer"],
    },
    "NYKAA.NS": {
        "name": "FSN E-Commerce Ventures (Nykaa)",
        "sector": "Consumer Cyclical",
        "notes": "listed 10 Nov 2021",
        "tags": ["NonCyclicalConsumer"],
    },
    "ASIANPAINT.NS": {
        "name": "Asian Paints",
        "sector": "Basic Materials",
        "notes": "long history",
        "tags": ["NonCyclicalConsumer"],
    },
    "LENSKART.NS": {
        "name": "Lenskart Solutions",
        "sector": "Healthcare",
        "notes": "listed 10 Nov 2025; show its real first date, never invent pre-listing data",
        "tags": ["NonCyclicalConsumer"],
    },
    "VMM.NS": {
        "name": "Vishal Mega Mart",
        "sector": "Consumer Cyclical",
        "notes": "listed 18 Dec 2024; show its real first date, never invent pre-listing data",
        "tags": ["NonCyclicalConsumer"],
    },
    "UNITDSPR.NS": {
        "name": "United Spirits",
        "sector": "Consumer Defensive",
        "notes": "long history (former NSE symbol MCDOWELL-N)",
        "tags": ["NonCyclicalConsumer"],
    },
    "DABUR.NS": {
        "name": "Dabur India",
        "sector": "Consumer Defensive",
        "notes": "long history",
        "tags": ["NonCyclicalConsumer"],
    },
    "TATACOMM.NS": {
        "name": "Tata Communications",
        "sector": "Communication Services",
        "notes": "long history (former NSE symbol VSNL)",
        "tags": ["NonCyclicalConsumer"],
    },
    "CHENNPETRO.NS": {
        "name": "Chennai Petroleum Corporation",
        "sector": "Energy",
        "notes": "long history",
        "tags": ["OilGas"],
    },
    "AEGISVOPAK.NS": {
        "name": "Aegis Vopak Terminals",
        "sector": "Energy",
        "notes": "listed 2 Jun 2025; show its real first date, never invent pre-listing data",
        "tags": ["OilGas"],
    },
    "UTIAMC.NS": {
        "name": "UTI Asset Management",
        "sector": "Financial Services",
        "notes": "listed 12 Oct 2020",
        "tags": ["CapitalMarket"],
    },
    "MOTILALOFS.NS": {
        "name": "Motilal Oswal Financial Services",
        "sector": "Financial Services",
        "notes": "listed 11 Sep 2007",
        "tags": ["CapitalMarket"],
    },
    "NUVAMA.NS": {
        "name": "Nuvama Wealth Management",
        "sector": "Financial Services",
        "notes": "listed 26 Sep 2023; show its real first date, never invent pre-listing data",
        "tags": ["CapitalMarket"],
    },
    "GROWW.NS": {
        "name": "Billionbrains Garage Ventures (Groww)",
        "sector": "Financial Services",
        "notes": "listed 12 Nov 2025; show its real first date, never invent pre-listing data",
        "tags": ["CapitalMarket"],
    },
    "IEX.NS": {
        "name": "Indian Energy Exchange",
        "sector": "Financial Services",
        "notes": "listed 23 Oct 2017",
        "tags": ["CapitalMarket"],
    },
    "NAM-INDIA.NS": {
        "name": "Nippon Life India Asset Management",
        "sector": "Financial Services",
        "notes": "listed 6 Nov 2017 (former NSE symbol RNAM)",
        "tags": ["CapitalMarket"],
    },
    "BSE.NS": {
        "name": "BSE Ltd",
        "sector": "Financial Services",
        "notes": "listed 3 Feb 2017",
        "tags": ["CapitalMarket"],
    },
    "ABSLAMC.NS": {
        "name": "Aditya Birla Sun Life AMC",
        "sector": "Financial Services",
        "notes": "listed 11 Oct 2021",
        "tags": ["CapitalMarket"],
    },
    "ICICIAMC.NS": {
        "name": "ICICI Prudential Asset Management",
        "sector": "Financial Services",
        "notes": "listed 19 Dec 2025; show its real first date, never invent pre-listing data",
        "tags": ["CapitalMarket"],
    },
}


# Stock tags: the sidebar Tag option shows "ALL" (every stock above) or one tag's stocks.
# A stock belongs to a tag when the tag's name is in its "tags" list.
TAG_ALL = "ALL"
TAGS = [TAG_ALL, "Midselect", "Smallcap", "AlphaQVLowVol", "Hospitals", "Energy", "TataGroup", "PrivateBank", "Tourism", "Hotels", "Metal", "NiftyNext50", "NonCyclicalConsumer", "OilGas", "CapitalMarket"]


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
