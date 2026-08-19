# app.py - Lithium Project Comparison Dashboard
# ============================================================================
#
# DESIGN:
#   - Sidebar: choose "Single Company" or "Compare Companies"
#   - Single Company: full deep-dive (existing dashboard) for any selected firm
#   - Compare: side-by-side metrics + comparison charts across firms
#   - Market sentiment & stock price = unique to the selected company / companies
#   - Value ratios, Resource & grade, Study timeline, Financial analysis,
#     Google Search Interest = comparable across companies
#
# To add a company: edit comparison_config.py (COMPANIES, STUDY_DATA, TIMELINE_DATA)
# ============================================================================
import altair as alt
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import plotly.graph_objects as go
import warnings
import re
from streamlit_gtag import st_gtag
import streamlit as st
from streamlit_page_analytics import StreamlitPageAnalytics
import uuid 
import time
from datetime import datetime
from streamlit_cookies_controller import CookieController

from comparison_config import (
    COMPANIES,
    DEFAULT_COMPANY,
    LIT_LABEL,
    LIT_TICKER,
    MARKET_CAP_OVERRIDES,
    STAGE_ORDER,
    STAGE_SHORT_MAP,
    STUDY_COLUMNS,
    STUDY_DATA,
    TIMELINE_DATA,
)

warnings.filterwarnings("ignore")

# ============================================================================
# USER AND SESSION IDS MET COOKIE - NIEUW
# ============================================================================
# Cookie controller voor herkenning van terugkerende gebruikers
try:
    controller = CookieController()
except Exception:
    controller = None

if "user_id" not in st.session_state:
    if controller:
        # Probeer bestaande cookie te lezen
        cookie_user_id = controller.get("user_id")
        if cookie_user_id:
            # BESTAANDE GEBRUIKER
            st.session_state.user_id = cookie_user_id
            st.session_state.is_returning = True
            st.session_state.visit_number = st.session_state.get("visit_number", 0) + 1
        else:
            # NIEUWE GEBRUIKER
            new_id = str(uuid.uuid4())
            try:
                controller.set("user_id", new_id, max_age=365*24*60*60)  # 1 jaar
            except Exception:
                pass
            st.session_state.user_id = new_id
            st.session_state.is_returning = False
            st.session_state.visit_number = 1
    else:
        # Fallback: geen cookie beschikbaar
        st.session_state.user_id = str(uuid.uuid4())
        st.session_state.is_returning = False
        st.session_state.visit_number = 1

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    layout="wide", 
    page_title="Lithium Project Comparison",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# Custom CSS to remove visual clutter and create a cleaner look
st.markdown("""
<style>
    /* Remove default Streamlit padding and margins */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    
    /* Remove the default divider lines */
    hr {
        margin: 0.5rem 0 !important;
        opacity: 0.3 !important;
    }
    
    /* Make headers more compact */
    h1, h2, h3, h4, h5, h6 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        font-weight: 600 !important;
        color: #1a1a2e !important;
    }
    
    h1 {
        font-size: 28px !important;
        margin-bottom: 0.25rem !important;
    }
    
    h2 {
        font-size: 20px !important;
        margin-top: 1rem !important;
    }
    
    h3 {
        font-size: 17px !important;
        margin-top: 0.75rem !important;
    }
    
    /* Remove extra spacing around subheaders */
    .stSubheader {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
        font-size: 18px !important;
    }
    
    /* Clean up metric cards */
    [data-testid="metric-container"] {
        background: transparent !important;
        padding: 0.5rem 0 !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Reduce spacing between columns */
    .row-widget.stColumns {
        gap: 0.5rem !important;
    }
    
    /* Make dataframes more compact */
    .stDataFrame {
        border: none !important;
    }
    
    .stDataFrame table {
        font-size: 13px !important;
    }
    
    /* Reduce spacing in expanders */
    .streamlit-expanderHeader {
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 0.5rem 0 !important;
    }
    
    .streamlit-expanderContent {
        padding-top: 0.5rem !important;
    }
    
    /* Clean up sidebar */
    .css-1d391kg {
        padding-top: 1rem !important;
    }
    
    /* Remove extra spacing around tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.25rem 0.5rem !important;
        font-size: 14px !important;
    }
    
    /* More compact info/warning boxes */
    .stAlert {
        padding: 0.5rem 1rem !important;
        margin-bottom: 0.5rem !important;
        font-size: 13px !important;
    }
    
    /* Reduce padding in columns */
    .css-1r6slb0 {
        padding: 0 !important;
    }
    
    /* Clean up select boxes */
    .stSelectbox label {
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    
    /* Compact radio buttons */
    .stRadio label {
        font-size: 13px !important;
    }
    
    /* Remove extra spacing in dividers */
    .element-container:has(hr) {
        margin: 0.25rem 0 !important;
    }
    
    /* Make captions smaller */
    .stCaption {
        font-size: 12px !important;
        color: #888 !important;
    }
</style>
""", unsafe_allow_html=True)
# ============================================================================
# SERPAPI CONFIG
# ============================================================================
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# ============================================================================
# GOOGLE ANALYTICS MET USER DATA - NIEUW
# ============================================================================
# Haal GA4 ID uit secrets (veilig!)
GA4_ID = st.secrets.get("GA4_ID", "")

# Alleen toevoegen als er een ID is ingesteld
if GA4_ID:
    st_gtag(
        id=GA4_ID,
        event_name="page_loaded",
        params={
            "app_name": "Lithium_Project_Comparison",
            "user_id": st.session_state.user_id,
            "is_returning": str(st.session_state.is_returning),
            "visit_number": st.session_state.visit_number
        }
    )

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
def render_sidebar():
    """Sidebar: choose Single Company or Compare mode + company selection."""
    with st.sidebar:
        st.markdown("### Navigation")
        
        # Use a cleaner style without extra boxes
        view_mode = st.radio(
            "View Mode",
            ["Single Company", "Compare Companies"],
            help="Single: deep-dive on one company. Compare: side-by-side comparison.",
            label_visibility="collapsed"
        )

        if view_mode == "Single Company":
            company = st.selectbox(
                "Select Company",
                list(COMPANIES.keys()),
                index=list(COMPANIES.keys()).index(DEFAULT_COMPANY),
                label_visibility="collapsed"
            )
            selected = [company]
        else:
            selected = st.multiselect(
                "Select Companies to Compare",
                list(COMPANIES.keys()),
                default=[DEFAULT_COMPANY, "Ioneer Ltd", "Lithium Americas Corp"],
                help="Pick 2 or more companies to compare.",
                label_visibility="collapsed"
            )
            if len(selected) < 2:
                st.warning("Select at least 2 companies.")

        st.markdown("")
        st.caption("MVP Demo — Not financial advice.")

        return view_mode, selected

# ============================================================================
# DATA HELPERS
# ============================================================================
def company_search_terms(companies):
    """Return unique Google Trends search terms for the selected companies."""
    terms = [COMPANIES[c]["search_term"] for c in companies]
    # De-duplicate while preserving order
    seen = set()
    return [t for t in terms if not (t in seen or seen.add(t))]


def company_tickers(companies):
    """Return {display_ticker_label: yf_ticker} for the selected companies."""
    return {
        f"{c} ({COMPANIES[c]['yf_ticker']})": COMPANIES[c]["yf_ticker"]
        for c in companies
    }


# ============================================================================
# STUDY DATA
# ============================================================================
@st.cache_data
def load_study_data(companies=None):
    """Load study data for one or more companies.

    Parameters
    ----------
    companies : list[str] | None
        Company display names. None/empty means ALL companies.
    """
    if companies is None:
        companies = list(COMPANIES.keys())

    frames = []
    for name in companies:
        raw = STUDY_DATA.get(name)
        if raw is None:
            continue
        df = pd.DataFrame(raw)
        df["Company"] = name
        df["Date"] = pd.to_datetime(df["Date"])
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=STUDY_COLUMNS + ["Company"])

    combined = pd.concat(frames, ignore_index=True)
    return combined.sort_values("Date")


# ============================================================================
# STOCK DATA (Yahoo Finance)
# ============================================================================
@st.cache_data(ttl=1800)
def get_stock_data(companies=None):
    """Fetch and normalize stock data for the selected companies.

    Always includes the Sprott Lithium Miners ETF (LITP) as a sector benchmark.

    Parameters
    ----------
    companies : list[str] | None
        Company display names. None/empty means ALL companies.
    """
    if companies is None:
        companies = list(COMPANIES.keys())

    def fetch_ticker(ticker):
        """Fetch 5-year stock history from Yahoo Finance."""
        try:
            df = yf.Ticker(ticker).history(period="5y").reset_index()[["Date", "Close", "Volume"]]
            if df is not None and not df.empty:
                return df.reset_index(drop=True)
        except Exception:
            pass
        return pd.DataFrame()

    all_data = []

    # Selected companies (use yfinance tickers only)
    for display, ticker in company_tickers(companies).items():
        data = fetch_ticker(ticker)
        if not data.empty:
            data["Ticker"] = display
            all_data.append(data)

    # Always include the Sprott Lithium Miners ETF benchmark
    lit = fetch_ticker(LIT_TICKER)
    if not lit.empty:
        lit["Ticker"] = LIT_LABEL
        all_data.append(lit)

    if all_data:
        data = pd.concat(all_data, ignore_index=True)
        return data

    return pd.DataFrame()


# ============================================================================
# GOOGLE TRENDS DATA
# ============================================================================
def fetch_google_trends_serpapi(search_terms):
    """Fetch Google Trends data using SerpApi for the given search terms."""
    if not SERPAPI_KEY or not search_terms:
        return None

    try:
        all_data = []

        for term in search_terms:
            params = {
                "api_key": SERPAPI_KEY,
                "engine": "google_trends",
                "q": term,
                "data_type": "TIMESERIES",
                "time_period": "today 5-y",
            }

            response = requests.get("https://serpapi.com/search", params=params)
            result = response.json()

            if "interest_over_time" in result:
                timeline = result["interest_over_time"].get("timeline_data", [])
                for item in timeline:
                    # FIX: use "timestamp" (epoch) — date strings vary per locale,
                    # e.g. "16 Aug 2026 -". SerpApi sends it as str -> int() cast.
                    if item.get("timestamp"):
                        date = pd.to_datetime(int(item["timestamp"]), unit="s", utc=True).tz_localize(None)
                    else:
                        date_str = item.get("date", "")

                        # FIX: Handle "Aug 10 – 16, 2025" format properly
                        try:
                            # First try normal parsing
                            date = pd.to_datetime(date_str)
                        except Exception:
                            # Handle week range: "Aug 10 – 16, 2025"
                            # Split and take the END date
                            parts = date_str.split("–")
                            end_part = parts[1].strip()  # "16, 2025"

                            start_part = parts[0].strip()  # "Aug 10"
                            month_name = start_part.split()[0]  # "Aug"

                            end_clean = end_part.replace(",", "").strip()  # "16 2025"
                            end_parts = end_clean.split()

                            day = int(end_parts[0])  # 16
                            year = int(end_parts[1])  # 2025

                            month_map = {
                                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                                'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                                'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                            }
                            month = month_map.get(month_name[:3], 1)

                            date = pd.Timestamp(year=year, month=month, day=day)

                    if "values" in item and item["values"]:
                        value = float(item["values"][0].get("value", 0))
                        all_data.append({"date": date, "term": term, "value": value})

        if not all_data:
            return None

        df = pd.DataFrame(all_data)
        pivot = df.pivot(index='date', columns='term', values='value').reset_index()
        pivot['date'] = pd.to_datetime(pivot['date'])

        for term in search_terms:
            if term not in pivot.columns:
                pivot[term] = 0

        return pivot

    except Exception as e:
        print(f"Error fetching Google Trends: {e}")
        return None


@st.cache_data(ttl=604800)
def fetch_single_company_trends(company):
    """Fetch Google Trends for ONE company (cached individually)."""
    search_term = COMPANIES[company]['search_term']
    
    if SERPAPI_KEY and search_term:
        data = fetch_google_trends_serpapi([search_term])
        if data is not None and not data.empty:
            return data
    return None

def get_google_trends(companies=None):
    """Get Google Trends data by combining per-company cached data."""
    if companies is None:
        companies = list(COMPANIES.keys())
    
    all_data = []
    for company in companies:
        data = fetch_single_company_trends(company)  # Each company uses its own cache!
        if data is not None and not data.empty:
            all_data.append(data)
    
    if not all_data:
        return None
    
    # Combine all company data into one DataFrame
    # Your existing fetch_google_trends_serpapi returns a pivot table
    # So we need to merge them properly
    combined = all_data[0]  # Start with first
    for df in all_data[1:]:
        # Merge on 'date' column (assuming both have 'date')
        combined = pd.merge(combined, df, on='date', how='outer')
    
    return combined.sort_values('date').reset_index(drop=True)

# ============================================================================
# DASHBOARD METRICS
# ============================================================================
@st.cache_data
def get_dashboard_metrics(companies=None):
    """Get the key market-sentiment metrics for the selected companies.

    Returns a dict keyed by company name, each with:
        current, return_30d, volume_change
    """
    if companies is None:
        companies = list(COMPANIES.keys())

    try:
        stock_data = get_stock_data(companies)

        if stock_data.empty:
            return {}

        # Helper: 30-day return using calendar days (not trading days)
        def calc_30d_return(df):
            df = df.copy()
            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
            df = df.sort_values('Date')
            current = df['Close'].iloc[-1]
            current_date = df['Date'].iloc[-1]
            target_date = current_date - pd.Timedelta(days=30)
            before = df[df['Date'] <= target_date]
            if before.empty:
                base = df['Close'].iloc[0]
            else:
                base = before['Close'].iloc[-1]
            return current, (current / base - 1) * 100

        # Helper: 30-day volume change (avg daily volume, last 30d vs previous 30d)
        def calc_30d_volume_change(df):
            df = df.copy()
            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
            df = df.sort_values('Date')
            if 'Volume' not in df.columns:
                return None
            latest = df['Date'].iloc[-1]
            cutoff_late = latest - pd.Timedelta(days=30)
            cutoff_early = latest - pd.Timedelta(days=60)
            recent = df[df['Date'] > cutoff_late]['Volume']
            prior = df[(df['Date'] > cutoff_early) & (df['Date'] <= cutoff_late)]['Volume']
            if len(recent) == 0 or len(prior) == 0:
                return None
            avg_recent = recent.mean()
            avg_prior = prior.mean()
            if avg_prior == 0:
                return None
            return (avg_recent / avg_prior - 1) * 100

        trends = get_google_trends(companies)

        # Build per-company metrics
        metrics = {}
        for company in companies:
            label = f"{company} ({COMPANIES[company]['yf_ticker']})"
            company_data = stock_data[stock_data['Ticker'] == label]
            if len(company_data) < 2:
                continue
            current, ret = calc_30d_return(company_data)
            volume_change = calc_30d_volume_change(company_data)

            # Google Trends value for this company (optional)
            search_current = None
            search_change = None
            search_term = COMPANIES[company]['search_term']
            if trends is not None and not trends.empty and search_term in trends.columns:
                series = trends[search_term].dropna()
                if len(series) >= 2:
                    search_current = series.iloc[-1]
                    search_30_ago = series.iloc[-30] if len(series) >= 30 else series.iloc[0]
                    search_change = search_current - search_30_ago

            metrics[company] = {
                'current': current,
                'return_30d': ret,
                'volume_change': volume_change,
                'search_current': search_current,
                'search_change': search_change,
            }

        # LIT benchmark metrics
        lit_data = stock_data[stock_data['Ticker'] == LIT_LABEL]
        if len(lit_data) >= 2:
            lit_current, lit_return = calc_30d_return(lit_data)
            metrics['_lit_benchmark'] = {
                'current': lit_current,
                'return_30d': lit_return,
            }

        return metrics
    except Exception as e:
        print(f"get_dashboard_metrics error: {e}")
        return {}


# ============================================================================
# CORRELATION DATA
# ============================================================================
@st.cache_data(ttl=604800)
def get_correlation_data(companies=None):
    """Correlation between lithium prices and search interest per company."""
    if companies is None:
        companies = list(COMPANIES.keys())

    try:
        trends = get_google_trends(companies)
        stock_data = get_stock_data(companies)

        if trends is None or trends.empty or stock_data.empty:
            return pd.DataFrame(), None

        lit_data = stock_data[stock_data['Ticker'] == LIT_LABEL].copy()
        if lit_data.empty:
            return pd.DataFrame(), None

        lit_data['Date'] = pd.to_datetime(lit_data['Date']).dt.tz_localize(None)
        trends['date'] = pd.to_datetime(trends['date']).dt.tz_localize(None)

        lit_data['Month'] = lit_data['Date'].dt.to_period('M')
        trends['Month'] = trends['date'].dt.to_period('M')

        lit_monthly = lit_data.groupby('Month')['Close'].mean().reset_index()

        # Melt trends to long format for multi-company correlation
        trend_cols = company_search_terms(companies)
        trend_cols_present = [c for c in trend_cols if c in trends.columns]
        if not trend_cols_present:
            return pd.DataFrame(), None

        # One merged frame per company search term
        all_merged = []
        for term in trend_cols_present:
            trends_monthly = trends.groupby('Month')[term].mean().reset_index()
            merged = pd.merge(lit_monthly, trends_monthly, on='Month', how='inner')
            if merged.empty:
                continue
            merged['Date'] = merged['Month'].dt.to_timestamp()
            merged['Lit_Indexed'] = merged['Close'] / merged['Close'].iloc[0] * 100
            merged['Search_Indexed'] = merged[term] / merged[term].max() * 100
            merged['Search_Term'] = term
            all_merged.append(merged)

        if not all_merged:
            return pd.DataFrame(), None

        return pd.concat(all_merged, ignore_index=True), None
    except Exception as e:
        return pd.DataFrame(), None


# ============================================================================
# SEARCH ANALYSIS
# ============================================================================
@st.cache_data(ttl=604800)
def get_monthly_search_pattern(companies=None):
    """Average search interest by month (Jan-Dec) per company."""
    if companies is None:
        companies = list(COMPANIES.keys())

    trends = get_google_trends(companies)
    if trends is None or trends.empty:
        return None

    search_terms = company_search_terms(companies)
    term_cols = [t for t in search_terms if t in trends.columns]
    if not term_cols:
        return None

    df = trends[['date'] + term_cols].copy()
    df['date'] = pd.to_datetime(df['date'])
    df['Month'] = df['date'].dt.month

    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }

    frames = []
    for term in term_cols:
        monthly = df.groupby('Month')[term].mean().reset_index()
        monthly.columns = ['Month', 'Interest']
        monthly['Term'] = term
        monthly['Month_Name'] = monthly['Month'].map(month_names)
        monthly = monthly.sort_values('Month').reset_index(drop=True)
        frames.append(monthly)

    if not frames:
        return None

    return pd.concat(frames, ignore_index=True)


def render_monthly_pattern(companies=None):
    """Compact bar chart of average monthly search interest (grouped)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    monthly = get_monthly_search_pattern(companies)
    if monthly is None or monthly.empty:
        return

    # Map search terms back to company display names
    term_to_company = {COMPANIES[c]['search_term']: c for c in companies}
    monthly['Company'] = monthly['Term'].map(term_to_company).fillna(monthly['Term'])

    # Color scale for companies
    color_scale = {c: COMPANIES[c]['color'] for c in companies}

    chart = alt.Chart(monthly).mark_bar(
        size=14,
        cornerRadiusTopLeft=3,
        cornerRadiusTopRight=3
    ).encode(
        x=alt.X('Month_Name:N',
                sort=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                title=None,
                axis=alt.Axis(labelAngle=0, labelFontSize=10, title=None)),
        y=alt.Y('Interest:Q',
                title='Avg Interest (0-100)',
                scale=alt.Scale(domain=[0, 100])),
        color=alt.Color('Company:N',
                        scale=alt.Scale(domain=list(color_scale.keys()),
                                        range=list(color_scale.values())),
                        legend=alt.Legend(orient="top", title=None, labelFontSize=10)),
        tooltip=[
            alt.Tooltip('Company:N', title='Company'),
            alt.Tooltip('Month_Name:N', title='Month'),
            alt.Tooltip('Interest:Q', title='Avg Interest', format='.1f')
        ]
    ).properties(height=160)

    st.altair_chart(chart, use_container_width=True)


# ============================================================================
# MARKET CAP DATA (ratio's)
# ============================================================================
@st.cache_data
def get_market_cap_data(companies=None):
    """Market cap at each study date from company stock data (price × shares outstanding)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    try:
        annual, stock = load_financial_data()

        results = []
        for company in companies:
            gvkey = COMPANIES[company]['gvkey']
            company_stock = stock[stock['gvkey'] == gvkey].copy()
            if company_stock.empty:
                continue

            company_stock['datadate'] = pd.to_datetime(company_stock['datadate'])
            company_stock = company_stock.sort_values('datadate').reset_index(drop=True)

            # Use the latest available study date per company (from study data)
            study_df = load_study_data([company])
            study_dates = {}
            for _, row in study_df.iterrows():
                if pd.notna(row.get('AfterTax_NPV_M')):
                    study_dates[row['Stage_Display']] = row['Date'].strftime('%Y-%m-%d')

            # Manual market-cap overrides take priority when Compustat has no
            # stock coverage for a company's older study dates (e.g. LAC's
            # pre-Oct-2023 split history is not in Stock_Daily_Combined.csv).
            comp_overrides = MARKET_CAP_OVERRIDES.get(company, {})

            for stage, date_str in study_dates.items():
                if stage in comp_overrides:
                    ov = comp_overrides[stage]
                    results.append({
                        'Company': company,
                        'Stage_Display': stage,
                        'MarketCap_M': ov['Stock_Price'] * ov['Shares_M'],
                        'Shares_M': ov['Shares_M'],
                        'Stock_Price': ov['Stock_Price'],
                    })
                    continue

                target = pd.Timestamp(date_str)
                idx = (company_stock['datadate'] - target).abs().idxmin()
                row = company_stock.iloc[idx]

                # Some records (e.g. first days of post-split LAC) have NaN
                # shares outstanding — use the nearest row with a valid count.
                if pd.isna(row.get('cshoc', np.nan)):
                    valid = company_stock[company_stock['cshoc'].notna()]
                    if valid.empty:
                        continue
                    idx = (valid['datadate'] - target).abs().idxmin()
                    row = valid.loc[idx]

                results.append({
                    'Company': company,
                    'Stage_Display': stage,
                    'MarketCap_M': row['prccd'] * row['cshoc'] / 1_000_000,
                    'Shares_M': row['cshoc'] / 1_000_000,
                    'Stock_Price': row['prccd']
                })

        return pd.DataFrame(results)
    except Exception as e:
        print(f"get_market_cap_data error: {e}")
        return pd.DataFrame()

# ============================================================================
# PROJECT STUDIES
# ============================================================================
def render_project_studies(companies=None):
    """Render the project study evolution section (single or comparison)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    is_compare = len(companies) > 1

    if is_compare:
        st.subheader("Project Study Comparison")
        render_study_comparison(companies)
        return

    # ------------------------------------------------------------------
    # SINGLE COMPANY VIEW (existing deep-dive)
    # ------------------------------------------------------------------
    company = companies[0]
    st.subheader(f"Project Study Evolution Over Time — {company}")

    df_studies = load_study_data([company])

    if not df_studies.empty:
        tab1, tab2, tab3 = st.tabs(["Economics", "Resource & Grade", "All Data"])

        with tab1:
            st.subheader("Value Ratios")
            ratio_data = df_studies[df_studies['AfterTax_NPV_M'].notna()].copy()
            mc_data = get_market_cap_data([company])

            if not ratio_data.empty and not mc_data.empty:
                merged = pd.merge(
                    ratio_data[['Stage_Display', 'AfterTax_NPV_M', 'Initial_Capex_M']],
                    mc_data[['Stage_Display', 'MarketCap_M', 'Shares_M', 'Stock_Price']],
                    on='Stage_Display', how='inner'
                ).dropna(subset=['MarketCap_M'])

                if not merged.empty:
                    # Bereken ratio's
                    merged['NPV_MarketCap'] = merged['AfterTax_NPV_M'] / merged['MarketCap_M']
                    merged['NPV_CAPEX'] = merged['AfterTax_NPV_M'] / merged['Initial_Capex_M']
                    merged['NPV_per_Share'] = merged['AfterTax_NPV_M'] / merged['Shares_M']

                    # Melt voor compacte grafiek
                    ratio_melted = merged.melt(
                        id_vars=['Stage_Display'],
                        value_vars=['NPV_MarketCap', 'NPV_CAPEX', 'NPV_per_Share'],
                        var_name='Ratio',
                        value_name='Value'
                    )
                    ratio_melted['Ratio'] = ratio_melted['Ratio'].map({
                        'NPV_MarketCap': 'NPV / Mkt Cap',
                        'NPV_CAPEX': 'NPV / CAPEX',
                        'NPV_per_Share': 'NPV / Share'
                    })
                    ratio_melted['Stage_Short'] = ratio_melted['Stage_Display'].map(STAGE_SHORT_MAP)
                    stage_order = merged['Stage_Display'].map(STAGE_SHORT_MAP).tolist()

                    # Compacte gefacetteerde grafiek — elke ratio eigen schaal
                    chart = alt.Chart(ratio_melted).mark_line(
                        point=alt.OverlayMarkDef(size=30, filled=True, stroke='white', strokeWidth=1),
                        strokeWidth=2,
                        color=COMPANIES[company]['color']
                    ).encode(
                        x=alt.X('Stage_Short:N',
                               title=None,
                               sort=stage_order,
                               axis=alt.Axis(labelFontSize=10, labelFontWeight='bold', titlePadding=8)),
                        y=alt.Y('Value:Q',
                               title=None,
                               scale=alt.Scale(zero=False),
                               axis=alt.Axis(labelFontSize=9)),
                        tooltip=[
                            alt.Tooltip('Stage_Display:N', title='Study'),
                            alt.Tooltip('Value:Q', title='Value', format='.2f')
                        ]
                    ).properties(height=110, width=200).facet(
                        row=alt.Row('Ratio:N', title=None,
                                   header=alt.Header(labelFontSize=10, labelAngle=0, labelAlign='left'))
                    )

                    # Halve breedte zoals Search Interest kolommen
                    col_chart, _ = st.columns([1, 1])
                    with col_chart:
                        st.altair_chart(chart, use_container_width=True)
                        st.caption("Values C$")

                      # Compacte tabel — 2 decimalen overal
                    with st.expander("View detailed data table", expanded=False):
                        display_ratios = merged[['Stage_Display', 'AfterTax_NPV_M', 'Initial_Capex_M',
                                             'MarketCap_M', 'NPV_MarketCap', 'NPV_CAPEX', 'NPV_per_Share',
                                             'Stock_Price']].copy()
                        display_ratios.columns = ['Study', 'NPV ($M)', 'CAPEX ($M)', 'Mkt Cap ($M)',
                                              'NPV/MktCap (×)', 'NPV/CAPEX (×)', 'NPV/Share ($)', 'Stock Price ($)']
                        for col in display_ratios.columns:
                            if col != 'Study':
                                display_ratios[col] = display_ratios[col].round(2)
                        st.dataframe(display_ratios, use_container_width=True, hide_index=True)
                else:
                    st.info("No market cap data available for studies.")
        with tab2:
            st.subheader("Resource & Grade Evolution")

            # Shared stage mapping for consistent x-axis ordering across all charts
            chart_h = 170  # Compact height matching Value Ratios proportions

            col1, col2 = st.columns(2)

            # ------------------------------------------------------------------
            # GRAPH 1: Recovery & Production (dual-axis, thin lines, no markers)
            # ------------------------------------------------------------------
            with col1:
                st.markdown("**Recovery & Production**")

                ops_melted = df_studies[['Stage_Display',
                                          'Metallurgical_Recovery_%',
                                          'Avg_Annual_Production_tpa']].copy().melt(
                    id_vars=['Stage_Display'],
                    value_vars=['Metallurgical_Recovery_%', 'Avg_Annual_Production_tpa'],
                    var_name='Metric',
                    value_name='Value'
                ).dropna(subset=['Value'])

                ops_melted['Metric'] = ops_melted['Metric'].map({
                    'Metallurgical_Recovery_%': 'Recovery (%)',
                    'Avg_Annual_Production_tpa': 'Production (tpa)'
                })
                ops_melted['Stage_Short'] = ops_melted['Stage_Display'].map(STAGE_SHORT_MAP)

                base_ops = alt.Chart(ops_melted).encode(
                    x=alt.X('Stage_Short:N',
                            title=None,
                            sort=STAGE_ORDER,
                            axis=alt.Axis(labelFontSize=10, labelFontWeight='bold', titlePadding=8))
                )

                recovery_line = base_ops.transform_filter(alt.datum.Metric == 'Recovery (%)').mark_line(
                    strokeWidth=2
                ).encode(
                    y=alt.Y('Value:Q', title='Recovery (%)', scale=alt.Scale(zero=False),
                            axis=alt.Axis(labelFontSize=9)),
                    color=alt.Color('Metric:N',
                                    scale=alt.Scale(domain=['Recovery (%)', 'Production (tpa)'],
                                                  range=['#2E86C1', '#F39C12']),
                                    legend=alt.Legend(orient="bottom", title=None)),
                    tooltip=[
                        alt.Tooltip('Stage_Display:N', title='Study'),
                        alt.Tooltip('Metric:N', title='Metric'),
                        alt.Tooltip('Value:Q', title='Recovery (%)', format='.1f')
                    ]
                )

                production_line = base_ops.transform_filter(alt.datum.Metric == 'Production (tpa)').mark_line(
                    strokeWidth=2
                ).encode(
                    y=alt.Y('Value:Q', title='Production (tpa)', scale=alt.Scale(zero=False),
                            axis=alt.Axis(labelFontSize=9)),
                    color=alt.Color('Metric:N',
                                    scale=alt.Scale(domain=['Recovery (%)', 'Production (tpa)'],
                                                  range=['#2E86C1', '#F39C12']),
                                    legend=alt.Legend(orient="bottom", title=None)),
                    tooltip=[
                        alt.Tooltip('Stage_Display:N', title='Study'),
                        alt.Tooltip('Metric:N', title='Metric'),
                        alt.Tooltip('Value:Q', title='Production (tpa)', format=',.0f')
                    ]
                )

                st.altair_chart(
                    alt.layer(recovery_line, production_line)
                       .resolve_scale(y='independent')
                       .resolve_legend(color='shared')
                       .properties(height=chart_h),
                    use_container_width=True
                )

            # ------------------------------------------------------------------
            # GRAPH 2: M&I & Inferred (shared Mt scale)
            # ------------------------------------------------------------------
            with col2:
                st.markdown("**M&I & Inferred**")

                res_melted = df_studies[['Stage_Display',
                                          'Resource_Measured_Indicated_Mt',
                                          'Resource_Inferred_Mt']].copy().melt(
                    id_vars=['Stage_Display'],
                    value_vars=['Resource_Measured_Indicated_Mt', 'Resource_Inferred_Mt'],
                    var_name='Metric',
                    value_name='Value'
                ).dropna(subset=['Value'])

                res_melted['Metric'] = res_melted['Metric'].map({
                    'Resource_Measured_Indicated_Mt': 'M&I (Mt)',
                    'Resource_Inferred_Mt': 'Inferred (Mt)'
                })
                res_melted['Stage_Short'] = res_melted['Stage_Display'].map(STAGE_SHORT_MAP)

                res_chart = alt.Chart(res_melted).mark_line(
                    strokeWidth=2
                ).encode(
                    x=alt.X('Stage_Short:N',
                            title=None,
                            sort=STAGE_ORDER,
                            axis=alt.Axis(labelFontSize=10, labelFontWeight='bold', titlePadding=8)),
                    y=alt.Y('Value:Q',
                            title='Tonnes (Mt)',
                            scale=alt.Scale(zero=True),
                            axis=alt.Axis(labelFontSize=9)),
                    color=alt.Color('Metric:N',
                                    legend=alt.Legend(orient="bottom", title=None),
                                    scale=alt.Scale(domain=['M&I (Mt)', 'Inferred (Mt)'],
                                                  range=['#2E86C1', '#F39C12'])),
                    tooltip=[
                        alt.Tooltip('Stage_Display:N', title='Study'),
                        alt.Tooltip('Metric:N', title='Resource'),
                        alt.Tooltip('Value:Q', title='Tonnes (Mt)', format=',.1f')
                    ]
                ).properties(height=chart_h)

                st.altair_chart(res_chart, use_container_width=True)

            # ------------------------------------------------------------------
            # ROW 2: Mine Life | Grade
            # ------------------------------------------------------------------
            col1, col2 = st.columns(2)

            # ------------------------------------------------------------------
            # GRAPH 3: Mine Life
            # ------------------------------------------------------------------
            with col1:
                st.markdown("**Mine Life**")

                mine_life_data = df_studies[['Stage_Display', 'Life_of_Mine_Years']].copy().dropna(subset=['Life_of_Mine_Years'])
                mine_life_data['Stage_Short'] = mine_life_data['Stage_Display'].map(STAGE_SHORT_MAP)

                mine_life_chart = alt.Chart(mine_life_data).mark_line(
                    strokeWidth=2,
                    color=COMPANIES[company]['color']
                ).encode(
                    x=alt.X('Stage_Short:N',
                            title=None,
                            sort=STAGE_ORDER,
                            axis=alt.Axis(labelFontSize=10, labelFontWeight='bold', titlePadding=8)),
                    y=alt.Y('Life_of_Mine_Years:Q',
                            title='Years',
                            scale=alt.Scale(zero=False),
                            axis=alt.Axis(labelFontSize=9)),
                    tooltip=[
                        alt.Tooltip('Stage_Display:N', title='Study'),
                        alt.Tooltip('Life_of_Mine_Years:Q', title='Mine Life (years)', format='.0f')
                    ]
                ).properties(height=chart_h)

                st.altair_chart(mine_life_chart, use_container_width=True)

            # ------------------------------------------------------------------
            # GRAPH 4: Grade
            # ------------------------------------------------------------------
            with col2:
                st.markdown("**Grade**")

                grade_data = df_studies[['Stage_Display', 'Average_Lithium_Grade']].copy().dropna(subset=['Average_Lithium_Grade'])
                grade_data['Stage_Short'] = grade_data['Stage_Display'].map(STAGE_SHORT_MAP)

                grade_chart = alt.Chart(grade_data).mark_line(
                    strokeWidth=2,
                    color=COMPANIES[company]['color']
                ).encode(
                    x=alt.X('Stage_Short:N',
                            title=None,
                            sort=STAGE_ORDER,
                            axis=alt.Axis(labelFontSize=10, labelFontWeight='bold', titlePadding=8)),
                    y=alt.Y('Average_Lithium_Grade:Q',
                            title='Grade (ppm)',
                            scale=alt.Scale(zero=False),
                            axis=alt.Axis(labelFontSize=9)),
                    tooltip=[
                        alt.Tooltip('Stage_Display:N', title='Study'),
                        alt.Tooltip('Average_Lithium_Grade:Q', title='Grade (ppm)', format='.0f')
                    ]
                ).properties(height=chart_h)

                st.altair_chart(grade_chart, use_container_width=True)

        with tab3:
            st.subheader("Complete Study Data")
            display_cols = [
                'Stage_Display', 'PressRelease_Date',
                'AfterTax_NPV_M', 'AfterTax_IRR_%',
                'Initial_Capex_M', 'Total_Capex_M',
                'Resource_Measured_Indicated_Mt', 'Resource_Inferred_Mt',
                'Average_Lithium_Grade', 'Metallurgical_Recovery_%',
                'Life_of_Mine_Years', 'Avg_Annual_Production_tpa',
                'Net_Operating_Cost_t', 'BaseCase_Li_Price',
                'Payback_Period_Years'
            ]

            display_df = df_studies[display_cols].copy()
            display_df.columns = [
                'Study', 'Date', 'NPV ($M)', 'IRR %',
                'Initial CAPEX ($M)', 'Total CAPEX ($M)',
                'M&I Resource (Mt)', 'Inferred Resource (Mt)',
                'Grade (ppm)', 'Recovery %',
                'Mine Life (years)', 'Annual Production (tpa)',
                'OPEX ($/t)', 'Li Price ($/t)',
                'Payback (years)'
            ]
            st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No study data available for this company.")


def render_study_comparison(companies):
    """Side-by-side comparison table + charts of study metrics across companies."""
    all_studies = load_study_data(companies)

    if all_studies.empty:
        st.info("No study data available for comparison.")
        return

    # ------------------------------------------------------------------
    # 1. Latest-study comparison table
    # ------------------------------------------------------------------
    st.markdown("**Latest Study Metrics — Side by Side**")

    # Take the latest study per company (max Date with at least one non-null metric)
    latest_rows = []
    for company in companies:
        sub = all_studies[all_studies['Company'] == company].copy()
        if sub.empty:
            continue
        # Pick the row with the most non-null values
        sub['_nonnull'] = sub[['AfterTax_NPV_M', 'AfterTax_IRR_%', 'Initial_Capex_M',
                               'Resource_Measured_Indicated_Mt', 'Average_Lithium_Grade']].notna().sum(axis=1)
        latest = sub.sort_values(['Date', '_nonnull']).iloc[-1]
        latest_rows.append({
            'Company': company,
            'Latest Study': latest['Stage_Display'],
            'Date': latest['Date'].strftime('%b %Y'),
            'AfterTax_NPV_M': latest['AfterTax_NPV_M'],
            'AfterTax_IRR_%': latest['AfterTax_IRR_%'],
            'Initial_Capex_M': latest['Initial_Capex_M'],
            'Payback (yr)': latest.get('Payback_Period_Years', None),
            'M&I (Mt)': latest['Resource_Measured_Indicated_Mt'],
            'Inferred (Mt)': latest['Resource_Inferred_Mt'],
            'Grade (ppm)': latest['Average_Lithium_Grade'],
            'Recovery (%)': latest['Metallurgical_Recovery_%'],
            'Mine Life (yr)': latest['Life_of_Mine_Years'],
            'Production (tpa)': latest['Avg_Annual_Production_tpa'],
            'OPEX ($/t)': latest['Net_Operating_Cost_t'],
        })

    if not latest_rows:
        st.info("No study data available for comparison.")
        return

    latest_df = pd.DataFrame(latest_rows)

    # Format numeric columns for display
    display_df = latest_df.copy()
    for col in display_df.columns:
        if col in ('Company', 'Latest Study', 'Date'):
            continue
        display_df[col] = display_df[col].apply(
            lambda v: f"{v:,.0f}" if pd.notna(v) else "N/A"
        )

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------
    # 1b. Value Ratios — company comparison (3 charts, one line per firm)
    # ------------------------------------------------------------------
    st.markdown("**Value Ratios — Company Comparison**")

    color_scale = {c: COMPANIES[c]['color'] for c in companies}

    mc_data = get_market_cap_data(companies)
    if not mc_data.empty:
        value_compare = pd.merge(
            all_studies[['Company', 'Stage_Display', 'AfterTax_NPV_M', 'Initial_Capex_M']],
            mc_data[['Company', 'Stage_Display', 'MarketCap_M', 'Shares_M']],
            on=['Company', 'Stage_Display'], how='inner'
        ).dropna(subset=['AfterTax_NPV_M', 'MarketCap_M'])

        if not value_compare.empty:
            value_compare['NPV/Mkt Cap'] = value_compare['AfterTax_NPV_M'] / value_compare['MarketCap_M']
            value_compare['NPV/CAPEX'] = value_compare.apply(
                lambda r: r['AfterTax_NPV_M'] / r['Initial_Capex_M']
                if pd.notna(r.get('Initial_Capex_M')) else None, axis=1
            )
            value_compare['NPV/Share'] = value_compare['AfterTax_NPV_M'] / value_compare['Shares_M']
            value_compare['Stage_Short'] = value_compare['Stage_Display'].map(STAGE_SHORT_MAP)

            ratio_cols = st.columns(3)
            for col, ratio in zip(ratio_cols, ['NPV/Mkt Cap', 'NPV/CAPEX', 'NPV/Share']):
                with col:
                    st.markdown(f"**{ratio}**")
                    sub = value_compare[['Company', 'Stage_Short', ratio]].dropna(subset=[ratio])
                    if not sub.empty:
                        chart = alt.Chart(sub).mark_line(
                            point=alt.OverlayMarkDef(size=25, filled=True, stroke='white', strokeWidth=1),
                            strokeWidth=2
                        ).encode(
                            x=alt.X('Stage_Short:N',
                                    title=None,
                                    sort=STAGE_ORDER,
                                    axis=alt.Axis(labelFontSize=9, labelFontWeight='bold', titlePadding=8)),
                            y=alt.Y(f'{ratio}:Q',
                                    title=None,
                                    scale=alt.Scale(zero=False),
                                    axis=alt.Axis(labelFontSize=8)),
                            color=alt.Color('Company:N',
                                            scale=alt.Scale(domain=list(color_scale.keys()),
                                                            range=list(color_scale.values())),
                                            legend=alt.Legend(orient="bottom", title=None, labelFontSize=9)),
                            tooltip=[
                                alt.Tooltip('Company:N', title='Company'),
                                alt.Tooltip('Stage_Short:N', title='Study'),
                                alt.Tooltip(f'{ratio}:Q', title=ratio, format='.2f')
                            ]
                        ).properties(height=220)
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.caption("No data available")
        else:
            st.info("No market cap data available for the selected companies.")
    else:
        st.info("No market cap data available.")

    # ------------------------------------------------------------------
    # 2. Comparison charts (multi-line overlays)
    # ------------------------------------------------------------------
    st.markdown("**Study Metrics Over Time — Company Comparison**")

    # Map colors
    color_scale = {c: COMPANIES[c]['color'] for c in companies}

    chart_data = all_studies.copy()
    chart_data['Stage_Short'] = chart_data['Stage_Display'].map(STAGE_SHORT_MAP)
    chart_data = chart_data.dropna(subset=['Stage_Short'])

    metric_defs = [
        ('AfterTax_NPV_M', 'After-Tax NPV (C$M)', ',.0f'),
        ('AfterTax_IRR_%', 'After-Tax IRR (%)', '.1f'),
        ('Initial_Capex_M', 'Initial CAPEX (C$M)', ',.0f'),
        ('Resource_Measured_Indicated_Mt', 'M&I Resource (Mt)', ',.0f'),
        ('Average_Lithium_Grade', 'Grade (ppm)', ',.0f'),
    ]

    # 2-column grid of comparison charts
    for i in range(0, len(metric_defs), 2):
        cols = st.columns(2)
        for j, (col, (metric, label, fmt)) in enumerate(zip(cols, metric_defs[i:i+2])):
            with col:
                st.markdown(f"**{label}**")
                sub = chart_data[['Company', 'Stage_Short', metric]].dropna(subset=[metric])
                if not sub.empty:
                    chart = alt.Chart(sub).mark_line(
                        point=alt.OverlayMarkDef(size=25, filled=True, stroke='white', strokeWidth=1),
                        strokeWidth=2
                    ).encode(
                        x=alt.X('Stage_Short:N',
                                title=None,
                                sort=STAGE_ORDER,
                                axis=alt.Axis(labelFontSize=10, labelFontWeight='bold', titlePadding=8)),
                        y=alt.Y(f'{metric}:Q',
                                title=None,
                                scale=alt.Scale(zero=False),
                                axis=alt.Axis(labelFontSize=9)),
                        color=alt.Color('Company:N',
                                        scale=alt.Scale(domain=list(color_scale.keys()),
                                                        range=list(color_scale.values())),
                                        legend=alt.Legend(orient="bottom", title=None, labelFontSize=10)),
                        tooltip=[
                            alt.Tooltip('Company:N', title='Company'),
                            alt.Tooltip('Stage_Short:N', title='Study'),
                            alt.Tooltip(f'{metric}:Q', title=label, format=fmt)
                        ]
                    ).properties(height=180)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.caption("No data available")

    st.caption("Only companies with study data are shown. Data for non-Century companies is placeholder/MVP.")


# ============================================================================
# KEY INSIGHTS
# ============================================================================
def render_key_insights(companies=None):
    """Render a clean executive summary of the latest study (single or compare)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    if len(companies) > 1:
        # Comparison mode: summary cards per company
        st.subheader("Key Insights — Latest Study Snapshot")
        cols = st.columns(min(len(companies), 4))
        for col, company in zip(cols, companies):
            with col:
                st.markdown(f"### {COMPANIES[company]['short_name']}")
                df_studies = load_study_data([company])
                if df_studies.empty:
                    st.caption("No study data")
                    continue

                df_studies = df_studies.dropna(subset=['AfterTax_NPV_M'])
                if df_studies.empty:
                    st.caption("No economic study data")
                    continue

                latest = df_studies.iloc[-1]
                st.metric("After-Tax NPV", f"${latest['AfterTax_NPV_M']:,.0f}M" if pd.notna(latest['AfterTax_NPV_M']) else "N/A")
                st.metric("After-Tax IRR", f"{latest['AfterTax_IRR_%']:.1f}%" if pd.notna(latest['AfterTax_IRR_%']) else "N/A")
                st.metric("M&I Resource", f"{latest['Resource_Measured_Indicated_Mt']:,.0f} Mt" if pd.notna(latest['Resource_Measured_Indicated_Mt']) else "N/A")
        st.caption("Latest study with NPV data per company. Placeholder data for non-Century companies.")
        return

    # ------------------------------------------------------------------
    # SINGLE COMPANY VIEW
    # ------------------------------------------------------------------
    company = companies[0]
    st.subheader(f"Key Insights — {company}")

    df_studies = load_study_data([company])

    if not df_studies.empty:
        latest = df_studies.iloc[-1]

        st.markdown(
            f"**Latest study:** {latest['Stage_Display']} — *press release {latest['PressRelease_Date']}*"
        )

        # Headline metrics — only the four most important figures
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("After-Tax NPV",
                      f"${latest['AfterTax_NPV_M']:,.0f}M" if pd.notna(latest['AfterTax_NPV_M']) else "N/A")
        with col2:
            st.metric("After-Tax IRR",
                      f"{latest['AfterTax_IRR_%']:.1f}%" if pd.notna(latest['AfterTax_IRR_%']) else "N/A")
        with col3:
            st.metric("Initial CAPEX",
                      f"${latest['Initial_Capex_M']:,.0f}M" if pd.notna(latest['Initial_Capex_M']) else "N/A")
        with col4:
            st.metric("M&I Resource",
                      f"{latest['Resource_Measured_Indicated_Mt']:,.1f} Mt"
                      if pd.notna(latest['Resource_Measured_Indicated_Mt']) else "N/A")

        # Supporting detail tucked away in an expander to avoid clutter
        with st.expander("Additional study details"):
            grade = f"{latest['Average_Lithium_Grade']:,.0f} ppm" if pd.notna(latest['Average_Lithium_Grade']) else "N/A"
            recovery = f"{latest['Metallurgical_Recovery_%']:,.1f}%" if pd.notna(latest['Metallurgical_Recovery_%']) else "N/A"
            if pd.notna(latest['Net_Operating_Cost_t']):
                opex_val = latest['Net_Operating_Cost_t']
                opex = f"-C${abs(opex_val):,.0f}/t (byproduct credits)" if opex_val < 0 else f"C${opex_val:,.0f}/t"
            else:
                opex = "N/A"
            mine_life = f"{latest['Life_of_Mine_Years']:,.0f} years" if pd.notna(latest['Life_of_Mine_Years']) else "N/A"
            production = f"{latest['Avg_Annual_Production_tpa']:,.0f} tpa" if pd.notna(latest['Avg_Annual_Production_tpa']) else "N/A"
            total_capex = f"C${latest['Total_Capex_M']:,.0f}M" if pd.notna(latest['Total_Capex_M']) else "N/A"
            li_price = f"C${latest['BaseCase_Li_Price']:,.0f}/t" if pd.notna(latest['BaseCase_Li_Price']) else "N/A"

            detail_df = pd.DataFrame({
                'Parameter': ['Lithium Grade', 'Metallurgical Recovery', 'Net Operating Cost',
                              'Mine Life', 'Avg. Annual Production', 'Total CAPEX', 'Base-Case Li Price'],
                'Value': [grade, recovery, opex, mine_life, production, total_capex, li_price]
            })
            st.dataframe(detail_df, use_container_width=True, hide_index=True)
            if pd.notna(latest['Net_Operating_Cost_t']) and latest['Net_Operating_Cost_t'] < 0:
                st.caption("Negative operating cost reflects byproduct credits.")

        st.caption("Source: Company technical reports and studies (MVP Demo Data)")
    else:
        st.info("No study data available")


# ============================================================================
# DASHBOARD (Market Sentiment)
# ============================================================================
def render_dashboard(companies=None):
    """Render the market-sentiment dashboard (single or comparison)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    is_compare = len(companies) > 1

    if is_compare:
        st.subheader("Market Sentiment — Side by Side")
    else:
        st.subheader("Market Sentiment")

    metrics = get_dashboard_metrics(companies)

    if not metrics:
        st.warning("Could not load dashboard metrics")
        return

    # Filter out the LIT benchmark key
    company_metrics = {k: v for k, v in metrics.items() if not k.startswith('_')}
    if not company_metrics:
        st.warning("Could not load company metrics")
        return

    if is_compare:
        # Side-by-side cards for each selected company
        cols = st.columns(len(company_metrics))
        for col, (company, m) in zip(cols, company_metrics.items()):
            with col:
                color = COMPANIES[company]['color']
                
                # Company name and ticker
                st.markdown(f"""
                <div style='
                    font-weight: 500;
                    font-size: 14px;
                    color: #1a1a2e;
                    margin-bottom: 2px;
                '>{company}</div>
                <div style='
                    font-size: 11px;
                    color: #999;
                    margin-bottom: 8px;
                '>{COMPANIES[company]['yf_ticker']}</div>
                """, unsafe_allow_html=True)
                
                # Price and return on same line - more compact
                price_color = "#27AE60" if m['return_30d'] >= 0 else "#E74C3C"
                st.markdown(f"""
                <div style='
                    display: flex;
                    align-items: baseline;
                    gap: 10px;
                    margin-bottom: 8px;
                '>
                    <span style='
                        font-size: 22px;
                        font-weight: 600;
                        color: #1a1a2e;
                        letter-spacing: -0.5px;
                    '>${m['current']:.2f}</span>
                    <span style='
                        font-size: 13px;
                        color: {price_color};
                        font-weight: 500;
                    '>{m['return_30d']:+.1f}%</span>
                    <span style='
                        font-size: 10px;
                        color: #bbb;
                        font-weight: 400;
                    '>30d</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Volume and Search on same line - clean and compact
                vol_change = m.get('volume_change', 0)
                vol_color = "#27AE60" if vol_change >= 0 else "#E74C3C"
                search_change = m.get('search_change', 0)
                search_color = "#27AE60" if search_change >= 0 else "#E74C3C"
                search_current = m.get('search_current', 0)
                
                st.markdown(f"""
                <div style='
                    display: flex;
                    gap: 16px;
                    font-size: 12px;
                    color: #777;
                    padding-top: 6px;
                    border-top: 1px solid #f0f0f0;
                '>
                    <span>Vol <span style='font-weight: 500; color: {vol_color};'>{vol_change:+.1f}%</span></span>
                    <span>Search <span style='font-weight: 500; color: #1a1a2e;'>{search_current:.0f}</span> <span style='color: {search_color};'>({search_change:+.0f})</span></span>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Single company
        company = list(company_metrics.keys())[0]
        m = company_metrics[company]
        
        # Two columns with tighter spacing
        col1, col2 = st.columns([1, 1])
        
        with col1:
            color = COMPANIES[company]['color']
            
            # Company header - smaller and cleaner
            st.markdown(f"""
            <div style='
                font-weight: 500;
                font-size: 14px;
                color: #1a1a2e;
                margin-bottom: 2px;
            '>{company}</div>
            <div style='
                font-size: 11px;
                color: #999;
                margin-bottom: 6px;
            '>{COMPANIES[company]['yf_ticker']}</div>
            """, unsafe_allow_html=True)
            
            # Price and return - smaller, more refined
            price_color = "#27AE60" if m['return_30d'] >= 0 else "#E74C3C"
            st.markdown(f"""
            <div style='
                display: flex;
                align-items: baseline;
                gap: 10px;
                margin-bottom: 6px;
            '>
                <span style='
                    font-size: 24px;
                    font-weight: 600;
                    color: #1a1a2e;
                    letter-spacing: -0.5px;
                '>${m['current']:.2f}</span>
                <span style='
                    font-size: 14px;
                    color: {price_color};
                    font-weight: 500;
                '>{m['return_30d']:+.1f}%</span>
                <span style='
                    font-size: 10px;
                    color: #bbb;
                    font-weight: 400;
                '>30d</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Volume and Search - clean and compact
            vol_change = m.get('volume_change', 0)
            vol_color = "#27AE60" if vol_change >= 0 else "#E74C3C"
            search_change = m.get('search_change', 0)
            search_color = "#27AE60" if search_change >= 0 else "#E74C3C"
            search_current = m.get('search_current', 0)
            
            st.markdown(f"""
            <div style='
                display: flex;
                gap: 20px;
                font-size: 12px;
                color: #777;
                padding-top: 6px;
                border-top: 1px solid #f0f0f0;
            '>
                <span>Volume <span style='font-weight: 500; color: {vol_color};'>{vol_change:+.1f}%</span></span>
                <span>Search <span style='font-weight: 500; color: #1a1a2e;'>{search_current:.0f}</span> <span style='color: {search_color};'>({search_change:+.0f})</span></span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if '_lit_benchmark' in metrics:
                lit = metrics['_lit_benchmark']
                lit_return_color = "#27AE60" if lit['return_30d'] >= 0 else "#E74C3C"
                
                st.markdown(f"""
                <div style='
                    font-weight: 500;
                    font-size: 14px;
                    color: #1a1a2e;
                    margin-bottom: 2px;
                '>Sprott Lithium Miners ETF</div>
                <div style='
                    font-size: 11px;
                    color: #999;
                    margin-bottom: 6px;
                '>LITP</div>
                <div style='
                    display: flex;
                    align-items: baseline;
                    gap: 10px;
                    margin-bottom: 6px;
                '>
                    <span style='
                        font-size: 24px;
                        font-weight: 600;
                        color: #1a1a2e;
                        letter-spacing: -0.5px;
                    '>${lit['current']:.2f}</span>
                    <span style='
                        font-size: 14px;
                        color: {lit_return_color};
                        font-weight: 500;
                    '>{lit['return_30d']:+.1f}%</span>
                    <span style='
                        font-size: 10px;
                        color: #bbb;
                        font-weight: 400;
                    '>30d</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.caption("No LIT benchmark data available")


# ============================================================================
# STOCK CHART
# ============================================================================
def render_stock_chart(companies=None):
    """Render the stock price chart (selected companies only)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    is_compare = len(companies) > 1

    if is_compare:
        st.markdown("**Stock Price — Comparison**")
    else:
        st.markdown("**Stock Price**")

    data = get_stock_data(companies)

    if not data.empty:
        chart = alt.Chart(data).mark_line().encode(
            x=alt.X("Date:T", axis=alt.Axis(format="%Y", tickCount="year", title="Year")),
            y=alt.Y("Close:Q", title="Close ($)"),
            color=alt.Color(
                "Ticker:N",
                title="Ticker",
                legend=alt.Legend(
                    orient="right",
                    title=None,
                    labelFontSize=11,
                    columns=1
                )
            ),
            tooltip=[
                alt.Tooltip("Ticker:N"),
                alt.Tooltip("Date:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("Close:Q", title="Close", format=".2f"),
            ]
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No stock data available")


# ============================================================================
# SEARCH INTEREST DEEP DIVE
# ============================================================================
def render_search_analysis(companies=None):
    """Clean search section with comparison support."""
    if companies is None:
        companies = list(COMPANIES.keys())

    is_compare = len(companies) > 1

    col1, col2 = st.columns(2)

    # Chart 1: Google Trends - multi-company overlay
    with col1:
        if is_compare:
            st.markdown("**Search Interest Over Time — Comparison**")
        else:
            st.markdown("**Search Interest Over Time**")
        trends = get_google_trends(companies)

        if trends is not None and not trends.empty:
            search_terms = company_search_terms(companies)
            term_cols = [t for t in search_terms if t in trends.columns]

            if term_cols:
                # Map search terms to company display names and colors
                term_to_company = {COMPANIES[c]['search_term']: c for c in companies}
                color_scale = {c: COMPANIES[c]['color'] for c in companies}

                # Melt to long format for multi-line chart
                melted = trends[['date'] + term_cols].melt(
                    id_vars=['date'],
                    value_vars=term_cols,
                    var_name='Term',
                    value_name='Interest'
                )
                melted['Company'] = melted['Term'].map(term_to_company).fillna(melted['Term'])

                trends_chart = alt.Chart(melted).mark_line(
                    strokeWidth=2,
                    opacity=0.8
                ).encode(
                    x=alt.X("date:T", axis=alt.Axis(format="%Y", tickCount="year", title="Year")),
                    y=alt.Y("Interest:Q", title="Interest (0-100)", scale=alt.Scale(domain=[0, 100])),
                    color=alt.Color('Company:N',
                                    scale=alt.Scale(domain=list(color_scale.keys()),
                                                    range=list(color_scale.values())),
                                    legend=alt.Legend(orient="top", title=None, labelFontSize=10)),
                    tooltip=[
                        alt.Tooltip("Company:N", title="Company"),
                        alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
                        alt.Tooltip("Interest:Q", title="Interest"),
                    ]
                ).properties(height=250)
                st.altair_chart(trends_chart, use_container_width=True)
            else:
                st.info("No search data available for the selected companies")
        else:
            st.info("No search data available (add SerpAPI key)")

        # Average monthly search interest - grouped bar chart
        st.markdown("**Average Monthly Search Interest**")
        render_monthly_pattern(companies)

    # Chart 2: Correlation (each company vs LIT)
    with col2:
        st.markdown("**Interest vs Market Performance**")
        corr_data, _ = get_correlation_data(companies)

        if corr_data is not None and not corr_data.empty:
            term_to_company = {COMPANIES[c]['search_term']: c for c in companies}
            color_scale = {c: COMPANIES[c]['color'] for c in companies}

            # Melt for proper legend
            df_melted = corr_data.melt(
                id_vars=['Date', 'Search_Term'],
                value_vars=['Lit_Indexed', 'Search_Indexed'],
                var_name='Series',
                value_name='Value'
            )

            # Clean labels
            df_melted['Series'] = df_melted['Series'].map({
                'Lit_Indexed': LIT_LABEL,
                'Search_Indexed': 'Search'
            })
            df_melted['Company'] = df_melted['Search_Term'].map(term_to_company).fillna(df_melted['Search_Term'])

            chart = alt.Chart(df_melted).mark_line(
                strokeWidth=2
            ).encode(
                x=alt.X('Date:T', axis=alt.Axis(format="%Y", tickCount="year", title="Year")),
                y=alt.Y('Value:Q', title='', scale=alt.Scale(zero=False)),
                color=alt.Color(
                    'Company:N',
                    scale=alt.Scale(domain=list(color_scale.keys()),
                                    range=list(color_scale.values())),
                    title=None,
                    legend=alt.Legend(orient="right", labelFontSize=10, columns=1)
                ),
                strokeDash=alt.StrokeDash(
                    'Series:N',
                    scale=alt.Scale(
                        domain=[LIT_LABEL, 'Search'],
                        range=[[], [5, 5]]
                    ),
                    legend=alt.Legend(orient="bottom", title=None, labelFontSize=9)
                )
            ).properties(height=250)

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No correlation data available")

    # Source
    st.caption("Source: Google Trends. Values represent relative search interest (0-100).")


# ============================================================================
# NEWS
# ============================================================================
def render_news_section(companies=None):
    """Render news section for the selected company/companies."""
    if companies is None:
        companies = list(COMPANIES.keys())

    st.subheader("Latest News & Press Releases across the web")

    for company in companies:
        ticker = COMPANIES[company]['yf_ticker']
        st.markdown(f"**{company}** ({ticker})")
        try:
            news_items = yf.Ticker(ticker).news or []
        except Exception:
            news_items = []

        if not news_items:
            st.info(f"No recent news found via Yahoo Finance for {ticker}.")
        else:
            for n in news_items[:5]:
                content = n.get("content", n)
                title = content.get("title", "Untitled")
                link = content.get("canonicalUrl", {}).get("url") or content.get("clickThroughUrl", {}).get("url", "#")
                publisher = content.get("provider", {}).get("displayName", "Unknown source")

                st.markdown(f"• **[{title}]({link})** — *{publisher}*")
                st.markdown("")
        st.markdown("")


# ============================================================================
# QA SECTION
# ============================================================================
def render_qa_section():
    """Render Q&A section"""
    st.subheader("Questions & Answers from Management")

    if "qa" not in st.session_state:
        st.session_state.qa = []

    is_admin = st.session_state.get("email") == st.secrets.get("admin_email", "")

    max_questions = 5
    remaining = max_questions - len(st.session_state.qa)

    if remaining > 0:
        st.caption(f"You can ask {remaining} more question{'s' if remaining > 1 else ''} (max {max_questions} per session)")

        # Gebruik losse widgets zonder form (geen st.form!)
        question = st.text_input("Ask a question about the company (min. 10 characters)", key="qa_question_input")
        
        col1, col2 = st.columns([1, 5])
        with col1:
            submitted = st.button("Submit question", key="qa_submit_button")
        
        if submitted and question:
            if len(question) < 10:
                st.warning("Could you add a bit more detail? Please use at least 10 characters.")
            else:
                st.session_state.qa.append({
                    "question": question,
                    "answer": None,
                    "likes": 0
                })
                st.rerun()
    else:
        st.warning("You've reached the maximum of 5 questions for this session.")

    # Determine company context for QA label (single company deep-dive)
    qa_company = DEFAULT_COMPANY
    if "selected_companies" in st.session_state and len(st.session_state.selected_companies) == 1:
        qa_company = st.session_state.selected_companies[0]

    for i, item in enumerate(st.session_state.qa):
        st.markdown(f"**Q: {item['question']}**")

        if is_admin:
            col_delete, col_like = st.columns([1, 10])
            with col_delete:
                if st.button("Delete", key=f"delete_{i}", help="Delete this question"):
                    st.session_state.qa.pop(i)
                    st.rerun()

        if st.button(f"{item['likes']}", key=f"like_{i}"):
            st.session_state.qa[i]["likes"] += 1

        if item["answer"]:
            st.write(f"**{qa_company}:** {item['answer']}")
        else:
            answer = st.text_input("", value="...", key=f"answer_{i}", label_visibility="collapsed")
            if answer and answer != "...":
                st.session_state.qa[i]["answer"] = answer
                st.rerun()

        st.markdown("")


# ============================================================================
# COMPANY FINANCIALS SECTION
# ============================================================================
@st.cache_data
def load_financial_data():
    """Load annual and stock data from Hugging Face."""
    # Hugging Face dataset configuration (set via Streamlit secrets on Cloud)
    hf_repo = st.secrets.get("HF_REPO", "").strip()
    hf_token = st.secrets.get("HF_TOKEN", "").strip()

    base = f"https://huggingface.co/datasets/{hf_repo}/resolve/main"

    if hf_token:
        # Private repo: authenticated download
        headers = {"Authorization": f"Bearer {hf_token}"}
        annual = pd.read_csv(
            f"{base}/Annual_Financials.csv",
            storage_options=headers,
            low_memory=False,
        )
        stock = pd.read_csv(
            f"{base}/Stock_Daily_Combined.csv",
            storage_options=headers,
            low_memory=False,
        )
    else:
        # Public repo: direct download
        annual = pd.read_csv(f"{base}/Annual_Financials.csv", low_memory=False)
        stock = pd.read_csv(f"{base}/Stock_Daily_Combined.csv", low_memory=False)
    return annual, stock


def build_company_financials(company, annual, stock):
    """Build the financial DataFrames for a single company.

    Returns (cash_flow_df, market_cap_df, financial_df) or (None, None, None)
    on missing data.
    """
    gvkey = COMPANIES[company]['gvkey']
    company_annual = annual[annual['gvkey'] == gvkey].copy()
    company_stock = stock[stock['gvkey'] == gvkey].copy()

    if company_annual.empty or company_stock.empty:
        return None, None, None

    company_annual['datadate'] = pd.to_datetime(company_annual['datadate'])
    company_annual = company_annual.sort_values('datadate').reset_index(drop=True)
    company_stock['datadate'] = pd.to_datetime(company_stock['datadate'])

    # ------------------------------------------------------------------
    # 1. CASH FLOW ANALYSE (full cash reconciliation)
    # ------------------------------------------------------------------
    cash_flow_data = []
    prev_cash = None
    for i in range(len(company_annual)):
        row = company_annual.iloc[i]
        year = row['fyear']

        oancf = row.get('oancf', 0) if pd.notna(row.get('oancf', 0)) else 0
        capx = row.get('capx', 0) if pd.notna(row.get('capx', 0)) else 0
        ivncf = row.get('ivncf', 0) if pd.notna(row.get('ivncf', 0)) else 0
        fincf = row.get('fincf', 0) if pd.notna(row.get('fincf', 0)) else 0
        che = row.get('che', 0) if pd.notna(row.get('che', 0)) else 0
        chech = row.get('chech', 0) if pd.notna(row.get('chech', 0)) else 0
        act = row.get('act', 0) if pd.notna(row.get('act', 0)) else 0
        lct = row.get('lct', 0) if pd.notna(row.get('lct', 0)) else 0

        # Beginning cash = prior year's reported cash (derived on first year)
        if prev_cash is None:
            begin_cash = che - chech
        else:
            begin_cash = prev_cash

        # Total cash burn = operating burn + capital expenditures
        operating_burn = abs(oancf) if oancf < 0 else 0
        capex_burn = abs(capx)
        total_cash_burn = operating_burn + capex_burn

        calc_change = oancf + ivncf + fincf
        residual = chech - calc_change

        cash_flow_data.append({
            'fyear': year,
            'Beginning Cash': begin_cash,
            'Operating Cash Flow': oancf,
            'Investing Cash Flow': ivncf,
            'Financing Cash Flow': fincf,
            'Other / FX Adjustment': residual,
            'Net Change in Cash': chech,
            'Cash Position': che,
            'Total Cash Burn': total_cash_burn,
            'Working Capital': act - lct
        })
        prev_cash = che

    cash_flow_df = pd.DataFrame(cash_flow_data)

    # ------------------------------------------------------------------
    # 2. MARKET CAP & STOCK PRICE
    # ------------------------------------------------------------------
    annual_marketcaps = []
    for year in sorted(company_annual['fyear'].unique()):
        year_stock = company_stock[company_stock['datadate'].dt.year == year]
        if not year_stock.empty:
            last_day = year_stock.iloc[-1]
            if pd.notna(last_day.get('cshoc', np.nan)):
                market_cap = last_day['prccd'] * last_day['cshoc']
                annual_marketcaps.append({
                    'fyear': year,
                    'market_cap': market_cap / 1_000_000,
                    'stock_price': last_day['prccd']
                })

    market_cap_df = pd.DataFrame(annual_marketcaps)

    # ------------------------------------------------------------------
    # 3. FINANCIAL OVERVIEW
    # ------------------------------------------------------------------
    financial_data = []
    for _, row in company_annual.iterrows():
        at = row.get('at', np.nan) if pd.notna(row.get('at', np.nan)) else np.nan
        lt = row.get('lt', np.nan) if pd.notna(row.get('lt', np.nan)) else np.nan
        ceq = row.get('ceq', np.nan) if pd.notna(row.get('ceq', np.nan)) else np.nan
        che = row.get('che', np.nan) if pd.notna(row.get('che', np.nan)) else np.nan
        dlc = row.get('dlc', 0) if pd.notna(row.get('dlc', 0)) else 0
        dltt = row.get('dltt', 0) if pd.notna(row.get('dltt', 0)) else 0

        financial_data.append({
            'fyear': row['fyear'],
            'Total Assets': at if not pd.isna(at) else np.nan,
            'Total Liabilities': lt if not pd.isna(lt) else np.nan,
            'Total Equity': ceq if not pd.isna(ceq) else np.nan,
            'Cash': che if not pd.isna(che) else np.nan,
            'Total Debt': (dlc + dltt)
        })
    financial_df = pd.DataFrame(financial_data)

    return cash_flow_df, market_cap_df, financial_df


def render_cash_flow_waterfall(cf, company):
    """Render the Plotly waterfall chart for a single company's cash story."""
    cf = cf.sort_values('fyear').reset_index(drop=True)

    if cf.empty:
        st.warning("Insufficient data available")
        return

    wf_x, wf_y, wf_base, wf_color, wf_text, wf_hover = [], [], [], [], [], []
    wf_tickvals, wf_ticktext = [], []

    pos = 0
    first = cf.iloc[0]
    open_cash = float(first['Beginning Cash'])
    wf_x.append(pos); pos += 1
    wf_y.append(open_cash); wf_base.append(0)
    wf_color.append('#85C1E9')
    wf_text.append('')
    wf_hover.append(f"Opening cash (start {int(first['fyear'])}): C${open_cash:,.2f}M")
    wf_tickvals.append(0); wf_ticktext.append('start')
    cum = open_cash

    for _, r in cf.iterrows():
        yr = int(r['fyear'])
        # Flows DURING this year (before the year-end bar)
        for delta, color, lbl in [
            (float(r['Financing Cash Flow']), '#2ECC71', 'Funding raised'),
            (float(r['Operating Cash Flow']), '#E74C3C', 'G&A / overhead'),
            (float(r['Investing Cash Flow']), '#8E44AD', 'CAPEX / project'),
        ]:
            wf_x.append(pos); pos += 1
            if delta >= 0:
                wf_base.append(cum); wf_y.append(delta)
                wf_text.append(f"+C${delta:,.1f}M")
                wf_hover.append(f"{yr} · {lbl}: +C${delta:,.2f}M")
            else:
                wf_base.append(cum + delta); wf_y.append(-delta)
                wf_text.append(f"−C${abs(delta):,.1f}M")
                wf_hover.append(f"{yr} · {lbl}: −C${abs(delta):,.2f}M")
            wf_color.append(color)
            cum += delta
        # Year-end cash (blue bar, no numbers above it)
        wf_x.append(pos); pos += 1
        wf_y.append(r['Cash Position']); wf_base.append(0)
        wf_color.append('#2E86C1')
        wf_text.append('')
        wf_hover.append(f"End of {yr}: C${r['Cash Position']:,.2f}M")
        wf_tickvals.append(pos - 1); wf_ticktext.append(f"{yr}")
        cum = r['Cash Position']

    fig = go.Figure(go.Bar(
        x=wf_x,
        y=wf_y,
        base=wf_base,
        marker_color=wf_color,
        text=wf_text,
        textposition='outside',
        textfont=dict(size=9, color='#333333'),
        customdata=wf_hover,
        hovertemplate='%{customdata}<extra></extra>',
        showlegend=False,
    ))

    # Legend (invisible color swatches so the chart explains itself)
    for color, name in [
        ('#2E86C1', 'Cash (year-end)'),
        ('#2ECC71', 'Funding raised'),
        ('#E74C3C', 'G&A / overhead'),
        ('#8E44AD', 'CAPEX / project'),
    ]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(color=color, size=10),
            name=name, showlegend=True,
        ))

    fig.update_layout(
        title=f"How Cash Flows Each Year — {company} (C$M)",
        height=520,
        template='plotly_white',
        barmode='overlay',
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0,
                    font=dict(size=11)),
        margin=dict(t=80, b=10, l=60, r=40),
    )
    # Only 11 labels: "start" + one year per blue bar (no clutter below the axis)
    fig.update_xaxes(tickvals=wf_tickvals, ticktext=wf_ticktext,
                     tickangle=0, tickfont=dict(size=10))

    st.plotly_chart(fig, width='stretch')


def render_financial_section(companies=None):
    """Render company financial data section (single or comparison)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    is_compare = len(companies) > 1

    try:
        annual, stock = load_financial_data()
    except Exception as e:
        st.error(f"Could not load financial data: {e}")
        return

    if is_compare:
        render_financial_comparison(companies, annual, stock)
        return

    # ------------------------------------------------------------------
    # SINGLE COMPANY DEEP-DIVE
    # ------------------------------------------------------------------
    company = companies[0]
    st.subheader(f"Financial Analysis — {company}")

    cash_flow_df, market_cap_df, financial_df = build_company_financials(company, annual, stock)

    if cash_flow_df is None:
        st.error("No financial data found for this company")
        return

    # ---- CASH FLOW WATERFALL ----
    render_cash_flow_waterfall(cash_flow_df, company)

    # ---- MARKET CAP vs ASSETS ----
    st.markdown("**Market Cap vs Total Assets**")

    if not market_cap_df.empty and not financial_df.empty:
        value_df = pd.merge(market_cap_df, financial_df[['fyear', 'Total Assets', 'Total Equity']], on='fyear', how='inner')

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=value_df['fyear'],
            y=value_df['Total Assets'],
            name='Total Assets',
            marker_color='#2ECC71',
            opacity=0.6,
            hovertemplate='<b>Year %{x}</b><br>Total Assets: C$%{y:.2f}M<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=value_df['fyear'],
            y=value_df['market_cap'],
            mode='lines+markers',
            name='Market Cap',
            line=dict(color='#2E86C1', width=3),
            marker=dict(size=10),
            hovertemplate='<b>Year %{x}</b><br>Market Cap: C$%{y:.2f}M<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=value_df['fyear'],
            y=value_df['Total Equity'],
            mode='lines+markers',
            name='Total Equity',
            line=dict(color='#F39C12', width=2, dash='dash'),
            marker=dict(size=8),
            hovertemplate='<b>Year %{x}</b><br>Total Equity: C$%{y:.2f}M<extra></extra>'
        ))
        fig.update_layout(
            title='Market Cap vs Assets vs Equity (C$M)',
            xaxis_title='Year',
            yaxis_title='C$ (M)',
            template='plotly_white',
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, itemclick=False, itemdoubleclick=False)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No market cap or financial data available")

    st.markdown("---")

    # ---- CASH FLOW OVERVIEW TABLE ----
    st.markdown("**Cash Flow Overview**")

    if not cash_flow_df.empty:
        display_cash = cash_flow_df[
            ['fyear', 'Beginning Cash', 'Operating Cash Flow', 'Investing Cash Flow',
             'Financing Cash Flow', 'Net Change in Cash', 'Cash Position']
        ].copy()
        display_cash.columns = ['Year', 'Beginning Cash', 'Operating CF', 'Investing CF',
                                'Financing CF', 'Net Change', 'Ending Cash']
        for col in display_cash.columns:
            if col != 'Year':
                display_cash[col] = display_cash[col].apply(
                    lambda x: f"C${x:,.3f}M" if pd.notna(x) else "N/A"
                )

        st.dataframe(display_cash, use_container_width=True, hide_index=True,
                     column_config={"Year": "Year"})
        st.caption(
            "Reconciliation: Ending Cash = Beginning Cash + Operating + Investing + Financing. "
            "Every year balances to the reported cash position."
        )

        st.markdown("**Cash Burn & Capital Raised**")
        display_burn = cash_flow_df[
            ['fyear', 'Total Cash Burn', 'Financing Cash Flow', 'Working Capital']
        ].copy()
        display_burn.columns = ['Year', 'Cash Burn (Op + CAPEX)', 'Net Capital Raised', 'Working Capital']
        for col in display_burn.columns:
            if col != 'Year':
                display_burn[col] = display_burn[col].apply(
                    lambda x: f"C${x:,.3f}M" if pd.notna(x) else "N/A"
                )
        st.dataframe(display_burn, use_container_width=True, hide_index=True,
                     column_config={"Year": "Year"})
        st.caption(
            "**Cash Burn** = negative operating cash flow + capital expenditures. "
            "**Net Capital Raised** = financing cash flow: positive = capital raised, negative = repayments."
        )
    else:
        st.warning("No cash flow data available")

    st.markdown("---")

    # ---- FINANCIAL OVERVIEW ----
    st.markdown("**Financial Overview**")

    if not financial_df.empty:
        display_financial = financial_df[['fyear', 'Total Assets', 'Total Liabilities', 'Total Equity', 'Total Debt']].copy()
        for col in display_financial.columns:
            if col != 'fyear':
                display_financial[col] = display_financial[col].apply(
                    lambda x: f"C${x:,.3f}M" if pd.notna(x) and isinstance(x, (int, float)) else "N/A"
                )

        st.dataframe(
            display_financial,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No financial data available")


def render_financial_comparison(companies, annual, stock):
    """Side-by-side financial comparison across companies (annual metrics)."""
    st.subheader("Financial Analysis — Side by Side")

    # Build financials for each company
    all_financials = {}
    for company in companies:
        cf, mc, fin = build_company_financials(company, annual, stock)
        if cf is not None and not cf.empty:
            all_financials[company] = {'cash_flow': cf, 'market_cap': mc, 'financial': fin}

    if not all_financials:
        st.error("No financial data found for any selected company")
        return

    # ------------------------------------------------------------------
    # 1. Latest-year key metrics side-by-side
    # ------------------------------------------------------------------
    st.markdown("**Latest Year Key Metrics**")

    rows = []
    for company, fin_data in all_financials.items():
        fin = fin_data['financial']
        cf = fin_data['cash_flow']
        if fin.empty:
            continue

        latest = fin.iloc[-1]
        latest_cf = cf[cf['fyear'] == latest['fyear']]
        if not latest_cf.empty:
            latest_cf = latest_cf.iloc[0]
        else:
            latest_cf = None

        rows.append({
            'Company': company,
            'Year': int(latest['fyear']) if pd.notna(latest['fyear']) else None,
            'Total Assets ($M)': round(latest['Total Assets'], 1) if pd.notna(latest['Total Assets']) else None,
            'Total Liabilities ($M)': round(latest['Total Liabilities'], 1) if pd.notna(latest['Total Liabilities']) else None,
            'Total Equity ($M)': round(latest['Total Equity'], 1) if pd.notna(latest['Total Equity']) else None,
            'Cash ($M)': round(latest['Cash'], 1) if pd.notna(latest['Cash']) else None,
            'Total Debt ($M)': round(latest['Total Debt'], 1) if pd.notna(latest['Total Debt']) else None,
            'Cash Burn ($M)': round(latest_cf['Total Cash Burn'], 1) if latest_cf is not None and pd.notna(latest_cf['Total Cash Burn']) else None,
            'Net Capital Raised ($M)': round(latest_cf['Financing Cash Flow'], 1) if latest_cf is not None and pd.notna(latest_cf['Financing Cash Flow']) else None,
        })

    if rows:
        comp_df = pd.DataFrame(rows)
        # Format display
        display_comp = comp_df.copy()
        for col in display_comp.columns:
            if col not in ('Company', 'Year'):
                display_comp[col] = display_comp[col].apply(
                    lambda v: f"C${v:,.1f}M" if pd.notna(v) else "N/A"
                )
        st.dataframe(display_comp, use_container_width=True, hide_index=True)
        st.caption("Latest available fiscal year per company.")

    # ------------------------------------------------------------------
    # 2. Combined chart: Cash position over time
    # ------------------------------------------------------------------
    st.markdown("**Cash Position Over Time**")

    color_scale = {c: COMPANIES[c]['color'] for c in companies}
    cash_chart_data = []
    for company, fin_data in all_financials.items():
        cf = fin_data['cash_flow']
        if cf is None or cf.empty:
            continue
        for _, row in cf.iterrows():
            cash_chart_data.append({
                'Year': row['fyear'],
                'Company': company,
                'Cash Position': row['Cash Position'],
            })

    if cash_chart_data:
        cash_df = pd.DataFrame(cash_chart_data)
        fig = go.Figure()
        for company in companies:
            sub = cash_df[cash_df['Company'] == company]
            if sub.empty:
                continue
            fig.add_trace(go.Scatter(
                x=sub['Year'],
                y=sub['Cash Position'],
                mode='lines+markers',
                name=company,
                line=dict(color=COMPANIES[company]['color'], width=3),
                marker=dict(size=8),
                customdata=[[company]] * len(sub),
                hovertemplate='<b>Year %{x}</b><br>%{customdata[0]}<br>Cash: C$%{y:.2f}M<extra></extra>',
            ))

        fig.update_layout(
            title='Cash Position by Company (C$M)',
            xaxis_title='Year',
            yaxis_title='C$ (M)',
            template='plotly_white',
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # 3. Combined chart: Total Assets vs Market Cap over time
    # ------------------------------------------------------------------
    st.markdown("**Total Assets vs Market Cap**")

    asset_data = []
    for company, fin_data in all_financials.items():
        fin = fin_data['financial']
        mc = fin_data['market_cap']
        if fin.empty or mc.empty:
            continue
        merged = pd.merge(fin[['fyear', 'Total Assets']], mc[['fyear', 'market_cap']], on='fyear', how='inner')
        for _, row in merged.iterrows():
            asset_data.append({
                'Year': row['fyear'],
                'Company': company,
                'Total Assets': row['Total Assets'],
                'Market Cap': row['market_cap'],
            })

    if asset_data:
        asset_df = pd.DataFrame(asset_data)

        fig = go.Figure()
        for company in companies:
            sub = asset_df[asset_df['Company'] == company]
            if sub.empty:
                continue
            color = COMPANIES[company]['color']
            fig.add_trace(go.Scatter(
                x=sub['Year'], y=sub['Total Assets'],
                mode='lines+markers', name=f"{company} — Assets",
                line=dict(color=color, width=2, dash='dot'),
                marker=dict(size=7),
            ))
            fig.add_trace(go.Scatter(
                x=sub['Year'], y=sub['Market Cap'],
                mode='lines+markers', name=f"{company} — Market Cap",
                line=dict(color=color, width=2.5),
                marker=dict(size=8),
            ))

        fig.update_layout(
            title='Total Assets & Market Cap (C$M)',
            xaxis_title='Year',
            yaxis_title='C$ (M)',
            template='plotly_white',
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, font=dict(size=10)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # 4. Financial overview tables per company (expander)
    # ------------------------------------------------------------------
    st.markdown("**Detailed Financial Overview**")

    tab_labels = [COMPANIES[c]['short_name'] for c in companies if c in all_financials]
    if tab_labels:
        tabs = st.tabs(tab_labels)
        for tab, company in zip(tabs, [c for c in companies if c in all_financials]):
            with tab:
                fin = all_financials[company]['financial']
                cf = all_financials[company]['cash_flow']

                if not fin.empty:
                    display_financial = fin[['fyear', 'Total Assets', 'Total Liabilities', 'Total Equity', 'Total Debt']].copy()
                    for col in display_financial.columns:
                        if col != 'fyear':
                            display_financial[col] = display_financial[col].apply(
                                lambda x: f"C${x:,.3f}M" if pd.notna(x) and isinstance(x, (int, float)) else "N/A"
                            )
                    st.dataframe(display_financial, use_container_width=True, hide_index=True)

                if not cf.empty:
                    display_cash = cf[['fyear', 'Beginning Cash', 'Operating Cash Flow',
                                       'Investing Cash Flow', 'Financing Cash Flow',
                                       'Net Change in Cash', 'Cash Position']].copy()
                    display_cash.columns = ['Year', 'Beginning Cash', 'Operating CF', 'Investing CF',
                                            'Financing CF', 'Net Change', 'Ending Cash']
                    for col in display_cash.columns:
                        if col != 'Year':
                            display_cash[col] = display_cash[col].apply(
                                lambda x: f"C${x:,.3f}M" if pd.notna(x) else "N/A"
                            )
                    st.markdown("**Cash Flow Overview**")
                    st.dataframe(display_cash, use_container_width=True, hide_index=True)


# ============================================================================
# PRESS RELEASE TIMELINE
# ============================================================================
def render_timeline(companies=None):
    """Render the press release / study timeline (single or comparison)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    is_compare = len(companies) > 1

    if is_compare:
        st.subheader("Study Timeline — Comparison")
    else:
        st.subheader("Press Release Timeline & Expectations")

    # Combine timeline data for the selected companies
    all_rows = []
    for company in companies:
        rows = TIMELINE_DATA.get(company, [])
        for row in rows:
            row_copy = dict(row)
            row_copy['Company'] = company
            all_rows.append(row_copy)

    if not all_rows:
        st.info("No timeline data available for the selected companies.")
        return

    timeline_df = pd.DataFrame(all_rows)

    # Show the table (grouped by company when in comparison)
    display_cols = ['Company', 'Study', 'Commitment date', 'Expected date', 'Actual date', 'Delay']
    if not is_compare:
        display_cols = ['Study', 'Commitment date', 'Expected date', 'Actual date', 'Delay']

    present_cols = [c for c in display_cols if c in timeline_df.columns]
    st.dataframe(timeline_df[present_cols], use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------
    # Build long-format event data for the chart
    # ------------------------------------------------------------------
    def parse_timeline_date(date_str):
        """Parse timeline date strings into datetime objects."""
        if date_str is None or date_str == '—' or date_str == '':
            return None

        s = str(date_str).strip()

        # DD-MM-YYYY format
        try:
            parts = s.split('-')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                return pd.to_datetime(f"{parts[2]}-{parts[1]}-{parts[0]}")
        except Exception:
            pass

        s_lower = s.lower()

        # Standard datetime parse
        try:
            return pd.to_datetime(s)
        except Exception:
            pass

        # Quarter references: 'Q1 2019' → end of quarter
        q_map = {'q1': (3, 31), 'q2': (6, 30), 'q3': (9, 30), 'q4': (12, 31)}
        for q, (month, day) in q_map.items():
            if q in s_lower:
                m = re.search(r'(\d{4})', s)
                if m:
                    return pd.to_datetime(f"{m.group(1)}-{month:02d}-{day}")

        # 'Late <Month> <Year>' → end of month
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        }
        for name, num in month_map.items():
            if name in s_lower:
                m = re.search(r'(\d{4})', s)
                if m:
                    return pd.to_datetime(f"{m.group(1)}-{num:02d}-28")

        # 'Late <Year>' / bare '<Year>' → end of year
        m = re.search(r'(\d{4})', s)
        if m:
            return pd.to_datetime(f"{m.group(1)}-12-31")

        return None

    # Collect all events
    event_rows = []
    for company in companies:
        rows = TIMELINE_DATA.get(company, [])
        for row in rows:
            study = row.get('Study', '')
            
            # Define event types and their display names
            event_mappings = {
                'Commitment date': ('Commitment', '📅 Commitment'),
                'Expected date': ('Expected', '⏳ Expected'),
                'Actual date': ('Actual', '✅ Actual'),
            }
            
            for date_key, (event_type, display_name) in event_mappings.items():
                date_str = row.get(date_key, '—')
                date = parse_timeline_date(date_str)
                if date is not None:
                    # Determine if this is a milestone (non-economic) event
                    is_milestone = study in {
                        'PoO_Submitted', 'PoO_Accepted', 'PoO_Approved',
                        'NEPA_Start', 'Final_EIS', 'Final_EA', 
                        'Record of Decision', 'FID', 'FAST41_Transparency', 
                        'FAST41_Covered', 'Fully_Permitted'
                    }
                    is_mre = study in {'MRE', 'MRE_U', 'MRE_U2', 'MRE_U3'}
                    is_economic = study in {'PEA', 'PEA_U', 'PFS', 'FS', 'FS_U'}
                    
                    # Determine category for visual grouping
                    if is_economic:
                        category = 'Economic Study'
                    elif is_mre:
                        category = 'Resource Estimate'
                    elif is_milestone:
                        category = 'Milestone'
                    else:
                        category = 'Other'
                    
                    event_rows.append({
                        'Company': company,
                        'Study': study,
                        'Event_Type': event_type,
                        'Event_Display': display_name,
                        'Date': date,
                        'Category': category,
                        'Is_Milestone': is_milestone,
                        'Is_Economic': is_economic,
                    })

    if not event_rows:
        return

    events_df = pd.DataFrame(event_rows)
    
    # Sort for display
    study_order = ['MRE', 'MRE_U', 'PEA', 'PEA_U', 'PFS', 'FS', 'FS_U', 
                   'PoO_Submitted', 'PoO_Accepted', 'PoO_Approved',
                   'NEPA_Start', 'Final_EIS', 'Final_EA',
                   'Record of Decision', 'FID', 'FAST41_Transparency', 
                   'FAST41_Covered', 'Fully_Permitted']
    
    existing_studies = [s for s in study_order if s in events_df['Study'].unique()]
    remaining_studies = [s for s in events_df['Study'].unique() if s not in existing_studies]
    y_order = existing_studies + remaining_studies
    y_order_rev = y_order[::-1]

    fig = go.Figure()

    # Color scheme
    colors = {
        'Commitment': '#F39C12',  # Gold/Orange
        'Expected': '#E74C3C',     # Red
        'Actual': '#2E86C1',       # Blue
    }
    
    # Symbols
    symbols = {
        'Commitment': 'diamond-open',
        'Expected': 'diamond-open',
        'Actual': 'circle',
    }
    
    # Size mapping (Actual slightly larger)
    sizes = {
        'Commitment': 12,
        'Expected': 12,
        'Actual': 14,
    }

    # For single company view: draw connector lines per study
    if not is_compare:
        # Draw connector lines (connecting Commitment → Expected → Actual for each study)
        for study in events_df['Study'].unique():
            study_events = events_df[events_df['Study'] == study].sort_values('Date')
            if len(study_events) >= 2:
                # Sort by date to draw the line
                sorted_events = study_events.sort_values('Date')
                fig.add_trace(go.Scatter(
                    x=sorted_events['Date'],
                    y=[study] * len(sorted_events),
                    mode='lines',
                    line=dict(color='#D5D8DC', width=2, dash='dot'),
                    hoverinfo='skip',
                    showlegend=False,
                ))

    # Add traces for each event type (Commitment, Expected, Actual)
    for event_type in ['Commitment', 'Expected', 'Actual']:
        sub = events_df[events_df['Event_Type'] == event_type]
        if sub.empty:
            continue
        
        color = colors.get(event_type, '#95A5A6')
        symbol = symbols.get(event_type, 'circle')
        size = sizes.get(event_type, 11)
        
        # Create the trace
        trace = go.Scatter(
            x=sub['Date'],
            y=sub['Study'],
            mode='markers+text' if not is_compare else 'markers',
            name=event_type,
            marker=dict(
                color=color, 
                size=size,
                symbol=symbol,
                line=dict(width=1.5, color='white')
            ),
            text=sub['Study'] if not is_compare else None,
            textposition='middle right',
            textfont=dict(size=13, color='#2C3E50'),
            hovertemplate=(
                f'<b>%{{y}}</b><br>'
                f'{event_type}: %{{x|%d-%m-%Y}}<br>'
                f'Company: %{{customdata[0]}}<extra></extra>'
            ),
            customdata=sub[['Company']].values,
            showlegend=True,
        )
        fig.add_trace(trace)

    # For comparison mode: add company colors as well
    if is_compare:
        # Add company-specific traces with different colors
        fig = go.Figure()
        
        # For each company, show their events with company color
        for company in companies:
            comp_color = COMPANIES[company]['color']
            comp_events = events_df[events_df['Company'] == company]
            
            if comp_events.empty:
                continue
            
            # Draw connector lines per study for this company
            for study in comp_events['Study'].unique():
                study_events = comp_events[comp_events['Study'] == study].sort_values('Date')
                if len(study_events) >= 2:
                    fig.add_trace(go.Scatter(
                        x=study_events['Date'],
                        y=[study] * len(study_events),
                        mode='lines',
                        line=dict(color=comp_color, width=2, dash='dot'),
                        opacity=0.3,
                        hoverinfo='skip',
                        showlegend=False,
                    ))
            
            # Add markers for each event type
            for event_type in ['Commitment', 'Expected', 'Actual']:
                sub = comp_events[comp_events['Event_Type'] == event_type]
                if sub.empty:
                    continue
                
                symbol = symbols.get(event_type, 'circle')
                size = sizes.get(event_type, 11)
                
                fig.add_trace(go.Scatter(
                    x=sub['Date'],
                    y=sub['Study'],
                    mode='markers',
                    name=f"{COMPANIES[company]['short_name']} — {event_type}",
                    marker=dict(
                        color=comp_color, 
                        size=size,
                        symbol=symbol,
                        line=dict(width=1.5, color='white')
                    ),
                    hovertemplate=(
                        f'<b>{company}</b><br>'
                        f'<b>%{{y}}</b><br>'
                        f'{event_type}: %{{x|%d-%m-%Y}}<extra></extra>'
                    ),
                ))

    # Update layout - HIDE the y-axis labels (the study names on the left)
    fig.update_layout(
        height=450 if not is_compare else 500,
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation='h', 
            yanchor='bottom', 
            y=1.02 if not is_compare else 1.05, 
            xanchor='center', 
            x=0.5,
            font=dict(size=12)
        ),
        yaxis=dict(
            title=None, 
            tickfont=dict(size=12, color='#2C3E50'),
            categoryorder='array',
            categoryarray=y_order_rev,
            tickmode='array',
            ticktext=[''] * len(y_order_rev),  # Hide the labels on the left
            tickvals=[s for s in y_order_rev],
            gridcolor='#ECF0F1',
            gridwidth=1,
            showticklabels=False,  # THIS HIDES THE Y-AXIS LABELS
        ),
        xaxis=dict(
            title=None, 
            tickfont=dict(size=11), 
            tickformat='%b %Y',
            gridcolor='#ECF0F1',
            gridwidth=1,
            showgrid=True,
        ),
        margin=dict(t=60, b=10, l=20, r=100),  # Reduced left margin since we removed labels
        plot_bgcolor='white',
        hoverlabel=dict(
            bgcolor='white',
            font_size=12,
            font_family='Arial',
        ),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # REMOVED the legend explanation text


# ============================================================================
# COMPARISON SNAPSHOT (NEW — quick overview at top of compare mode)
# ============================================================================
def render_comparison_snapshot(companies):
    """A compact 'at-a-glance' summary of the selected companies.

    Combines stock, financial, study, and search metrics into one table.
    """
    st.subheader("Comparison Snapshot")

    metrics = get_dashboard_metrics(companies)
    company_metrics = {k: v for k, v in metrics.items() if not k.startswith('_')}

    if not company_metrics:
        st.warning("Could not load comparison metrics")
        return

    # Latest year financials
    annual, stock = load_financial_data()

    rows = []
    for company in companies:
        m = company_metrics.get(company)
        if m is None:
            continue

        row = {
            'Company': company,
            'Ticker': COMPANIES[company]['yf_ticker'],
            'Price ($)': f"${m['current']:.2f}" if m.get('current') is not None else "N/A",
            '30d Return': f"{m['return_30d']:.1f}%" if m.get('return_30d') is not None else "N/A",
        }

        if m.get('volume_change') is not None:
            row['30d Volume Δ'] = f"{m['volume_change']:+.1f}%"

        # Latest search interest
        if m.get('search_current') is not None:
            row['Search Interest'] = f"{m['search_current']:.0f}"
            row['Search Δ (30d)'] = f"{m['search_change']:+.0f}" if m.get('search_change') is not None else "N/A"

        # Latest financials
        if annual is not None and stock is not None:
            cf, mc, fin = build_company_financials(company, annual, stock)
            if fin is not None and not fin.empty:
                latest = fin.iloc[-1]
                row['Year'] = int(latest['fyear']) if pd.notna(latest['fyear']) else None
                row['Cash ($M)'] = f"C${latest['Cash']:,.0f}M" if pd.notna(latest['Cash']) else "N/A"
                if cf is not None and not cf.empty:
                    latest_cf = cf[cf['fyear'] == latest['fyear']]
                    if not latest_cf.empty:
                        burn = latest_cf.iloc[0]['Total Cash Burn']
                        row['Cash Burn ($M)'] = f"C${burn:,.0f}M" if pd.notna(burn) else "N/A"

        # Latest study NPV
        study_df = load_study_data([company])
        if not study_df.empty:
            study_npv = study_df.dropna(subset=['AfterTax_NPV_M'])
            if not study_npv.empty:
                row['Study NPV ($M)'] = f"${study_npv.iloc[-1]['AfterTax_NPV_M']:,.0f}M"
                row['Study IRR'] = f"{study_npv.iloc[-1]['AfterTax_IRR_%']:.1f}%"

        rows.append(row)

    if rows:
        snapshot_df = pd.DataFrame(rows)
        st.dataframe(snapshot_df, use_container_width=True, hide_index=True)

    st.caption("All values are the latest available per company. Some rows may be missing data in this MVP.")


# ============================================================================
# MAIN APP
# ============================================================================

with StreamlitPageAnalytics.track(
    name="Lithium_Project_Comparison",
    session_id=st.session_state.session_id,
    user_id=st.session_state.user_id
):
    view_mode, selected_companies = render_sidebar()

    # Store for dynamic QA label
    st.session_state.selected_companies = selected_companies

    # If compare mode has < 2 companies, fall back to showing the single selected or warn
    if len(selected_companies) == 0:
        st.warning("Please select at least one company.")
        st.stop()

    is_compare = view_mode == "Compare Companies" and len(selected_companies) >= 2

    # Title - more compact
    company_display = ", ".join([COMPANIES[c]['short_name'] for c in selected_companies])
    if is_compare:
        st.title(f"Project Comparison: {company_display}")
    else:
        st.title(selected_companies[0])

    # Disclaimer - smaller and less prominent
    st.caption("MVP/Demo — Data may be inaccurate. Not financial advice.")

    # Show data source if set
    if 'data_source' in st.session_state:
        st.caption(f"Data source: {st.session_state.data_source}")

    # ============================================================================
    # SECTION 0: COMPARISON SNAPSHOT (compare mode only)
    # ============================================================================
    if is_compare:
        render_comparison_snapshot(selected_companies)
        st.markdown("")  # Small gap instead of divider

    # ============================================================================
    # SECTION 1: EXECUTIVE SUMMARY (Market Sentiment)
    # ============================================================================
    render_dashboard(selected_companies)
    st.markdown("")  # Small gap

    # ============================================================================
    # SECTION 2: THE ASSET (Resource & Economics)
    # ============================================================================
    render_project_studies(selected_companies)
    st.markdown("")

    # ============================================================================
    # SECTION 3: KEY INSIGHTS (Latest Study Highlights)
    # ============================================================================
    render_key_insights(selected_companies)
    st.markdown("")

    # ============================================================================
    # SECTION 4: MARKET CONTEXT (Stock Performance)
    # ============================================================================
    st.subheader("Stock Performance")
    render_stock_chart(selected_companies)
    st.markdown("")

    # ============================================================================
    # SECTION 5: TRACK RECORD (Press Release Timeline)
    # ============================================================================
    render_timeline(selected_companies)
    st.markdown("")

    # ============================================================================
    # SECTION 6: SENTIMENT ANALYSIS
    # ============================================================================
    st.subheader("Sentiment Analysis")
    st.caption("Press releases & interviews over time")
    
    if not is_compare:
        # Press release dates from the past year (Century Lithium; MVP placeholder)
        press_release_dates = [
            "July 24, 2025",
            "August 6, 2025",
            "August 22, 2025",
            "August 29, 2025",
            "September 18, 2025",
            "September 22, 2025",
            "October 1, 2025",
            "October 17, 2025",
            "October 20, 2025",
            "October 27, 2025",
            "November 24, 2025",
            "November 25, 2025",
            "December 2, 2025",
            "December 11, 2025",
            "December 22, 2025",
            "January 14, 2026",
            "February 23, 2026",
            "March 9, 2026",
            "March 10, 2026",
            "March 11, 2026",
            "March 16, 2026",
            "March 23, 2026",
            "April 9, 2026",
            "April 23, 2026",
            "May 4, 2026",
            "May 5, 2026",
            "July 14, 2026",
            "July 15, 2026",
        ]

        sentiment_df = pd.DataFrame({
            "Date": pd.to_datetime(press_release_dates),
            "Event": [f"PR #{i+1}" for i in range(len(press_release_dates))],
            "Sentiment": ["Pending"] * len(press_release_dates),
        })
        sentiment_df["Date"] = sentiment_df["Date"].dt.strftime("%b %d, %Y")

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(
                sentiment_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.TextColumn("Date", width="medium"),
                    "Event": st.column_config.TextColumn("Event", width="medium"),
                    "Sentiment": st.column_config.TextColumn("Score", width="small"),
                },
            )
    else:
        st.caption("Sentiment analysis per company to be added for comparison mode.")
    st.markdown("")

    # ============================================================================
    # SECTION 7: FINANCIAL HEALTH (Cash, Burn, Dilution)
    # ============================================================================
    st.subheader("Financial Health")
    render_financial_section(selected_companies)
    st.markdown("")

    # ============================================================================
    # SECTION 8: MARKET DEMAND (Google Search Interest)
    # ============================================================================
    st.subheader("Market Demand")
    render_search_analysis(selected_companies)
    st.markdown("")

    # ============================================================================
    # SECTION 9: NEWS
    # ============================================================================
    render_news_section(selected_companies)
    st.markdown("")

    # ============================================================================
    # SECTION 10: MANAGEMENT DUE DILIGENCE
    # ============================================================================
    st.subheader("Management Due Diligence")
    st.markdown("")

    # ============================================================================
    # SECTION 11: Q&A
    # ============================================================================
    render_qa_section()

# python -m streamlit run app.py