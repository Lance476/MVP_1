# views.py
# ============================================================================
# ALLE weergave-functies van de app. Elke functie tekent één onderdeel
# (sidebar, dashboard, studies, timeline, ...) en haalt zijn data via data.py.
# ============================================================================
import altair as alt
import pandas as pd
import plotly.graph_objects as go
import re
import streamlit as st
import yfinance as yf

from config import COMPANIES, DEFAULT_COMPANY, LIT_LABEL, STAGE_ORDER, STAGE_SHORT_MAP, STOCK_CLUSTERS, TIMELINE_DATA, TIME_PERIODS, DEFAULT_TIME_PERIOD, YOUTUBE_VIDEOS, lithium_companies
from data import (
    company_term_map,
    get_cluster_stock_data,
    STOCK_INTERVAL_CONFIG,
    get_dashboard_metrics,
    get_monitor_returns,
    get_feedback_email,
    get_google_trends,
    get_market_cap_data,
    get_monthly_search_pattern,
    get_search_volume_data,
    get_stock_data,
    build_company_financials,
    load_financial_data,
    load_study_data,
    send_feedback,
    stock_cache_ttl_label,
    track_event,
    track_expander_open,
    track_period_change,
    track_qa_like,
    track_qa_submit,
    track_tab_click,
)

# Denser intraday windows exceed Altair's default 5000-row cap.
alt.data_transformers.disable_max_rows()


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

        st.markdown("")
        st.caption("MVP Demo — Not financial advice.")

        return view_mode, selected





def render_dashboard(companies=None):
    """Market Monitor — 5 squares side-by-side (one per entity)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    st.subheader("Market Monitor")
    board = get_monitor_returns(companies)
    rows = board.get("rows", [])
    if not rows:
        st.warning("Could not load market monitor data")
        return

    def _color(v):
        return "#1a7f37" if v >= 0 else "#d1242f"

    def _pct(v):
        if v is None:
            return "n/a"
        sign = "+" if v >= 0 else ""
        return f"{sign}{v:.1f}%"

    def _colored(v, size="13px"):
        """% value in green/red — slightly larger, normal weight so the
        digits stay crisp and readable at card size."""
        if v is None:
            return f"<span style='color:#9ca3af; font-size:{size};'>n/a</span>"
        return (f"<span style='font-weight:400; font-size:{size}; "
                f"color:{_color(v)};'>{_pct(v)}</span>")

    def _plain(v, size="10px", color="#1f2937"):
        """% value in a neutral dark color — used for the small
        volume-change numbers so they don't compete with the red/green
        return figures."""
        if v is None:
            return f"<span style='color:#9ca3af; font-size:{size};'>n/a</span>"
        return (f"<span style='font-weight:400; font-size:{size}; "
                f"color:{color};'>{_pct(v)}</span>")

    def _card(r):
        name = r["name"]
        ticker = r.get("ticker", "")
        price = ""
        if r.get("price") is not None:
            price = f"<div style='font-size:12px; color:#6b7280;'>$ {r['price']:.2f}</div>"
        else:
            # Empty spacer line with the same height as the price row, so cards
            # without a price (e.g. the cluster "avg of N members" cards) keep
            # the same height as the ticker cards and all squares align.
            price = "<div style='font-size:12px;'>&nbsp;</div>"

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
            # value1/value2 are already rendered <span>s from _colored();
            # only wrap them in the small gray "vol" label here.
            return (f"{value1} <span style='color:#8a9099; font-size:10px;'>"
                    f"vol {value2}</span>")

        row = (
            _line("1D", _pair(_colored(r["returns"].get("1d")),
                              _plain(r.get("volume_changes", {}).get("1d"))))
            + _line("7D", _pair(_colored(r["returns"].get("7d")),
                                _plain(r.get("volume_changes", {}).get("7d"))))
            + _line("30D", _pair(_colored(r["returns"].get("30d")),
                                 _plain(r.get("volume_changes", {}).get("30d"))))
        )
        return f"""
        <div style='border:1px solid #e5e7eb; border-radius:10px; padding:12px;
                    background:#ffffff; box-shadow:0 1px 2px rgba(0,0,0,0.05);
                    height:100%;'>
          <div style='font-weight:600; font-size:13px; color:#1f2937;'>{name}</div>
          <div style='font-size:11px; color:#9ca3af;'>{ticker}</div>
          {price}
          <div style='margin-top:8px;'>{row}</div>
        </div>
        """

    cols = st.columns(len(rows))
    for col, r in zip(cols, rows):
        with col:
            st.markdown(_card(r), unsafe_allow_html=True)

    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.caption("Data from Yahoo Finance — Updates Daily")
    st.caption("Volume: 1D vs previous trading day; 7D/30D vs typical (median) daily volume over the same window")


def render_stock_chart(companies=None):
    """Render the stock price charts grouped into 3 clusters.

    Cluster 1: Nevada Lithium Juniors
    Cluster 2: Canadian Lithium Juniors
    Cluster 3: Australian Producers

    A horizontal time-period selector (1D, 7D, 30D, 90D, 1Y) lets users
    zoom in on recent price action — encouraging repeat visits to monitor
    short-term movements.  Each cluster is rendered inside a collapsible
    ``st.expander`` so users can focus on the groups they care about.
    """
    import altair as alt

    if companies is None:
        companies = list(COMPANIES.keys())

    # ------------------------------------------------------------------
    # Time-period selector
    # ------------------------------------------------------------------
    period_labels = [p["label"] for p in TIME_PERIODS]
    default_idx = (
        period_labels.index(DEFAULT_TIME_PERIOD)
        if DEFAULT_TIME_PERIOD in period_labels
        else len(period_labels) - 1
    )
    selected_period = st.radio(
        "Time period",
        options=period_labels,
        index=default_idx,
        horizontal=True,
        label_visibility="collapsed",
        key="stock_period_radio",
    )

    period_days = next(
        (p["days"] for p in TIME_PERIODS if p["label"] == selected_period), 365
    )
    track_period_change(selected_period)

    cluster_data = get_cluster_stock_data(period_days=period_days)

    # x-axis format / tick density depends on the selected period
    axis_cfg = {
        1:   {"format": "%H:%M",   "tick_count": "hour",  "title": "Time (UTC)"},
        7:   {"format": "%m/%d %H:%M", "tick_count": "day", "title": "Date"},
        30:  {"format": "%m/%d",   "tick_count": "week",  "title": "Date"},
        90:  {"format": "%m/%d",   "tick_count": "month", "title": "Month"},
        365: {"format": "%Y-%m",   "tick_count": "month", "title": "Date"},
    }
    ax = axis_cfg.get(period_days, axis_cfg[365])

    # Bar density per window — straight from STOCK_INTERVAL_CONFIG (data.py)
    bar_interval = STOCK_INTERVAL_CONFIG.get(period_days, {}).get("interval", "daily")
    st.caption(
        f"Data: {selected_period} view using {bar_interval} bars (Yahoo Finance); "
        f"refreshed every {stock_cache_ttl_label(period_days)}. "
        f"Illiquid stocks may show fewer bars."
    )

    # Predefined colors per cluster for consistency
    cluster_colors = {
        "Nevada Juniors": [
            "#2E86C1", "#F39C12", "#27AE60", "#8E44AD",
            "#E67E22", "#16A085", "#C0392B",
        ],
        "Canadian Juniors": [
            "#1A5276", "#148F77", "#B03A2E",
        ],
        "Australian Producers + Benchmark": [
            "#D35400", "#7D3C98", "#1B4F72",
        ],
    }

    # ------------------------------------------------------------------
    # Cluster charts — each inside a collapsible expander
    # ------------------------------------------------------------------
    for cluster_key, cluster_info in STOCK_CLUSTERS.items():
        data = cluster_data.get(cluster_key)
        label = cluster_info["label"]

        with st.expander(f"**{label}**", expanded=True):
            track_expander_open(label)

            if data is None or data.empty:
                st.info("No stock data available for this cluster.")
                continue

            color_scale = alt.Scale(
                domain=list(cluster_info["members"].keys()),
                range=cluster_colors.get(
                    cluster_key, ["#95A5A6"] * len(cluster_info["members"])
                ),
            )

            chart = alt.Chart(data).mark_line(
                # Clean, continuous line per ticker (Yahoo Finance style).
                # Point markers are only added when a cluster is nearly
                # empty (a handful of bars), where a bare line would be
                # hard to see.
                strokeWidth=2,
                point=(
                    alt.OverlayMarkDef(
                        size=32, filled=True, stroke="white", strokeWidth=0.5
                    )
                    if len(data) < 50
                    else False
                ),
            ).encode(
                x=alt.X(
                    "Date:T",
                    axis=alt.Axis(
                        format=ax["format"],
                        tickCount=ax["tick_count"],
                        title=ax["title"],
                    ),
                ),
                y=alt.Y(
                    "Normalized:Q",
                    title="Indexed (start = 100)",
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(
                    "Ticker:N",
                    title=None,
                    scale=color_scale,
                    legend=alt.Legend(
                        orient="right",
                        title=None,
                        labelFontSize=11,
                        columns=1,
                    ),
                ),
                # One continuous line per ticker (Yahoo Finance style):
                # bars connect straight across nightly/weekend gaps instead
                # of being split into separate per-session segments.
                detail=[alt.Detail("Ticker:N")],
                tooltip=[
                    alt.Tooltip("Ticker:N"),
                    alt.Tooltip(
                        "Date:T",
                        title="Date",
                        format=(
                            "%Y-%m-%d %H:%M"
                            if period_days <= 90
                            else "%Y-%m-%d"
                        ),
                    ),
                    alt.Tooltip("Normalized:Q", title="Indexed", format=".1f"),
                ],
            ).properties(height=280)

            st.altair_chart(chart, use_container_width=True)

    # ------------------------------------------------------------------
    # Simple cluster comparison: performance per cluster for the period
    # ------------------------------------------------------------------
    st.markdown(f"**{selected_period} Performance — Cluster Comparison**")

    summary_rows = []
    for cluster_key, cluster_info in STOCK_CLUSTERS.items():
        data = cluster_data.get(cluster_key)
        if data is None or data.empty:
            continue

        latest_perf = (
            data.sort_values("Date")
            .groupby("Ticker")["Normalized"]
            .last()
            .sort_values(ascending=False)
        )
        if latest_perf.empty:
            continue

        best = latest_perf.index[0]
        best_val = latest_perf.iloc[0]
        avg_val = latest_perf.mean()

        summary_rows.append({
            "Cluster": cluster_info["label"],
            "Avg (index)": f"{avg_val:.0f}",
            "Best performer": best,
            "Best (index)": f"{best_val:.0f}",
        })

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.markdown("")


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

    st.caption("All values are the latest available per company. Some rows may be missing data in this MVP.")





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
                    ratio_data[['Stage_Display', 'AfterTax_NPV_M', 'Initial_Capex_M']],
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

                    # Compact faceted chart — each ratio has its own scale
                    # Note: `point` overlay is required so companies with only ONE
                    # study stage (e.g. Surge: only PEA) still show a visible marker
                    # (a bare line mark with a single point is invisible in Vega-Lite).
                    chart = alt.Chart(ratio_melted).mark_line(
                        strokeWidth=2,
                        color=COMPANIES[company]['color'],
                        point=alt.OverlayMarkDef(
                            size=42, filled=True, stroke='white', strokeWidth=1
                        )
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

                    # Half width like the Search Interest columns
                    col_chart, _ = st.columns([1, 1])
                    with col_chart:
                        st.altair_chart(chart, use_container_width=True)
                        st.caption("Values C$")

                    # Compact table — 2 decimals everywhere
                    with st.expander("View detailed data table", expanded=False):
                        track_expander_open("View detailed data table")
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
                        st.dataframe(display_ratios, use_container_width=True, hide_index=True)
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

        st.caption("Source: Company technical reports and studies (MVP Demo Data)")
    else:
        st.info("No study data available")





def render_monthly_pattern(companies=None):
    """Compact bar chart of average monthly search interest (grouped)."""
    if companies is None:
        companies = list(COMPANIES.keys())

    monthly = get_monthly_search_pattern(companies)
    if monthly is None or monthly.empty:
        return

    # Map search terms back to company display names
    term_to_company = company_term_map(companies)
    monthly['Company'] = monthly['Term'].map(term_to_company).fillna(monthly['Term'])

    # Average across the firm's individual search terms so each company has
    # one bar per month
    monthly = (
        monthly.groupby(['Company', 'Month', 'Month_Name'], as_index=False)['Interest']
        .mean()
        .sort_values('Month')
    )

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


def _render_coming_soon_tiles(label):
    """Row of three green 'coming soon' teaser tiles (1D / 7D / 30D).

    Shared by every section that wants to announce upcoming graphs —
    keeps the tiles pixel-identical everywhere.
    """
    for col, window in zip(st.columns(3), ["1D", "7D", "30D"]):
        with col:
            st.markdown(
                f"""
                <div class="coming-soon-box">
                    <div class="coming-soon-window">{window}</div>
                    <div class="coming-soon-label">{label}</div>
                    <div class="coming-soon-badge">🚧 Coming soon</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_search_analysis(companies=None):
    """Search section: coming-soon windows + Google Ads search volume."""
    if companies is None:
        companies = list(COMPANIES.keys())

    # ------------------------------------------------------------------
    # Coming-soon placeholders: 1D / 7D / 30D search-interest graphs are
    # on the roadmap.  Tease them now so viewers know what to expect and
    # have a reason to come back.
    # ------------------------------------------------------------------
    _render_coming_soon_tiles("Search Interest graph")

    # ------------------------------------------------------------------
    # Google Ads Search Volume (company + Nevada Lithium + lithium stocks)
    # Three blank lines: breathing room below the coming-soon tiles so the
    # title does not visually crowd them.
    # ------------------------------------------------------------------
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("**Google Ads Search Volume**")
    sv_data = get_search_volume_data(companies)

    if sv_data is not None and not sv_data.empty:
        # Color scale: company color for the firm's own line, fixed colors
        # for the two benchmarks.
        color_scale = {c: COMPANIES[c]['color'] for c in companies}
        color_scale["lithium stocks"] = "#95A5A6"
        color_scale["Nevada Lithium"] = "#E74C3C"

        # Chronological month order (the labels are strings like "8/2025",
        # which would otherwise sort alphabetically).
        month_order = [
            "8/2025", "9/2025", "10/2025", "11/2025", "12/2025",
            "1/2026", "2/2026", "3/2026", "4/2026", "5/2026", "6/2026", "7/2026",
        ]

        sv_chart = alt.Chart(sv_data).mark_line(
            strokeWidth=2
        ).encode(
            x=alt.X('Month:N', title=None, sort=month_order,
                    axis=alt.Axis(labelAngle=-45, labelFontSize=9)),
            y=alt.Y('Search_Volume:Q', title='Search Volume',
                    scale=alt.Scale(zero=False)),
            color=alt.Color(
                'Company:N',
                scale=alt.Scale(domain=list(color_scale.keys()),
                                range=list(color_scale.values())),
                title=None,
                legend=alt.Legend(orient="right", labelFontSize=10, columns=1)
            ),
            tooltip=[
                alt.Tooltip('Company:N', title='Series'),
                alt.Tooltip('Month:N', title='Month'),
                alt.Tooltip('Search_Volume:Q', title='Search Volume', format=',.0f')
            ]
        ).properties(height=250)

        st.altair_chart(sv_chart, use_container_width=True)
    else:
        st.info("No search volume data available")


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

    # Header row: title left, "notify me" call-to-action far right.  Clicks
    # are tracked in GA4 (notify_q2_cash_click) to measure demand for the
    # upcoming Q2 cash figures.
    header_cols = st.columns([0.72, 0.28], vertical_alignment="center")
    with header_cols[0]:
        st.subheader(
            "Quarterly Cash Overview"
            + (" — Side by Side" if is_compare else "")
        )
    with header_cols[1]:
        if st.button(
            "🔔 Notify me when Q2 Cash is known",
            key="notify_q2_cash",
            use_container_width=True,
            type="primary",
        ):
            track_event("notify_q2_cash_click", {"companies": ", ".join(companies)})
            st.toast("Thanks! Q2 cash will appear here as soon as it's known. 📊")

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
    # Historical vs planned/ongoing milestones: compute the split point
    # ------------------------------------------------------------------
    planned_events = events_df[events_df['Status'] == 'Future']
    split_date = planned_events['Date'].min() if not planned_events.empty else None
    x_min_all = events_df['Date'].min()
    x_max_all = events_df['Date'].max()

    # Sort studies for consistent y-axis ordering
    study_order = ['MRE', 'MRE_U', 'PEA', 'PEA_U', 'PFS', 'FS', 'FS_U',
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
                   'Flowsheet Optimization', 'Defense Supply Chain Integration']

    existing_studies = [s for s in study_order if s in events_df['Study'].unique()]
    remaining_studies = [s for s in events_df['Study'].unique() if s not in existing_studies]
    y_order = existing_studies + remaining_studies
    y_order_rev = y_order[::-1]

    colors = {'Commitment': '#F39C12', 'Expected': '#E74C3C', 'Actual': '#2E86C1', 'Planned': '#8E44AD'}
    symbols = {'Commitment': 'diamond-open', 'Expected': 'diamond-open', 'Actual': 'circle', 'Planned': 'triangle-up-open'}
    sizes = {'Commitment': 12, 'Expected': 12, 'Actual': 14, 'Planned': 14}
    event_labels = {'Commitment': 'Commitment', 'Expected': 'Expected', 'Actual': 'Actual', 'Planned': 'Planned / Ongoing'}

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
            fig.add_trace(go.Scatter(
                x=sub['Date'],
                y=sub['Study'],
                mode='markers+text',
                name=event_labels.get(event_type, event_type),
                marker=dict(
                    color=colors.get(event_type, '#95A5A6'),
                    size=sizes.get(event_type, 11),
                    symbol=symbols.get(event_type, 'circle'),
                    line=dict(width=1.5, color='white')
                ),
                text=sub['Study'],
                textposition='middle right',
                textfont=dict(size=10, color='#2C3E50'),
                hovertemplate=(
                    f'<b>%{{y}}</b><br>'
                    f'{event_labels.get(event_type, event_type)}: %{{x|%d-%m-%Y}}<extra></extra>'
                ),
            ))

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
            font=dict(size=10)
        ),
        yaxis=dict(
            title=None,
            tickfont=dict(size=10, color='#2C3E50'),
            categoryorder='array',
            categoryarray=y_order_rev,
            tickmode='array',
            ticktext=[''] * len(y_order_rev),
            tickvals=[s for s in y_order_rev],
            gridcolor='#ECF0F1',
            gridwidth=1,
            showticklabels=False,
        ),
        xaxis=dict(
            title=None,
            tickfont=dict(size=10),
            tickformat='%b %Y',
            gridcolor='#ECF0F1',
            gridwidth=1,
            showgrid=True,
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
    fig.update_xaxes(range=[x_min_all - pad, x_max_all + pad + right_pad])

    if split_date is not None:
        fig.add_vrect(
            x0=split_date, x1=x_max_all + pad,
            fillcolor="rgba(142, 68, 173, 0.05)",
            line_width=0,
            layer="below",
        )
        fig.add_vline(
            x=split_date,
            line_dash="dash",
            line_color="#8E44AD",
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
    st.dataframe(timeline_df[present_cols], use_container_width=True, hide_index=True)

    # ====================================================================
    # COMMITMENT SENTENCES (uitklapbaar, compact)
    # ====================================================================
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

        with st.expander(f"Commitment sentences — {company}"):
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

            st.caption("Source: company press releases and disclosures (MVP demo).")


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
    
    /* Notify-me call-to-action buttons (light green, eye-catching).
       Streamlit >= 1.39 exposes every element key as a "st-key-<key>"
       CSS class, so these rules only hit the two notify buttons. */
    .st-key-notify_q2_cash button,
    .st-key-notify_interview button {
        background-color: #D8F3DC !important;
        color: #1B4332 !important;
        border: 1.5px solid #40916C !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 4px rgba(64, 145, 108, 0.35) !important;
    }
    
    .st-key-notify_q2_cash button:hover,
    .st-key-notify_interview button:hover,
    .st-key-notify_q2_cash button:focus,
    .st-key-notify_interview button:focus {
        background-color: #B7E4C7 !important;
        color: #1B4332 !important;
        border-color: #2D6A4F !important;
    }
    
    /* "Coming soon" placeholder tiles (1D / 7D / 30D search interest) */
    .coming-soon-box {
        border: 2px dashed #A3CBB9 !important;
        border-radius: 10px !important;
        background: #F4FBF7 !important;
        padding: 1.1rem 0.75rem !important;
        text-align: center !important;
        min-height: 118px !important;
    }
    .coming-soon-window {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #2D6A4F !important;
        letter-spacing: 1px !important;
    }
    .coming-soon-label {
        font-size: 12.5px !important;
        color: #6B7C74 !important;
        margin-top: 2px !important;
    }
    .coming-soon-badge {
        display: inline-block !important;
        margin-top: 8px !important;
        padding: 2px 10px !important;
        border-radius: 999px !important;
        background: #D8F3DC !important;
        color: #1B4332 !important;
        font-size: 11.5px !important;
        font-weight: 600 !important;
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

    # Header row: title left, "notify me" call-to-action far right.  Clicks
    # are tracked in GA4 (notify_interview_click) to measure demand for
    # new-interview alerts.
    header_cols = st.columns([0.72, 0.28], vertical_alignment="center")
    with header_cols[0]:
        st.subheader("Sentiment Analysis")
        st.caption("YouTube interviews & coverage over time")
    with header_cols[1]:
        if st.button(
            "🔔 Notify me at new Interview",
            key="notify_interview",
            use_container_width=True,
            type="primary",
        ):
            track_event("notify_interview_click", {"companies": ", ".join(companies)})
            st.toast("Thanks! You'll be alerted when a new interview drops. 🎥")

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
        # Still show the 'coming soon' teaser tiles so every company keeps
        # the same layout — with or without interview data.
        _render_coming_soon_tiles("Youtube Search Interest graph")
        return

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    # Newest interviews first: the table below acts as a "what's latest"
    # list.  The bubble chart positions points by date on the x-axis, so
    # the sort order does not affect it.
    df = df.sort_values("Date", ascending=False).reset_index(drop=True)

    # ------------------------------------------------------------------
    # 1. Video table (newest first)
    # ------------------------------------------------------------------
    table_df = df.copy()
    table_df["Date"] = table_df["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(
        table_df[["Date", "Title", "Channel", "Duration", "Views", "URL"]],
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

    # ------------------------------------------------------------------
    # Coming soon: YouTube search-interest graphs (1D / 7D / 30D) —
    # the same teaser tiles as in the Google Trends section.
    # ------------------------------------------------------------------
    _render_coming_soon_tiles("Youtube Search Interest graph")
    st.markdown("")
    st.markdown("")

    # ------------------------------------------------------------------
    # 2. Interview timeline chart: when (x-axis) × views (y-axis),
    #    uniform blue bubbles (channel shown on hover)
    # ------------------------------------------------------------------
    st.markdown("**Interview Timeline — When & Views**")

    chart = (
        alt.Chart(df)
        .mark_circle(opacity=0.75, stroke="white", strokeWidth=1, size=140, color="#1F77B4")
        .encode(
            x=alt.X("Date:T", title=None, axis=alt.Axis(format="%b %Y")),
            y=alt.Y("Views:Q", title="Views", scale=alt.Scale(zero=False)),
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

    if no_data:
        st.caption(f"No YouTube data yet for: {', '.join(no_data)}.")


def _link_button(label, url):
    """Render a small button-styled hyperlink."""
    st.markdown(
        f'<a href="{url}" target="_blank" '
        'style="display:inline-block;padding:0.3rem 0.9rem;background:#FF4B4B;'
        'color:white;border-radius:0.3rem;text-decoration:none;font-size:14px;'
        f'font-weight:500;">{label}</a>',
        unsafe_allow_html=True,
    )


def render_feedback_section():
    """Compact contact options: LinkedIn, email, or leave a message."""
    with st.expander("Leave feedback"):
        track_expander_open("Leave feedback")

        linkedin_url = st.secrets.get("LINKEDIN_URL", "")
        feedback_email = get_feedback_email()

        # Quick contact buttons
        buttons = []
        if linkedin_url:
            buttons.append(("Connect on LinkedIn", linkedin_url))
        if feedback_email:
            buttons.append((
                "Send an email",
                f"mailto:{feedback_email}?subject=Feedback%20Lithium%20Project%20Comparison",
            ))

        if buttons:
            cols = st.columns(len(buttons))
            for col, (label, url) in zip(cols, buttons):
                with col:
                    _link_button(label, url)

        # Or leave a message directly
        if buttons:
            st.markdown("**Or leave a message:**")
        message = st.text_area(
            "Your message",
            key="feedback_message",
            placeholder="What works well, what's missing, what should I improve?",
            height=100,
            label_visibility="collapsed" if buttons else "visible",
        )

        # No minimum length: any message is accepted (empty clicks are ignored)
        if st.button("Send message", key="feedback_submit") and message.strip():
            ok, channel = send_feedback(message)
            track_event("feedback_submit", {"channel": channel})
            if ok:
                if channel == "local":
                    st.success("Thanks! Your message has been recorded.")
                else:
                    st.success("Thanks! Your message has been sent.")
            else:
                st.error("Could not send your message right now. Please try again later.")
