# config.py
# ============================================================================
# ALLE data-input voor de app: bedrijven, studies, timeline, overrides.
#
# Hoe voeg je een bedrijf toe? Voeg één entry toe in COMPANIES en vul
# STUDY_DATA / TIMELINE_DATA aan. De rest werkt automatisch.
# ============================================================================

# ============================================================================
# COMPANY REGISTRY
# ============================================================================
# Each entry maps a display name to its identifiers for every data source:
#   - gvkey:        Company identifier (financials CSV)
#   - yf_ticker:    Yahoo Finance ticker (stock data)
#   - search_terms: Google Trends search terms (SerpApi) — each term is
#                   fetched with its own query so its interest values are
#                   normalized 0-100 independently of the other terms.
# ============================================================================

COMPANIES = {
    "Century Lithium": {
        "gvkey": 106098,
        "yf_ticker": "LCE.V",
        "search_terms": ['"Century Lithium"', '"LCE stock"', 'LCE.V'],
        "short_name": "Century",
        "color": "#2E86C1",
    },
    "American Battery Technology Co": {
        "gvkey": 26366,
        "yf_ticker": "ABAT",
        "search_terms": ['"American Battery Technology"', '"ABAT stock"', '"Tonopah Flats"'],
        "short_name": "ABTC",
        "color": "#F39C12",
    },
    "Ioneer": {
        "gvkey": 290341,
        "yf_ticker": "IONR",
        "search_terms": ['ioneer', '"IONR stock"', '"Rhyolite Ridge"'],
        "short_name": "Ioneer",
        "color": "#27AE60",
    },
    "Lithium Americas": {
        "gvkey": 43404,
        "yf_ticker": "LAC",
        "search_terms": ['"Lithium Americas"', '"LAC stock"', '"Thacker Pass"'],
        "short_name": "LAC",
        "color": "#8E44AD",
    },
    "Surge Battery Metals": {
        "gvkey": 106045,
        "yf_ticker": "NILI",
        "search_terms": ['"Surge Battery Metals"', '"NILI stock"', '"Surge Battery"'],
        "short_name": "Surge",
        "color": "#E67E22",
    },
    "American Lithium Corp": {
        "gvkey": 107393,
        "yf_ticker": "LIACF",
        "search_terms": ['"American Lithium"', '"LIACF stock"', 'LI', 'TLC'],
        "short_name": "ALC",
        "color": "#C0392B",
    },
}

DEFAULT_COMPANY = "Century Lithium"

# ============================================================================
# STOCK PERFORMANCE CLUSTERS
# ============================================================================
# Grouped stock performance comparison so investors can compare lithium
# juniors from every region producing the commodity.
# Each entry maps a display label to its Yahoo Finance ticker.
# ============================================================================
STOCK_CLUSTERS = {

    # =========================
    # 🇺🇸 USA
    # =========================

    "Nevada Juniors": {
        "label": "USA",
        "members": {
            "Lithium Americas": "LAC",
            "American Battery Technology": "ABAT",
            "Ioneer": "IONR",
            "Century Lithium": "LCE.V",
            "Surge Battery Metals": "NILIF",
        }
    },

    # =========================
    # 🇨🇦 CANADA
    # =========================

    "Canada Juniors": {
        "label": "Canada",
        "members": {
            "Patriot Battery Metals": "PMET",
            "Frontier Lithium": "FL",
            "Brunswick Exploration": "BRW",
            "Lithium Ionic": "LTH.V",
            "E3 Lithium": "ETL",
            "Rock Tech Lithium": "RCK.V",
        }
    },

    # =========================
    # 🇦🇷🇨🇱🇧🇴 LITHIUM TRIANGLE
    # =========================

    "Lithium Triangle Juniors": {
        "label": "Lithium Triangle",
        "members": {
            "Galan Lithium": "GLN.AX",
            "Lake Resources": "LKE.AX",
            "Lithium Argentina": "LAR.TO",
            "Lithium Chile": "LITH.V",
        }
    },

    # =========================
    # 🇦🇺 AUSTRALIA
    # =========================

    "Australia Juniors": {
        "label": "Australia",
        "members": {
            "Delta Lithium": "DLI.AX",
            "Core Lithium": "CXO.AX",
            "Liontown Resources": "LTR.AX",
        }
    },

    # =========================
    # 🇧🇷 BRAZIL
    # =========================

    "Brazil Juniors": {
        "label": "Brazil",
        "members": {
            "Atlas Lithium": "ATLX",
            "Sigma Lithium": "SGML",
        }
    },

    # =========================
    # 🌍 AFRICA
    # =========================

    "Africa Juniors": {
        "label": "Africa",
        "members": {
            "Atlantic Lithium": "ALLIF",
            "Kodal Minerals": "KOD.L",
            "Tantalex Lithium Resources": "TTX.V",
        }
    },

    # =========================
    # 🇪🇺 EUROPE
    # =========================

    "Europe Juniors": {
        "label": "Europe",
        "members": {
            "European Lithium": "EUR.AX",
            "Vulcan Energy": "VUL.AX",
            "Savannah Resources": "SAV.L",
            "European Metals Holdings": "EMH.L",
        }
    },
}

# ============================================================================
# TIME PERIODS FOR STOCK CHART FILTERING
# ============================================================================
# Time period options shown as a filter above the stock performance charts.
# Each entry maps a display label to the number of calendar days to look back
# from the most recent trading day available in the cached 1-year data.
# ============================================================================
TIME_PERIODS = [
    {"label": "1D",   "days": 1},
    {"label": "7D",   "days": 7},
    {"label": "30D",  "days": 30},
    {"label": "90D",  "days": 90},
    {"label": "1Y",   "days": 365},
]

# 1D by default: the stock chart opens on the live intraday view — the
# window returning visitors check first.
DEFAULT_TIME_PERIOD = "1D"

# ============================================================================
# GOOGLE ADS SEARCH VOLUME (per company, monthly)
# ============================================================================
# Monthly Google Ads search volume for each company's brand terms, plus two
# sector-wide benchmarks ("lithium stocks" and "Nevada Lithium") that are
# shown alongside every company's own line in the search-volume chart.
# ============================================================================
SEARCH_DATA = {
    "Lithium Americas": {
        "months": ["8/2025", "9/2025", "10/2025", "11/2025", "12/2025", "1/2026", "2/2026", "3/2026", "4/2026", "5/2026", "6/2026", "7/2026"],
        "values": [4400, 33100, 27100, 8100, 4400, 8100, 4400, 4400, 4400, 5400, 5400, 3600],
    },
    "American Battery Technology": {
        "months": ["8/2025", "9/2025", "10/2025", "11/2025", "12/2025", "1/2026", "2/2026", "3/2026", "4/2026", "5/2026", "6/2026", "7/2026"],
        "values": [880, 1300, 5400, 1900, 1000, 1000, 880, 480, 590, 1000, 880, 590],
    },
    "Ioneer": {
        "months": ["8/2025", "9/2025", "10/2025", "11/2025", "12/2025", "1/2026", "2/2026", "3/2026", "4/2026", "5/2026", "6/2026", "7/2026"],
        "values": [720, 880, 1300, 590, 880, 880, 1900, 1000, 720, 480, 720, 720],
    },
    "Century Lithium": {
        "months": ["8/2025", "9/2025", "10/2025", "11/2025", "12/2025", "1/2026", "2/2026", "3/2026", "4/2026", "5/2026", "6/2026", "7/2026"],
        "values": [140, 140, 260, 140, 170, 320, 320, 260, 170, 140, 170, 140],
    },
    "Surge Battery Metals": {
        "months": ["8/2025", "9/2025", "10/2025", "11/2025", "12/2025", "1/2026", "2/2026", "3/2026", "4/2026", "5/2026", "6/2026", "7/2026"],
        "values": [110, 140, 480, 210, 210, 320, 260, 170, 170, 210, 260, 170],
    },
    "lithium stocks": {
        "months": ["8/2025", "9/2025", "10/2025", "11/2025", "12/2025", "1/2026", "2/2026", "3/2026", "4/2026", "5/2026", "6/2026"],
        "values": [5400, 8100, 12100, 3600, 3600, 6600, 4400, 3600, 3600, 4400, 2900],
    },
    "Nevada Lithium": {
        "months": ["8/2025", "9/2025", "10/2025", "11/2025", "12/2025", "1/2026", "2/2026", "3/2026", "4/2026", "5/2026", "6/2026"],
        "values": [390, 480, 590, 390, 390, 480, 2900, 480, 320, 390, 320],
    },
}

# ============================================================================
# STUDY STAGE LABELS & ORDER
# ============================================================================
STAGE_ORDER = ['MRE', 'MRE_U', 'PEA', 'PEA_U', 'PFS', 'FS', 'FS_U', 'FP', 'FID']
STAGE_SHORT_MAP = {
    'Mineral Resource Estimate': 'MRE',
    'Mineral Resource Estimate (Updated)': 'MRE_U',
    'Preliminary Economic Assessment': 'PEA',
    'Preliminary Economic Assessment (Updated)': 'PEA_U',
    'Pre-Feasibility Study': 'PFS',
    'Feasibility Study': 'FS',
    'Feasibility Study (Updated)': 'FS_U',
    'Fully Permitted': 'FP',
    'FID': 'FID'
}

# ============================================================================
# STUDY DATA (per company)
# ============================================================================
# NOTE: Study economics are best-effort public figures and should be verified
# against the underlying technical reports. The UI labels the app as MVP demo.
# ============================================================================

STUDY_COLUMNS = [
    'Stage', 'Stage_Display', 'Date', 'PressRelease_Date',
    'AfterTax_NPV_M', 'AfterTax_IRR_%',
    'Initial_Capex_M', 'Total_Capex_M',
    'Resource_Measured_Indicated_Mt', 'Resource_Inferred_Mt',
    'Average_Lithium_Grade', 'Metallurgical_Recovery_%',
    'Life_of_Mine_Years', 'Avg_Annual_Production_tpa',
    'Net_Operating_Cost_t', 'BaseCase_Li_Price',
    'Payback_Period_Years',
]

STUDY_DATA = {
    # ------------------------------------------------------------------
    # Angel Island — Century Lithium Corp (gvkey 106098)
    # ------------------------------------------------------------------
    "Century Lithium": {
        "Stage": ["MRE", "PEA", "PFS", "FS", "FS_U"],
        "Stage_Display": [
            "Mineral Resource Estimate",
            "Preliminary Economic Assessment",
            "Pre-Feasibility Study",
            "Feasibility Study",
            "Feasibility Study (Updated)"
        ],
        "Date": ["2018-01-05", "2018-09-06", "2020-05-19", "2024-04-29", "2026-02-23"],
        "PressRelease_Date": ["1-5-2018", "6-9-2018", "19-5-2020", "29-4-2024", "23-2-2026"],
        "AfterTax_NPV_M": [None, 1450, 1052, 3010, 4010],
        "AfterTax_IRR_%": [None, 32.7, 25.8, 17.1, 27.4],
        "Initial_Capex_M": [None, 482, 493, 1537, 997.4],
        "Total_Capex_M": [None, 482, 493, 3524, 1657],
        "Resource_Measured_Indicated_Mt": [597, 831, 593, 1207.33, 1138],
        "Resource_Inferred_Mt": [779, 1120, 2.3, 119, 187],
        "Average_Lithium_Grade": [899, 867, 1073, 957, 1149],
        "Metallurgical_Recovery_%": [80, 81.5, 86.5, 78, 84],
        "Life_of_Mine_Years": [None, 40, 40, 40, 40],
        "Avg_Annual_Production_tpa": [None, 24042, 27400, 34000, 26500],
        "Net_Operating_Cost_t": [None, 3983, 3329, 2766, 4389],
        "BaseCase_Li_Price": [None, 13000, 9500, 24000, 24000],
        "Payback_Period_Years": [None, 2.7, 4.4, 9, None],
    },

    # ------------------------------------------------------------------
    # Tonopah Flats — American Battery Technology Co (gvkey 26366)
    # ------------------------------------------------------------------
    "American Battery Technology Co": {
        "Stage": ["MRE", "PEA", "PEA_U", "PFS"],
        "Stage_Display": [
            "Mineral Resource Estimate",
            "Preliminary Economic Assessment",
            "Preliminary Economic Assessment (Updated)",
            "Pre-Feasibility Study"
        ],
        "Date": ["2023-02-26", "2023-12-21", "2024-04-24", "2025-10-16"],
        "PressRelease_Date": ["26-2-2023", "21-12-2023", "24-4-2024", "16-10-2025"],
        "AfterTax_NPV_M": [None, 4410, 4410, 2570],
        "AfterTax_IRR_%": [None, 65.8, 65.8, 21.8],
        "Initial_Capex_M": [None, 1060, 785, 2000],
        "Total_Capex_M": [None, 1060, 785, 2000],
        "Resource_Measured_Indicated_Mt": [5287, 5400, 3160, 2333.7],
        "Resource_Inferred_Mt": [15.8, 18.03, 21.2, 21.5],
        "Average_Lithium_Grade": [None, None, 596, 805],
        "Metallurgical_Recovery_%": [None, 90, 90, None],
        "Life_of_Mine_Years": [None, 50, 50, 45],
        "Avg_Annual_Production_tpa": [None, 33000, 30000, 30000],
        "Net_Operating_Cost_t": [None, 4636, 4636, 6994],
        "BaseCase_Li_Price": [None, 30303, 30303, 23000],
        "Payback_Period_Years": [None, 2.4, 2.4, 7.5],
    },

    # ------------------------------------------------------------------
    # Rhyolite Ridge — Ioneer Ltd (gvkey 290341)
    # ------------------------------------------------------------------
    "Ioneer": {
        "Stage": ["PFS", "FS", "MRE_U", "Fully_Permitted", "FID", "FS_U"],
        "Stage_Display": [
            "Pre-Feasibility Study",
            "Feasibility Study",
            "Mineral Resource Estimate (Updated)",
            "Fully Permitted",
            "FID",
            "Feasibility Study (Updated)"
        ],
        "Date": ["2018-10-23", "2020-04-30", "2023-04-26", "2024-10-24", "2025-01-15", "2025-10-29"],
        "PressRelease_Date": ["23-10-2018", "30-4-2020", "26-4-2023", "24-10-2024", "15-1-2025", "29-10-2025"],
        "AfterTax_NPV_M": [1820, 1265, None, None, None, 2237],
        "AfterTax_IRR_%": [27.7, 20.8, None, None, None, 18],
        "Initial_Capex_M": [599, 785, None, None, None, 1683],
        "Total_Capex_M": [599, 785, None, None, None, 1683],
        "Resource_Measured_Indicated_Mt": [None, 146.5, None, None, None, 260],
        "Resource_Inferred_Mt": [None, None, None, None, None, 7],
        "Average_Lithium_Grade": [None, None, None, None, None, None],
        "Metallurgical_Recovery_%": [None, None, None, None, None, None],
        "Life_of_Mine_Years": [30, 26, None, None, None, 82],
        "Avg_Annual_Production_tpa": [20200, 22000, None, None, None, 20400],
        "Net_Operating_Cost_t": [1796, 2510, None, None, None, 2933],
        "BaseCase_Li_Price": [None, 13000, None, None, None, None],
        "Payback_Period_Years": [4.1, 5.2, None, None, None, 7],
    },

    # ------------------------------------------------------------------
    # Thacker Pass — Lithium Americas Corp (gvkey 43404)
    # ------------------------------------------------------------------
    "Lithium Americas": {
        "Stage": ["MRE_U", "PFS", "Fully_Permitted", "FS", "FS_U"],
        "Stage_Display": [
            "Mineral Resource Estimate (Updated)",
            "Pre-Feasibility Study",
            "Fully Permitted",
            "Feasibility Study",
            "Feasibility Study (Updated)"
        ],
        "Date": ["2018-04-05", "2018-06-21", "2021-01-15", "2023-01-31", "2025-01-07"],
        "PressRelease_Date": ["5-4-2018", "21-6-2018", "15-1-2021", "31-1-2023", "7-1-2025"],
        "AfterTax_NPV_M": [None, 2600, None, 5700, 8700],
        "AfterTax_IRR_%": [None, 29.3, None, 21.4, 20],
        "Initial_Capex_M": [None, 1059, None, 3996, 12441],
        "Total_Capex_M": [None, 1059, None, 3996, 12441],
        "Resource_Measured_Indicated_Mt": [8.3, 3.1, None, 16.1, 44.5],
        "Resource_Inferred_Mt": [None, 3.0, None, None, None],
        "Average_Lithium_Grade": [2917, 3283, None, 2070, 2230],
        "Metallurgical_Recovery_%": [None, 83, None, None, None],
        "Life_of_Mine_Years": [None, 46, None, 40, 85],
        "Avg_Annual_Production_tpa": [None, 60000, None, 80000, 160000],
        "Net_Operating_Cost_t": [None, 2570, None, 6743, 8039],
        "BaseCase_Li_Price": [None, 12000, None, 24000, 24000],
        "Payback_Period_Years": [None, 5.2, None, 5.2, None],
    },

    # ------------------------------------------------------------------
    # Keystone — Surge Battery Metals Inc (gvkey 106045)
    # ------------------------------------------------------------------
    "Surge Battery Metals": {
        "Stage": ["MRE", "MRE_U", "PEA"],
        "Stage_Display": [
            "Mineral Resource Estimate",
            "Mineral Resource Estimate (Updated)",
            "Preliminary Economic Assessment"
        ],
        "Date": ["2024-02-22", "2024-09-24", "2025-06-09"],
        "PressRelease_Date": ["22-2-2024", "24-9-2024", "9-6-2025"],
        "AfterTax_NPV_M": [None, None, 9210],
        "AfterTax_IRR_%": [None, None, 22.8],
        "Initial_Capex_M": [None, None, 5232],
        "Total_Capex_M": [None, None, 5232],
        "Resource_Measured_Indicated_Mt": [None, None, None],
        "Resource_Inferred_Mt": [None, None, None],
        "Average_Lithium_Grade": [None, None, None],
        "Metallurgical_Recovery_%": [None, None, None],
        "Life_of_Mine_Years": [None, None, None],
        "Avg_Annual_Production_tpa": [None, None, 86300],
        "Net_Operating_Cost_t": [None, None, 5097],
        "BaseCase_Li_Price": [None, None, None],
        "Payback_Period_Years": [None, None, 4.7],
    },

    # ------------------------------------------------------------------
    # TLC — American Lithium Corp (gvkey 107393)
    # ------------------------------------------------------------------
    "American Lithium Corp": {
        "Stage": ["MRE", "MRE_U", "PEA"],
        "Stage_Display": [
            "Mineral Resource Estimate",
            "Mineral Resource Estimate (Updated)",
            "Preliminary Economic Assessment"
        ],
        "Date": ["2020-05-21", "2023-01-16", "2023-02-01"],
        "PressRelease_Date": ["21-5-2020", "16-1-2023", "1-2-2023"],
        "AfterTax_NPV_M": [None, None, 3261],
        "AfterTax_IRR_%": [None, None, 27.5],
        "Initial_Capex_M": [None, None, 1431],
        "Total_Capex_M": [None, None, 1431],
        "Resource_Measured_Indicated_Mt": [None, None, None],
        "Resource_Inferred_Mt": [None, None, None],
        "Average_Lithium_Grade": [None, None, None],
        "Metallurgical_Recovery_%": [None, None, None],
        "Life_of_Mine_Years": [None, None, None],
        "Avg_Annual_Production_tpa": [None, None, None],
        "Net_Operating_Cost_t": [None, None, 7443],
        "BaseCase_Li_Price": [None, None, None],
        "Payback_Period_Years": [None, None, 3.8],
    },
}

# ============================================================================
# HISTORICAL MARKET DATA OVERRIDES
# ============================================================================
# Some companies (e.g. LAC) have stock data that only begins after a
# corporate event (LAC's Oct-2023 split), so earlier study dates have no
# price × shares record. Provide the market data manually here.
# ============================================================================

MARKET_CAP_OVERRIDES = {
    "Lithium Americas": {
        "Pre-Feasibility Study": {
            "Date": "2018-06-29",
            "Stock_Price": 5.39,
            "Shares_M": 88.591,
        },
        "Feasibility Study": {
            "Date": "2023-01-31",
            "Stock_Price": 24.89,
            "Shares_M": 135.035,
        },
    },
}

# ============================================================================
# PRESS RELEASE TIMELINE (per company)
#
# Optional key "Status": "Future" marks milestones that have NOT happened yet
# (planned / ongoing). The timeline chart separates these from the historical
# events with a dashed split line and distinct open-triangle markers.
# ============================================================================

TIMELINE_DATA = {
    "Century Lithium": [
        {"Study": "MRE", "Commitment date": "13-03-2018", "Expected date": "30-06-2018", "Actual date": "01-05-2018", "Delay": "—", "Commitment Evidence": "the results included in the upcoming resource estimate, which is expected to be completed soon after final assays are received.", "Expected Evidence": "—"},
        {"Study": "PEA", "Commitment date": "09-05-2018", "Expected date": "30-09-2018", "Actual date": "06-09-2018", "Delay": "—", "Commitment Evidence": "Results of the PEA are anticipated in the latter part of July, 2018", "Expected Evidence": "—"},
        {"Study": "PFS", "Commitment date": "01-10-2018", "Expected date": "30-06-2019", "Actual date": "19-05-2020", "Delay": "~10 months", "Commitment Evidence": "Cypress anticipates the PFS to be completed in Q1 2019", "Expected Evidence": "—"},
        {"Study": "FAST41_Transparency", "Commitment date": "—", "Expected date": "—", "Actual date": "06-08-2025", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "FS", "Commitment date": "28-01-2021", "Expected date": "31-03-2022", "Actual date": "29-04-2024", "Delay": "~2.1 years", "Commitment Evidence": "towards a feasibility study later this year. Cypress ... is fully financed to advance the Clayton Valley Lithium Project to a feasibility study.", "Expected Evidence": "—"},
        {"Study": "FS_U", "Commitment date": "24-02-2025", "Expected date": "—", "Actual date": "23-02-2026", "Delay": "—", "Commitment Evidence": "Century Lithium will initiate work on an Updated Feasibility Study for Angel Island", "Expected Evidence": "—"},
        {"Study": "PoO_Submitted", "Commitment date": "30-12-2020", "Expected date": "—", "Actual date": "05-05-2026", "Delay": "—", "Commitment Evidence": "The data will aid in the design of a feasibility-level plan-of-operations (POO) for the Project in coordination with the National Environmental Policy Act process…", "Expected Evidence": "—"},
        {"Study": "BLM Comments on Draft PoO", "Commitment date": "—", "Expected date": "Within the next month (May 2026)", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Finalize Mine Plan of Operations", "Commitment date": "—", "Expected date": "2026", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Demonstration Plant Construction", "Commitment date": "—", "Expected date": "H2 2026", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Strategic Partnering / Offtake", "Commitment date": "—", "Expected date": "Ongoing", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
    ],
    "Lithium Americas": [
        {"Study": "MRE_U", "Commitment date": "23-10-2017", "Expected date": "—", "Actual date": "05-04-2018", "Delay": "—", "Commitment Evidence": "Conducting an exploration program with the objective of expanding and upgrading the existing NI 43-101 compliant resource.", "Expected Evidence": "—"},
        {"Study": "PFS", "Commitment date": "23-10-2017", "Expected date": "30-06-2018", "Actual date": "21-06-2018", "Delay": "—", "Commitment Evidence": "Q2 2018 - complete PFS, including updated resource and reserve estimates.", "Expected Evidence": "—"},
        {"Study": "PoO_Submitted", "Commitment date": "21-06-2018", "Expected date": "30-09-2018", "Actual date": "01-08-2019", "Delay": "~10 months", "Commitment Evidence": "A Mine Plan of Operations is expected to be ready for submission in Q3 2018...", "Expected Evidence": "—"},
        {"Study": "NEPA_Start", "Commitment date": "—", "Expected date": "—", "Actual date": "21-01-2020", "Delay": "—", "Commitment Evidence": "The NOI formally commences the National Environmental Policy Act (\"NEPA\") EIS preparation and public engagement process by the U.S. Department of the Interior Bureau of Land Management (\"BLM\").", "Expected Evidence": "—"},
        {"Study": "Final_EIS", "Commitment date": "21-06-2019", "Expected date": "30-09-2019", "Actual date": "04-12-2020", "Delay": "~14 months", "Commitment Evidence": "Q3 2019 - Submit EIS for Phase 1. — Lithium Americas, PFS press release, June 21, 2018.", "Expected Evidence": "—"},
        {"Study": "Record of Decision", "Commitment date": "25-09-2019", "Expected date": "31-12-2020", "Actual date": "15-01-2021", "Delay": "~15 days", "Commitment Evidence": "The Company's engagement with government and Tribal stakeholders is planned to continue over the next year in anticipation of the ROD being issued in Q4 2020.", "Expected Evidence": "—"},
        {"Study": "FS", "Commitment date": "12-11-2019", "Expected date": "30-06-2020", "Actual date": "31-01-2023", "Delay": "~2.6 years", "Commitment Evidence": "Lithium Americas expects to release an NI 43-101 compliant definitive feasibility study by mid-2020... — September 25, 2019.", "Expected Evidence": "—"},
        {"Study": "FID", "Commitment date": "16-10-2024", "Expected date": "—", "Actual date": "01-04-2025", "Delay": "—", "Commitment Evidence": "The Company and GM are targeting making the FID and issuing full notice to proceed for Thacker Pass by the end of the year...", "Expected Evidence": "—"},
        {"Study": "FS_U", "Commitment date": "14-03-2024", "Expected date": "—", "Actual date": "07-01-2025", "Delay": "—", "Commitment Evidence": "The 2023 drilling program at Thacker Pass to further define and expand the resource estimate concluded successfully in December 2023.", "Expected Evidence": "—"},
        {"Study": "Definitive Capital Estimate", "Commitment date": "—", "Expected date": "Q3 2026", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Mechanical Completion (Phase 1)", "Commitment date": "—", "Expected date": "Late 2027", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Commercial Production", "Commitment date": "—", "Expected date": "2028", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
    ],
    "American Battery Technology Co": [
        {"Study": "MRE", "Commitment date": "—", "Expected date": "—", "Actual date": "28-02-2023", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PEA", "Commitment date": "—", "Expected date": "—", "Actual date": "21-12-2023", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PEA_U", "Commitment date": "31-12-2023", "Expected date": "—", "Actual date": "24-04-2024", "Delay": "—", "Commitment Evidence": "ABTC is publishing this Amended Resource Estimate and Initial Assessment with Project Economics for the Tonopah Flats Lithium Project, Esmeralda and Nye Counties, Nevada, USA (Amended Initial Assessment), that includes these changes and other updates.", "Expected Evidence": "—"},
        {"Study": "PoO_Submitted", "Commitment date": "—", "Expected date": "—", "Actual date": "26-03-2025", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "FAST41_Transparency", "Commitment date": "—", "Expected date": "—", "Actual date": "30-06-2025", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "FAST41_Covered", "Commitment date": "—", "Expected date": "—", "Actual date": "19-08-2025", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PFS", "Commitment date": "18-01-2024", "Expected date": "—", "Actual date": "16-10-2025", "Delay": "—", "Commitment Evidence": "Updated Initial Assessment provides necessary data and recommends next steps to further develop the resource, including the completion of a Pre-Feasibility Study", "Expected Evidence": "—"},
        {"Study": "NEPA_Start", "Commitment date": "03-10-2023", "Expected date": "—", "Actual date": "02-07-2026", "Delay": "—", "Commitment Evidence": "ABTC is advancing the Tonopah Flats Lithium Project through the federal permitting process, including the preparation of the required environmental baseline studies for the NEPA review.", "Expected Evidence": "—"},
        {"Study": "Pilot Operations", "Commitment date": "—", "Expected date": "2026–2027", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Second Recycling Facility", "Commitment date": "—", "Expected date": "Shortly (June 2026)", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "DOE Grant Reinstatement", "Commitment date": "—", "Expected date": "June 2026", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Definitive Feasibility Study", "Commitment date": "—", "Expected date": "2026", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Commercial Production (Phase 1)", "Commitment date": "—", "Expected date": "2028", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
    ],
    "Ioneer": [
        {"Study": "PFS", "Commitment date": "22-08-2017", "Expected date": "30-03-2018", "Actual date": "23-10-2018", "Delay": "~6 months", "Commitment Evidence": "Global Geoscience has made rapid progress towards developing the Rhyolite Ridge Lithium-Boron Project... and commenced a fully-funded Pre-Feasibility Study (PFS) to be completed by early 2018.", "Expected Evidence": "—"},
        {"Study": "FS", "Commitment date": "20-10-2018", "Expected date": "30-09-2019", "Actual date": "30-04-2020", "Delay": "~7 months", "Commitment Evidence": "Engineering and design firm Fluor Corporation ... was appointed to complete the project's definitive feasibility study which is expected to be finished in quarter three 2019.", "Expected Evidence": "—"},
        {"Study": "PoO_Submitted", "Commitment date": "30-04-2020", "Expected date": "30-06-2020", "Actual date": "18-07-2022", "Delay": "~2.1 years", "Commitment Evidence": "The Plan of Operations will be submitted to the BLM in 2Q 2020.", "Expected Evidence": "—"},
        {"Study": "PoO_Accepted", "Commitment date": "—", "Expected date": "—", "Actual date": "17-08-2022", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "NEPA_Start", "Commitment date": "—", "Expected date": "—", "Actual date": "20-12-2022", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "27-03-2023", "Expected date": "—", "Actual date": "26-04-2023", "Delay": "—", "Commitment Evidence": "Mineral Resource update due April 2023.", "Expected Evidence": "—"},
        {"Study": "Final_EIS", "Commitment date": "23-01-2023", "Expected date": "23-01-2024", "Actual date": "20-09-2024", "Delay": "~7 months", "Commitment Evidence": "EIS completed within approximately 12-months of NOI publish date", "Expected Evidence": "—"},
        {"Study": "Record of Decision", "Commitment date": "30-03-2022", "Expected date": "30-03-2024", "Actual date": "24-10-2024", "Delay": "~6 months", "Commitment Evidence": "The Company's current best estimate is that a ROD would be received in 1Q 2024.", "Expected Evidence": "—"},
        {"Study": "FID", "Commitment date": "—", "Expected date": "—", "Actual date": "15-01-2025", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "FS_U", "Commitment date": "31-01-2023", "Expected date": "—", "Actual date": "29-10-2025", "Delay": "—", "Commitment Evidence": "Based on these outcomes, an updated capital and operating cost estimate will be provided to stakeholders before making an FID.", "Expected Evidence": "—"},
        {"Study": "Sign MOUs with KIND & Hyundai", "Commitment date": "—", "Expected date": "July 2026", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Final Investment Decision", "Commitment date": "—", "Expected date": "H2 2026", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "First Commercial Production", "Commitment date": "—", "Expected date": "2029", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
    ],
    "Surge Battery Metals": [
        {"Study": "PoO_Submitted", "Commitment date": "—", "Expected date": "—", "Actual date": "21-11-2023", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "MRE", "Commitment date": "16-01-2024", "Expected date": "—", "Actual date": "22-02-2024", "Delay": "—", "Commitment Evidence": "Surge Battery Metals announced on January 16, 2024 that it had retained Dr. Bruce Davis to prepare a maiden Mineral Resource Estimate, which was subsequently announced on February 22, 2024.", "Expected Evidence": "—"},
        {"Study": "PoO_Accepted", "Commitment date": "—", "Expected date": "—", "Actual date": "28-02-2024", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—", "Actual date": "24-09-2024", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "NEPA_Start", "Commitment date": "—", "Expected date": "—", "Actual date": "20-12-2024", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "Final_EA", "Commitment date": "—", "Expected date": "—", "Actual date": "05-03-2025", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PEA", "Commitment date": "22-02-2024", "Expected date": "31-12-2024", "Actual date": "09-06-2025", "Delay": "~5 months", "Commitment Evidence": "Surge expects to undertake a PEA study on the NNLP with an anticipated target reporting date in Q4 of 2024.", "Expected Evidence": "—"},
        {"Study": "Scaled-up Leach & Separation Testing", "Commitment date": "—", "Expected date": "Q3 2026", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "PFS", "Commitment date": "—", "Expected date": "Q4 2026", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
        {"Study": "Flowsheet Optimization", "Commitment date": "—", "Expected date": "Ongoing", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
    ],
    "American Lithium Corp": [
        {"Study": "MRE", "Commitment date": "19-06-2019", "Expected date": "30-12-2019", "Actual date": "21-05-2020", "Delay": "~4 months", "Commitment Evidence": "With drilling ongoing, the company expects to deliver a maiden resource and early stage economic study in 2019.", "Expected Evidence": "—"},
        {"Study": "PoO_Submitted", "Commitment date": "—", "Expected date": "—", "Actual date": "13-01-2021", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PoO_Accepted", "Commitment date": "—", "Expected date": "—", "Actual date": "17-06-2021", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PoO_Approved", "Commitment date": "—", "Expected date": "—", "Actual date": "11-01-2022", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—", "Actual date": "01-12-2022", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PEA", "Commitment date": "05-10-2021", "Expected date": "31-03-2022", "Actual date": "01-02-2023", "Delay": "~10 months", "Commitment Evidence": "Optimization of process engineering and pre-concentration work being fast-tracked to enable completion of a Preliminary Economic Assessment ('PEA') during Q1 2022.", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "08-12-2023", "Expected date": "—", "Actual date": "27-02-2025", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "Defense Supply Chain Integration", "Commitment date": "—", "Expected date": "Ongoing", "Actual date": "—", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—", "Status": "Future"},
    ],
}

# ============================================================================
# YOUTUBE VIDEOS (per company) — SENTIMENT SECTION
# ============================================================================
# Hand-collected YouTube coverage per company, used as input for the
# Sentiment section. Each entry maps a company display name (must match
# COMPANIES keys) to a list of video records:
#   - date:     publish date (YYYY-MM-DD)
#   - title:    video title
#   - channel:  YouTube channel name
#   - duration: video length (MM:SS or H:MM:SS)
#   - views:    view count at time of collection
#   - url:      YouTube link
# ============================================================================

YOUTUBE_VIDEOS = {
    "Century Lithium": [
        {
            "date": "2026-02-26",
            "title": "Analyst Mark Reichman - Century Lithium (CYDVF) - Updated Angel Island Feasibility Study Highlights",
            "channel": "channelchek",
            "duration": "2:00",
            "views": 163,
            "url": "https://www.youtube.com/watch?v=-XNVLN3om9o"
        },
        {
            "date": "2026-02-24",
            "title": "Century Lithium updated study delivers $4B NPV for Angel Island Project while reducing initial costs",
            "channel": "Proactive Investors",
            "duration": "6:25",
            "views": 877,
            "url": "https://www.youtube.com/watch?v=Pz_N9Io2UIk"
        },
        {
            "date": "2025-12-02",
            "title": "Century Lithium reports breakthrough results in rare earth recovery from Angel Island project",
            "channel": "Proactive Investors",
            "duration": "4:53",
            "views": 1066,
            "url": "https://www.youtube.com/watch?v=Tra7bM4XoGU"
        },
        {
            "date": "2025-04-15",
            "title": "Century Lithium: Project Update, U.S. Policy, Permitting, Feasibility | Bill Willoughby",
            "channel": "Rock Stock Channel",
            "duration": "27:19",
            "views": 1231,
            "url": "https://www.youtube.com/watch?v=DYfheN_tVgY"
        },
        {
            "date": "2025-10-27",
            "title": "Century Lithium: Battery materials quality lithium for LFP & LMA",
            "channel": "Proactive Investors",
            "duration": "1:03",
            "views": 324,
            "url": "https://www.youtube.com/watch?v=Smjkgn8Xzq8"
        },
        {
            "date": "2026-02-26",
            "title": "Century Lithium's Angel Island project - Permitting and next steps revealed",
            "channel": "Proactive Investors",
            "duration": "1:28",
            "views": 217,
            "url": "https://www.youtube.com/watch?v=PqdBmP2OXfs"
        },
        {
            "date": "2023-02-09",
            "title": "Century Lithium Corp.",
            "channel": "Century Lithium Corp.",
            "duration": "3:50",
            "views": 973,
            "url": "https://www.youtube.com/watch?v=IHHx4rfZBC4"
        },
        {
            "date": "2026-02-26",
            "title": "Lithium production costs slashed at Century Lithium's Angel Island project",
            "channel": "Proactive Investors",
            "duration": "0:52",
            "views": 363,
            "url": "https://www.youtube.com/watch?v=X8Llcs1Q6hw"
        },
        {
            "date": "2025-05-06",
            "title": "Century Lithium achieves breakthrough in direct lithium with high recovery and battery-grade purity",
            "channel": "Proactive Investors",
            "duration": "5:28",
            "views": 635,
            "url": "https://www.youtube.com/watch?v=lWHq8VD35DY"
        },
        {
            "date": "2025-10-02",
            "title": "Century Lithium Presentation / Q&A (OTCQX: CYDVF; TSX-V: LCE) - Bill Willoughby, President & CEO",
            "channel": "San Diego Torrey Hills Capital",
            "duration": "1:11:46",
            "views": 460,
            "url": "https://www.youtube.com/watch?v=Oj2ye28H8g8"
        },
        {
            "date": "2025-02-24",
            "title": "Century Lithium identifies CAPEX reduction for Angel Island project, plans updated feasibility study",
            "channel": "Proactive Investors",
            "duration": "6:10",
            "views": 554,
            "url": "https://www.youtube.com/watch?v=narDvkg6wjk"
        },
        {
            "date": "2023-02-10",
            "title": "Century Lithium teams with Koch Technology to use its technology for Lithium Extraction",
            "channel": "Proactive Investors",
            "duration": "3:27",
            "views": 1637,
            "url": "https://www.youtube.com/watch?v=Bg7g4p72igE"
        },
        {
            "date": "2025-10-27",
            "title": "Century Lithium relocates demonstration plant to Tonopah Airport to advance Angel Island project",
            "channel": "Proactive Investors",
            "duration": "4:46",
            "views": 854,
            "url": "https://www.youtube.com/watch?v=IjEj3ObShLs"
        },
        {
            "date": "2026-01-31",
            "title": "Lithium vs Lead Acid: Are Century Lithium Batteries Worth It on a Boat?",
            "channel": "Fishy Business",
            "duration": "2:05",
            "views": 384,
            "url": "https://www.youtube.com/watch?v=1FF8KNn5LPg"
        },
        {
            "date": "2025-10-01",
            "title": "Century Lithium secures FAST-41 status and completes baseline studies at Angel Island project",
            "channel": "Proactive Investors",
            "duration": "5:18",
            "views": 803,
            "url": "https://www.youtube.com/watch?v=dQ60Lu3jKsk"
        },
        {
            "date": "2025-12-03",
            "title": "Century Lithium: Rare Earths breakthrough Our new ion exchange process works",
            "channel": "Proactive Investors",
            "duration": "0:58",
            "views": 881,
            "url": "https://www.youtube.com/watch?v=aOMBXS53CfI"
        },
        {
            "date": "2025-10-28",
            "title": "Century Lithium Corp: Lithium extraction new plant & battery-grade production",
            "channel": "Proactive Investors",
            "duration": "0:39",
            "views": 220,
            "url": "https://www.youtube.com/watch?v=MA_nXxewgPM"
        },
        {
            "date": "2025-01-21",
            "title": "Century Lithium announces MOU with Orica for sodium hydroxide offtake agreement",
            "channel": "Proactive Investors",
            "duration": "4:46",
            "views": 591,
            "url": "https://www.youtube.com/watch?v=LcxmmdGcm0Y"
        },
        {
            "date": "2024-08-30",
            "title": "Mining News Flash with Century Lithium and Calibre Mining",
            "channel": "Swiss Resource Capital AG",
            "duration": "4:19",
            "views": 2100,
            "url": "https://www.youtube.com/watch?v=b9wXDsKfQd0"
        },
        {
            "date": "2023-04-19",
            "title": "Tips & Hints - Century Lithium Batteries",
            "channel": "What's Up Downunder",
            "duration": "0:35",
            "views": 186,
            "url": "https://www.youtube.com/watch?v=d8xm0fUPdJs"
        },
        {
            "date": "2023-05-25",
            "title": "Century Lithium confirms 2nd production of battery grade lithium from Clayton Valley Project",
            "channel": "Proactive Investors",
            "duration": "4:14",
            "views": 1550,
            "url": "https://www.youtube.com/watch?v=CM3fGtZv4T8"
        },
        {
            "date": "2024-04-29",
            "title": "Century Lithium Unveils Robust Feasibility Study Results for Clayton Valley Lithium Project",
            "channel": "Proactive Investors",
            "duration": "4:34",
            "views": 442,
            "url": "https://www.youtube.com/watch?v=nUKjH0-bBbM"
        },
        {
            "date": "2025-04-30",
            "title": "Century Lithium advances Angel Island project to support U.S. supply chain",
            "channel": "Proactive Investors",
            "duration": "5:11",
            "views": 556,
            "url": "https://www.youtube.com/watch?v=hOjelTLQ9lM"
        },
        {
            "date": "2023-03-30",
            "title": "Become an Early Mover in Century Lithium",
            "channel": "channelchek",
            "duration": "0:28",
            "views": 323,
            "url": "https://www.youtube.com/watch?v=wYz8BRiz0Tc"
        },
        {
            "date": "2023-08-17",
            "title": "Century Lithium: Good Progress with Partner Koch Technology Solutions at the Pilot Plant",
            "channel": "Swiss Resource Capital AG",
            "duration": "3:56",
            "views": 2033,
            "url": "https://www.youtube.com/watch?v=MyxYoKBN8io"
        },
        {
            "date": "2024-08-30",
            "title": "Bergbau-Nachrichten mit Century Lithium und Calibre Mining",
            "channel": "Swiss Resource Capital AG",
            "duration": "4:26",
            "views": 1874,
            "url": "https://www.youtube.com/watch?v=65-tnSKWST8"
        },
        {
            "date": "2023-05-24",
            "title": "Mining Newsflash with M&A Activities in the Lithium Sector, Century Lithium and Ion Energy",
            "channel": "Swiss Resource Capital AG",
            "duration": "3:25",
            "views": 406,
            "url": "https://www.youtube.com/watch?v=9ze89z5hOfA"
        },
    ],
}
# ============================================================================
# LITHIUM BEDRIJVEN - CASH OVERZICHT
# Data: Kwartaalcijfers 2024-2026
# Valuta: USD of CAD (per bedrijf aangegeven)
# ============================================================================

lithium_companies = {

    # =========================================================
    # 1. CENTURY LITHIUM (CYDVF) - VALUTA: CAD
    # =========================================================
    "Century Lithium": {
        "currency": "CAD",
        "data": [
            {"quarter": "2024 Q1", "cash": 12.49, "change": -1.90, "burn": 1.90, "financing": 0, "underlying_burn": 1.90, "runway_2q": None, "runway_4q": None},
            {"quarter": "2024 Q2", "cash": 10.30, "change": -2.19, "burn": 2.19, "financing": 0, "underlying_burn": 2.19, "runway_2q": 14.1, "runway_4q": None},
            {"quarter": "2024 Q3", "cash": 7.85, "change": -2.45, "burn": 2.45, "financing": 0, "underlying_burn": 2.45, "runway_2q": 9.6, "runway_4q": None},
            {"quarter": "2024 Q4", "cash": 5.99, "change": -1.86, "burn": 1.86, "financing": 0, "underlying_burn": 1.86, "runway_2q": 8.3, "runway_4q": 8.0},
            {"quarter": "2025 Q1", "cash": 4.65, "change": -1.34, "burn": 1.34, "financing": 0, "underlying_burn": 1.34, "runway_2q": 8.7, "runway_4q": 6.6},
            {"quarter": "2025 Q2", "cash": 3.98, "change": -0.67, "burn": 0.67, "financing": 0, "underlying_burn": 0.67, "runway_2q": 11.9, "runway_4q": 7.8},
            # 2025 Q3: financing kwartaal - underlying burn GESCHAT (gemiddelde van 2025 Q4=1.47 en 2025 Q2=0.67)
            {"quarter": "2025 Q3", "cash": 6.72, "change": +2.74, "burn": 0, "financing": 3.9, "underlying_burn": 1.07, "runway_2q": 15.7, "runway_4q": 13.1},
            {"quarter": "2025 Q4", "cash": 5.25, "change": -1.47, "burn": 1.47, "financing": 0, "underlying_burn": 1.47, "runway_2q": 8.7, "runway_4q": 7.7},
            # 2026 Q1: financing kwartaal - underlying burn GESCHAT (gewogen: 0.67×1 + 1.47×2)/3 = 1.20
            {"quarter": "2026 Q1", "cash": 10.57, "change": +5.32, "burn": 0, "financing": 7.00, "underlying_burn": 1.20, "runway_2q": 21.1, "runway_4q": 18.6},
        ]
    },

    # =========================================================
    # 2. AMERICAN BATTERY (ABAT) - VALUTA: USD
    # =========================================================
    "American Battery": {
        "currency": "USD",
        "data": [
            {"quarter": "2023 Q4", "cash": 7.73, "change": -10.18, "burn": 10.18, "financing": 0, "underlying_burn": 10.18, "runway_2q": None, "runway_4q": None},
            {"quarter": "2024 Q1", "cash": 6.06, "change": -1.67, "burn": 1.67, "financing": 0, "underlying_burn": 1.67, "runway_2q": 9.7, "runway_4q": None},
            # 2024 Q2: financing kwartaal - underlying burn GESCHAT (laatste schone = 1.67)
            {"quarter": "2024 Q2", "cash": 7.00, "change": +0.94, "burn": 0, "financing": 0.94, "underlying_burn": 1.67, "runway_2q": 10.5, "runway_4q": None},
            {"quarter": "2024 Q3", "cash": 5.77, "change": -1.23, "burn": 1.23, "financing": 0, "underlying_burn": 1.23, "runway_2q": 11.3, "runway_4q": 15.4},
            # 2024 Q4: financing kwartaal - underlying burn GESCHAT (laatste schone = 1.23)
            {"quarter": "2024 Q4", "cash": 20.62, "change": +14.85, "burn": 0, "financing": 14.85, "underlying_burn": 1.23, "runway_2q": 50.3, "runway_4q": 46.7},
            {"quarter": "2025 Q1", "cash": 7.85, "change": -12.77, "burn": 12.77, "financing": 0, "underlying_burn": 12.77, "runway_2q": 1.5, "runway_4q": 2.2},
            # 2025 Q2: financing kwartaal - underlying burn GESCHAT (laatste schone = 12.77)
            {"quarter": "2025 Q2", "cash": 12.47, "change": +4.62, "burn": 0, "financing": 4.62, "underlying_burn": 12.77, "runway_2q": 2.9, "runway_4q": 3.0},
            # 2025 Q3: financing kwartaal - underlying burn GESCHAT (laatste schone = 12.77)
            {"quarter": "2025 Q3", "cash": 30.92, "change": +18.45, "burn": 0, "financing": 18.45, "underlying_burn": 12.77, "runway_2q": 7.3, "runway_4q": 4.9},
            # 2025 Q4: financing kwartaal - underlying burn GESCHAT (laatste schone = 12.77)
            {"quarter": "2025 Q4", "cash": 48.69, "change": +17.77, "burn": 0, "financing": 17.77, "underlying_burn": 12.77, "runway_2q": 11.4, "runway_4q": 6.1},
            {"quarter": "2026 Q1", "cash": 38.49, "change": -10.20, "burn": 10.20, "financing": 0, "underlying_burn": 10.20, "runway_2q": 9.0, "runway_4q": 7.1},
        ]
    },
    # =========================================================
    # 3. SURGE BATTERY (NILIF) - VALUTA: CAD
    # =========================================================
    "Surge Battery": {
        "currency": "CAD",
        "data": [
            {"quarter": "2024 Q1", "cash": 5.31, "change": -2.10, "burn": 2.10, "financing": 0, "underlying_burn": 2.10, "runway_2q": None, "runway_4q": None},
            {"quarter": "2024 Q2", "cash": 4.80, "change": -0.51, "burn": 0.51, "financing": 0, "underlying_burn": 0.51, "runway_2q": 11.0, "runway_4q": None},
            {"quarter": "2024 Q3", "cash": 3.06, "change": -1.74, "burn": 1.74, "financing": 0, "underlying_burn": 1.74, "runway_2q": 4.1, "runway_4q": None},
            {"quarter": "2024 Q4", "cash": 0.91, "change": -2.15, "burn": 2.15, "financing": 0, "underlying_burn": 2.15, "runway_2q": 1.4, "runway_4q": 2.8},
            {"quarter": "2025 Q1", "cash": 0.78, "change": -0.13, "burn": 0.13, "financing": 0, "underlying_burn": 0.13, "runway_2q": 7.6, "runway_4q": 5.8},
            # 2025 Q2: financing kwartaal - underlying burn GESCHAT (laatste schone = 0.13)
            {"quarter": "2025 Q2", "cash": 2.55, "change": +1.77, "burn": 0, "financing": 1.77, "underlying_burn": 0.13, "runway_2q": 58.8, "runway_4q": 43.9},
            {"quarter": "2025 Q3", "cash": 1.21, "change": -1.34, "burn": 1.34, "financing": 0, "underlying_burn": 1.34, "runway_2q": 2.7, "runway_4q": 3.6},
            # 2025 Q4: financing kwartaal - underlying burn GESCHAT (gewogen: 0.13×1 + 1.34×2)/3 = 0.94)
            {"quarter": "2025 Q4", "cash": 2.69, "change": +1.48, "burn": 0, "financing": 1.48, "underlying_burn": 0.94, "runway_2q": 8.6, "runway_4q": 6.0},
            # 2026 Q1: financing kwartaal - underlying burn GESCHAT (gewogen: 1.34×1 + 0.94×2)/3 = 1.07)
            {"quarter": "2026 Q1", "cash": 30.01, "change": +27.32, "burn": 0, "financing": 27.32, "underlying_burn": 1.07, "runway_2q": 84.1, "runway_4q": 78.0},
        ]
    },

    # =========================================================
    # 4. LITHIUM AMERICAS (LAC) - VALUTA: USD
    # =========================================================
    "Lithium Americas": {
        "currency": "USD",
        "data": [
            {"quarter": "2023 Q4", "cash": 195.52, "change": -12.90, "burn": 12.90, "financing": 0, "underlying_burn": 12.90, "runway_2q": None, "runway_4q": None},
            {"quarter": "2024 Q1", "cash": 147.24, "change": -48.28, "burn": 48.28, "financing": 0, "underlying_burn": 48.28, "runway_2q": 7.3, "runway_4q": None},
            # 2024 Q2: financing kwartaal - underlying burn GESCHAT (laatste schone = 48.28)
            {"quarter": "2024 Q2", "cash": 375.83, "change": +228.59, "burn": 0, "financing": 228.59, "underlying_burn": 48.28, "runway_2q": 23.4, "runway_4q": None},
            {"quarter": "2024 Q3", "cash": 341.16, "change": -34.67, "burn": 34.67, "financing": 0, "underlying_burn": 34.67, "runway_2q": 14.8, "runway_4q": 16.7},
            # 2024 Q4: financing kwartaal - underlying burn GESCHAT (laatste schone = 34.67)
            {"quarter": "2024 Q4", "cash": 593.89, "change": +252.73, "burn": 0, "financing": 252.73, "underlying_burn": 34.67, "runway_2q": 51.4, "runway_4q": 50.8},
            {"quarter": "2025 Q1", "cash": 446.62, "change": -147.27, "burn": 147.27, "financing": 0, "underlying_burn": 147.27, "runway_2q": 4.9, "runway_4q": 7.0},
            # 2025 Q2: financing kwartaal - underlying burn GESCHAT (gewogen: 34.67×1 + 147.27×2)/3 = 109.74)
            {"quarter": "2025 Q2", "cash": 508.85, "change": +62.23, "burn": 0, "financing": 62.23, "underlying_burn": 109.74, "runway_2q": 13.9, "runway_4q": 9.3},
            {"quarter": "2025 Q3", "cash": 385.31, "change": -123.54, "burn": 123.54, "financing": 0, "underlying_burn": 123.54, "runway_2q": 9.4, "runway_4q": 9.5},
            # 2025 Q4: financing kwartaal - underlying burn GESCHAT (gewogen: 147.27×1 + 123.54×2)/3 = 131.45)
            {"quarter": "2025 Q4", "cash": 568.23, "change": +182.92, "burn": 0, "financing": 182.92, "underlying_burn": 131.45, "runway_2q": 13.0, "runway_4q": 10.4},
            # 2026 Q1: financing kwartaal - underlying burn GESCHAT (gewogen: 123.54×1 + 131.45×2)/3 = 128.81)
            {"quarter": "2026 Q1", "cash": 758.51, "change": +190.28, "burn": 0, "financing": 190.28, "underlying_burn": 128.81, "runway_2q": 17.7, "runway_4q": 14.5},
        ]
    },

    # =========================================================
    # 5. AMERICAN LITHIUM (AMLIF) - VALUTA: CAD
    # =========================================================
    "American Lithium": {
        "currency": "CAD",
        "data": [
            {"quarter": "2024 Q1", "cash": 11.89, "change": -7.01, "burn": 7.01, "financing": 0, "underlying_burn": 7.01, "runway_2q": None, "runway_4q": None},
            {"quarter": "2024 Q2", "cash": 8.97, "change": -2.92, "burn": 2.92, "financing": 0, "underlying_burn": 2.92, "runway_2q": 5.4, "runway_4q": None},
            {"quarter": "2024 Q3", "cash": 5.73, "change": -3.24, "burn": 3.24, "financing": 0, "underlying_burn": 3.24, "runway_2q": 2.8, "runway_4q": None},
            {"quarter": "2024 Q4", "cash": 3.49, "change": -2.24, "burn": 2.24, "financing": 0, "underlying_burn": 2.24, "runway_2q": 3.8, "runway_4q": 4.4},
            {"quarter": "2025 Q1", "cash": 1.11, "change": -2.38, "burn": 2.38, "financing": 0, "underlying_burn": 2.38, "runway_2q": 1.4, "runway_4q": 1.9},
            {"quarter": "2025 Q2", "cash": 0.36, "change": -0.75, "burn": 0.75, "financing": 0, "underlying_burn": 0.75, "runway_2q": 1.2, "runway_4q": 1.5},
            # 2025 Q3: financing kwartaal - underlying burn GESCHAT (laatste schone = 0.75)
            {"quarter": "2025 Q3", "cash": 7.63, "change": +7.27, "burn": 0, "financing": 7.27, "underlying_burn": 0.75, "runway_2q": 30.5, "runway_4q": 27.7},
            {"quarter": "2025 Q4", "cash": 4.34, "change": -3.29, "burn": 3.29, "financing": 0, "underlying_burn": 3.29, "runway_2q": 4.0, "runway_4q": 4.8},
            # 2026 Q1: financing kwartaal - underlying burn GESCHAT (gewogen: 0.75×1 + 3.29×2)/3 = 2.44)
            {"quarter": "2026 Q1", "cash": 7.57, "change": +3.23, "burn": 0, "financing": 3.23, "underlying_burn": 2.44, "runway_2q": 9.3, "runway_4q": 6.7},
        ]
    },
}
