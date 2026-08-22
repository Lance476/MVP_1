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
from streamlit_cookies_manager import CookieManager

from config import COMPANIES
from data import track_page_loaded, track_company_selection, track_view_mode_change
from views import (
    apply_styles,
    render_comparison_snapshot,
    render_dashboard,
    render_feedback_section,
    render_financial_section,
    render_qa_section,
    render_search_analysis,
    render_sentiment_analysis,
    render_sidebar,
    render_stock_chart,
    render_studies,
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
    "MVP/Demo — Data may be inaccurate. Not financial advice.\n\n"
    "I hope to improve the comparability of Junior Lithium Mining firms. "
    "To simplify this, I focused on advanced Lithium projects in Nevada.\n\n"
    "Upcoming upgrades:\n"
    "1. Switch from Google Trends (0-100) to Advanced Search Volume. "
    "For the firm, project, and relevant terms.\n"
    "2. Improve Cash on Hand from Yearly to Quarterly. "
    "This makes it clear under what circumstances capital raises has been done. "
    "Also monitor current cash levels.\n"
    "3. Integrating News Sources, LinkedIn, X, Company Press Releases, YT (Interview), etc.\n"
    "4. In the Timeline, future milestones and expectations will be shown.\n\n"
    "28-08-2026 Today i worked primarily on the performance of firms, clustered together, and how well Century Lithium is actually searched on Google. The first one, Lithium projects in Nevada haven't go with the traction of Lithium price, although, they still performed better than Canadian lithium juniors over the past year. The Google search Ad, combined with the views on YT video's for Century Lithium are actually a bit disappointing, and there is massive room for upside on YT Views.\n\n"
    "PS: If you aspire entrepreneurship, a connection of mine pressed me 1.5 years ago when we saw each other at the toilets of a festival at night, who did start entrepreneurship, pressed on my to just start. So this is for you, i just spent a few weeks on Youtube whether a non-technical person can build cool stuff. A few weeks of doubt, and still. It's there. It's the best decision one can make to start anyway. So this is for you, just start, and you will figure it out along the way.\n\n"
    "Each day at 00:00 European Time, I upload a new version and share the progress made through the existing link. I'm always open to hear your feedback and suggestions."
)

    if 'data_source' in st.session_state:
        st.caption(f"Data source: {st.session_state.data_source}")

    # Feedback form: visitors can leave a comment that is sent to the owner
    render_feedback_section()

    # --- SECTIONS (volgorde van de dashboard-pagina) ---------------------
    if is_compare:
        render_comparison_snapshot(selected_companies)
        st.markdown("")

    render_dashboard(selected_companies)
    st.markdown("")

    render_studies(selected_companies)

    render_timeline(selected_companies)
    st.markdown("")

    st.subheader("Stock Performance")
    render_stock_chart(selected_companies)
    st.markdown("")

    st.subheader("Google Search Interest")
    render_search_analysis(selected_companies)
    st.markdown("")

    render_sentiment_analysis(selected_companies)
    st.markdown("")

    st.subheader("Financial Health")
    render_financial_section(selected_companies)
    st.markdown("")

    st.subheader("Management Due Diligence")
    st.markdown("")

    render_qa_section()

# python -m streamlit run app.py