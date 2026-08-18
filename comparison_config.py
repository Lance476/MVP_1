# comparison_config.py
# ============================================================================
# Company registry & comparison configuration
# ============================================================================

# ============================================================================
# COMPANY REGISTRY
# ============================================================================
# Central source of truth for all companies in the comparison platform.
# Each entry maps a display name to its identifiers for every data source:
#   - gvkey:       Compustat identifier (financials CSV)
#   - yf_ticker:   Yahoo Finance ticker (stock data)
#   - search_term: Google Trends search term (SerpApi)
#
# TIP: To add a company later, add one entry here — every section
# (market sentiment, stock, studies, financials, trends) picks it up
# automatically.
# ============================================================================

COMPANIES = {
    "Century Lithium Corp": {
        "gvkey": 106098,
        "yf_ticker": "LCE.V",
        "search_term": "Century Lithium",
        "short_name": "Century",
        "color": "#2E86C1",
    },
    "American Battery Technology": {
        "gvkey": 26366,
        "yf_ticker": "ABAT",
        "search_term": "American Battery Technology",
        "short_name": "ABTC",
        "color": "#F39C12",
    },
    "Ioneer Ltd": {
        "gvkey": 290341,
        "yf_ticker": "IONR",
        "search_term": "Ioneer",
        "short_name": "Ioneer",
        "color": "#27AE60",
    },
    "Lithium Americas Corp": {
        "gvkey": 43404,
        "yf_ticker": "LAC",
        "search_term": "Lithium Americas",
        "short_name": "LAC",
        "color": "#8E44AD",
    },
    "Surge Battery Metals Inc": {
        "gvkey": 106045,
        "yf_ticker": "NILI.V",
        "search_term": "Surge Battery Metals",
        "short_name": "Surge",
        "color": "#E67E22",
    },
    "Noram Lithium Corp": {
        "gvkey": 187729,
        "yf_ticker": "NRM.V",
        "search_term": "Noram Lithium",
        "short_name": "Noram",
        "color": "#16A085",
    },
    "American Lithium Corp": {
        "gvkey": 107393,
        "yf_ticker": "LI",
        "search_term": "American Lithium",
        "short_name": "ALC",
        "color": "#C0392B",
    },
}

DEFAULT_COMPANY = "Century Lithium Corp"

# ============================================================================
# YAHOO FINANCE TICKERS
# ============================================================================
# Used by the stock chart & market sentiment. Includes the Sprott Lithium
# Miners ETF (LITP) as a market benchmark.
LIT_TICKER = "LITP"
LIT_LABEL = "Sprott Lithium Miners ETF (LITP)"

# ============================================================================
# STUDY STAGE LABELS & ORDER
# ============================================================================
# Shared mapping of study stage display names to their short labels, plus the
# canonical x-axis order used by all study charts.
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
# Each company gets its own DataFrame of study stages. The schema is shared
# so all downstream rendering functions work unchanged.
#
# NOTE: Study economics below are the user-provided table covering the seven
# Nevada lithium projects (Keystone, Rhyolite Ridge, Thacker Pass, Angel
# Island, Tonopah Flats, Zeus, TLC). They are best-effort public figures and
# should still be verified against the underlying technical reports before
# relying on them for investment analysis. The UI labels the app as MVP demo.
#
# Where a study only reports a single CAPEX figure (labelled Total_Capex_M in
# the source table), we mirror it into Initial_Capex_M so the NPV/CAPEX ratio
# renders. Adjust if you have a distinct initial-CAPEX number per study.
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
    "Century Lithium Corp": {
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
    "American Battery Technology": {
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
    "Ioneer Ltd": {
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
    "Lithium Americas Corp": {
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
    "Surge Battery Metals Inc": {
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
    "Noram Lithium Corp": {
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
# Some companies (e.g. LAC) have Compustat stock data that only begins after a
# corporate event (LAC's Oct-2023 split), so earlier study dates have no
# price × shares record in Stock_Daily_Combined.csv. Provide the market data
# manually here, keyed by (company display name, study Stage_Display).
#
# Fields per entry:
#   - Date:        trading date of the price / share count
#   - Stock_Price: closing share price (USD) on that date
#   - Shares_M:    shares outstanding (in millions) on that date
#
# MarketCap_M is computed automatically as Stock_Price × Shares_M.
# ============================================================================

MARKET_CAP_OVERRIDES = {
    "Lithium Americas Corp": {
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
# Press-release milestones for each project. "Actual date" is the press
# release date from the study table; Commitment/Expected are left as "—"
# where not available.
# ============================================================================

TIMELINE_DATA = {
    "Century Lithium Corp": [
        {"Study": "MRE", "Commitment date": "07-02-2018", "Expected date": "—",
         "Actual date": "01-05-2018", "Delay": "—"},
        {"Study": "PEA", "Commitment date": "09-05-2018", "Expected date": "Late July 2018",
         "Actual date": "06-09-2018", "Delay": "~6 weeks"},
        {"Study": "PFS", "Commitment date": "01-10-2018", "Expected date": "Q1 2019",
         "Actual date": "19-05-2020", "Delay": "~14 months"},
        {"Study": "FS", "Commitment date": "15-06-2022", "Expected date": "Late 2022",
         "Actual date": "29-04-2024", "Delay": "~16 months"},
        {"Study": "FS_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "23-02-2026", "Delay": "—"},
    ],
    "American Battery Technology": [
        {"Study": "MRE", "Commitment date": "—", "Expected date": "—",
         "Actual date": "26-02-2023", "Delay": "—"},
        {"Study": "PEA", "Commitment date": "—", "Expected date": "—",
         "Actual date": "21-12-2023", "Delay": "—"},
        {"Study": "PEA_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "24-04-2024", "Delay": "—"},
        {"Study": "PFS", "Commitment date": "—", "Expected date": "—",
         "Actual date": "16-10-2025", "Delay": "—"},
    ],
    "Ioneer Ltd": [
        {"Study": "PFS", "Commitment date": "—", "Expected date": "—",
         "Actual date": "23-10-2018", "Delay": "—"},
        {"Study": "FS", "Commitment date": "—", "Expected date": "—",
         "Actual date": "30-04-2020", "Delay": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "26-04-2023", "Delay": "—"},
        {"Study": "Fully_Permitted", "Commitment date": "—", "Expected date": "—",
         "Actual date": "24-10-2024", "Delay": "—"},
        {"Study": "FID", "Commitment date": "—", "Expected date": "—",
         "Actual date": "15-01-2025", "Delay": "—"},
        {"Study": "FS_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "29-10-2025", "Delay": "—"},
    ],
    "Lithium Americas Corp": [
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "05-04-2018", "Delay": "—"},
        {"Study": "PFS", "Commitment date": "—", "Expected date": "—",
         "Actual date": "21-06-2018", "Delay": "—"},
        {"Study": "Fully_Permitted", "Commitment date": "—", "Expected date": "—",
         "Actual date": "15-01-2021", "Delay": "—"},
        {"Study": "FS", "Commitment date": "—", "Expected date": "—",
         "Actual date": "31-01-2023", "Delay": "—"},
        {"Study": "FS_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "07-01-2025", "Delay": "—"},
    ],
    "Surge Battery Metals Inc": [
        {"Study": "MRE", "Commitment date": "—", "Expected date": "—",
         "Actual date": "22-02-2024", "Delay": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "24-09-2024", "Delay": "—"},
        {"Study": "PEA", "Commitment date": "—", "Expected date": "—",
         "Actual date": "09-06-2025", "Delay": "—"},
    ],
    "Noram Lithium Corp": [
        {"Study": "MRE", "Commitment date": "—", "Expected date": "—",
         "Actual date": "24-07-2017", "Delay": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "16-08-2021", "Delay": "—"},
        {"Study": "PEA", "Commitment date": "—", "Expected date": "—",
         "Actual date": "08-12-2021", "Delay": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "30-01-2023", "Delay": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "11-06-2024", "Delay": "—"},
    ],
    "American Lithium Corp": [
        {"Study": "MRE", "Commitment date": "—", "Expected date": "—",
         "Actual date": "21-05-2020", "Delay": "—"},
        {"Study": "MRE_U", "Commitment date": "—", "Expected date": "—",
         "Actual date": "16-01-2023", "Delay": "—"},
        {"Study": "PEA", "Commitment date": "—", "Expected date": "—",
         "Actual date": "01-02-2023", "Delay": "—"},
    ],
}