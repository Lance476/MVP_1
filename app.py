# app.py - Lithium Project Comparison Dashboard
# ============================================================================
#
# PROJECTCONTEXT: zie PROJECT.md (vergelijking van pre-revenue lithium juniors —
# studie-economie, kaspositie en mijlpalen zijn belangrijker dan omzet/EBITDA).
#
# STRUCTUUR:
#   - config.py : ALLE data-input (bedrijven, studies, timeline) — hier pas je
#                 data aan (nieuw bedrijf toevoegen = config.py aanpassen)
#   - data.py   : ALLE data-functies (ophalen & berekenen)
#   - views.py  : ALLE weergave-functies (elke sectie op het scherm)
#   - app.py    : dit bestand — startpunt & volgorde van de secties
#
# To add a company: edit config.py (COMPANIES, STUDY_DATA, TIMELINE_DATA)
# ============================================================================
import time
import uuid

import streamlit as st
from streamlit_cookies_controller import CookieController

from config import COMPANIES
from data import track_page_loaded, track_company_selection, track_view_mode_change
from views import (
    apply_styles,
    render_comparison_snapshot,
    render_dashboard,
    render_feedback_section,
    render_qa_section,
    render_search_analysis,
    render_sentiment_analysis,
    render_sidebar,
    render_stock_chart,
    render_studies,
    render_cash_overview,
    render_timeline,
)

# ============================================================================
# USER AND SESSION IDS MET COOKIE
# ============================================================================
try:
    controller = CookieController()
except Exception:
    controller = None

if "user_id" not in st.session_state:
    if controller:
        cookie_user_id = controller.get("user_id")
        if cookie_user_id:
            # RETURNING USER
            st.session_state.user_id = cookie_user_id
            st.session_state.is_returning = True
            st.session_state.visit_number = st.session_state.get("visit_number", 0) + 1
        else:
            # NEW USER
            new_id = str(uuid.uuid4())
            try:
                controller.set("user_id", new_id, max_age=365*24*60*60)  # 1 year
            except Exception:
                pass
            st.session_state.user_id = new_id
            st.session_state.is_returning = False
            st.session_state.visit_number = 1
    else:
        # Fallback: no cookie available
        st.session_state.user_id = str(uuid.uuid4())
        st.session_state.is_returning = False
        st.session_state.visit_number = 1

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()

# ============================================================================
# PAGE CONFIG + STYLES
# ============================================================================
st.set_page_config(
    layout="wide",
    page_title="Lithium Project Comparison",
    page_icon="",
    initial_sidebar_state="expanded"
)
apply_styles()

# Fire page_loaded once per session
track_page_loaded()

# ============================================================================
# MAIN APP
# ============================================================================
with st.container():
    view_mode, selected_companies = render_sidebar()

    # Track view mode and company selection changes
    track_view_mode_change(view_mode)
    track_company_selection(selected_companies)

    # Store for dynamic QA label
    st.session_state.selected_companies = selected_companies

    if len(selected_companies) == 0:
        st.warning("Please select at least one company.")
        st.stop()

    is_compare = view_mode == "Compare Companies" and len(selected_companies) >= 2

    # Title
    company_display = ", ".join([COMPANIES[c]['short_name'] for c in selected_companies])
    if is_compare:
        st.title(f"Project Comparison: {company_display}")
    else:
        st.title(selected_companies[0])

    st.caption(
    "MVP/Demo — Data may include errors. Not financial advice.\n\n"
    "I hope to improve the comparability, Exposure & Ability to monitor Junior Mining Lithium firms.\n"
    "To simplify this idea, I focus on advanced Lithium projects in Nevada.\n\n"
    "Upcoming upgrades:\n"
    "Monitoring Future to measure Interest For the Firm, (Lithium) interest in Nevada, And in Lithium in General.\n\n"
    "Integrating News Sources, i.e. LinkedIn, X, Company Press Releases, YT Interview.\n\n"
    "📅 31-08-2026: Version 4 will be deployed (existing link)."
)

    if 'data_source' in st.session_state:
        st.caption(f"Data source: {st.session_state.data_source}")

    # --- SECTIONS ("newsroom" order: live -> search -> events -> reference) ---
    # Returning visitors come for what CHANGED (price, catalysts), so the
    # dynamic layers sit above the fold; the static reference library and the
    # feedback ask sit at the bottom, after value has been delivered.

    # 1. LIVE — price layer: the daily reason to come back
    render_dashboard(selected_companies)
    st.markdown("")

    st.subheader("Stock Performance")
    render_stock_chart(selected_companies)
    st.markdown("")

    # 2. AT A GLANCE — cross-company summary (compare mode only)
    if is_compare:
        render_comparison_snapshot(selected_companies)
        st.markdown("")

    # 3. SEARCH — Google Trends teaser + Google Ads Search Volume,
    #    directly after the price charts (attention layer first)
    st.subheader("Google Trends")
    render_search_analysis(selected_companies)
    st.markdown("")

    # 4. EVENTS — upcoming catalysts/permits: the event-driven return trigger
    render_timeline(selected_companies)
    st.markdown("")

    render_sentiment_analysis(selected_companies)
    st.markdown("")

    # 5. QUARTERLY — cash position & runway
    render_cash_overview(selected_companies)
    st.markdown("")

    # 6. REFERENCE — static study economics & value ratios
    render_studies(selected_companies)
    st.markdown("")

    # 7. COMMUNITY — Q&A first, feedback ask last (post-value conversion)
    st.subheader("Management Due Diligence")
    st.markdown("")

    render_qa_section()
    st.markdown("")

    # Feedback form: visitors can leave a comment that is sent to the owner
    render_feedback_section()

# python -m streamlit run app.py