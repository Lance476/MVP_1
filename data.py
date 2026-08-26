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


@st.cache_data(ttl=3600)  # 1h — daily bars barely move intraday
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

SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# ============================================================================
# GOOGLE TRENDS SNAPSHOT (PINNED ~30 DAYS)
# ============================================================================
# De Google Trends grafiek (via SerpApi) wordt bewust VASTGEZET voor 30 dagen.
# De eerste keer dat de app draait (of nadat de snapshot verlopen is) wordt de
# data via SerpApi opgehaald en weggeschreven naar trends_snapshot.csv +
# trends_snapshot_meta.json. Die twee bestanden worden in git gecommit, zodat
# elke Streamlit Cloud deploy exact dezelfde grafiek toont tot de 30 dagen om
# zijn. Na 30 dagen haalt de app verse data op — commit de twee bestanden dan
# opnieuw om de nieuwe snapshot vast te zetten.
# ============================================================================
TRENDS_SNAPSHOT_FILE = "trends_snapshot.csv"
TRENDS_SNAPSHOT_META_FILE = "trends_snapshot_meta.json"
TRENDS_SNAPSHOT_TTL_DAYS = 30


def _parse_trends_timestamp(item):
    """Extract a naive datetime from one SerpApi timeline point."""
    # Use "timestamp" (epoch) — date strings vary per locale.
    if item.get("timestamp"):
        return pd.to_datetime(int(item["timestamp"]), unit="s", utc=True).tz_localize(None)

    date_str = item.get("date", "")

    try:
        return pd.to_datetime(date_str)
    except Exception:
        # Handle week range: "Aug 10 – 16, 2025" → take END date
        parts = date_str.split("–")
        end_part = parts[1].strip()
        start_part = parts[0].strip()
        month_name = start_part.split()[0]
        end_clean = end_part.replace(",", "").strip()
        end_parts = end_clean.split()
        day = int(end_parts[0])
        year = int(end_parts[1])
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        month = month_map.get(month_name[:3], 1)
        return pd.Timestamp(year=year, month=month, day=day)


def fetch_google_trends_serpapi(search_terms):
    """Fetch Google Trends data via SerpApi for a list of search terms.

    Each term is fetched with its OWN query, so its interest values are
    normalized 0-100 independently (not relative to the other terms).
    """
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

            if "interest_over_time" not in result:
                continue

            timeline = result["interest_over_time"].get("timeline_data", [])

            for item in timeline:
                date = _parse_trends_timestamp(item)

                values = item.get("values") or []
                if not values:
                    continue
                raw_value = values[0].get("value", values[0].get("extracted_value", 0))
                try:
                    value = float(raw_value)
                except (TypeError, ValueError):
                    continue
                all_data.append({"date": date, "term": term, "value": value})

        if not all_data:
            return None

        df = pd.DataFrame(all_data)
        pivot = df.pivot_table(index='date', columns='term', values='value',
                               aggfunc='mean').reset_index()
        pivot['date'] = pd.to_datetime(pivot['date'])

        for term in search_terms:
            if term not in pivot.columns:
                pivot[term] = 0

        # Keep columns in the configured term order
        ordered_cols = ['date'] + list(search_terms)
        return pivot[ordered_cols]

    except Exception as e:
        print(f"Error fetching Google Trends: {e}")
        return None


@st.cache_data(ttl=604800)
def fetch_single_company_trends(company, search_terms):
    """Fetch Google Trends for ONE company (cached individually).

    `search_terms` is an explicit argument so the cache key changes whenever
    the configured terms change (otherwise stale combined-query data could be
    served for up to a week after a config update).
    """
    if SERPAPI_KEY and search_terms:
        data = fetch_google_trends_serpapi(list(search_terms))
        if data is not None and not data.empty:
            return data
    return None


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


def _save_trends_snapshot(df):
    """Persist the trends snapshot + timestamp so it survives future deploys."""
    try:
        df.to_csv(TRENDS_SNAPSHOT_FILE, index=False)
        with open(TRENDS_SNAPSHOT_META_FILE, "w") as f:
            json.dump({"snapshot_date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}, f)
    except Exception as e:
        print(f"trends snapshot write error: {e}")


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
    """Get Google Trends data, PINNED to a ~30-day snapshot.

    The trends graph intentionally freezes for 30 days so it does not change
    on every code patch/deploy. If a fresh snapshot exists it is returned
    directly (no SerpApi call). Only after 30 days does the app re-fetch from
    SerpApi and write a new snapshot (commit the two snapshot files to pin it
    for another month).
    """
    if companies is None:
        companies = list(COMPANIES.keys())

    # Prefer the pinned snapshot while it is still fresh (< 30 days old)
    if _trends_snapshot_is_fresh():
        snapshot = _load_trends_snapshot()
        if snapshot is not None and not snapshot.empty:
            return snapshot

    all_data = []
    for company in companies:
        terms = tuple(COMPANIES[company]['search_terms'])
        data = fetch_single_company_trends(company, terms)
        if data is not None and not data.empty:
            all_data.append(data)

    if not all_data:
        return None

    combined = all_data[0]
    for df in all_data[1:]:
        combined = pd.merge(combined, df, on='date', how='outer')

    combined = combined.sort_values('date').reset_index(drop=True)

    # Pin this freshly fetched data for the next 30 days
    _save_trends_snapshot(combined)

    return combined


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
                df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
                return df.sort_values("Date").reset_index(drop=True)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()

    def calc_returns(df):
        """Return (rets, vol_changes, last_price, last_date, last_volume)."""
        row = df.iloc[-1]
        current = float(row["Close"])
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
            "ticker": f"Average of {n} companies",
            "kind": "cluster",
            "cluster_key": _cluster_key,
            "price": None,
            "volume": avg_vol,
            "returns": avg,
            "volume_changes": avg_vol_chg,
        })

    # --- final card order -------------------------------------------------
    # Selected company(s) first, then the region clusters in STOCK_CLUSTERS
    # order (Nevada, Canada, Australia, Lithium Triangle, Brazil, Africa, Europe).
    rows = list(company_rows)
    for row in cluster_rows:
        rows.append(row)

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


@st.cache_data(ttl=604800)
def get_search_volume_data(companies=None):
    """Google Ads search volume (monthly) for the selected companies.

    Returns a long-format DataFrame with columns:
        Month, Company, Search_Volume

    For every selected company, the company's own line is included plus the
    two sector benchmarks "lithium stocks" and "Nevada Lithium", so each
    company's chart shows 3 lines.
    """
    from config import SEARCH_DATA

    if companies is None:
        companies = list(COMPANIES.keys())

    # Benchmarks shown alongside every company's own line
    benchmark_keys = ["lithium stocks", "Nevada Lithium"]

    rows = []
    for company in companies:
        # The company's own series (if present in SEARCH_DATA)
        series_keys = [company] + benchmark_keys
        for key in series_keys:
            data = SEARCH_DATA.get(key)
            if data is None:
                continue
            months = data.get("months", [])
            values = data.get("values", [])
            for month, value in zip(months, values):
                rows.append({
                    "Month": month,
                    "Company": key,
                    "Search_Volume": value,
                })

    if not rows:
        return pd.DataFrame(columns=["Month", "Company", "Search_Volume"])

    return pd.DataFrame(rows)


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
# USER FEEDBACK
# ============================================================================

import os
import smtplib
from email.mime.text import MIMEText


def get_feedback_email():
    """Return the owner's feedback email address (set FEEDBACK_EMAIL in secrets)."""
    return st.secrets.get("FEEDBACK_EMAIL", "")


def send_feedback(message, contact=""):
    """Send visitor feedback to the app owner.

    Delivery order (first configured channel wins):
      1. Formspree web form  — set FORMSPREE_FORM_ID in secrets (works on
         Streamlit Community Cloud, no SMTP ports needed).
      2. SMTP email          — set SMTP_HOST, SMTP_PORT, SMTP_USER,
         SMTP_PASSWORD and FEEDBACK_EMAIL in secrets (e.g. Gmail app password).
      3. Local fallback      — append to feedback.csv so no feedback is lost
         while running locally without any channel configured.

    Returns (success: bool, channel: str).
    """
    message = (message or "").strip()
    if not message:
        return False, "empty"

    # 1) Formspree
    form_id = st.secrets.get("FORMSPREE_FORM_ID", "")
    if form_id:
        try:
            resp = requests.post(
                f"https://formspree.io/f/{form_id}",
                json={
                    "message": message,
                    "contact": contact or "anonymous",
                    "source": "Lithium Project Comparison",
                },
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if resp.ok:
                return True, "formspree"
            print(f"Formspree feedback error: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"Formspree feedback error: {e}")

    # 2) SMTP email
    smtp_host = st.secrets.get("SMTP_HOST", "")
    feedback_email = st.secrets.get("FEEDBACK_EMAIL", "")
    if smtp_host and feedback_email:
        try:
            port = int(st.secrets.get("SMTP_PORT", 587))
            user = st.secrets.get("SMTP_USER", "")
            password = st.secrets.get("SMTP_PASSWORD", "")

            msg = MIMEText(f"Contact: {contact or 'anonymous'}\n\n{message}")
            msg["Subject"] = "Feedback — Lithium Project Comparison"
            msg["From"] = user or feedback_email
            msg["To"] = feedback_email

            with smtplib.SMTP(smtp_host, port, timeout=15) as server:
                server.starttls()
                if user and password:
                    server.login(user, password)
                server.sendmail(msg["From"], [feedback_email], msg.as_string())
            return True, "email"
        except Exception as e:
            print(f"SMTP feedback error: {e}")

    # 3) Local fallback
    try:
        row = pd.DataFrame([{
            "timestamp": pd.Timestamp.now().isoformat(),
            "contact": contact or "anonymous",
            "message": message,
        }])
        header = not os.path.exists("feedback.csv")
        row.to_csv("feedback.csv", mode="a", header=header, index=False)
        return True, "local"
    except Exception as e:
        print(f"Local feedback error: {e}")
        return False, "none"
