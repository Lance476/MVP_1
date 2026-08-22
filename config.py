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
    "Noram Lithium": {
        "gvkey": 187729,
        "yf_ticker": "NRM",
        "search_terms": ['"Noram Lithium"', '"NRM stock"', 'Zeus'],
        "short_name": "Noram",
        "color": "#16A085",
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
# Grouped stock performance comparison so investors can compare Nevada
# lithium juniors vs Canadian juniors vs Australian producers/ETF-benchmark.
# Each entry maps a display label to its Yahoo Finance ticker.
# ============================================================================
STOCK_CLUSTERS = {
    "Nevada Juniors": {
        "label": "Nevada Lithium Juniors",
        "members": {
            "Lithium Americas": "LAC",
            "American Battery Technology": "ABAT",
            "Ioneer": "IONR",
            "Century Lithium": "LCE.V",
            "Surge Battery Metals": "NILI",
            "Noram Lithium": "NRM",
            "Nevada Lithium": "NVLHF",
        },
    },
    "Canadian Juniors": {
        "label": "Canadian Lithium Juniors",
        "members": {
            "E3 Lithium": "ETL.V",
            "Patriot Battery Metals": "PMETF",
            "Critical Elements Lithium": "CRE.V",
        },
    },
    "Australian Producers + Benchmark": {
        "label": "Australian Producers + Sprott ETF",
        "members": {
            "Pilbara Minerals": "PLS.AX",
            "Mineral Resources": "MIN.AX",
            "Liontown Resources": "LTR.AX",
            "Sprott Lithium Miners ETF": "LITP",
        },
    },
}

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
    "Noram Lithium": {
        "months": ["8/2025", "9/2025", "10/2025", "11/2025", "12/2025", "1/2026", "2/2026", "3/2026", "4/2026", "5/2026", "6/2026", "7/2026"],
        "values": [10, 20, 40, 20, 20, 20, 20, 10, 10, 10, 20, 10],
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
# MARKT BENCHMARK (Sprott Lithium Miners ETF)
# ============================================================================
LIT_TICKER = "LITP"
LIT_LABEL = "Sprott Lithium Miners ETF (LITP)"

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
    # Zeus — Noram Lithium Corp (gvkey 187729)
    # ------------------------------------------------------------------
    "Noram Lithium": {
        "Stage": ["MRE", "MRE_U", "PEA", "MRE_U2", "MRE_U3"],
        "Stage_Display": [
            "Mineral Resource Estimate",
            "Mineral Resource Estimate (Updated)",
            "Preliminary Economic Assessment",
            "Mineral Resource Estimate (Updated)",
            "Mineral Resource Estimate (Updated)"
        ],
        "Date": ["2017-07-24", "2021-08-16", "2021-12-08", "2023-01-30", "2024-06-11"],
        "PressRelease_Date": ["24-7-2017", "16-8-2021", "8-12-2021", "30-1-2023", "11-6-2024"],
        "AfterTax_NPV_M": [None, None, 1299, None, None],
        "AfterTax_IRR_%": [None, None, 31, None, None],
        "Initial_Capex_M": [None, None, None, None, None],
        "Total_Capex_M": [None, None, None, None, None],
        "Resource_Measured_Indicated_Mt": [None, None, None, None, None],
        "Resource_Inferred_Mt": [None, None, None, None, None],
        "Average_Lithium_Grade": [None, None, None, None, None],
        "Metallurgical_Recovery_%": [None, None, None, None, None],
        "Life_of_Mine_Years": [None, None, None, None, None],
        "Avg_Annual_Production_tpa": [None, None, 31900, None, None],
        "Net_Operating_Cost_t": [None, None, 3355, None, None],
        "BaseCase_Li_Price": [None, None, None, None, None],
        "Payback_Period_Years": [None, None, 3.23, None, None],
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
    ],
    "Surge Battery Metals": [
        {"Study": "PoO_Submitted", "Commitment date": "—", "Expected date": "—", "Actual date": "21-11-2023", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "MRE", "Commitment date": "16-01-2024", "Expected date": "—", "Actual date": "22-02-2024", "Delay": "—", "Commitment Evidence": "Surge Battery Metals announced on January 16, 2024 that it had retained Dr. Bruce Davis to prepare a maiden Mineral Resource Estimate, which was subsequently announced on February 22, 2024.", "Expected Evidence": "—"},
        {"Study": "PoO_Accepted", "Commitment date": "—", "Expected date": "—", "Actual date": "28-02-2024", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—", "Actual date": "24-09-2024", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "NEPA_Start", "Commitment date": "—", "Expected date": "—", "Actual date": "20-12-2024", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "Final_EA", "Commitment date": "—", "Expected date": "—", "Actual date": "05-03-2025", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PEA", "Commitment date": "22-02-2024", "Expected date": "31-12-2024", "Actual date": "09-06-2025", "Delay": "~5 months", "Commitment Evidence": "Surge expects to undertake a PEA study on the NNLP with an anticipated target reporting date in Q4 of 2024.", "Expected Evidence": "—"},
    ],
    "Noram Lithium": [
        {"Study": "MRE", "Commitment date": "20-07-2016", "Expected date": "—", "Actual date": "24-07-2017", "Delay": "—", "Commitment Evidence": "Subsurface exploration in the form of shallow drilling core holes will be required to determine a preliminary resource estimate of the lithium and potassium contained within the near surface area central to the Zeus claims.", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "29-10-2020", "Expected date": "30-03-2021", "Actual date": "16-08-2021", "Delay": "~4 months", "Commitment Evidence": "Noram expects to complete an updated NI 43-101 compliant resource estimate report by the end of Q1 2021.", "Expected Evidence": "—"},
        {"Study": "PEA", "Commitment date": "30-07-2020", "Expected date": "31-12-2020", "Actual date": "08-12-2021", "Delay": "~11 months", "Commitment Evidence": "planning engineering and economic studies toward a Preliminary Economic Assessment in 2020 (PEA).", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "30-07-2022", "Expected date": "—", "Actual date": "30-01-2023", "Delay": "—", "Commitment Evidence": "Phase VI drilling in mid-2022", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "07-11-2023", "Expected date": "—", "Actual date": "11-06-2024", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
    ],
    "American Lithium Corp": [
        {"Study": "MRE", "Commitment date": "19-06-2019", "Expected date": "30-12-2019", "Actual date": "21-05-2020", "Delay": "~4 months", "Commitment Evidence": "With drilling ongoing, the company expects to deliver a maiden resource and early stage economic study in 2019.", "Expected Evidence": "—"},
        {"Study": "PoO_Submitted", "Commitment date": "—", "Expected date": "—", "Actual date": "13-01-2021", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PoO_Accepted", "Commitment date": "—", "Expected date": "—", "Actual date": "17-06-2021", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PoO_Approved", "Commitment date": "—", "Expected date": "—", "Actual date": "11-01-2022", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—", "Actual date": "01-12-2022", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
        {"Study": "PEA", "Commitment date": "05-10-2021", "Expected date": "31-03-2022", "Actual date": "01-02-2023", "Delay": "~10 months", "Commitment Evidence": "Optimization of process engineering and pre-concentration work being fast-tracked to enable completion of a Preliminary Economic Assessment ('PEA') during Q1 2022.", "Expected Evidence": "—"},
        {"Study": "MRE_U", "Commitment date": "08-12-2023", "Expected date": "—", "Actual date": "27-02-2025", "Delay": "—", "Commitment Evidence": "—", "Expected Evidence": "—"},
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
