from pytrends.request import TrendReq
import pandas as pd
import plotly.graph_objects as go

import streamlit as st

# =========================
# INSTELLINGEN
# =========================

ZOEKTERMEN = [
    "Clayton Valley",
    "Century Lithium",
    "lithium stocks"
]

PERIODE = "today 1-m"
LAND = ""  # wereldwijd

# Stijl van het label boven elke graph (lettertype + grootte),
# in dezelfde format als het 'Google Trends' label.
LABEL_STYLE = (
    "font-family:Arial, sans-serif; font-size:15px; "
    "font-weight:400; color:#4b5563;"
)


# =========================
# GOOGLE TRENDS
# =========================

pytrends = TrendReq(
    hl="en-US",
    tz=0
)


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_trends_data(term, periode=PERIODE, land=LAND):
    """Haal de interest-over-time data op voor één zoekterm (1 dag gecachet).

    Google rate-limits snelle achter elkaar komende verzoeken (HTTP 429).
    Daarom: pauze tussen verzoeken + retry met backoff. Blijft het misgaan,
    dan geven we None terug zodat de app doorloopt met een nette melding.
    """
    import time
    from pytrends.exceptions import TooManyRequestsError

    max_pogingen = 3
    for poging in range(max_pogingen):
        try:
            pytrends.build_payload(
                kw_list=[term],
                timeframe=periode,
                geo=land
            )

            data = pytrends.interest_over_time()
            break
        except TooManyRequestsError:
            if poging == max_pogingen - 1:
                print(f"Google Trends 429 (rate limit) voor '{term}' — overslaan.")
                return None
            time.sleep(15 * (poging + 1))  # 15s, 30s, ... wachten en opnieuw
        except Exception as e:
            print(f"Trends-fout voor '{term}': {e}")
            return None
    else:
        return None

    # Pauze: voorkomt dat de volgende term-tegen-query direct een 429 krijgt
    time.sleep(3)

    if data is None or data.empty:
        return None

    if "isPartial" in data.columns:
        data = data.drop(columns=["isPartial"])

    return data


def build_trends_figure(term, data):
    """Bouw de Plotly-graph voor één zoekterm (zonder titel).

    Plotly rendert als vector in de browser, net als de andere charts in de
    app — de datumlabels zijn zo altijd haarscherp (geen raster zoals het
    oude matplotlib).  Stijl blijft gelijk: blauwe lijn, alleen eerste en
    laatste datum op de x-as, y-as alleen 0 en 100, geen grid/randen.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data.index,
        y=data[term],
        mode="lines",
        line=dict(color="#1f77b4", width=2),
        hovertemplate="%{x|%d %b %Y} · %{y:.0f}<extra></extra>",
    ))

    # Alleen eerste en laatste datum op de x-as
    fig.update_xaxes(
        tickvals=[data.index[0], data.index[-1]],
        ticktext=[
            data.index[0].strftime("%d %b %Y"),
            data.index[-1].strftime("%d %b %Y"),
        ],
        tickfont=dict(family="Arial, sans-serif", size=14, color="#4b5563"),
        showline=False, zeroline=False,
        ticks="",
    )

    # Alleen 0 en 100 op de y-as
    fig.update_yaxes(
        tickvals=[0, 100],
        tickfont=dict(family="Arial, sans-serif", size=14, color="#4b5563"),
        showline=False, zeroline=False,
        ticks="",
    )

    fig.update_layout(
        dragmode=False, hovermode="closest",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=30),
        font=dict(family="Arial, sans-serif"),
        showlegend=False,
        height=240,
    )
    return fig


def get_7d_change(term):
    """Bereken de 7d-vs-vorige-7d change (%) voor één zoekterm.
    Returns None als er te weinig data is."""
    data = fetch_trends_data(term)
    if data is None or len(data) < 14:
        return None

    huidig_gemiddelde = data[term].tail(7).mean()
    vorig_gemiddelde = data[term].iloc[-14:-7].mean()

    if vorig_gemiddelde > 0:
        return (huidig_gemiddelde - vorig_gemiddelde) / vorig_gemiddelde * 100
    return None


# =========================
# 7D VS VORIGE 7D (CLI-rapport)
# =========================

if __name__ == "__main__":

    for term in ZOEKTERMEN:

        data = fetch_trends_data(term)

        if data is None:
            print(f"\nGeen data gevonden voor: {term}")
            continue

        huidige_7d = data[term].tail(7)
        vorige_7d = data[term].iloc[-14:-7]

        huidig_gemiddelde = huidige_7d.mean()
        vorig_gemiddelde = vorige_7d.mean()

        if vorig_gemiddelde > 0:
            change = (
                (huidig_gemiddelde - vorig_gemiddelde)
                / vorig_gemiddelde
            ) * 100
        else:
            change = None

        print("\n" + "=" * 40)
        print(term)
        print("=" * 40)

        print(f"Huidige 7d gemiddelde: {huidig_gemiddelde:.1f}")
        print(f"Vorige 7d gemiddelde:  {vorig_gemiddelde:.1f}")

        if change is not None:
            print(f"7d change:             {change:+.1f}%")
        else:
            print("7d change:             Niet genoeg data")
