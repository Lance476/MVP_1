# views.py
# ============================================================================
# ALLE weergave-functies van de app. Elke functie tekent één onderdeel
# (sidebar, dashboard, studies, timeline, ...) en haalt zijn data via data.py.
# ============================================================================
import altair as alt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import re
import streamlit as st
import yfinance as yf

from config import COMPANIES, DEFAULT_COMPANY, STAGE_ORDER, STAGE_SHORT_MAP, STOCK_CLUSTERS, TIMELINE_DATA, YOUTUBE_VIDEOS, lithium_companies
from data import (
    get_cluster_stock_data,
    get_equity_stock_data,
    get_equity_intraday_window_data,
    get_intraday_stock_data,
    get_dashboard_metrics,
    get_lithium_futures,
    get_lithium_spot_history,
    get_monitor_returns,
    get_market_cap_data,
    get_stock_data,
    build_company_financials,
    load_financial_data,
    load_study_data,
    track_event,
    track_expander_open,
    track_qa_like,
    track_qa_submit,
    track_tab_click,
)


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
                default=[DEFAULT_COMPANY, "Ioneer", "Lithium Americas"],
                help="Pick 2 or more companies to compare.",
                label_visibility="collapsed"
            )
            if len(selected) < 2:
                st.warning("Select at least 2 companies.")

        # Builder-profiel: subtiel, onderaan — bewijs dat er een echt persoon
        # achter zit, zonder de focus van de data af te leiden.  Doel-blank
        # en rel=noreferrer zodat de link overal veilig opent (elk apparaat,
        # elke browser), zonder referrer-lekkage.
        st.markdown(
            "<div style='margin-top:12px; padding-top:10px; "
            "border-top:1px solid rgba(128,128,128,0.25); "
            "font-size:12px; color:#6b7280; line-height:1.6;'>"
            "Built by <b style='color:#374151;'>Lance</b> · "
            "<a href='https://www.linkedin.com/in/lance39/' target='_blank' "
            "rel='noopener noreferrer' "
            "style='color:#1f77b4; text-decoration:none;'>"
            "&#128279; LinkedIn</a>"
            "</div>",
            unsafe_allow_html=True,
        )

        return view_mode, selected


def render_top_mover_hook(companies=None):
    """'Hook' bovenaan: één subtiele balk die meteen laat zien dat er iets
    leeft — de sterkste *individuele* aandelen (1D en 30D) over alle regio's.
    We zoeken bewust op bedrijfsniveau (niet per regio) zodat de mover
    specifiek is.  Gebruikt de al-gebruikte, gecachte equity-data per regio —
    geen extra netwerk.
    """
    from data import get_equity_stock_data, STOCK_CLUSTERS  # safe local import
    if companies is None:
        companies = list(COMPANIES.keys())

    # ---- Beste individuele mover over alle clusterleden, per periode ----
    best = {"1d": None, "30d": None}
    worst = {"1d": None, "30d": None}
    for _key, cluster in STOCK_CLUSTERS.items():
        df = get_equity_stock_data(_key)
        if df is None or df.empty or "Symbol" not in df.columns:
            continue
        for sym, g in df.groupby("Symbol"):
            g = g.sort_values("Date")
            if len(g) < 2:
                continue
            close = g["Close"]
            last = close.iloc[-1]

            # 1D = laatste bar vs. de ONMIDDELLIJK vorige handelsdag (de rij
            # er direct vóór).  Dit matcht de dagwijziging van Yahoo.  (Een
            # "-2 dagen"-versie slaat per ongeluk een handelsdag over en
            # blies de beweging op, zie do/vr/weekend.)
            base_1d = close.iloc[-2]
            if base_1d:
                ret_1d = (last / base_1d - 1) * 100
                if best["1d"] is None or ret_1d > best["1d"][1]:
                    best["1d"] = (str(g["Ticker"].iloc[0]), ret_1d)
                if worst["1d"] is None or ret_1d < worst["1d"][1]:
                    worst["1d"] = (str(g["Ticker"].iloc[0]), ret_1d)

            # 30D = laatste bar vs. de dag ~30 dagen terug.
            tgt = g["Date"].iloc[-1] - pd.Timedelta(days=30)
            prior = g[g["Date"] <= tgt]
            if not prior.empty:
                base_30 = prior["Close"].iloc[-1]
                if base_30:
                    ret_30 = (last / base_30 - 1) * 100
                    if best["30d"] is None or ret_30 > best["30d"][1]:
                        best["30d"] = (str(g["Ticker"].iloc[0]), ret_30)
                    if worst["30d"] is None or ret_30 < worst["30d"][1]:
                        worst["30d"] = (str(g["Ticker"].iloc[0]), ret_30)

    parts = []
    for label, text in [("1d", "BEST 1D"), ("1d_worst", "WORST 1D"),
                        ("30d", "BEST 30D"), ("30d_worst", "WORST 30D")]:
        hit = worst[label.replace("_worst", "")] if label.endswith("_worst") else best[label]
        if not hit:
            continue
        name, v = hit
        col = "#1a7f37" if v >= 0 else "#d1242f"
        parts.append(
            f"<span style='color:#111111;'>{text}</span> "
            f"<b style='color:#111111;'>{name}</b> "
            f"<span style='color:{col}; font-weight:700;'>{v:+.1f}%</span>")

    if not parts:
        return

    st.markdown(
        "<div style='display:flex; align-items:center; gap:16px; flex-wrap:wrap; "
        "justify-content:center; padding:10px 14px; border-radius:8px; "
        "background:#f3f4f6; margin:0 0 18px 0; font-size:13px; "
        "font-family:\"Segoe UI\", \"Helvetica Neue\", Arial, sans-serif;'>"
        + "&nbsp;·&nbsp;".join(parts)
        + "</div>",
        unsafe_allow_html=True)


def _nice_ceil(x):
    """Rond een positief getal naar boven af op een 'rond' percentage
    (1, 2, 2.5, 3, 5, 10 x 10^k) zodat schaallabels netjes lezen (5%, 10%…)."""
    if x <= 0:
        return 1.0
    p = 0
    while 10 ** p < x:
        p += 1
    base = 10.0 ** (p - 1)
    for nice in (1, 2, 2.5, 3, 5, 10):
        if x <= nice * base:
            return nice * base
    return 10 * base


def render_dashboard(companies=None):
    """Market Monitor cards: selected company(s) + region clusters, rendered
    in rows of max 4, followed by the regional performance ranking."""
    if companies is None:
        companies = list(COMPANIES.keys())

    board = get_monitor_returns(companies)
    rows = board.get("rows", [])
    if not rows:
        st.warning("Could not load market monitor data")
        return

    def _color(v):
        return "#1a7f37" if v >= 0 else "#d1242f"

    def _pct(v):
        if v is None or pd.isna(v):
            return "n/a"
        sign = "+" if v >= 0 else ""
        return f"{sign}{v:.1f}%"

    def _colored(v):
        """Price return percentage — larger, light weight, professional font."""
        if v is None or pd.isna(v):
            return "<span style='color:#9ca3af; font-size:12px;'>n/a</span>"
        return (f"<span style='font-weight:400; font-size:14px; "
                f"font-family:\"Segoe UI\", \"Helvetica Neue\", Arial, sans-serif; "
                f"letter-spacing:0.3px; color:{_color(v)};'>"
                f"{_pct(v)}</span>")

    def _volume_colored(v):
        """Volume change percentage — neutral black, original (inherited) size."""
        if v is None or pd.isna(v):
            return "<span style='color:#9ca3af;'>&#8211;</span>"
        sign = "+" if v >= 0 else ""
        return f"<span style='color:#111111;'>{sign}{v:.1f}%</span>"

    def _fmt_volume(v):
        if v is None or pd.isna(v):
            return "n/a"
        if v >= 1e9:
            return f"{v / 1e9:.2f}B"
        if v >= 1e6:
            return f"{v / 1e6:.2f}M"
        if v >= 1e3:
            return f"{v / 1e3:.1f}K"
        return f"{v:,.0f}"

    def _card(r):
        name = r["name"]
        ticker = r.get("ticker", "")
        is_cluster = r.get("kind") == "cluster"
        subtitle = ""
        if is_cluster and ticker:
            subtitle = (
                f"<div style='font-size:10px; font-weight:400; color:#9ca3af; "
                f"margin-top:1px; margin-bottom:15px;'>{ticker}</div>"
            )
        price = ""
        if r.get("price") is not None:
            price = (
                f"<div style='font-size:14px; font-weight:400; "
                f"font-family:\"Segoe UI\", \"Helvetica Neue\", Arial, sans-serif;"
                f" color:#1f2937;'>"
                f"$ {r['price']:.2f}"
                f" <span style='font-size:11px; font-weight:400; color:#9ca3af;'>"
                f"{ticker}</span></div>"
            )

        def _line(label, value_html):
            return (
                "<div style='display:flex; justify-content:space-between; "
                "align-items:center; font-size:11px; padding:2px 0; "
                "border-bottom:1px solid #f3f4f6;'>"
                f"<span style='color:#9ca3af;'>{label}</span>"
                f"<span>{value_html}</span>"
                "</div>"
            )

        def _pair(value1, value2):
            return f"{value1} <span style='color:#8a9099; font-size:10px;'>vol {value2}</span>"

        row = (
            _line("1D", _colored(r["returns"].get("1d")))
            + _line("7D", _colored(r["returns"].get("7d")))
            + _line("30D", _colored(r["returns"].get("30d")))
            # Volume-regel: inhoud (label + getal) leeggemaakt — de rij zelf
            # blijft bestaan zodat hier later iets anders geplaatst kan worden.
            + _line("", "")
        )
        return f"""
        <div style='border:1px solid #e5e7eb; border-radius:10px; padding:12px;
                    background:#ffffff; box-shadow:0 1px 2px rgba(0,0,0,0.05);
                    height:100%;'>
          <div style='font-weight:600; font-size:13px; color:#1f2937;
                      white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{name}</div>
          {subtitle}
          {price}
          <div style='margin-top:8px;'>{row}</div>
        </div>
        """

    # ---- cards in rows of max 4, with vertical space between rows ----
    _MAX_COLS_PER_ROW = 4
    for start in range(0, len(rows), _MAX_COLS_PER_ROW):
        chunk = rows[start:start + _MAX_COLS_PER_ROW]
        cols = st.columns(len(chunk))
        for col, r in zip(cols, chunk):
            with col:
                st.markdown(_card(r), unsafe_allow_html=True)
        if start + _MAX_COLS_PER_ROW < len(rows):
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

    # ---- performance ranking (region clusters only), USA highlighted ----
    st.markdown("<div style='height:52px;'></div>", unsafe_allow_html=True)

    def _perf_cell(header, key):
        cluster_rows = [r for r in rows if r.get("kind") == "cluster"]
        # Rangschikking: eerst alle positieve (groene) rendementen, van hoog
        # naar laag; daarna de negatieve (rode); ontbrekende waardes onderaan.
        vals = sorted(
            ((r["name"], r["returns"].get(key)) for r in cluster_rows),
            key=lambda t: (
                t[1] is None,          # None altijd onderaan
                not (t[1] is not None and t[1] >= 0),  # groen eerst, rood daarna
                -(t[1] or 0),          # binnen elke groep: hoog -> laag
            ),
        )
        if not vals:
            st.caption("n/a")
            return
        numeric = [v for _, v in vals if v is not None]
        max_abs = max(abs(v) for v in numeric) if numeric else 1.0
        rng = _nice_ceil(max_abs)

        # Header (1D/7D/30D) op een EIGEN regel, links — zoals origineel.
        st.markdown(
            f"<div style='font-weight:700; font-size:14px; color:#111111; "
            f"margin-bottom:2px;'>{header}</div>",
            unsafe_allow_html=True)

        # Gedeelde schaal boven de balken: -rng / 0 / +rng, uitgelijnd met de
        # centrumlijn (negatief links, positief rechts).
        def _tick_label(x):
            if x == 0:
                return "0"
            return f"{x:g}%"

        st.markdown(
            f"<div style='display:flex; align-items:center; margin-bottom:14px;'>"
            f"<span style='width:105px; flex-shrink:0;'></span>"
            f"<div style='flex:1 1 auto; position:relative; height:16px;'>"
            f"<span style='position:absolute; left:0; top:0; font-size:14px; "
            f"color:#9ca3af;'>{_tick_label(-rng)}</span>"
            f"<span style='position:absolute; left:50%; top:0; transform:translateX(-50%); "
            f"font-size:14px; color:#9ca3af;'>0</span>"
            f"<span style='position:absolute; right:0; top:0; font-size:14px; "
            f"color:#9ca3af;'>{_tick_label(rng)}</span>"
            f"</div></div>",
            unsafe_allow_html=True)

        for name, v in vals:
            if v is None:
                st.markdown(
                    f"<div style='font-size:11px; padding:2px 0;'>"
                    f"<span style='color:#9ca3af;'>{name}</span>"
                    f"</div>", unsafe_allow_html=True)
                continue
            frac = min(abs(v) / rng, 1.0)      # 0..1
            bar_w = frac * 50.0                # half of the bar area
            left = 50.0 if v >= 0 else 50.0 - bar_w
            display_name = name.replace(" Lithium", "")
            # USA markeren met een subtiele accentkleur (niet vet) — dezelfde
            # blauw als de charts, zodat het opvalt zonder te schreeuwen.
            name_style = "color:#1f77b4;" if display_name == "USA" else ""
            st.markdown(
                f"<div style='font-size:12px; padding:4px 0;'>"
                f"<div style='display:flex; align-items:center;'>"
                f"<span style='{name_style} font-weight:400; font-size:14px; width:105px; flex-shrink:0;'>"
                f"{display_name}</span>"
                f"<div style='flex:1 1 auto; position:relative; height:17px;'>"
                f"<div style='position:absolute; left:50%; top:0; bottom:0; width:1px; "
                f"background:#d1d5db;'></div>"
                f"<div style='position:absolute; left:{left:.1f}%; width:{bar_w:.1f}%; "
                f"height:17px; background:{_color(v)}; border-radius:3px;'>&nbsp;</div>"
                f"</div></div></div>",
                unsafe_allow_html=True)

    left, mid, right = st.columns(3)
    with left:
        _perf_cell("1D", "1d")
    with mid:
        _perf_cell("7D", "7d")
    with right:
        _perf_cell("30D", "30d")


# ===========================================================================
# EQUITY MARKETS — per-region drill-down on individual stocks
# ===========================================================================
_EQUITY_PALETTE = [
    "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
    "#8c564b", "#e377c2", "#17becf", "#bcbd22",
]

# Session window (tz, open h/m, close h/m) per ticker suffix — used by the
# live 1D renderer to show the FULL trading day (including the part of the
# day that has not traded yet).
_SESSION_WINDOWS = {
    ".AX": ("Australia/Sydney", 10, 0, 16, 0),
    ".TO": ("America/Toronto", 9, 30, 16, 0),
    ".V": ("America/Vancouver", 9, 30, 16, 0),
    ".L": ("Europe/London", 8, 0, 16, 30),
}
_DEFAULT_SESSION = ("America/New_York", 9, 30, 16, 0)


def _session_window(tickers):
    """Return (tz_name, open_ts, close_ts) for today's session of a cluster.

    Picks the exchange shared by the MAJORITY of tickers (ties -> NY default),
    so one stray foreign listing inside a regional cluster no longer shifts
    the whole chart's clock.
    """
    counts = {}
    for t in tickers:
        matched = False
        for suffix, cfg in _SESSION_WINDOWS.items():
            if str(t).endswith(suffix):
                counts[cfg] = counts.get(cfg, 0) + 1
                matched = True
                break
        if not matched:
            counts[_DEFAULT_SESSION] = counts.get(_DEFAULT_SESSION, 0) + 1
    # Majority vote; ties fall back to the NY default.
    best = max(
        counts.items(),
        key=lambda kv: (kv[1], kv[0] is _DEFAULT_SESSION),
    )[0]
    tz_name, oh, om, ch, cm = best
    base = pd.Timestamp.now(tz=tz_name).normalize()
    return (tz_name,
            base + pd.Timedelta(hours=oh, minutes=om),
            base + pd.Timedelta(hours=ch, minutes=cm))


def _currency_label(ticker):
    """Trading-currency of a ticker based on its exchange suffix."""
    t = str(ticker)
    if t.endswith((".TO", ".V")):
        return "CAD"
    if t.endswith(".AX"):
        return "AUD"
    if t.endswith(".L"):
        return "GBP"
    return "USD"


def _render_intraday_chart(members):
    """Live 1D chart (TestGraph style): 5-minute bars at actual prices.

    Shows the full session window with a grey 'yet to come' zone and a dashed
    line at the newest bar, so investors can see where each stock stands now
    and how much of the day still has to come. Illiquid tickers are forward-
    filled on a shared 5-minute grid so their lines continue as a flat line.
    """
    if not members:
        st.info("Geen live data beschikbaar voor deze regio.")
        return

    tickers = [m["ticker"] for m in members]
    tz_name, session_open, session_close = _session_window(tickers)
    session_open_n = session_open.tz_localize(None)
    session_close_n = session_close.tz_localize(None)

    fig = go.Figure()  # Plotly SVG renderer → scherp, nooit wazig

    # Shared 5-minute grid from the session open up to the newest real bar.
    # Only keep bars INSIDE the plotted session: mixed clusters can contain
    # listings from other exchanges whose newest bar predates this session's
    # open (e.g. a TSX-V stock seen on the Sydney clock). Such stale bars push
    # grid_end BEFORE session_open_n, which makes pd.date_range() return an
    # EMPTY grid and crashes grid[-1] further down with
    # "IndexError: index -1 is out of bounds for axis 0 with size 0".
    frames = []
    skipped = []
    for m in members:
        df = m["data"].copy()
        df["Date"] = (
            pd.to_datetime(df["Date"], utc=True)
            .dt.tz_convert(tz_name).dt.tz_localize(None)
        )
        df = df[df["Date"] >= session_open_n]
        if df.empty:
            skipped.append(f"{m['display']} ({m['ticker']})")
            continue
        frames.append((m, df))
    if not frames:
        st.info(
            "No prices yet — the market is still closed."
        )
        return
    grid_end = max(df["Date"].max() for _, df in frames)
    grid = pd.date_range(session_open_n, grid_end, freq="5min")

    # Draw each stock as a crisp SVG line. A coloured dot marks the newest
    # 5-minute bar; the firm name + % sits to the right, black and regular
    # (not bold), so it matches the ranking cards above.
    ends = []
    all_prices = []
    for i, (m, df) in enumerate(frames):
        color = _EQUITY_PALETTE[i % len(_EQUITY_PALETTE)]
        s = df.set_index("Date")["Close"]
        s = s.reindex(s.index.union(grid)).sort_index().ffill().reindex(grid)
        ys = s.values.astype(float)
        fig.add_trace(go.Scatter(
            x=list(grid), y=ys, mode="lines",
            line=dict(color=color, width=2.5),
            hoverinfo="skip", showlegend=False,
        ))
        all_prices.extend(y for y in ys if not pd.isna(y))
        last_val = float(ys[-1])
        if pd.isna(last_val):
            continue
        fig.add_trace(go.Scatter(
            x=[grid[-1]], y=[last_val], mode="markers",
            marker=dict(color=color, size=9, line=dict(width=0)),
            hoverinfo="skip", showlegend=False,
        ))
        valid = s.dropna()
        if len(valid) >= 2 and valid.iloc[0]:
            pct = (last_val / float(valid.iloc[0]) - 1) * 100
        else:
            pct = 0.0
        ends.append({"x": grid[-1], "y": last_val, "name": m["display"],
                     "pct": pct})

    if ends and all_prices:
        # Y-range: a two-line (name + %) label block is ~5.5% of the plotted
        # height, so consecutive right-hand labels must sit min_gap apart to
        # avoid printing on top of each other near the session close.
        ylo = min(all_prices)
        yhi = max(all_prices)
        if yhi == ylo:  # single flat line — give the range a little height
            yhi = ylo + 1.0
        pad = 0.06 * (yhi - ylo)
        ylo -= pad
        yhi += pad
        min_gap = 0.055 * (yhi - ylo)

        # Highest line first, then push each label down only far enough to
        # clear the one above it (keeps the movement to a minimum).
        ends.sort(key=lambda e: e["y"], reverse=True)
        placed_y = None
        for e in ends:
            y = e["y"]
            if placed_y is not None and placed_y - y < min_gap:
                y = placed_y - min_gap
            e["label_y"] = y
            placed_y = y

        for e in ends:
            sign = "+" if e["pct"] >= 0 else ""
            fig.add_annotation(
                x=e["x"], y=e["label_y"], text=e["name"], textangle=0,
                xshift=12, yshift=9, showarrow=False,
                xanchor="left", yanchor="middle",
                font=dict(color="#111111", size=11),
            )
            fig.add_annotation(
                x=e["x"], y=e["label_y"], text=f"{sign}{e['pct']:.1f}%",
                textangle=0, xshift=12, yshift=-9, showarrow=False,
                xanchor="left", yanchor="middle",
                font=dict(color="#111111", size=11),
            )
    else:
        ylo, yhi = (min(all_prices), max(all_prices)) if all_prices else (0, 1)

    # Tickers whose exchange is closed during this session are not plotted;
    # say so instead of silently dropping them from the chart.
    if skipped:
        st.caption(
            "Not shown — trades outside this session: "
            + ", ".join(skipped)
        )

    # Extremely light zone over the remaining session time + dashed 'now' line.
    # Kept intentionally subtle (low opacity) so the focus stays on the lines
    # and the black firm labels.
    now_n = pd.Timestamp.now(tz=tz_name).tz_localize(None)
    if session_open_n <= now_n < session_close_n:
        fig.add_vrect(
            x0=now_n, x1=session_close_n, fillcolor="#f4f6f8", opacity=0.55,
            line_width=0, layer="below",
        )
        fig.add_vline(
            x=now_n, line_dash="dot", line_color="#cfd6de", line_width=1,
            opacity=0.7, layer="below",
        )

    # Crisp axes, matching the old minimal look: no frame/box, only the light
    # horizontal grid at quarter alpha, an hourly x-axis and a slight tail on
    # the right so the final labels have room before the edge.
    fig.update_xaxes(
        range=[session_open_n, session_close_n + pd.Timedelta(minutes=12)],
        tickformat="%H:%M", dtick=3600000,
        tickfont=dict(size=11), showline=False, zeroline=False,
        tickcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(
        range=[ylo, yhi],
        tickfont=dict(size=12), showgrid=True, zeroline=False,
        gridcolor="rgba(0,0,0,0.25)",
    )
    fig.update_layout(
        dragmode=False, hovermode=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=20, t=20, b=40),
        height=640,
        font=dict(family=("Source Sans Pro, Helvetica Neue, Arial, "
                          "DejaVu Sans, sans-serif")),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_equity_history_chart(period, data):
    """Multi-day chart: every individual stock indexed to 100 at window start."""
    days = {"7D": 7, "30D": 30, "1Y": 366}.get(period, 366)
    cutoff = data["Date"].max() - pd.Timedelta(days=days)

    fig = go.Figure()  # Plotly SVG renderer → scherp, nooit wazig
    symbols = list(dict.fromkeys(data["Symbol"]))
    n_plotted = 0
    for i, sym in enumerate(symbols):
        g = data[data["Symbol"] == sym].sort_values("Date")
        g = g[g["Date"] >= cutoff]
        if len(g) < 2:
            continue
        norm = g["Close"].values / g["Close"].values[0] * 100.0
        # Centered moving average over a 6-day window: day X becomes the
        # mean of the surrounding days.
        # Using a CENTERED window (rather than a trailing one) is key — it
        # makes the line smooth by averaging the days around each point,
        # instead of always dragging behind on past values (which is what
        # made the line feel spiky / laggy).  min_periods=1 keeps the edges
        # present (no leading NaNs).
        norm = np.array(
            pd.Series(norm, index=pd.DatetimeIndex(g["Date"]))
            .rolling(window=6, center=True, min_periods=1).mean().values
        )
        # The centered window averages the first point with the days AFTER
        # it, so the leading edge is no longer exactly the starting close.
        # Pin it back to 100 so the chart always starts on the reference
        # baseline (start = 100) as intended.
        norm[0] = 100.0
        color = _EQUITY_PALETTE[n_plotted % len(_EQUITY_PALETTE)]
        fig.add_trace(go.Scatter(
            x=list(g["Date"]), y=norm, mode="lines",
            line=dict(color=color, width=2.5),
            name=f"{g['Ticker'].iloc[0]} ({sym}) · "
                 f"{_currency_label(sym)}",
            hoverinfo="skip",
        ))
        n_plotted += 1

    if n_plotted == 0:
        st.info("Geen data beschikbaar voor deze periode.")
        return

    # Baseline at the indexed start (100).
    fig.add_hline(y=100, line_dash="dash", line_color="#888888",
                  line_width=1, opacity=0.7)

    # Period-specific x spacing, matching the old matplotlib locators.
    if period == "7D":
        tickformat, dtick = "%b %d", "D2"   # every 2 days
    elif period == "30D":
        tickformat, dtick = "%b %d", "W1"   # weekly
    else:
        tickformat, dtick = "%b '%y", "M2"  # every 2 months

    fig.update_xaxes(
        tickformat=tickformat, dtick=dtick,
        tickfont=dict(size=11), showline=False, zeroline=False,
        tickcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(
        tickfont=dict(size=12), showgrid=True, zeroline=False,
        gridcolor="rgba(0,0,0,0.25)",
    )
    fig.update_layout(
        dragmode=False, hovermode=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=20, t=20, b=70),
        height=640,
        font=dict(family=("Source Sans Pro, Helvetica Neue, Arial, "
                          "DejaVu Sans, sans-serif")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.18,
                    xanchor="center", x=0.5, font=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_equity_returns_table(cluster_key, period):
    """Returns table: Stock | Symbol | 1D | 7D | 30D | 1Y per member.

    De 1D-kolom komt (in de 1D-view) uit de live intraday-feed (3 min cache):
    laatste prijs vandaag vs. slotkoers van de vorige handelsdag — zo staat
    er dezelfde beweging als op Yahoo.  7D/30D/1Y komen uit de daghistorie.
    """
    df = get_equity_stock_data(cluster_key)
    if df.empty:
        st.info("Geen dagdata beschikbaar voor de returns-tabel.")
        return

    # Laatste verhandelde prijs per ticker uit de live intraday-feed.
    live = {}
    if period == "1D":
        for m in get_intraday_stock_data().get(cluster_key, []):
            d = m.get("data")
            if d is not None and not d.empty:
                live[m["ticker"]] = (
                    d["Close"].iloc[-1],
                    d["Date"].iloc[-1].normalize(),
                )

    def fmt(x):
        if x is None or pd.isna(x):
            return "n/a"
        return f"{x:+.1f}%"

    rows_out = []
    for sym, g in df.groupby("Symbol"):
        g = g.sort_values("Date").reset_index(drop=True)
        if len(g) < 2:
            continue
        close = g["Close"]

        def ret(days):
            target = g["Date"].iloc[-1] - pd.Timedelta(days=days)
            prior = g[g["Date"] <= target]
            if prior.empty:
                return None
            base = prior["Close"].iloc[-1]
            if not base:
                return None
            return (close.iloc[-1] / base - 1) * 100

        # 1D: live prijs vs. vorige slotkoers; val terug op dagbars als de
        # intraday-feed (nog) geen bars heeft (bijv. vóór beursopen).
        r1d = None
        if sym in live:
            last_px, last_day = live[sym]
            prior = g[g["Date"] < last_day]
            if not prior.empty and prior["Close"].iloc[-1]:
                r1d = (last_px / prior["Close"].iloc[-1] - 1) * 100
        if r1d is None:
            r1d = ret(2)  # previous trading day (weekend-safe)

        rows_out.append({
            "Stock": g["Ticker"].iloc[0],
            "Symbol": sym,
            "1D": r1d,
            "7D": ret(7),
            "30D": ret(30),
            "1Y": ((close.iloc[-1] / close.iloc[0] - 1) * 100
                   if close.iloc[0] else None),
        })

    out = pd.DataFrame(rows_out)
    for c in ["1D", "7D", "30D", "1Y"]:
        out[c] = out[c].map(fmt)
    st.dataframe(out, use_container_width=True, hide_index=True)


def render_stock_chart(companies=None):
    """Equity Markets — regional drill-down: pick a region + period and inspect
    the individual stocks driving that region's performance.

    1D shows a live intraday chart at actual ticker prices; 7D/30D/1Y plot
    each stock indexed to 100 at the start of the selected window. A returns
    table (Stock | Symbol | 1D | 7D | 30D | 1Y) sits below the chart.
    """
    cluster_keys = list(STOCK_CLUSTERS.keys())
    # Ruimte tussen de ranking charts hierboven en de bullet-selector
    st.markdown("<div style='height:36px;'></div>", unsafe_allow_html=True)
    region_key = st.radio(
        "Cluster",
        cluster_keys,
        format_func=lambda k: STOCK_CLUSTERS[k]["label"],
        index=0,
        horizontal=True,
        key="equity_cluster_radio",
        label_visibility="collapsed",
    )
    period = st.radio(
        "Period",
        ["1D", "7D", "30D", "1Y"],
        index=0,  # default 1D (live intraday)
        horizontal=True,
        key="equity_period_radio",
        label_visibility="collapsed",
    )

    if period == "1D":
        st.markdown(
            "<p style='text-align:right;'>🔴 <b>MARKET DATA · DELAYED</b></p>",
            unsafe_allow_html=True)
        intraday = get_intraday_stock_data()
        region_rows = intraday.get(region_key, [])
        # Real "updated" time = newest 5-minute bar actually received.
        stamps = []
        for m in region_rows:
            d = pd.to_datetime(m["data"]["Date"], utc=True)
            if not d.empty:
                stamps.append(d.max())
        if stamps:
            latest_bar = max(stamps).tz_convert("America/New_York")
            tz_name = {"America/New_York": "ET"}.get(latest_bar.tz.key, "ET")
            st.markdown(
                "<p style='text-align:right; color:#6b7280; font-size:12px;'>"
                f"Updated {latest_bar.strftime('%H:%M')} {tz_name}</p>",
                unsafe_allow_html=True)
        _render_intraday_chart(region_rows)
    else:
        # 7D / 30D / 1Y: 1-hour bars smoothed with EWMA (span=12), so the line
        # reflects real intraday movement and reads as a clean trend line.
        days = {"7D": 7, "30D": 30, "1Y": 365}.get(period, 7)
        data = get_equity_intraday_window_data(region_key, days)
        if data.empty:
            st.info("Geen data beschikbaar voor deze regio.")
            return
        _render_equity_history_chart(period, data)

    # Returns-tabel standaard ingeklapt om de grafiek niet te overheersen.
    with st.expander("Returns", expanded=False):
        track_expander_open("Returns")
        _render_equity_returns_table(region_key, period)


def render_lithium_futures():
    """Lithium-prij sectie in twee kolommen.

    Linkerkolom  : "Lithium Price" (huidige/verleden prijs — data volgt later).
    Rechterkolom : "Lithium Futures" — live gescrapede term-structure
                   (metal.com via Playwright, 1 uur cache).
    """
    result = get_lithium_futures()
    contracts = (result or {}).get("contracts", [])
    updated = (result or {}).get("updated")
    if not contracts:
        st.info("Lithium futures couldn't be loaded.")
        return

    from Futures import make_chart_plotly

    fig = make_chart_plotly(contracts)
    if fig is None:
        st.info("Lithium futures couldn't be loaded.")
        return

    # Titel per kolom (zelfde opmaak als de "Google Trends"-subheader).
    col_price, col_futures = st.columns(2)

    with col_price:
        st.subheader("Lithium Price")
        df_spot, spot = get_lithium_spot_history()
        if df_spot is None or spot.get("price") is None:
            st.info("Lithium price couldn't be loaded.")
        else:
            # Prijs + change (groen/rood, zelfde stijl als de futures-change)
            kleur = "#1a7f37" if (spot["change_usd"] or 0) >= 0 else "#d1242f"
            pct = spot["change_percent"]
            chg = spot["change_usd"]
            # Zelfde format als de futures-regel:
            # "<prijs> · 1d change +x.x% · <periode>"
            datum_kort = pd.to_datetime(spot["date"]).strftime("%b %d '%y")
            st.markdown(
                f"<p style='font-weight:400; font-size:14px; font-family:\"Segoe UI\", \"Helvetica Neue\", Arial, sans-serif; letter-spacing:0.3px;'>"
                f"<b style='color:#374151; font-size:18px;'>${spot['price']:,.2f}</b>"
                f" &nbsp;·&nbsp; 1d change "
                f"<span style='color:{kleur};'>"
                f"{('%+.1f%%' % float(pct)) if pct not in (None, '') else ''}"
                f"{(' (%+.2f)' % float(chg)) if chg is not None else ''}</span>"
                f" &nbsp;·&nbsp; <span style='color:#9ca3af;'>{datum_kort}</span></p>",
                unsafe_allow_html=True,
            )

    with col_futures:
        st.subheader("Lithium Futures")
        from Futures import day_change, contract_to_month
        change = day_change(contracts)
        if change is not None:
            front_month = contract_to_month(contracts[0]["contract"])
            kleur = "#1a7f37" if change >= 0 else "#d1242f"
            _diff = contracts[0]["latest"] - contracts[0]["open"]
            _sign = "+" if _diff >= 0 else "-"
            st.markdown(
                f"<p style='font-weight:400; font-size:14px; font-family:\"Segoe UI\", \"Helvetica Neue\", Arial, sans-serif; letter-spacing:0.3px; margin-top:0;'>"
                f"<b style='color:#374151; font-size:18px;'>¥{contracts[0]['latest']:,.0f}</b>"
                f" &nbsp;·&nbsp; 1d change <span style='color:{kleur};'>{change:+.1f}% ({_sign}¥{abs(_diff):,.0f})</span>"
                f" &nbsp;·&nbsp; <span style='color:#9ca3af;'>{front_month}</span></p>",
                unsafe_allow_html=True,
            )

        # 10M outlook boven de grafiek, links uitgelijnd met de prijsregel.
        from Futures import forward_12m
        fwd = forward_12m(contracts)
        if fwd:
            pct, horizon, _front_lbl, _target_lbl = fwd
            kleur_fwd = "#1a7f37" if pct >= 0 else "#d1242f"
            st.markdown(
                f"<p style='font-weight:400; font-size:14px; font-family:\"Segoe UI\", \"Helvetica Neue\", Arial, sans-serif; letter-spacing:0.3px;'>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{horizon} months change <span style='color:{kleur_fwd};'>{pct:+.1f}%</span></p>",
                unsafe_allow_html=True,
            )

        # Plotly rendert als vector → de datums/CNY-waarden zijn net zo
        # scherp als de HTML-tekst erboven (geen raster zoals matplotlib).
        st.plotly_chart(fig, use_container_width=True)

def render_comparison_snapshot(companies):
    """A compact 'at-a-glance' summary of the selected companies.

    Combines stock, financial, study, and search metrics into one table.
    """
    import pandas as pd
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

    st.caption("All values are the latest available per company. Some rows may be missing data.")





def render_project_studies(companies=None):
    """Render the project study evolution section (single or comparison)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    is_compare = len(companies) > 1

    if is_compare:
        st.subheader("Project Study Comparison")
        st.session_state.pop("studies_detail_ratios", None)
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

        # Track tab clicks
        track_tab_click("Economics")
        track_tab_click("Resource & Grade")
        track_tab_click("All Data")

        with tab1:
            st.subheader("Value Ratios")
            ratio_data = df_studies[df_studies['AfterTax_NPV_M'].notna()].copy()
            mc_data = get_market_cap_data([company])

            if not ratio_data.empty and not mc_data.empty:
                merged = pd.merge(
                    ratio_data[['Stage_Display', 'Date', 'AfterTax_NPV_M', 'Initial_Capex_M']],
                    mc_data[['Stage_Display', 'MarketCap_M', 'Shares_M', 'Stock_Price']],
                    on='Stage_Display', how='inner'
                ).dropna(subset=['MarketCap_M'])

                if not merged.empty:
                    # Calculate ratios
                    merged['NPV_MarketCap'] = merged['AfterTax_NPV_M'] / merged['MarketCap_M']
                    merged['NPV_CAPEX'] = merged['AfterTax_NPV_M'] / merged['Initial_Capex_M']
                    merged['NPV_per_Share'] = merged['AfterTax_NPV_M'] / merged['Shares_M']

                    # Melt for compact chart
                    ratio_melted = merged.melt(
                        id_vars=['Stage_Display', 'Date'],
                        value_vars=['NPV_MarketCap', 'NPV_CAPEX', 'NPV_per_Share'],
                        var_name='Ratio',
                        value_name='Value'
                    )
                    ratio_melted['Ratio'] = ratio_melted['Ratio'].map({
                        'NPV_MarketCap': 'NPV / Mkt Cap',
                        'NPV_CAPEX': 'NPV / CAPEX',
                        'NPV_per_Share': 'NPV / Share'
                    })

                    # Date-based x-axis: exact same time window + year ticks
                    # as the Milestone Tracker / YT Videos below, so the study
                    # results line up 1-on-1 with those charts' dates.
                    x_domain, year_ticks = _milestone_x_domain([company])

                    # Universal y-scale (0 → max) shared by ALL three panels,
                    # so the ratio values are directly comparable and the axis
                    # numbers on the right are identical for every panel.
                    y_max = float(ratio_melted['Value'].max()) if not ratio_melted.empty else 1.0
                    y_domain = [0, y_max * 1.08]

                    # Faceted chart on a shared date axis — each ratio has its
                    # own y-scale. `point` overlay is required so companies with
                    # only ONE study stage still show a visible marker.
                    # Build as 3 stacked panels (vconcat) with the ratio name as
                    # a rotated y-axis title: that keeps the plot area as wide
                    # as the YT Videos / Milestone Tracker charts below (a row
                    # facet would reserve ~100px for left header labels).
                    # Explicit same x-domain + ticks on every panel so the dates
                    # line up 1-on-1 across panels AND with the charts below.
                    def _ratio_panel(ratio_label, show_x_labels=True):
                        x_axis_kwargs = dict(format='%b %Y',
                                             grid=True,
                                             gridColor='#ECECEC',
                                             gridDash=[3, 3],
                                             values=year_ticks,
                                             labelFontSize=12)
                        if not show_x_labels:
                            # Top panels: hide date labels (shown once at the
                            # bottom panel) but keep the identical axis/ticks
                            # so all panels stay aligned with each other and
                            # with the charts below.
                            x_axis_kwargs.update(labels=False, ticks=False, grid=False)
                        return alt.Chart(
                            ratio_melted[ratio_melted['Ratio'] == ratio_label]
                        ).mark_line(
                            strokeWidth=2,
                            color=COMPANIES[company]['color'],
                            point=alt.OverlayMarkDef(
                                size=42, filled=True, stroke='white', strokeWidth=1
                            )
                        ).encode(
                            x=alt.X('Date:T',
                                    title=None,
                                    axis=alt.Axis(**x_axis_kwargs),
                                    scale=alt.Scale(zero=False, domain=x_domain)
                                    if x_domain else alt.Scale(zero=False)),
                            y=alt.Y('Value:Q',
                                    title=None,
                                    scale=alt.Scale(zero=True, domain=y_domain),
                                    axis=alt.Axis(labelFontSize=11,
                                                  format='.1f',
                                                  grid=True,
                                                  gridColor='#ECECEC',
                                                  gridDash=[3, 3],
                                                  orient='right')),
                            tooltip=[
                                alt.Tooltip('Stage_Display:N', title='Study'),
                                alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
                                alt.Tooltip('Value:Q', title='Value', format='.2f')
                            ]
                        ).properties(
                            height=96,
                            # Ratio name as a horizontal, right-aligned title
                            # ABOVE the panel: readable without tilting your
                            # head and no overlap with the axis numbers.
                            title=alt.TitleParams(
                                ratio_label,
                                anchor='end',
                                fontSize=13,
                                fontWeight='bold',
                                dy=-4,
                            )
                        )

                    chart = alt.vconcat(
                        _ratio_panel('NPV / Mkt Cap', show_x_labels=False),
                        _ratio_panel('NPV / CAPEX', show_x_labels=False),
                        _ratio_panel('NPV / Share'),
                        spacing=6,
                    ).configure_view(stroke=None)

                    # Full width, so the dates align exactly with the
                    # Milestone Tracker and YT Videos charts below
                    st.altair_chart(chart, use_container_width=True)
                    st.caption("Values C$")

                    # Compact table — 2 decimals everywhere.
                    # The expander itself is rendered later (just above
                    # Management Due Diligence, after Quarterly Cash) via
                    # render_data_expanders(); here we only prepare + store it.
                    display_ratios = merged[['Stage_Display', 'AfterTax_NPV_M', 'Initial_Capex_M',
                                         'MarketCap_M', 'NPV_MarketCap', 'NPV_CAPEX', 'NPV_per_Share',
                                         'Stock_Price']].copy()
                    display_ratios.columns = ['Study', 'NPV ($M)', 'CAPEX ($M)', 'Mkt Cap ($M)',
                                          'NPV/MktCap (×)', 'NPV/CAPEX (×)', 'NPV/Share ($)', 'Stock Price ($)']
                    for col in display_ratios.columns:
                        if col != 'Study':
                            display_ratios[col] = display_ratios[col].apply(
                                lambda x: round(x, 2) if pd.notna(x) else x
                            )
                    st.session_state["studies_detail_ratios"] = (company, display_ratios)
                else:
                    st.info("No market cap data available for studies.")
        with tab2:
            st.subheader("Resource & Grade Evolution")

            # Shared stage mapping for consistent x-axis ordering across all charts
            chart_h = 170  # Compact height matching Value Ratios proportions

            col1, col2 = st.columns(2)

            # ------------------------------------------------------------------
            # GRAPH 1: Production & Mine Life (dual-axis, thin lines, no markers)
            # ------------------------------------------------------------------
            with col1:
                st.markdown("**Production & Mine Life**")

                ops_melted = df_studies[['Stage_Display',
                                          'Avg_Annual_Production_tpa',
                                          'Life_of_Mine_Years']].copy().melt(
                    id_vars=['Stage_Display'],
                    value_vars=['Avg_Annual_Production_tpa', 'Life_of_Mine_Years'],
                    var_name='Metric',
                    value_name='Value'
                ).dropna(subset=['Value'])

                ops_melted['Metric'] = ops_melted['Metric'].map({
                    'Avg_Annual_Production_tpa': 'Production (tpa)',
                    'Life_of_Mine_Years': 'Mine Life (years)'
                })
                ops_melted['Stage_Short'] = ops_melted['Stage_Display'].map(STAGE_SHORT_MAP)

                base_ops = alt.Chart(ops_melted).encode(
                    x=alt.X('Stage_Short:N',
                            title=None,
                            sort=STAGE_ORDER,
                            axis=alt.Axis(labelFontSize=10, labelFontWeight='bold', titlePadding=8))
                )

                production_line = base_ops.transform_filter(alt.datum.Metric == 'Production (tpa)').mark_line(
                    strokeWidth=2,
                    point=alt.OverlayMarkDef(
                        size=36, filled=True, stroke='white', strokeWidth=1
                    )
                ).encode(
                    y=alt.Y('Value:Q', title='Production (tpa)', scale=alt.Scale(zero=False),
                            axis=alt.Axis(labelFontSize=9)),
                    color=alt.Color('Metric:N',
                                    scale=alt.Scale(domain=['Production (tpa)', 'Mine Life (years)'],
                                                  range=['#2E86C1', '#F39C12']),
                                    legend=alt.Legend(orient="bottom", title=None)),
                    tooltip=[
                        alt.Tooltip('Stage_Display:N', title='Study'),
                        alt.Tooltip('Metric:N', title='Metric'),
                        alt.Tooltip('Value:Q', title='Production (tpa)', format=',.0f')
                    ]
                )

                mine_life_line = base_ops.transform_filter(alt.datum.Metric == 'Mine Life (years)').mark_line(
                    strokeWidth=2,
                    point=alt.OverlayMarkDef(
                        size=36, filled=True, stroke='white', strokeWidth=1
                    )
                ).encode(
                    y=alt.Y('Value:Q', title='Mine Life (years)', scale=alt.Scale(zero=False),
                            axis=alt.Axis(labelFontSize=9)),
                    color=alt.Color('Metric:N',
                                    scale=alt.Scale(domain=['Production (tpa)', 'Mine Life (years)'],
                                                  range=['#2E86C1', '#F39C12']),
                                    legend=alt.Legend(orient="bottom", title=None)),
                    tooltip=[
                        alt.Tooltip('Stage_Display:N', title='Study'),
                        alt.Tooltip('Metric:N', title='Metric'),
                        alt.Tooltip('Value:Q', title='Mine Life (years)', format='.0f')
                    ]
                )

                st.altair_chart(
                    alt.layer(production_line, mine_life_line)
                       .resolve_scale(y='independent')
                       .resolve_legend(color='shared')
                       .properties(height=chart_h),
                    use_container_width=True
                )

            # ------------------------------------------------------------------
            # GRAPH 2: Grade & Recovery (dual-axis, thin lines, no markers)
            # ------------------------------------------------------------------
            with col2:
                st.markdown("**Grade & Recovery**")

                gr_melted = df_studies[['Stage_Display',
                                          'Average_Lithium_Grade',
                                          'Metallurgical_Recovery_%']].copy().melt(
                    id_vars=['Stage_Display'],
                    value_vars=['Average_Lithium_Grade', 'Metallurgical_Recovery_%'],
                    var_name='Metric',
                    value_name='Value'
                ).dropna(subset=['Value'])

                gr_melted['Metric'] = gr_melted['Metric'].map({
                    'Average_Lithium_Grade': 'Grade (ppm)',
                    'Metallurgical_Recovery_%': 'Recovery (%)'
                })
                gr_melted['Stage_Short'] = gr_melted['Stage_Display'].map(STAGE_SHORT_MAP)

                base_gr = alt.Chart(gr_melted).encode(
                    x=alt.X('Stage_Short:N',
                            title=None,
                            sort=STAGE_ORDER,
                            axis=alt.Axis(labelFontSize=10, labelFontWeight='bold', titlePadding=8))
                )

                grade_line = base_gr.transform_filter(alt.datum.Metric == 'Grade (ppm)').mark_line(
                    strokeWidth=2,
                    point=alt.OverlayMarkDef(
                        size=36, filled=True, stroke='white', strokeWidth=1
                    )
                ).encode(
                    y=alt.Y('Value:Q', title='Grade (ppm)', scale=alt.Scale(zero=False),
                            axis=alt.Axis(labelFontSize=9)),
                    color=alt.Color('Metric:N',
                                    scale=alt.Scale(domain=['Grade (ppm)', 'Recovery (%)'],
                                                  range=['#2E86C1', '#F39C12']),
                                    legend=alt.Legend(orient="bottom", title=None)),
                    tooltip=[
                        alt.Tooltip('Stage_Display:N', title='Study'),
                        alt.Tooltip('Metric:N', title='Metric'),
                        alt.Tooltip('Value:Q', title='Grade (ppm)', format=',.0f')
                    ]
                )

                recovery_line = base_gr.transform_filter(alt.datum.Metric == 'Recovery (%)').mark_line(
                    strokeWidth=2,
                    point=alt.OverlayMarkDef(
                        size=36, filled=True, stroke='white', strokeWidth=1
                    )
                ).encode(
                    y=alt.Y('Value:Q', title='Recovery (%)', scale=alt.Scale(zero=False),
                            axis=alt.Axis(labelFontSize=9)),
                    color=alt.Color('Metric:N',
                                    scale=alt.Scale(domain=['Grade (ppm)', 'Recovery (%)'],
                                                  range=['#2E86C1', '#F39C12']),
                                    legend=alt.Legend(orient="bottom", title=None)),
                    tooltip=[
                        alt.Tooltip('Stage_Display:N', title='Study'),
                        alt.Tooltip('Metric:N', title='Metric'),
                        alt.Tooltip('Value:Q', title='Recovery (%)', format='.1f')
                    ]
                )

                st.altair_chart(
                    alt.layer(grade_line, recovery_line)
                       .resolve_scale(y='independent')
                       .resolve_legend(color='shared')
                       .properties(height=chart_h),
                    use_container_width=True
                )

            # ------------------------------------------------------------------
            # ROW 2: M&I & Inferred (shared Mt scale)
            # ------------------------------------------------------------------
            col1, col2 = st.columns(2)

            # ------------------------------------------------------------------
            # GRAPH 3: M&I & Inferred
            # ------------------------------------------------------------------
            with col1:
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
                    strokeWidth=2,
                    point=alt.OverlayMarkDef(
                        size=36, filled=True, stroke='white', strokeWidth=1
                    )
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
            all_studies[['Company', 'Stage_Display', 'Date', 'AfterTax_NPV_M', 'Initial_Capex_M']],
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

            # Long format + shared time window & universal y-scale, so the
            # compare panels use exactly the same date axis and 0→max scale
            # as the single-company Value Ratios chart.
            ratio_melted_c = value_compare.melt(
                id_vars=['Company', 'Date'],
                value_vars=['NPV/Mkt Cap', 'NPV/CAPEX', 'NPV/Share'],
                var_name='Ratio',
                value_name='Value'
            ).dropna(subset=['Value'])

            x_domain_c, year_ticks_c = _milestone_x_domain(companies)
            y_max_c = float(ratio_melted_c['Value'].max()) if not ratio_melted_c.empty else 1.0
            y_domain_c = [0, y_max_c * 1.08]

            def _compare_panel(ratio_label, show_x_labels=True, show_legend=True):
                x_axis_kwargs = dict(format='%b %Y',
                                     grid=True,
                                     gridColor='#ECECEC',
                                     gridDash=[3, 3],
                                     values=year_ticks_c,
                                     labelFontSize=12)
                if not show_x_labels:
                    x_axis_kwargs.update(labels=False, ticks=False, grid=False)
                return alt.Chart(
                    ratio_melted_c[ratio_melted_c['Ratio'] == ratio_label]
                ).mark_line(
                    strokeWidth=2,
                    point=alt.OverlayMarkDef(size=30, filled=True, stroke='white', strokeWidth=1)
                ).encode(
                    x=alt.X('Date:T',
                            title=None,
                            axis=alt.Axis(**x_axis_kwargs),
                            scale=alt.Scale(zero=False, domain=x_domain_c)
                            if x_domain_c else alt.Scale(zero=False)),
                    y=alt.Y('Value:Q',
                            title=None,
                            scale=alt.Scale(zero=True, domain=y_domain_c),
                            axis=alt.Axis(labelFontSize=11,
                                          format='.1f',
                                          grid=True,
                                          gridColor='#ECECEC',
                                          gridDash=[3, 3],
                                          orient='right')),
                    color=alt.Color('Company:N',
                                    scale=alt.Scale(domain=list(color_scale.keys()),
                                                    range=list(color_scale.values())),
                                    legend=alt.Legend(orient='bottom', title=None, labelFontSize=10)
                                    if show_legend else None),
                    tooltip=[
                        alt.Tooltip('Company:N', title='Company'),
                        alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
                        alt.Tooltip('Value:Q', title=ratio_label, format='.2f')
                    ],
                ).properties(
                    height=96,
                    title=alt.TitleParams(
                        ratio_label,
                        anchor='end',
                                fontSize=13,
                        fontWeight='bold',
                        dy=-4,
                    )
                )

            chart_c = alt.vconcat(
                _compare_panel('NPV/Mkt Cap', show_x_labels=False, show_legend=False),
                _compare_panel('NPV/CAPEX', show_x_labels=False, show_legend=False),
                _compare_panel('NPV/Share'),
                spacing=6,
            ).configure_view(stroke=None)
            st.altair_chart(chart_c, use_container_width=True)
        else:
            st.info("No market cap data available for the selected companies.")
    else:
        st.info("No market cap data available.")

    # ------------------------------------------------------------------
    # 2. Comparison charts (multi-line overlays)
    # ------------------------------------------------------------------
    st.markdown("**Study Metrics Over Time — Company Comparison**")

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

    st.caption("Only companies with study data are shown. Data for additional companies is added continuously.")





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
            track_expander_open("Additional study details")
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

        st.caption("Source: Company technical reports and studies (public filings)")
    else:
        st.info("No study data available")





def render_search_analysis(companies=None):
    """Google Trends section: drie trends-graphs naast elkaar (links naar
    rechts), één per zoekterm uit Sentiment.py. Boven elke graph staat de
    zoekterm als label (zelfde format als het 'Google Trends' label,
    met eigen lettertype en grootte)."""
    from Sentiment import (
        ZOEKTERMEN, LABEL_STYLE, fetch_trends_data, build_trends_figure,
        get_7d_change,
    )

    cols = st.columns(len(ZOEKTERMEN))

    for col, term in zip(cols, ZOEKTERMEN):
        with col:
            # Zoekterm als label boven de graph (lettertype + grootte vastgelegd in LABEL_STYLE)
            st.markdown(
                f"<p style='{LABEL_STYLE} margin-bottom:0.25rem;'>\"{term}\"</p>",
                unsafe_allow_html=True,
            )

            data = fetch_trends_data(term)
            if data is None:
                st.info("Google Trends data temporarily unavailable (rate limited) — try again in a minute.")
                continue

            fig = build_trends_figure(term, data)
            # Plotly rendert als vector → haarscherp, net als de rest van de app.
            st.plotly_chart(fig, use_container_width=True)

            # 7d change onder de graph (groen bij stijging, rood bij daling)
            change = get_7d_change(term)
            if change is not None:
                kleur = "#1a7f37" if change >= 0 else "#d1242f"
                st.markdown(
                    f"<p style='font-weight:400; font-size:14px; font-family:\"Segoe UI\", \"Helvetica Neue\", Arial, sans-serif; letter-spacing:0.3px; color:{kleur}; margin-top:0;'>"
                    f"7d change: {change:+.1f}%</p>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption("7d change: Niet genoeg data")


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

        question = st.text_input("Ask a question about the company (min. 10 characters)", key="qa_question_input")

        col1, col2 = st.columns([1, 5])
        with col1:
            submitted = st.button("Submit question", key="qa_submit_button")

        if submitted and question:
            if len(question) < 10:
                st.warning("Could you add a bit more detail? Please use at least 10 characters.")
            else:
                track_qa_submit()
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
            track_qa_like()
            st.session_state.qa[i]["likes"] += 1

        if item["answer"]:
            st.write(f"**{qa_company}:** {item['answer']}")
        else:
            answer = st.text_input("", value="...", key=f"answer_{i}", label_visibility="collapsed")
            if answer and answer != "...":
                st.session_state.qa[i]["answer"] = answer
                st.rerun()

        st.markdown("")


_LITHIUM_KEY = {
    # sidebar name in COMPANIES  ->  key in lithium_companies
    "American Battery Technology Co": "American Battery",
    "Surge Battery Metals": "Surge Battery",
    "American Lithium Corp": "American Lithium",
}


def render_cash_overview(companies=None):
    """Render the quarterly cash overview: a cash chart plus a compact
    table (Quarter, Cash) for every selected company."""
    if companies is None:
        companies = list(COMPANIES.keys())

    # Map selected companies to their lithium_companies entry (skip if absent)
    available = []
    for c in companies:
        key = _LITHIUM_KEY.get(c, c)
        entry = lithium_companies.get(key)
        if entry and entry.get("data"):
            available.append({"company": c, "key": key, "entry": entry})

    if not available:
        st.warning("No quarterly cash data available for the selected companies.")
        return

    is_compare = len(available) > 1
    st.subheader("Quarterly Cash Overview" + (" — Side by Side" if is_compare else ""))

    currencies = sorted({a["entry"]["currency"] for a in available})
    shared_currency = currencies[0] if len(currencies) == 1 else None

    # Expected-cash-runway basis: the data carries two variants (trailing
    # 2-quarter and trailing 4-quarter average underlying burn). Let the
    # user pick which one(s) get drawn on the secondary axis.
    runway_label_to_mode = {
        "Both (2Q & 4Q)": "both",
        "Trailing 2Q avg": "2q",
        "Trailing 4Q avg": "4q",
    }
    has_runway_variants = any(
        {"runway_2q", "runway_4q"} & set(pd.DataFrame(a["entry"]["data"]).columns)
        for a in available
    )
    runway_mode = "both"
    if has_runway_variants:
        runway_label = st.radio(
            "Runway basis",
            list(runway_label_to_mode.keys()),
            index=1,  # default: Trailing 2Q avg runway basis
            horizontal=True,
            help="Expected cash runway in months, computed with the average "
                 "underlying cash burn over the trailing 2 or 4 quarters.",
        )
        runway_mode = runway_label_to_mode[runway_label]

    def build_cash_chart(entries_list, currency, runway_mode="both"):
        """Line chart of the cash position per quarter, extended with the
        financing raised per quarter (bars, only where money was actually
        raised) and the expected cash runway in months on a secondary
        right-hand axis. Two runway variants are supported:
        runway_2q (trailing 2-quarter avg underlying burn) and runway_4q
        (trailing 4-quarter avg); runway_mode picks which to draw.
        The y-axis names the actual currency (USD/CAD)."""
        fig = go.Figure()
        for a in entries_list:
            c = a["company"]
            df = pd.DataFrame(a["entry"]["data"])
            display_name = COMPANIES[c]["short_name"]
            color = COMPANIES[c]["color"]

            # --- Cash position (primary line, left axis) ------------------
            fig.add_trace(go.Scatter(
                x=df["quarter"],
                y=df["cash"],
                mode="lines+markers",
                name="Cash",
                legendgroup=display_name,
                line=dict(color=color, width=2.5),
                marker=dict(size=9),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{display_name} Cash<br>"
                    f"{currency} <b>%{{y:,.2f}}M</b>"
                    "<extra></extra>"
                ),
            ))

            # --- Financing raised (bars, only quarters with a raise) ------
            fin = df[df["financing"].fillna(0) > 0]
            if not fin.empty:
                fig.add_trace(go.Bar(
                    x=fin["quarter"],
                    y=fin["financing"],
                    name="Financing",
                    legendgroup=display_name,
                    marker=dict(color=color, opacity=0.40),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"{display_name} Financing<br>"
                        f"{currency} <b>%{{y:,.2f}}M</b> raised"
                        "<extra></extra>"
                    ),
                ))

            # --- Expected cash runway (months, secondary right axis) ------
            def _add_runway(col, label, dash_style, symbol, basis_text=None, line_color=None):
                if col not in df.columns:
                    return
                # basis_text explains the runway methodology, e.g.
                # "Estimated Cash Runway Calculated on Cash Burn of Last 2
                # Quartals" for the 2Q variant (which starts at 2024 Q2) and
                # "...Last 4 Quartals" for the 4Q variant (starts at 2024 Q4).
                basis_line = f"<i>{basis_text}</i><br>" if basis_text else ""
                fig.add_trace(go.Scatter(
                    x=df["quarter"],
                    y=df[col],
                    mode="lines+markers",
                    name=f"Runway {label}".strip(),
                    legendgroup=display_name,
                    yaxis="y2",
                    line=dict(color=line_color or color, width=1.8, dash=dash_style),
                    marker=dict(size=6, symbol=symbol, color=line_color or color),
                    connectgaps=False,   # gap where history is insufficient (None)
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"{display_name} – Estimated Cash Runway<br>"
                        f"{basis_line}"
                        "<b>%{y:,.1f}</b> months left"
                        "<extra></extra>"
                    ),
                ))

            if "runway_2q" in df.columns or "runway_4q" in df.columns:
                # New schema: trailing-average underlying burn variants.
                if runway_mode in ("both", "2q"):
                    _add_runway("runway_2q", "(2Q)", "dot", "diamond",
                                "Calculated on cash burn of last 2 quarters",
                                line_color="#7F8C8D")
                if runway_mode in ("both", "4q"):
                    _add_runway("runway_4q", "(4Q)", "dash", "cross",
                                "Calculated on cash burn of last 4 quarters",
                                line_color="#7F8C8D")
            elif "runway" in df.columns:
                # Legacy fallback: single pre-computed runway column.
                _add_runway("runway", "", "dot", "diamond", line_color="#7F8C8D")

        # Size the top margin to the horizontal legend so it never overlaps
        # the chart title. Plotly wraps legend items (~2 per row); reserve
        # roughly 24px per legend row + a fixed slot for the title itself.
        legend_rows = max(1, -(-len(fig.data) // 2))  # ceil(items / 2)
        top_margin = 75 + legend_rows * 24

        fig.update_layout(
            title=dict(
                text="Cash Position by Quarter",
                x=0,
                xanchor="left",
                y=0.98,
                yanchor="top",
                font=dict(weight="normal")
            ),
            yaxis_title=f"Cash ({currency} millions)",
            template="plotly_white",
            height=420,
            margin=dict(t=top_margin),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                        itemclick=False, itemdoubleclick=False),
        )
        # Secondary axis for the runway (months) on the right-hand side.
        fig.update_layout(
            yaxis2=dict(
                title=dict(text="Runway (months)"),
                overlaying="y",
                side="right",
                showgrid=False,
            )
        )
        return fig

    if shared_currency:
        # All companies report in the same currency: one combined chart with
        # that currency (USD or CAD) on the y-axis.
        use_log = False
        if is_compare:
            use_log = st.checkbox(
                "Log scale (companies differ strongly in magnitude)",
                value=False,
                key="cash_overview_log_scale",
            )
        fig = build_cash_chart(available, shared_currency, runway_mode)
        if use_log:
            fig.update_yaxes(type="log")
        st.plotly_chart(fig, use_container_width=True)

        if is_compare:
            tab_labels = [COMPANIES[a["company"]]["short_name"] for a in available]
            tabs = st.tabs(tab_labels)
            for tab, a in zip(tabs, available):
                with tab:
                    _render_cash_table(a)
        else:
            _render_cash_table(available[0])
    else:
        # Mixed currencies (e.g. USD + CAD): a separate chart per company so
        # every y-axis shows its own currency.
        tab_labels = [COMPANIES[a["company"]]["short_name"] for a in available]
        tabs = st.tabs(tab_labels)
        for tab, a in zip(tabs, available):
            with tab:
                cur = a["entry"]["currency"]
                st.plotly_chart(build_cash_chart([a], cur, runway_mode), use_container_width=True)
                _render_cash_table(a)


def _render_cash_table(a):
    """Compact table: Quarter, Cash and Cash Burn per quarter."""
    entry = a["entry"]
    cur = entry["currency"]
    df = pd.DataFrame(entry["data"])

    # Prefer the operating burn (cash burn excluding financing) when present;
    # it is the figure that drives the runway estimates on the chart.
    if "underlying_burn" in df.columns:
        burn_col = "underlying_burn"
    elif "burn" in df.columns:
        burn_col = "burn"
    else:
        burn_col = None

    cols = ["quarter", "cash"] + ([burn_col] if burn_col else [])
    display = df[cols].copy()
    rename = {"quarter": "Quarter", "cash": "Cash"}
    if burn_col:
        rename[burn_col] = "Cash Burn"
    display = display.rename(columns=rename)

    def _fmt(v):
        if v is None:
            return ""
        try:
            return f"{float(v):,.2f}"
        except (TypeError, ValueError):
            return str(v)

    display["Cash"] = display["Cash"].apply(_fmt)
    if "Cash Burn" in display.columns:
        display["Cash Burn"] = display["Cash Burn"].apply(_fmt)

    st.dataframe(display, use_container_width=True, hide_index=True)
    st.caption(f"All amounts in {cur} millions.")


def render_financial_section(companies=None):
    """Render the side-by-side financial comparison section."""
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





def _parse_timeline_date(date_str):
    """Parse timeline date strings into datetime objects.

    Shared by the Milestone Tracker and the Interview Timeline so that
    both charts use exactly the same time window.
    """
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

    # 'Ongoing' → today, so in-progress activities are placed at the current date
    if 'ongoing' in s_lower:
        return pd.Timestamp.today()

    # Bare '<Year>' (exactly 4 digits) → end of year
    if re.fullmatch(r'\d{4}', s):
        return pd.to_datetime(f"{s}-12-31")

    # Standard datetime parse
    try:
        return pd.to_datetime(s)
    except Exception:
        pass

    # Half-year references: 'H1 2026' → end of H1, 'H2 2026' → end of H2
    h_map = {'h1': (6, 30), 'h2': (12, 31)}
    for h, (month, day) in h_map.items():
        if h in s_lower:
            m = re.search(r'(\d{4})', s)
            if m:
                return pd.to_datetime(f"{m.group(1)}-{month:02d}-{day}")

    # Quarter references: 'Q1 2019' → end of quarter
    q_map = {'q1': (3, 31), 'q2': (6, 30), 'q3': (9, 30), 'q4': (12, 31)}
    for q, (month, day) in q_map.items():
        if q in s_lower:
            m = re.search(r'(\d{4})', s)
            if m:
                return pd.to_datetime(f"{m.group(1)}-{month:02d}-{day}")

    # Month references ('Late <Month> <Year>', '<Month> <Year>') → end of month
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

    # Bare '<Year>' → end of year
    m = re.search(r'(\d{4})', s)
    if m:
        return pd.to_datetime(f"{m.group(1)}-12-31")

    return None


def _year_axis_ticks(start, end, step=2):
    """Shared x-axis ticks: Jan 1st of every `step` years.

    Used by both the Milestone Tracker and the Interview Timeline so the
    date labels sit at exactly the same horizontal position on both charts.
    """
    first_year = start.year if start.month == 1 and start.day == 1 else start.year + 1
    years = range(first_year, end.year + 1, step)
    return [pd.Timestamp(year=y, month=1, day=1) for y in years]

def _milestone_x_domain(companies):
    """Shared x-domain + year ticks derived from the Milestone Tracker dates.

    Used by the Milestone Tracker's siblings (YT Videos, Value Ratios) so all
    date-based charts sit on exactly the same horizontal time window.
    """
    milestone_dates = []
    for company in companies:
        for row in TIMELINE_DATA.get(company, []):
            for key in ('Commitment date', 'Expected date', 'Actual date'):
                parsed = _parse_timeline_date(row.get(key))
                if parsed is not None:
                    milestone_dates.append(parsed)
    if not milestone_dates:
        return None, None
    m_min, m_max = pd.Series(milestone_dates).min(), pd.Series(milestone_dates).max()
    pad = (m_max - m_min) * 0.08
    right_pad = (m_max - m_min) * 0.25
    x_domain = [(m_min - pad).to_pydatetime(), (m_max + pad + right_pad).to_pydatetime()]
    return x_domain, _year_axis_ticks(x_domain[0], x_domain[1])


def render_timeline(companies=None):
    """Render the press release / study timeline (single or comparison)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    is_compare = len(companies) > 1

    if is_compare:
        st.subheader("Milestone Tracker — Comparison")
    else:
        st.subheader("Milestone Tracker")

    # Combine timeline data for the selected companies
    all_rows = []
    for company in companies:
        for row in TIMELINE_DATA.get(company, []):
            row_copy = dict(row)
            row_copy['Company'] = company
            row_copy['Status'] = row.get('Status', 'Historical')
            all_rows.append(row_copy)

    if not all_rows:
        st.info("No timeline data available for the selected companies.")
        return

    timeline_df = pd.DataFrame(all_rows)

    # ------------------------------------------------------------------
    # Build long-format event data for the chart
    # ------------------------------------------------------------------
    parse_timeline_date = _parse_timeline_date

    event_mappings = {
        'Commitment date': 'Commitment',
        'Expected date': 'Expected',
        'Actual date': 'Actual',
    }

    # Collect all events
    event_rows = []
    for company in companies:
        for row in TIMELINE_DATA.get(company, []):
            study = row.get('Study', '')
            is_future = row.get('Status', 'Historical') == 'Future'
            for date_key, event_type in event_mappings.items():
                date = parse_timeline_date(row.get(date_key, '—'))
                if date is not None:
                    event_rows.append({
                        'Company': company,
                        'Study': study,
                        'Event_Type': 'Planned' if is_future else event_type,
                        'Status': 'Future' if is_future else 'Historical',
                        'Date': date,
                    })

    if not event_rows:
        return

    events_df = pd.DataFrame(event_rows)

    # ------------------------------------------------------------------
    # Volledige milestone-namen (geen afkortingen/codes) in de graph
    # ------------------------------------------------------------------
    FULL_STUDY_NAMES = {
        'MRE': 'Mineral Resource Estimate',
        'MRE_U': 'Mineral Resource Estimate (Update)',
        'PEA': 'Preliminary Economic Assessment',
        'PEA_U': 'Preliminary Economic Assessment (Update)',
        'PFS': 'Pre-Feasibility Study',
        'FS': 'Feasibility Study',
        'FS_U': 'Feasibility Study (Update)',
        'PoO_Submitted': 'Plan of Operations Submitted',
        'PoO_Accepted': 'Plan of Operations Accepted',
        'PoO_Approved': 'Plan of Operations Approved',
        'NEPA_Start': 'NEPA Review Started',
        'Final_EIS': 'Final Environmental Impact Statement',
        'Final_EA': 'Final Environmental Assessment',
        'Record of Decision': 'Record of Decision',
        'FID': 'Final Investment Decision',
        'FAST41_Transparency': 'FAST-41 Transparency Listing',
        'FAST41_Covered': 'FAST-41 Covered Project',
        'Fully_Permitted': 'Fully Permitted',
    }

    def _full_study(name):
        return FULL_STUDY_NAMES.get(name, name)

    events_df['Study'] = events_df['Study'].map(_full_study)

    # ------------------------------------------------------------------
    # Historical vs planned/ongoing milestones: compute the split point
    # ------------------------------------------------------------------
    planned_events = events_df[events_df['Status'] == 'Future']
    split_date = planned_events['Date'].min() if not planned_events.empty else None
    x_min_all = events_df['Date'].min()
    x_max_all = events_df['Date'].max()

    # Sort studies for consistent y-axis ordering (volledige namen)
    study_order = [_full_study(s) for s in
                   ['MRE', 'MRE_U', 'PEA', 'PEA_U', 'PFS', 'FS', 'FS_U',
                    'PoO_Submitted', 'PoO_Accepted', 'PoO_Approved',
                    'NEPA_Start', 'Final_EIS', 'Final_EA',
                    'Record of Decision', 'FID', 'FAST41_Transparency',
                    'FAST41_Covered', 'Fully_Permitted',
                    # Upcoming / futuristic milestones (2026 and later)
                    'Pilot Operations', 'Second Recycling Facility',
                    'DOE Grant Reinstatement', 'Definitive Feasibility Study',
                    'Commercial Production (Phase 1)', 'BLM Comments on Draft PoO',
                    'Finalize Mine Plan of Operations', 'Demonstration Plant Construction',
                    'Strategic Partnering / Offtake', 'Sign MOUs with KIND & Hyundai',
                    'Final Investment Decision', 'First Commercial Production',
                    'Definitive Capital Estimate', 'Mechanical Completion (Phase 1)',
                    'Commercial Production', 'Scaled-up Leach & Separation Testing',
                    'Flowsheet Optimization', 'Defense Supply Chain Integration']]

    existing_studies = [s for s in study_order if s in events_df['Study'].unique()]
    remaining_studies = [s for s in events_df['Study'].unique() if s not in existing_studies]
    y_order = existing_studies + remaining_studies
    y_order_rev = y_order[::-1]

    colors = {'Commitment': '#F39C12', 'Expected': '#E74C3C', 'Actual': '#2E86C1', 'Planned': '#9CA3AF'}
    symbols = {'Commitment': 'diamond-open', 'Expected': 'diamond-open', 'Actual': 'circle', 'Planned': 'triangle-up-open'}
    sizes = {'Commitment': 12, 'Expected': 12, 'Actual': 14, 'Planned': 14}
    # Begrijpelijke termen voor de legenda (kort + self-explanatory).
    # De 'Expected date' is de beloofde leverdatum — vandaar 'Promised'.
    event_labels = {
        'Commitment': 'Announced',
        'Expected': 'Promised',
        'Actual': 'Delivered',
        'Planned': 'Upcoming',
    }

    fig = go.Figure()

    # Connector lines per study (Commitment → Expected → Actual)
    if is_compare:
        for company in companies:
            comp_color = COMPANIES[company]['color']
            comp_studies = events_df[events_df['Company'] == company]['Study'].unique()
            for study in comp_studies:
                study_events = events_df[
                    (events_df['Company'] == company) & (events_df['Study'] == study)
                ].sort_values('Date')
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
    else:
        for study in events_df['Study'].unique():
            study_events = events_df[events_df['Study'] == study].sort_values('Date')
            if len(study_events) >= 2:
                fig.add_trace(go.Scatter(
                    x=study_events['Date'],
                    y=[study] * len(study_events),
                    mode='lines',
                    line=dict(color='#D5D8DC', width=2, dash='dot'),
                    hoverinfo='skip',
                    showlegend=False,
                ))

    # Event markers
    if is_compare:
        for company in companies:
            comp_color = COMPANIES[company]['color']
            comp_events = events_df[events_df['Company'] == company]
            for event_type in ['Commitment', 'Expected', 'Actual', 'Planned']:
                sub = comp_events[comp_events['Event_Type'] == event_type]
                if sub.empty:
                    continue
                fig.add_trace(go.Scatter(
                    x=sub['Date'],
                    y=sub['Study'],
                    mode='markers',
                    name=f"{COMPANIES[company]['short_name']} — {event_labels.get(event_type, event_type)}",
                    marker=dict(
                        color=comp_color,
                        size=sizes.get(event_type, 11),
                        symbol=symbols.get(event_type, 'circle'),
                        line=dict(width=1.5, color='white')
                    ),
                    hovertemplate=(
                        f'<b>{company}</b><br>'
                        f'<b>%{{y}}</b><br>'
                        f'{event_labels.get(event_type, event_type)}: %{{x|%d-%m-%Y}}<extra></extra>'
                    ),
                ))
    else:
        for event_type in ['Commitment', 'Expected', 'Actual', 'Planned']:
            sub = events_df[events_df['Event_Type'] == event_type]
            if sub.empty:
                continue
            # Study-namen staan op de y-as (links); de markers hoeven dus
            # geen tekst mee te slepen — geen overlappende termen meer.
            fig.add_trace(go.Scatter(
                x=sub['Date'],
                y=sub['Study'],
                mode='markers',
                name=event_labels.get(event_type, event_type),
                marker=dict(
                    color=colors.get(event_type, '#95A5A6'),
                    size=sizes.get(event_type, 11),
                    symbol=symbols.get(event_type, 'circle'),
                    line=dict(width=1.5, color='white')
                ),
                hovertemplate=(
                    f'<b>%{{y}}</b><br>'
                    f'{event_labels.get(event_type, event_type)}: %{{x|%d-%m-%Y}}<extra></extra>'
                ),
            ))

    # ------------------------------------------------------------------
    # Milestone-namen IN de graph (single view): één keer per rij, boven
    # het eerste (linker) symbool van die rij — leesbaar, zonder overlap.
    # ------------------------------------------------------------------
    if not is_compare:
        for study in y_order:
            sub = events_df[events_df['Study'] == study]
            if sub.empty:
                continue
            first = sub.sort_values('Date').iloc[0]
            fig.add_annotation(
                x=first['Date'], y=study,
                yshift=18, xshift=-6, xanchor='left',
                text=study,
                showarrow=False,
                font=dict(size=12, color='#2C3E50'),
            )

    # Hide y-axis labels (study names shown via markers/text and tooltips)
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
            # Single view: milestone-namen staan IN de graph (boven het
            # eerste symbool van elke rij), dus de as-labels blijven leeg.
            # Compare mode: namen wél op de as (meerdere bedrijven per rij).
            ticktext=(y_order_rev if is_compare else [''] * len(y_order_rev)),
            tickvals=[s for s in y_order_rev],
            showgrid=False,
            showticklabels=is_compare,
            automargin=True,
        ),
        xaxis=dict(
            title=None,
            tickfont=dict(size=12),
            tickformat='%b %Y',
            showgrid=False,
        ),
        margin=dict(t=60, b=10, l=20, r=100),
        plot_bgcolor='white',
        hoverlabel=dict(
            bgcolor='white',
            font_size=12,
            font_family='Arial',
        ),
    )

    # ------------------------------------------------------------------
    # Split line + shading: historical milestones (left) vs planned (right)
    # ------------------------------------------------------------------
    # Pad the x-range; add extra room on the right so the 'middle right'
    # study labels are not clipped at the plot edge.
    pad = (x_max_all - x_min_all) * 0.08
    right_pad = (x_max_all - x_min_all) * 0.25
    fig.update_xaxes(
        range=[x_min_all - pad, x_max_all + pad + right_pad],
        tickvals=_year_axis_ticks(x_min_all - pad, x_max_all + pad + right_pad),
    )

    if split_date is not None:
        fig.add_vrect(
            x0=split_date, x1=x_max_all + pad,
            fillcolor="rgba(156, 163, 175, 0.06)",
            line_width=0,
            layer="below",
        )
        fig.add_vline(
            x=split_date,
            line_dash="dash",
            line_color="#9CA3AF",
            line_width=1.5,
        )

    st.plotly_chart(fig, use_container_width=True, key="timeline_chart")

    # Show the table (grouped by company when in comparison)
    display_cols = ['Company', 'Study', 'Status', 'Commitment date', 'Expected date', 'Actual date', 'Delay']
    if not is_compare:
        display_cols = ['Study', 'Status', 'Commitment date', 'Expected date', 'Actual date', 'Delay']

    if 'Status' in timeline_df.columns:
        timeline_df['Status'] = timeline_df['Status'].map(
            lambda v: 'Planned / Ongoing' if v == 'Future' else 'Historical'
        )

    present_cols = [c for c in display_cols if c in timeline_df.columns]
    # The expander itself is rendered later (just above Management Due
    # Diligence, after Quarterly Cash) via render_data_expanders(); here
    # we only prepare + store its contents.
    st.session_state["milestone_detail"] = {
        "timeline_df": timeline_df[present_cols],
        "companies": companies,
        "is_compare": is_compare,
    }


def render_data_expanders():
    """Render the two detail expanders (studies data table + milestone
    dates/evidence) BELOW Quarterly Cash, just above Management Due
    Diligence — so they don't interrupt the aligned date-based charts."""
    detail = st.session_state.get("milestone_detail")

    # 1. Value Ratios detailed table (stored by render_studies)
    ratios = st.session_state.get("studies_detail_ratios")
    if ratios is not None:
        with st.expander("View detailed data table", expanded=False):
            track_expander_open("View detailed data table")
            st.dataframe(ratios[1], use_container_width=True, hide_index=True)

    # 3. YouTube video table (stored by render_sentiment_analysis)
    yt_table = st.session_state.get("youtube_video_table")
    if yt_table is not None:
        with st.expander("YouTube videos — show table", expanded=False):
            st.dataframe(
                yt_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "Channel": st.column_config.TextColumn("Channel", width="medium"),
                    "Duration": st.column_config.TextColumn("Duration", width="small"),
                    "Views": st.column_config.NumberColumn("Views", format="%d", width="small"),
                    "URL": st.column_config.LinkColumn("Video", display_text="Watch ▶", width="small"),
                },
            )

    # 2. Milestone dates, delays & commitment evidence (stored by render_timeline)
    if detail is not None:
        with st.expander("Dates, delays & commitment evidence", expanded=False):
            timeline_df = detail["timeline_df"]
            companies = detail["companies"]
            is_compare = detail["is_compare"]

            st.dataframe(timeline_df, use_container_width=True, hide_index=True)

            st.markdown("")  # spacing between table and evidence

            # ================================================================
            # COMMITMENT SENTENCES (in dezelfde expander)
            # ================================================================
            for company in companies:
                rows = TIMELINE_DATA.get(company, [])
                if not rows:
                    continue

                has_evidence = any(
                    r.get('Commitment Evidence', '—') != '—' or
                    r.get('Expected Evidence', '—') != '—'
                    for r in rows
                )
                if not has_evidence:
                    continue

                if is_compare:
                    st.markdown(f"#### Commitment sentences — {company}")

                for r in rows:
                    commitment_evidence = r.get('Commitment Evidence', '—')
                    expected_evidence = r.get('Expected Evidence', '—')

                    if commitment_evidence == '—' and expected_evidence == '—':
                        continue

                    study = r.get('Study', '')
                    commitment_date = r.get('Commitment date', '—')
                    expected_date = r.get('Expected date', '—')
                    actual_date = r.get('Actual date', '—')
                    delay = r.get('Delay', '—')

                    # Compact header line per milestone
                    label_parts = [f"**{study}**"]
                    if commitment_date != '—':
                        label_parts.append(f"commitment {commitment_date}")
                    if expected_date != '—':
                        label_parts.append(f"expected {expected_date}")
                    if actual_date != '—':
                        label_parts.append(f"actual {actual_date}")
                    if delay != '—':
                        label_parts.append(f"delay {delay}")
                    st.markdown(" • ".join(label_parts))

                    if commitment_evidence != '—':
                        st.markdown(f"> “{commitment_evidence}”")

                    if expected_evidence != '—':
                        st.caption(f"Expected evidence: “{expected_evidence}”")

                    st.markdown("")

                st.caption("Source: company press releases and disclosures.")


def apply_styles():
    """Custom CSS to remove visual clutter and create a cleaner look."""
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
    
    /* Tighten vertical spacing to remove large white gaps between sections */
    [data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
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

    /* Collapse dead whitespace between the studies tabs (expander) and
       the next section (Milestone Tracker): no empty spacer blocks exist
       in the code, so strip the default element margins instead. */
    [data-testid="stExpander"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    [data-testid="stTabs"] {
        margin-bottom: 0 !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-panel"] {
        padding-bottom: 0 !important;
    }

    /* GA4 tracking (streamlit_gtag) renders an invisible iframe per
       tracking call; each iframe reserves ~26px of whitespace. Collapse
       them to zero height — they are never meant to be visible. */
    iframe.stCustomComponentV1 {
        height: 0 !important;
        min-height: 0 !important;
        display: block !important;
    }
    [data-testid="stElementContainer"]:has(> div > iframe.stCustomComponentV1) {
        height: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
    }

    /* Hide the scrollbars Streamlit renders between/around Altair (Vega)
       charts (e.g. the stacked Value Ratios panels): the charts fit the
       container, the bars are dead clutter. */
    [data-testid="stArrowVegaLiteChart"] > div,
    .stAltairChart,
    [class*="vega-embed"] {
        overflow: hidden !important;
        scrollbar-width: none !important;   /* Firefox */
    }
    [data-testid="stArrowVegaLiteChart"] > div::-webkit-scrollbar,
    .stAltairChart::-webkit-scrollbar,
    [class*="vega-embed"]::-webkit-scrollbar {
        display: none !important;           /* Chrome / Edge / Safari */
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


# Alias: app.py calls render_studies (was render_project_studies)
render_studies = render_project_studies


def _parse_duration_minutes(duration_str):
    """Parse a YouTube duration string ('M:SS' or 'H:MM:SS') into minutes."""
    try:
        parts = [int(p) for p in str(duration_str).split(":")]
    except ValueError:
        return None
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours, minutes, seconds = 0, parts[0], parts[1]
    else:
        return None
    return round(hours * 60 + minutes + seconds / 60, 1)


def render_sentiment_analysis(companies=None):
    """Sentiment Analysis section (YouTube interviews & coverage over time)."""
    if companies is None:
        companies = list(COMPANIES.keys())
    is_compare = len(companies) > 1

    # ------------------------------------------------------------------
    # Collect YouTube video records for the selected companies (config.py)
    # ------------------------------------------------------------------
    rows = []
    no_data = []
    for company in companies:
        videos = YOUTUBE_VIDEOS.get(company, [])
        if not videos:
            no_data.append(company)
            continue
        for v in videos:
            rows.append({
                "Company": company,
                "Date": v["date"],
                "Title": v["title"],
                "Channel": v["channel"],
                "Duration": v["duration"],
                "Minutes": _parse_duration_minutes(v["duration"]),
                "Views": int(v["views"]),
                "URL": v["url"],
            })

    if not rows:
        st.info("No YouTube interview data available for the selected company(ies) yet.")
        st.session_state.pop("youtube_video_table", None)
        return

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date", ascending=True).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Time window: copy the Milestone Tracker's x-range exactly (same
    # min/max event dates + same padding), so both charts align 1-on-1.
    # ------------------------------------------------------------------
    x_domain, year_ticks = _milestone_x_domain(companies)

    # ------------------------------------------------------------------
    # 1. Interview timeline chart: when (x-axis) × views (y-axis),
    #    uniform blue bubbles (channel shown on hover), no gridlines.
    #    Same year ticks (Jan 1st, every 2 years) as the Milestone
    #    Tracker, so the date labels align exactly.
    # ------------------------------------------------------------------
    st.markdown("**YouTube Videos**")

    chart = (
        alt.Chart(df)
        .mark_circle(opacity=0.75, stroke="white", strokeWidth=1, size=140, color="#1F77B4")
        .encode(
            x=alt.X(
                "Date:T",
                title=None,
                axis=alt.Axis(format="%b %Y", grid=False, values=year_ticks, labelFontSize=12),
                scale=alt.Scale(zero=False, domain=x_domain) if x_domain else alt.Scale(zero=False),
            ),
            y=alt.Y("Views:Q", title="Views", scale=alt.Scale(zero=False),
                    axis=alt.Axis(grid=False, orient="right",
                                  titleAngle=0, titleAlign="right",
                                  titleFontSize=13, titleFontWeight="bold",
                                  titleX=38, titleY=-4)),
            tooltip=[
                alt.Tooltip("Date:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("Title:N", title="Title"),
                alt.Tooltip("Channel:N", title="Channel"),
                alt.Tooltip("Duration:N", title="Duration"),
                alt.Tooltip("Views:Q", title="Views", format=","),
            ],
        )
        .properties(height=340)
    )
    st.altair_chart(chart, use_container_width=True)

    # ------------------------------------------------------------------
    # 2. Video table (newest first) — collapsible detail.
    #    The expander itself is rendered later (just above Management Due
    #    Diligence, after Quarterly Cash) via render_data_expanders();
    #    here we only prepare + store the table.
    # ------------------------------------------------------------------
    table_df = df.copy()
    table_df["Date"] = table_df["Date"].dt.strftime("%Y-%m-%d")
    st.session_state["youtube_video_table"] = table_df[["Date", "Title", "Channel", "Duration", "Views", "URL"]]

    if no_data:
        st.caption(f"No YouTube data yet for: {', '.join(no_data)}.")


