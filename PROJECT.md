# PROJECT.md – Lithium Juniors Comparison (Streamlit Cloud)

## Doel
Interactieve vergelijking van junior lithium-ontwikkelaars in Nevada (pre-revenue). Bedrijven hebben nog geen inkomsten: **studie-economie, kaspositie/cash burn, mijlpalen & financieringsvooruitzichten zijn belangrijker dan omzet/EBITDA** (zoals bij volwassen bedrijven).

## Kernonderwerpen die de app toont
- Project studies (NPV, IRR, CAPEX, resources, grade) – vergelijking over de tijd
- Kaspositie, cash burn, hefboomwerking/dilutierisico, marktkapitalisatie
- Route naar productie: mijlpalen, vergunningen, FID, bronverwijzingen
- Marktsentiment: koers, zoekinteresse, nieuws

## Let op (domein-specifiek)
- Fasen MRE → PEA → PFS → FS → FID/permitted zijn de "trechter" naar productie
- Capex is groot t.o.v. kleine beurswaarde → value ratios (NPV/market cap, NPV/capex) zijn essentieel
- Placeholders voor niet-Century bedrijven in de data

## Structuur (alleen 4 bestanden)
| Bestand | Rol |
|---|---|
| `app.py` | Orchestrator: welke secties, volgorde |
| `config.py` | Alle data-input: bedrijven, studies, timeline |
| `data.py` | Data ophalen & berekenen |
| `views.py` | Alle scherm-weergave |

## Techniek
- Streamlit Cloud, Yahoo Finance, SerpApi (Google Trends), Hugging Face (financiële data)
- Caching via `st.cache_data`

## Lithium Futures (live scrape via Playwright)
De term-structure-grafiek ("Lithium Futures Prices", sectie tussen de
Equity/returns-tabel en Google Trends) wordt **live** gescraped van metal.com
met Playwright (headless Chromium) — er is bewust géén fallback-afbeelding.

Browser-install stappen:

1. **Lokaal**: `pip install -r requirements.txt`, daarna één keer
   `python -m playwright install chromium` (de app doet dit ook automatisch
   bij de eerste scrape, gecached via `st.cache_resource`).
2. **Streamlit Cloud**:
   - `playwright` staat in `requirements.txt`.
   - `packages.txt` bevat de apt-libraries die Chromium nodig heeft; Streamlit
     Cloud installeert die automatisch bij de deploy.
   - De Chromium-browser zelf wordt bij de eerste app-run gedownload door
     `_ensure_playwright_browser()` in `data.py` (één keer per app-lifetime,
     daarna gecached). Duurt ~1 minuut bij een verse deploy.
3. De scrape zelf is gecached met `st.cache_data` (TTL 1 uur) in
   `get_lithium_futures()` — de site wordt dus maximaal 1x per uur belast.
