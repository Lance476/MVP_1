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

from config import COMPANIES, DEFAULT_COMPANY, LIT_LABEL, STAGE_ORDER, STAGE_SHORT_MAP, STOCK_CLUSTERS, TIMELINE_DATA, YOUTUBE_VIDEOS
from data import (
    company_term_map,
    get_cluster_stock_data,
    get_correlation_data,
    get_dashboard_metrics,
    get_feedback_email,
    get_google_trends,
    get_market_cap_data,
    get_monthly_search_pattern,
    get_search_volume_data,
    get_stock_data,
    get_trends_snapshot_info,
    build_company_financials,
    load_financial_data,
    load_study_data,
    send_feedback,
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

        st.markdown("")
        st.caption("MVP Demo — Not financial advice.")

        return view_mode, selected





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

                # Price, return and volume on one line - clean and compact
                price_color = "#27AE60" if m['return_30d'] >= 0 else "#E74C3C"
                vol_change = m.get('volume_change', 0)
                vol_color = "#27AE60" if vol_change >= 0 else "#E74C3C"

                st.markdown(f"""
                <div style='
                    display: flex;
                    align-items: baseline;
                    gap: 10px;
                '>
                    <span style='font-size: 22px; font-weight: 600; color: #1a1a2e;'>${m['current']:.2f}</span>
                    <span style='font-size: 13px; color: {price_color}; font-weight: 500;'>{m['return_30d']:+.1f}%</span>
                    <span style='font-size: 11px; color: #777;'>| Vol <span style='font-weight: 500; color: {vol_color};'>{vol_change:+.1f}%</span></span>
                    <span style='font-size: 10px; color: #bbb;'>30d</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Single company
        company = list(company_metrics.keys())[0]
        m = company_metrics[company]

        # Two columns with tighter spacing
        col1, col2 = st.columns([1, 1])

        with col1:
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

            # Price, return and volume on one line - clean and compact
            price_color = "#27AE60" if m['return_30d'] >= 0 else "#E74C3C"
            vol_change = m.get('volume_change', 0)
            vol_color = "#27AE60" if vol_change >= 0 else "#E74C3C"

            st.markdown(f"""
            <div style='
                display: flex;
                align-items: baseline;
                gap: 10px;
            '>
                <span style='font-size: 22px; font-weight: 600; color: #1a1a2e;'>${m['current']:.2f}</span>
                <span style='font-size: 13px; color: {price_color}; font-weight: 500;'>{m['return_30d']:+.1f}%</span>
                <span style='font-size: 11px; color: #777;'>| Vol <span style='font-weight: 500; color: {vol_color};'>{vol_change:+.1f}%</span></span>
                <span style='font-size: 10px; color: #bbb;'>30d</span>
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


def render_stock_chart(companies=None):
    """Render the stock price charts grouped into 3 clusters.

    Cluster 1: Nevada Lithium Juniors
    Cluster 2: Canadian Lithium Juniors
    Cluster 3: Australian Producers + Sprott ETF benchmark
    """
    import altair as alt
    if companies is None:
        companies = list(COMPANIES.keys())

    cluster_data = get_cluster_stock_data()

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
            "#D35400", "#7D3C98", "#1B4F72", "#F1C40F",
        ],
    }

    for cluster_key, cluster_info in STOCK_CLUSTERS.items():
        data = cluster_data.get(cluster_key)
        if data is None or data.empty:
            st.markdown(f"**{cluster_info['label']}**")
            st.info("No stock data available for this cluster.")
            continue

        color_scale = alt.Scale(
            domain=list(cluster_info["members"].keys()),
            range=cluster_colors.get(cluster_key, ["#95A5A6"] * len(cluster_info["members"]))
        )

        chart = alt.Chart(data).mark_line(strokeWidth=2, point=False).encode(
            x=alt.X("Date:T", axis=alt.Axis(format="%Y", tickCount="year", title="Year")),
            y=alt.Y("Normalized:Q", title="Indexed (start = 100)", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "Ticker:N",
                title=None,
                scale=color_scale,
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
                alt.Tooltip("Normalized:Q", title="Indexed", format=".1f"),
            ]
        ).properties(height=280)

        st.markdown(f"**{cluster_info['label']}**")
        st.altair_chart(chart, use_container_width=True)

    # ------------------------------------------------------------------
    # Simple cluster comparison: 12-month performance per cluster
    # ------------------------------------------------------------------
    st.markdown("**12-Month Performance — Cluster Comparison**")

    summary_rows = []
    for cluster_key, cluster_info in STOCK_CLUSTERS.items():
        data = cluster_data.get(cluster_key)
        if data is None or data.empty:
            continue

        # Latest normalized value per member (indexed to 100 at start)
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
    try:
        annual, stock = load_financial_data()
    except Exception as e:
        print(f"render_comparison_snapshot: could not load financial data: {e}")
        annual, stock = None, None

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
                    chart = alt.Chart(ratio_melted).mark_line(
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
                    strokeWidth=2
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
                    strokeWidth=2
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
                    strokeWidth=2
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
                    strokeWidth=2
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


def render_search_analysis(companies=None):
    """Clean search section with comparison support."""
    if companies is None:
        companies = list(COMPANIES.keys())

    # ------------------------------------------------------------------
    # Two charts side by side:
    #   Left:  Interest vs Market Performance (per company)
    #   Right: Google Ads Search Volume (company + Nevada Lithium + lithium stocks)
    # ------------------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Google Trends**")
        corr_data, _ = get_correlation_data(companies)

        # Show when the pinned trends snapshot was taken and when it refreshes.
        # The Google Trends graph (SerpApi) is intentionally frozen for ~30 days
        # so it does not change on every code patch/deploy.
        snapshot_date, expires_date = get_trends_snapshot_info()
        if snapshot_date is not None and expires_date is not None:
            st.caption(
                f"🔒 Graph fixed since {snapshot_date.strftime('%d %b %Y')} — "
                f"refreshes on {expires_date.strftime('%d %b %Y')}"
            )

        if corr_data is not None and not corr_data.empty:
            color_scale = {c: COMPANIES[c]['color'] for c in companies}

            # Melt for proper legend (corr_data already carries Company)
            df_melted = corr_data.melt(
                id_vars=['Date', 'Company'],
                value_vars=['Search_Indexed'],
                var_name='Series',
                value_name='Value'
            )

            # Clean labels
            df_melted['Series'] = df_melted['Series'].map({
                'Search_Indexed': 'Search'
            })

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
                tooltip=[
                    alt.Tooltip('Company:N', title='Company'),
                    alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
                    alt.Tooltip('Value:Q', title='Search Interest', format='.1f')
                ]
            ).properties(height=250)

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No correlation data available")

    with col2:
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
            for date_key, event_type in event_mappings.items():
                date = parse_timeline_date(row.get(date_key, '—'))
                if date is not None:
                    event_rows.append({
                        'Company': company,
                        'Study': study,
                        'Event_Type': event_type,
                        'Date': date,
                    })

    if not event_rows:
        return

    events_df = pd.DataFrame(event_rows)

    # Sort studies for consistent y-axis ordering
    study_order = ['MRE', 'MRE_U', 'PEA', 'PEA_U', 'PFS', 'FS', 'FS_U',
                   'PoO_Submitted', 'PoO_Accepted', 'PoO_Approved',
                   'NEPA_Start', 'Final_EIS', 'Final_EA',
                   'Record of Decision', 'FID', 'FAST41_Transparency',
                   'FAST41_Covered', 'Fully_Permitted']

    existing_studies = [s for s in study_order if s in events_df['Study'].unique()]
    remaining_studies = [s for s in events_df['Study'].unique() if s not in existing_studies]
    y_order = existing_studies + remaining_studies
    y_order_rev = y_order[::-1]

    colors = {'Commitment': '#F39C12', 'Expected': '#E74C3C', 'Actual': '#2E86C1'}
    symbols = {'Commitment': 'diamond-open', 'Expected': 'diamond-open', 'Actual': 'circle'}
    sizes = {'Commitment': 12, 'Expected': 12, 'Actual': 14}

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
            for event_type in ['Commitment', 'Expected', 'Actual']:
                sub = comp_events[comp_events['Event_Type'] == event_type]
                if sub.empty:
                    continue
                fig.add_trace(go.Scatter(
                    x=sub['Date'],
                    y=sub['Study'],
                    mode='markers',
                    name=f"{COMPANIES[company]['short_name']} — {event_type}",
                    marker=dict(
                        color=comp_color,
                        size=sizes.get(event_type, 11),
                        symbol=symbols.get(event_type, 'circle'),
                        line=dict(width=1.5, color='white')
                    ),
                    hovertemplate=(
                        f'<b>{company}</b><br>'
                        f'<b>%{{y}}</b><br>'
                        f'{event_type}: %{{x|%d-%m-%Y}}<extra></extra>'
                    ),
                ))
    else:
        for event_type in ['Commitment', 'Expected', 'Actual']:
            sub = events_df[events_df['Event_Type'] == event_type]
            if sub.empty:
                continue
            fig.add_trace(go.Scatter(
                x=sub['Date'],
                y=sub['Study'],
                mode='markers+text',
                name=event_type,
                marker=dict(
                    color=colors.get(event_type, '#95A5A6'),
                    size=sizes.get(event_type, 11),
                    symbol=symbols.get(event_type, 'circle'),
                    line=dict(width=1.5, color='white')
                ),
                text=sub['Study'],
                textposition='middle right',
                textfont=dict(size=12, color='#2C3E50'),
                hovertemplate=(
                    f'<b>%{{y}}</b><br>'
                    f'{event_type}: %{{x|%d-%m-%Y}}<extra></extra>'
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
            font=dict(size=12)
        ),
        yaxis=dict(
            title=None,
            tickfont=dict(size=12, color='#2C3E50'),
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
            tickfont=dict(size=11),
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

    st.plotly_chart(fig, use_container_width=True, key="timeline_chart")

    # Show the table (grouped by company when in comparison)
    display_cols = ['Company', 'Study', 'Commitment date', 'Expected date', 'Actual date', 'Delay']
    if not is_compare:
        display_cols = ['Study', 'Commitment date', 'Expected date', 'Actual date', 'Delay']

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

    st.subheader("Sentiment Analysis")
    st.caption("YouTube interviews & coverage over time")

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
        return

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date", ascending=True).reset_index(drop=True)

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
