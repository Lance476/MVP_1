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