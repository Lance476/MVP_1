from playwright.sync_api import sync_playwright
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import sys

# Windows-consoles gebruiken vaak cp1252; zonder dit crasht print() op de
# emoji-statusregels hieronder. Op Linux/Streamlit Cloud is dit een no-op.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

def contract_to_month(contract):
    """Converts LC2508 -> Aug 25"""
    year = contract[2:4]  # 25 instead of 2025
    month_num = int(contract[4:6])
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return f"{months[month_num-1]} '{year}"

def scrape_lithium():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        print("Fetching Metal.com...")
        page.goto("https://www-old.metal.com/Lithium", wait_until="networkidle")
        
        try:
            page.click("button:has-text('Got it')", timeout=5000)
            page.wait_for_timeout(1000)
        except:
            pass
        
        futures_data = []
        seen = set()
        rows = page.query_selector_all("div:has-text('LC')")
        
        for row in rows:
            text = row.inner_text()
            if "LC" in text and "CNY" in text:
                parts = text.split()
                clean = [p for p in parts if p.replace(',', '').replace('.', '').isdigit() or p.startswith('LC')]
                
                if len(clean) >= 6 and clean[0].startswith('LC') and clean[0] not in seen:
                    try:
                        futures_data.append({
                            "contract": clean[0],
                            "latest": float(clean[1].replace(',', '')),
                            "open": float(clean[2].replace(',', '')),
                            "high": float(clean[3].replace(',', '')),
                            "low": float(clean[4].replace(',', ''))
                        })
                        seen.add(clean[0])
                    except:
                        pass
        
        futures_data.sort(key=lambda x: x['contract'])
        print(f"  ✅ {len(futures_data)} futures found")
        
        browser.close()
        return futures_data

def day_change(data):
    """Dagbeweging (%) van het front-month (eerstvolle) contract:
    latest t.o.v. de openingsprijs van vandaag. None als er geen data is."""
    if not data:
        return None
    front = data[0]
    if not front.get("open"):
        return None
    return (front["latest"] / front["open"] - 1) * 100


def forward_12m(data):
    """Market-implied ~12M forward: het verschil (%) tussen het front-month
    contract en het contract het dichtst bij 12 maanden vooruit.

    Positief  = contango     (markt prijst verder vooruit hoger)
    Negatief  = backwardation (markt prijst verder vooruit lager)

    Zit er geen contract op exact 12 maanden in de data, dan wordt het verst
    genoteerde contract gebruikt en is de horizon korter (bijv. 10M).
    Returns (pct, horizon_maanden, front_label, target_label) of None.
    """
    if not data or len(data) < 2:
        return None
    front = data[0]
    if not front.get("latest"):
        return None
    fy, fm = int(front["contract"][2:4]), int(front["contract"][4:6])

    def _months_after(item):
        iy, im = int(item["contract"][2:4]), int(item["contract"][4:6])
        return (iy - fy) % 100 * 12 + (im - fm)

    # Contract met de grootste horizon (meestal 11-12 maanden bij GFEX)
    target = max(data[1:], key=_months_after)
    horizon = _months_after(target)
    if horizon <= 0 or not target.get("latest"):
        return None
    pct = (target["latest"] / front["latest"] - 1) * 100
    return pct, horizon, contract_to_month(front["contract"]), contract_to_month(target["contract"])


def make_chart_plotly(data):
    """Build the lithium futures term-structure as a Plotly figure.

    Plotly rendert in de browser als vector (HTML/SVG), net als de andere
    charts in de app — daardoor zijn de datums en CNY-waarden net zo scherp
    als de HTML-tekst erboven, i.t.t. een matplotlib-rasterversie.  Stijl
    blijft gelijk aan de oude matplotlib-versie: blauwe lijn, minimalistische
    as, geen grid/randen, max ~6 x-labels.
    Returns a plotly.graph_objects.Figure (or None when there is no data).
    """
    if not data:
        return None

    contracts = [contract_to_month(item['contract']) for item in data]
    current_prices = [item['latest'] for item in data]

    _font = dict(family="Segoe UI, Helvetica Neue, Arial, sans-serif",
                 size=14)

    # Max ~6 labels op de x-as, verspreid (eerst was elke maand te druk).
    label_step = max(1, -(-len(contracts) // 6))
    tick_ids = list(range(0, len(contracts), label_step))
    x_nums = list(range(len(contracts)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_nums, y=current_prices, mode="lines+markers",
        line=dict(color="#1f77b4", width=2),
        marker=dict(color="#1f77b4", size=5),
        customdata=contracts,
        hovertemplate="%{customdata} · ¥%{y:,.0f}<extra></extra>",
    ))

    fig.update_xaxes(
        tickvals=tick_ids,
        ticktext=[contracts[i] for i in tick_ids],
        tickfont=dict(**_font, color="#374151"),
        showline=False, zeroline=False,
        ticks="",
        showticklabels=True,
    )
    fig.update_yaxes(
        tickfont=dict(**_font, color="#6b7280"),
        tickprefix="¥", tickformat=",",
        nticks=5,
        showline=False, zeroline=False,
        ticks="",
    )

    fig.update_layout(
        dragmode=False, hovermode="closest",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=30),
        font=dict(family="Segoe UI, Helvetica Neue, Arial, sans-serif"),
        showlegend=False,
        height=360,
    )
    return fig


def make_chart(data):
    """Build the lithium futures term-structure line chart.

    Style matches the Google Trends charts (Sentiment.py): a simple blue
    line, no in-graph numbers, and a minimalistic price axis on the left.
    Returns the matplotlib Figure (or None when there is no data) without
    saving or showing it, so views.py can render it with st.pyplot() inside
    the Streamlit app.  The standalone `__main__` block below still saves
    the PNG and calls plt.show().
    """
    if not data:
        print("No data!")
        return None

    # Convert contract codes to readable months
    contracts = [contract_to_month(item['contract']) for item in data]
    current_prices = [item['latest'] for item in data]

    # Lettertype matcht de caption onder de grafiek (views.py):
    # Segoe UI / Helvetica Neue / Arial, 14px, normaal gewicht.
    _label_font = {
        "family": ["Segoe UI", "Helvetica Neue", "Arial", "sans-serif"],
        "fontsize": 16,
        "fontweight": "normal",
    }

    # Hoge dpi (300) zodat de gedownscaled PNG naar de kolombreedte scherp
    # blijft — HTML-tekst boven/onder de grafiek is vector (altijd scherp),
    # maar de matplotlib-rasterschaalt in de browser anders wazig bij teksten.
    # Streamlit toont de figuur op dezelfde breedte; hogere dpi alleen meer
    # resolutie.
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    # Zelfde blauwe lijn als de Google Trends graphs
    ax.plot(contracts, current_prices,
            linewidth=2, color='#1f77b4')

    # X-as: contract-maanden, geen tick-streepjes — zelfde font als de
    # caption, en bewust níét vetgedrukt.  Bij veel contracten staat anders
    # elke maand naast elkaar (druk/onsmogelijk te lezen): toon max ~6
    # labels, verspreid over de as.  De lijn zelf toont wel elke maand.
    ax.set_xticks(range(len(contracts)))
    label_step = max(1, -(-len(contracts) // 6))  # ceil-deling
    ax.set_xticks(range(0, len(contracts), label_step))
    ax.set_xticklabels([contracts[i] for i in range(0, len(contracts), label_step)],
                       color="#374151", **_label_font)
    ax.tick_params(axis='x', length=0)

    # Y-as: simpele minimalistische prijs-as links (geen randen, geen
    # tick-streepjes, alleen een paar nette prijslabels)
    ymin, ymax = min(current_prices), max(current_prices)
    spread = ymax - ymin
    if spread > 0:
        step = spread / 4
        yticks = [ymin + i * step for i in range(5)]
    else:
        yticks = [ymin]
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"¥{v:,.0f}" for v in yticks],
                       color="#6b7280", **_label_font)
    ax.tick_params(axis='y', length=0)
    ax.set_ylabel('')

    # Wat headroom zodat de lijn niet tegen de rand plakt
    pad = max(0.05 * spread, 1)
    ax.set_ylim(ymin - pad, ymax + pad)

    # Geen grid en geen randen → minimalistisch
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    return fig

# ===== RUN THE PROGRAM =====
if __name__ == "__main__":
    print("🚀 Lithium Price Scraper")
    print("=" * 40)
    
    data = scrape_lithium()
    
    if data:
        print("\n📊 Data overview:")
        print("-" * 60)
        for item in data:
            month = contract_to_month(item['contract'])
            print(f"  {month}: ¥{item['latest']:,.0f}")
        
        fig = make_chart(data)
        if fig is not None:
            fig.savefig('lithium_chart.png', dpi=150)
            print("✅ Chart saved as 'lithium_chart.png'")
            plt.show()