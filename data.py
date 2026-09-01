# data.py
# ============================================================================
# ALLE data-functies van de app: ophalen (Yahoo Finance, SerpApi, Hugging Face),
# berekenen (metrics, market cap, search patterns) en tracking (GA4).
#
# Elke functie hier levert data/logica; views.py tekent het op het scherm.
# ============================================================================



from config import COMPANIES


def company_search_terms(companies):
    """Return unique individual Google Trends search terms for the companies."""
    terms = []
    for c in companies:
        terms.extend(COMPANIES[c]["search_terms"])
    # De-duplicate while preserving order
    seen = set()
    return [t for t in terms if not (t in seen or seen.add(t))]


def company_term_map(companies):
    """Return {individual search term: company display name} for the companies."""
    term_map = {}
    for c in companies:
        for t in COMPANIES[c]["search_terms"]:
            term_map[t] = c
    return term_map


def company_tickers(companies):
    """Return {display_ticker_label: yf_ticker} for the selected companies."""
    return {
        f"{c} ({COMPANIES[c]['yf_ticker']})": COMPANIES[c]["yf_ticker"]
        for c in companies
    }


import pandas as pd
import yfinance as yf
import streamlit as st

from config import STOCK_CLUSTERS, TIME_PERIODS


@st.cache_data(ttl=21600)  # 6h — 5y DAILY history used for market cap & 30d metrics
def get_stock_data(companies=None):
    """Fetch and normalize stock data for the selected companies.

    Parameters
    ----------
    companies : list[str] | None
        Company display names. None/empty means ALL companies.
    """
    if companies is None:
        from config import COMPANIES
        companies = list(COMPANIES.keys())

    def fetch_ticker(ticker):
        """Fetch 5-year stock history from Yahoo Finance."""
        try:
            df = yf.Ticker(ticker).history(period="5y").reset_index()[["Date", "Close", "Volume"]]
            if df is not None and not df.empty:
                return df.reset_index(drop=True)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()

    all_data = []

    # Selected companies
    for display, ticker in company_tickers(companies).items():
        data = fetch_ticker(ticker)
        if not data.empty:
            data["Ticker"] = display
            all_data.append(data)

    if all_data:
        data = pd.concat(all_data, ignore_index=True)
        return data

    return pd.DataFrame()


# ===========================================================================
# STOCK DATA DENSITY — one Yahoo period/interval per chart window
# ===========================================================================
# Yahoo caps how far back each intraday interval reaches:
#   1m -> ~7 days | 5m / 15m / 30m -> 60 days | 1h -> 730 days
# 1D uses 5m bars so the live chart shows real trades (matching the
# matplotlib intraday renderer / TestGraph.py); 1m would only flood the
# screen with empty fill-in for illiquid names.
#   1D -> 5m | 7D -> 5m | 30D -> 5m | 90D -> 1h | 1Y -> daily
# Illiquid tickers only print a bar when a trade happens, so they can stay
# sparse regardless of interval.
STOCK_INTERVAL_CONFIG = {
    1:   {"period": "1d",  "interval": "5m"},
    7:   {"period": "1mo", "interval": "5m"},
    30:  {"period": "1mo", "interval": "5m"},
    90:  {"period": "3mo", "interval": "1h"},
    365: {"period": "1y",  "interval": "1d"},
}

# Per-window cache TTL (seconds).  Short windows stay near-live for
# returning visitors; long windows are daily-grain and barely change
# intraday, so they can sit in the cache much longer without anyone
# noticing.  This keeps total Yahoo Finance traffic low on Streamlit
# Cloud while the 1D chart still feels fresh.
STOCK_CACHE_TTL_SECONDS = {
    1:   180,    # 3 min  — quasi-live intraday (5m bars)
    7:   900,    # 15 min
    30:  3600,   # 1 hour
    90:  21600,  # 6 hours
    365: 86400,  # 24 hours — daily bars only move at market close
}


def stock_cache_ttl_label(period_days):
    """Human-readable refresh rate for the selected chart window."""
    seconds = STOCK_CACHE_TTL_SECONDS.get(period_days, 3600)
    if seconds >= 3600 and seconds % 3600 == 0:
        hours = seconds // 3600
        return f"{hours} hour" + ("s" if hours > 1 else "")
    return f"{seconds // 60} min"


def _fetch_cluster_stock_data(period_days):
    """Fetch, filter and normalise cluster stock history for the chart.

    Fetches every cluster ticker at the interval matching *period_days*
    (see STOCK_INTERVAL_CONFIG), slices it to the last *period_days* days
    and re-normalises Close to start at 100 so the frontend can draw one
    continuous line per ticker (Yahoo Finance style).
    """
    cfg = STOCK_INTERVAL_CONFIG.get(period_days, STOCK_INTERVAL_CONFIG[365])

    result = {}
    for cluster_key, cluster in STOCK_CLUSTERS.items():
        frames = []
        for display, ticker in cluster["members"].items():
            try:
                df = yf.Ticker(ticker).history(
                    period=cfg["period"], interval=cfg["interval"]
                ).reset_index()
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                continue
            if df.empty:
                continue
            # Intraday bars come back with a "Datetime" index column.
            if "Datetime" in df.columns:
                df = df.rename(columns={"Datetime": "Date"})
            df = df[[c for c in ["Date", "Close", "Volume"] if c in df.columns]]
            df = df.dropna(subset=["Close"])
            df["Ticker"] = display
            frames.append(df)

        if not frames:
            result[cluster_key] = pd.DataFrame()
            continue

        df_all = pd.concat(frames, ignore_index=True)
        df_all["Date"] = pd.to_datetime(df_all["Date"], utc=True).dt.tz_localize(None)
        df_all = df_all.sort_values("Date")

        cutoff = df_all["Date"].max() - pd.Timedelta(days=period_days)
        df = df_all[df_all["Date"] >= cutoff]

        parts = []
        session_end = df["Date"].max()
        for ticker, group in df.groupby("Ticker"):
            group = group.copy()
            if len(group) < 2:
                # Illiquid tickers can end up with a single bar inside the
                # window (a lone bar renders as an invisible dot).  Fall back
                # to the ticker's last bars from the FULL fetch — the sliced
                # frame would only return the same lone bar again.
                fallback = df_all[df_all["Ticker"] == ticker].tail(2)
                if len(fallback) > len(group):
                    group = fallback.copy()
            if period_days == 1 and len(group) >= 2 \
                    and group["Date"].iloc[-1].date() == session_end.date():
                # 1D view: illiquid stocks only print a bar when a trade
                # happens, so their line would stop mid-day while liquid
                # names span the whole session.  Carry the last known price
                # forward to the end of the session — flat segments simply
                # mean "no trades, price unchanged" (how chart providers
                # render illiquid names).
                grid = pd.date_range(group["Date"].iloc[0], session_end, freq="1min")
                filled = (group.set_index("Date")[["Close"]]
                          .reindex(grid).ffill()
                          .rename_axis("Date")
                          .reset_index())
                filled["Ticker"] = ticker
                group = filled
            first_close = group["Close"].iloc[0]
            if first_close and first_close > 0:
                group["Normalized"] = group["Close"] / first_close * 100
            else:
                group["Normalized"] = group["Close"]
            parts.append(group)
        result[cluster_key] = pd.concat(parts, ignore_index=True)

    return result


def _make_cluster_cache(period_days):
    """Build one cached fetcher for *period_days* with its OWN static ttl.

    st.cache_data requires the ttl to be fixed at decoration time, so each
    chart window gets its own tiny wrapper.  Without a decorator-level ttl a
    cache entry never expires while the app runs — which froze the charts on
    their very first fetch (the "still showing yesterday" bug).
    *period_days* is ALSO passed as an argument so every window lands on its
    own cache entry regardless of how Streamlit hashes closures.
    """
    @st.cache_data(
        ttl=STOCK_CACHE_TTL_SECONDS[period_days],
        show_spinner="Fetching stock data (Yahoo Finance)…",
    )
    def _cached(window):
        return _fetch_cluster_stock_data(window)

    return _cached


# One cached fetcher per chart window (1D, 7D, 30D, 90D, 1Y).
_CLUSTER_CACHE_BY_WINDOW = {
    days: _make_cluster_cache(days) for days in STOCK_INTERVAL_CONFIG
}


def get_cluster_stock_data(period_days=365):
    """Public wrapper: pick the per-window cached fetcher and call it."""
    cached_fetch = _CLUSTER_CACHE_BY_WINDOW.get(period_days)
    if cached_fetch is None:
        # Unknown window -> fall back to the 1-year (daily bars) cache.
        cached_fetch = _CLUSTER_CACHE_BY_WINDOW[365]
    return cached_fetch(period_days)


@st.cache_data(ttl=900)  # 15 min — dagbars bewegen intraday weinig, maar de
# laatste bar (vandaag) verandert wel; te lange cache toonde gisteren als "1D".
def get_equity_stock_data(cluster_key):
    """Daily 1-year Close history for every stock in one cluster.

    Returns a DataFrame with columns ``Date``, ``Close``, ``Ticker`` where
    ``Ticker`` is the human-readable display name of each member of the
    cluster.  Used by the "Equity Markets" drill-down so each individual
    stock can be plotted (indexed to 100) and its 1D/7D/30D/1Y returns
    computed from a single daily fetch.
    """
    cluster = STOCK_CLUSTERS.get(cluster_key)
    if not cluster:
        return pd.DataFrame()

    frames = []
    for display, ticker in cluster["members"].items():
        try:
            df = yf.Ticker(ticker).history(period="1y", interval="1d").reset_index()
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
        if df.empty:
            continue
        # Intraday/raw bars can come back with a "Datetime" index column.
        if "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "Date"})
        df = df[["Date", "Close"]].dropna(subset=["Close"])
        df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_localize(None)
        df = df.sort_values("Date").reset_index(drop=True)
        df["Ticker"] = display
        df["Symbol"] = ticker
        frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


@st.cache_data(ttl=STOCK_CACHE_TTL_SECONDS[7])  # 15 min — intraday beweegt snel
def get_equity_intraday_window_data(cluster_key, days):
    """Close history for every stock in one cluster, over a window.

    For day X the frontend takes the average of the surrounding days (a
    centered rolling window), so the line is smooth instead of spiky.  This
    layer just returns raw daily Close prices.
    """
    # Daily bars for every window (7D/30D/1Y); one point per trading day.
    interval = "1d"
    fetch_period = "1y"

    cluster = STOCK_CLUSTERS.get(cluster_key)
    if not cluster:
        return pd.DataFrame()

    frames = []
    for display, ticker in cluster["members"].items():
        try:
            df = yf.Ticker(ticker).history(
                period=fetch_period, interval=interval).reset_index()
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
        if df.empty:
            continue
        if "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "Date"})
        df = df[["Date", "Close"]].dropna(subset=["Close"])
        df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_localize(None)
        df = df.sort_values("Date").reset_index(drop=True)
        df["Ticker"] = display
        df["Symbol"] = ticker

        # Slice to the requested window so the normalised chart starts at the
        # right point instead of at the beginning of the Yahoo fetch period.
        cutoff = df["Date"].max() - pd.Timedelta(days=days)
        df = df[df["Date"] >= cutoff].reset_index(drop=True)
        if df.empty:
            continue
        frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ===========================================================================
# INTRADAY (1D) STOCK DATA — raw prices for the matplotlib renderer
# ===========================================================================
# The 1D view shows live intraday price action (5-minute bars) at the actual
# ticker price — NOT the indexed-to-100 chart used by the multi-day Altair
# view.  See TestGraph.py for the reference visual format.
# Refreshed every STOCK_CACHE_TTL_SECONDS[1] (3 min) so returning visitors
# see near-real-time movement — the "live" reason to come back.
@st.cache_data(
    ttl=STOCK_CACHE_TTL_SECONDS[1],
    show_spinner="Fetching today's intraday data (Yahoo Finance)…",
)
def get_intraday_stock_data():
    """Fetch 1D intraday data (5m bars) for every cluster ticker.

    Returns
    -------
    dict[str, list[dict]]
        Keyed by cluster_key.  Each value is a list of per-ticker dicts with
        keys: ``display`` (label), ``ticker`` (yf symbol), ``name`` (display
        name), ``currency`` and ``data`` (DataFrame with tz-naive ``Date`` +
        ``Close`` columns).  No normalisation is applied — prices stay real so
        the matplotlib renderer can plot them with open/close lines like
        TestGraph.py.
    """
    result = {}
    for cluster_key, cluster in STOCK_CLUSTERS.items():
        members = []
        for display, ticker in cluster["members"].items():
            try:
                stock = yf.Ticker(ticker)
                df = stock.history(period="1d", interval="5m")
                if df.empty:
                    continue
                df = df.reset_index()
                # Intraday bars come back with a "Datetime" index column.
                if "Datetime" in df.columns:
                    df = df.rename(columns={"Datetime": "Date"})
                df = df[["Date", "Close"]].dropna(subset=["Close"])
                if df.empty:
                    continue
                # Strip timezone so matplotlib date-formatters work cleanly.
                df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_localize(None)
                df = df.sort_values("Date").reset_index(drop=True)
            except Exception as e:
                print(f"Error fetching intraday {ticker}: {e}")
                continue
            # Currency is a separate (slower) call; fall back to USD.
            currency = "USD"
            try:
                currency = stock.info.get("currency", "USD")
            except Exception:
                pass
            members.append({
                "display": display,
                "ticker": ticker,
                "name": display,
                "currency": currency,
                "data": df,
            })
        if members:
            result[cluster_key] = members
    return result


import numpy as np
import pandas as pd
import streamlit as st

from config import MARKET_CAP_OVERRIDES, STUDY_COLUMNS, STUDY_DATA


@st.cache_data
def load_study_data(companies=None):
    """Load study data for one or more companies.

    Parameters
    ----------
    companies : list[str] | None
        Company display names. None/empty means ALL companies.
    """
    from config import COMPANIES
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


@st.cache_data
def get_market_cap_data(companies=None):
    """Market cap at each study date from company stock data (price × shares outstanding)."""
    from config import COMPANIES
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

            # Manual market-cap overrides take priority when the stock dataset
            # has no coverage for a company's older study dates (e.g. LAC's
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


import json
import os
import pandas as pd
import requests
import streamlit as st

from config import COMPANIES


# ============================================================================
# GOOGLE TRENDS SNAPSHOT (PINNED ~30 DAYS)
# ============================================================================
# Legacy pinned snapshot (trends_snapshot.csv + trends_snapshot_meta.json).
# De live trends-graphs draaien tegenwoordig via pytrends (Sentiment.py);
# dit snapshot wordt alleen nog gelezen door get_google_trends() (o.a. de
# Comparison Snapshot metrics). Er is geen SerpApi meer nodig.
# ============================================================================
TRENDS_SNAPSHOT_FILE = "trends_snapshot.csv"
TRENDS_SNAPSHOT_META_FILE = "trends_snapshot_meta.json"
TRENDS_SNAPSHOT_TTL_DAYS = 30


def _trends_snapshot_is_fresh():
    """Return True when the pinned snapshot is still within the 30-day TTL."""
    if not os.path.exists(TRENDS_SNAPSHOT_META_FILE):
        return False
    try:
        with open(TRENDS_SNAPSHOT_META_FILE, "r") as f:
            meta = json.load(f)
        snapshot_date = pd.to_datetime(meta.get("snapshot_date"))
        if pd.isna(snapshot_date):
            return False
        return (pd.Timestamp.now() - snapshot_date) <= pd.Timedelta(days=TRENDS_SNAPSHOT_TTL_DAYS)
    except Exception as e:
        print(f"trends snapshot meta read error: {e}")
        return False


def _load_trends_snapshot():
    """Load the pinned trends DataFrame from trends_snapshot.csv."""
    if not os.path.exists(TRENDS_SNAPSHOT_FILE):
        return None
    try:
        df = pd.read_csv(TRENDS_SNAPSHOT_FILE)
        if "date" not in df.columns:
            return None
        df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        print(f"trends snapshot read error: {e}")
        return None


def get_trends_snapshot_info():
    """Return (snapshot_date, expires_date) for the pinned trends graph.

    Used by views.py to show the user how long the graph stays fixed.
    """
    try:
        if not os.path.exists(TRENDS_SNAPSHOT_META_FILE):
            return None, None
        with open(TRENDS_SNAPSHOT_META_FILE, "r") as f:
            meta = json.load(f)
        snapshot_date = pd.to_datetime(meta.get("snapshot_date"))
        if pd.isna(snapshot_date):
            return None, None
        expires = snapshot_date + pd.Timedelta(days=TRENDS_SNAPSHOT_TTL_DAYS)
        return snapshot_date, expires
    except Exception:
        return None, None


def get_google_trends(companies=None):
    """Google Trends data uit het vaste snapshot-bestand (legacy).

    SerpApi is volledig verwijderd; de live trends-graphs draaien via
    pytrends (Sentiment.py). Deze functie leest alleen nog de gepinde
    trends_snapshot.csv (zolang die 'vers' is) voor o.a. de
    Comparison Snapshot metrics. Geen netwerkverzoekken meer.
    """
    if companies is None:
        companies = list(COMPANIES.keys())

    if _trends_snapshot_is_fresh():
        snapshot = _load_trends_snapshot()
        if snapshot is not None and not snapshot.empty:
            return snapshot

    return None


import numpy as np
import pandas as pd
import streamlit as st

from config import COMPANIES


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


import pandas as pd
import streamlit as st

from config import COMPANIES


@st.cache_data(ttl=3600)  # 1h — no TTL here froze 'current' prices until restart
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

            # Google Trends value for this company (optional) — averaged over
            # the firm's individual search terms.
            search_current = None
            search_change = None
            if trends is not None and not trends.empty:
                comp_terms = [t for t in COMPANIES[company]['search_terms']
                              if t in trends.columns]
                if comp_terms:
                    series = trends[comp_terms].dropna(how='all').mean(axis=1).dropna()
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

        return metrics
    except Exception as e:
        print(f"get_dashboard_metrics error: {e}")
        return {}

@st.cache_data(ttl=300)  # 5 min — keeps the live price under each ticker near-real-time
def get_monitor_returns(companies=None):
    """Last 1d / 7d / 30d % returns for the top market-monitor section.

    Rows per kind:
      * "company"  -- one row per selected firm (name, ticker, current price)
      * "cluster"  -- one equal-weight average row per STOCK_CLUSTERS region
                      (USA Nevada / Canada / Australia / Lithium Triangle /
                      Brazil / Africa / Europe) of the members' % returns

    Cards are ordered: selected company(s) first, then the region clusters
    in STOCK_CLUSTERS order.

    Returns {"as_of": "YYYY-MM-DD" or None, "rows": [...]}.
    """
    if companies is None:
        companies = list(COMPANIES.keys())

    periods = {"1d": 1, "7d": 7, "30d": 30}

    def fetch_ticker(ticker):
        """~3 months of daily close+volume (enough for 1/7/30-day returns)."""
        try:
            df = yf.Ticker(ticker).history(period="3mo").reset_index()
            cols = [c for c in ["Date", "Close", "Volume"] if c in df.columns]
            df = df[cols]
            if not df.empty:
                # Yahoo appends a placeholder row for "today" with a NaN Close
                # on non-trading days (weekends/holidays).  Dropping it keeps
                # the last row a real trading day — otherwise every return
                # and the price render as nan%.
                df = df.dropna(subset=["Close"]).reset_index(drop=True)
                df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
                return df.sort_values("Date").reset_index(drop=True)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()

    def calc_returns(df):
        """Return (rets, vol_changes, last_price, last_date, last_volume)."""
        # Use the last row with a real close — never a NaN placeholder bar
        # (Yahoo emits those on non-trading days like weekends).
        df = df.dropna(subset=["Close"])
        if df.empty:
            return ({label: None for label in periods},
                    {label: None for label in periods}, None, None, None)
        row = df.iloc[-1]
        current = float(row["Close"])
        if not pd.notna(current):
            current = None
        last_date = row["Date"]
        last_volume = None
        has_vol = "Volume" in df.columns and pd.notna(row.get("Volume"))
        if has_vol:
            last_volume = float(row["Volume"])
        out = {}
        vol_out = {}
        for label, days in periods.items():
            target = last_date - pd.Timedelta(days=days)
            base_rows = df[df["Date"] <= target]
            if base_rows.empty:
                base_row = df.iloc[0]
            else:
                base_row = base_rows.iloc[-1]
            base = float(base_row["Close"])
            out[label] = (current / base - 1) * 100 if base else None
            # Volume: compare today's volume against the TYPICAL daily
            # volume in the window (median, zero-volume days excluded) —
            # not the single bar N days ago.  For illiquid juniors one
            # day's volume is noise: a quiet base day produced wild
            # percentages like +330%.
            if label == "1d":
                window_vols = df[df["Date"] < last_date]["Volume"].tail(1)
            else:
                window_vols = df[(df["Date"] > target)
                                 & (df["Date"] < last_date)]["Volume"]
            window_vols = window_vols.dropna()
            window_vols = window_vols[window_vols > 0]
            if has_vol and not window_vols.empty:
                typical_vol = float(window_vols.median())
                vol_out[label] = (last_volume / typical_vol - 1) * 100 if typical_vol else None
            else:
                vol_out[label] = None
        return out, vol_out, current, last_date, last_volume

    company_rows = []
    cluster_rows = []
    etf_row = None
    as_dates = []

    # --- one row per selected company ---------------------------------
    for company in companies:
        ticker = COMPANIES[company]["yf_ticker"]
        df = fetch_ticker(ticker)
        if df.empty:
            continue
        returns, vol_changes, price, last_date, last_volume = calc_returns(df)
        as_dates.append(last_date)
        company_rows.append({
            "name": company,
            "ticker": ticker,
            "kind": "company",
            "price": price,
            "volume": last_volume,
            "returns": returns,
            "volume_changes": vol_changes,
        })

    # --- clusters (equal-weight average of member returns) -------------
    for _cluster_key, cluster in STOCK_CLUSTERS.items():
        member_rets = {label: [] for label in periods}
        member_vol_changes = {label: [] for label in periods}
        member_vols = []
        for display, ticker in cluster["members"].items():
            df = fetch_ticker(ticker)
            if df.empty:
                continue
            returns, vol_changes, _price, last_date, last_volume = calc_returns(df)
            as_dates.append(last_date)
            for label in periods:
                if returns[label] is not None:
                    member_rets[label].append(returns[label])
                if vol_changes[label] is not None:
                    member_vol_changes[label].append(vol_changes[label])
            if last_volume is not None:
                member_vols.append(last_volume)
        if not any(member_rets.values()):
            continue
        avg = {label: (sum(v) / len(v)) if v else None
               for label, v in member_rets.items()}
        avg_vol_chg = {label: (sum(v) / len(v)) if v else None
                       for label, v in member_vol_changes.items()}
        avg_vol = (sum(member_vols) / len(member_vols)) if member_vols else None
        n = max((len(v) for v in member_rets.values()), default=0)
        cluster_rows.append({
            "name": cluster["label"],
            "ticker": f"Average of {n}",
            "kind": "cluster",
            "cluster_key": _cluster_key,
            "price": None,
            "volume": avg_vol,
            "returns": avg,
            "volume_changes": avg_vol_chg,
        })

    # --- final card order -------------------------------------------------
    # Selected company(s) first, then the region clusters in a curated order.
    # Default follows STOCK_CLUSTERS, but Europe is placed before Australia so
    # the "8 squares" card row reads: USA, Canada, Lithium Triangle, Europe,
    # Brazil, Africa, Australia.
    _card_order = [
        "USA Juniors",
        "Canada Juniors",
        "Lithium Triangle Juniors",
        "Europe Juniors",
        "Brazil Juniors",
        "Africa Juniors",
        "Australia Juniors",
    ]
    by_key = {r["cluster_key"]: r for r in cluster_rows}
    ordered_rows = [by_key[k] for k in _card_order if k in by_key]
    rows = list(company_rows) + ordered_rows

    return {
        "as_of": max(as_dates).strftime("%Y-%m-%d") if as_dates else None,
        "rows": rows,
    }

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


import streamlit as st
from streamlit_gtag import st_gtag

GA4_ID = st.secrets.get("GA4_ID", "")

# Session markers to prevent duplicate events (Streamlit reruns on every
# interaction, so without a guard we would duplicate events 3-4x per session).
if "page_loaded_fired" not in st.session_state:
    st.session_state.page_loaded_fired = False
if "last_view_mode" not in st.session_state:
    st.session_state.last_view_mode = None
if "last_companies" not in st.session_state:
    st.session_state.last_companies = None
if "last_stock_period" not in st.session_state:
    st.session_state.last_stock_period = None


def _can_track():
    return bool(GA4_ID)


def track_event(name, params=None):
    """Send a GA4 custom event (only if GA4 is configured)."""
    if not _can_track():
        return
    data = {
        "app_name": "Lithium_Project_Comparison",
        "user_id": st.session_state.get("user_id", ""),
        "is_returning": str(st.session_state.get("is_returning", "")),
        "visit_number": str(st.session_state.get("visit_number", "")),
    }
    if params:
        data.update(params)
    try:
        st_gtag(id=GA4_ID, event_name=name, params=data)
    except Exception:
        pass


def track_page_loaded():
    """Fire page_loaded ONCE per session (not on every rerun)."""
    if not _can_track() or st.session_state.get("page_loaded_fired", False):
        return
    st.session_state.page_loaded_fired = True
    track_event("page_loaded")


def track_view_mode_change(view_mode):
    if not _can_track() or st.session_state.get("last_view_mode") == view_mode:
        return
    st.session_state.last_view_mode = view_mode
    track_event("view_mode_change", {"view_mode": view_mode})


def track_company_selection(companies):
    if not _can_track():
        return
    key = tuple(sorted(companies))
    if st.session_state.get("last_companies") == key:
        return
    st.session_state.last_companies = key
    track_event("company_selection", {
        "companies": ", ".join(companies),
        "company_count": len(companies),
    })


def track_period_change(period):
    """Track when the user changes the stock-chart time-period filter."""
    if not _can_track() or st.session_state.get("last_stock_period") == period:
        return
    st.session_state.last_stock_period = period
    track_event("stock_period_change", {"period": period})


def track_tab_click(tab_name):
    track_event("tab_click", {"tab_name": tab_name})


def track_expander_open(expander_name):
    track_event("expander_open", {"expander_name": expander_name})


def track_qa_submit():
    track_event("qa_submit")


def track_qa_like():
    track_event("qa_like")


# ============================================================================
# LITHIUM FUTURES (LIVE SCRAPE — metal.com via Playwright)
# ============================================================================
# Futures.py scraped de lithium-futures term structure (CNY-contracten) van
# metal.com met Playwright (headless Chromium). De Chromium-browser wordt één
# keer per app-lifetime geïnstalleerd (gecached via st.cache_resource), zodat
# dit ook op Streamlit Cloud werkt. Fouten leveren een lege lijst op — er is
# bewust GEEN fallback-afbeelding (zie PROJECT.md voor de install-steps).
# ============================================================================

@st.cache_resource(show_spinner=False)
def _ensure_playwright_browser():
    """Zorg dat headless Chromium beschikbaar is voor Playwright.

    Streamlit Cloud voert `playwright install` niet uit tijdens de deploy,
    dus de browser wordt hier één keer gedownload (gecached voor de
    app-lifetime). Returns True zodra er een browser te launchen is.
    """
    import subprocess
    import sys

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright niet geïnstalleerd — voeg 'playwright' toe aan requirements.txt")
        return False

    def _can_launch():
        try:
            with sync_playwright() as p:
                p.chromium.launch(headless=True).close()
            return True
        except Exception as e:
            print(f"Playwright chromium launch failed: {e}")
            return False

    if _can_launch():
        return True

    # Eenmalige browser-installatie (ook de eerste lokale run)
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True, capture_output=True, timeout=600,
        )
    except Exception as e:
        print(f"playwright install chromium failed: {e}")
        return False

    return _can_launch()


@st.cache_data(ttl=3600, show_spinner=False)  # 1 uur — spotprijs beweegt traag
def get_lithium_spot_history():
    """Dagelijkse lithium-spotprijs (metalcharts.org via Spot.py) als groeiende
    tijdserie.  Elke dag wordt maximaal één datapunt toegevoegd aan
    lithium_spot_data.csv (Date, Price_USD, Change_USD, Change_Percent,
    Update_Time) — bestaat de rij voor vandaag al, dan wordt hij niet
    gedupliceerd.  Returns (DataFrame, dict) of (None, None) bij een lege CSV
    en een mislukte fetch.
    """
    import os
    import re
    import pandas as pd
    from Spot import get_lithium_data

    csv_path = os.path.join(os.path.dirname(__file__), "lithium_spot_data.csv")
    cols = ["Date", "Price_USD", "Change_USD", "Change_Percent", "Update_Time"]

    def _read_csv():
        if os.path.isfile(csv_path):
            try:
                df = pd.read_csv(csv_path)
                return df[cols].copy()
            except Exception:
                pass
        return pd.DataFrame(columns=cols)

    df = _read_csv()

    # Live fetch; bij succes en nog geen rij voor vandaag → append.
    data = get_lithium_data()
    if data and data.get("price") is not None:
        today = data["scrape_date"]
        if today not in set(df["Date"]):
            df = pd.concat([df, pd.DataFrame([{
                "Date": today,
                "Price_USD": data["price"],
                "Change_USD": data["change_usd"],
                "Change_Percent": data["percent_change"],
                "Update_Time": data["update_time"],
            }])], ignore_index=True)
            try:
                df.to_csv(csv_path, index=False)
            except Exception:
                pass  # read-only FS (Streamlit Cloud): lijn blijft dan sessie-lokaal

    if df.empty:
        return None, None

    df = df.sort_values("Date").reset_index(drop=True)
    latest = df.iloc[-1]

    # NaN (lege velden in de CSV) → None, zodat de views er netjes mee omgaan
    def _clean(v):
        return None if (v is None or (isinstance(v, float) and v != v)) else v

    # Bron-tijd ("August 29, 2026, 2:00 PM EDT") → kort "14:00 ET",
    # zelfde format als de futures-caption.
    raw_time = _clean(latest["Update_Time"])
    updated_et = None
    if raw_time:
        m = re.search(r"(\d{1,2}):(\d{2}) ([AP]M)", str(raw_time))
        if m:
            h, mm, ap = int(m.group(1)), m.group(2), m.group(3)
            h24 = h % 12 + (12 if ap == "PM" else 0)
            updated_et = f"{h24:02d}:{mm} ET"
        else:
            updated_et = str(raw_time)

    return df, {
        "price": _clean(latest["Price_USD"]),
        "change_usd": _clean(latest["Change_USD"]),
        "change_percent": _clean(latest["Change_Percent"]),
        "date": _clean(latest["Date"]),
        "update_time": updated_et,
    }


@st.cache_data(ttl=3600, show_spinner=False)  # 1 uur — term structure verandert traag
def get_lithium_futures():
    """Lithium futures term structure van metal.com (live scrape).

    Returns een dict:
        {"contracts": [ {contract, latest, open, high, low}, ... ],
         "updated":   "HH:MM" in Amerikaans/Oosterse tijd (ET) — tijd van de
                      laatste geslaagde scrape, geconverteerd naar de NYSE-zone}

    Bij een mislukte scrape: {"contracts": [], "updated": None} (geen fallback).
    Omdat de hele return gecached zit, blijft `updated` de werkelijke
    scrape-tijd, ook als de data later uit de cache komt.
    """
    if not _ensure_playwright_browser():
        return {"contracts": [], "updated": None}

    try:
        from Futures import scrape_lithium
        contracts = scrape_lithium()
        return {
            "contracts": contracts,
            "updated": pd.Timestamp.now(tz="America/New_York").strftime("%H:%M"),
        }
    except Exception as e:
        print(f"Lithium futures scrape error: {e}")
        return {"contracts": [], "updated": None}
