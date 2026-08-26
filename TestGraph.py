import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from zoneinfo import ZoneInfo

# Tickers en bedrijfsnamen
tickers = {
    "LAC": "Lithium Americas Corp.",
    "ABAT": "American Battery Technology",
    "IONR": "Ioneer Ltd",
    "LCE.V": "Century Lithium Corp.",
    "NILI.V": "Surge Battery Metals",
    "NVLH.V": "Nevada Lithium"
}

print("📊 Bezig met ophalen van intraday data voor vandaag...\n")

# Data opslaan in een dictionary
data_dict = {}

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d", interval="5m")
        
        if not data.empty:
            data.index = data.index.tz_convert(
                ZoneInfo("America/New_York")
            )
            
            data_dict[ticker] = {
                'name': name,
                'data': data,
                'currency': stock.info.get('currency', 'USD')
            }
            
            print(
                f"✅ {name} ({ticker}): "
                f"{len(data)} datapunten geladen"
            )
        else:
            print(
                f"⚠️ Geen intraday data voor "
                f"{name} ({ticker})"
            )
            
    except Exception as e:
        print(f"❌ Fout bij {ticker}: {e}")

# Controleer of er data is
if not data_dict:
    print("\n❌ Geen data beschikbaar. Probeer het later opnieuw.")
    exit()

# Maak één grafiek
fig, ax = plt.subplots(figsize=(14, 8))

# Kleuren voor de lijnen
colors = [
    '#1f77b4',
    '#ff7f0e',
    '#2ca02c',
    '#d62728',
    '#9467bd',
    '#8c564b',
    '#e377c2'
]

# Plot elke ticker
for idx, (ticker, info) in enumerate(data_dict.items()):
    data = info['data']
    name = info['name']
    currency = info['currency']
    
    if 'Close' in data.columns:
        prices = data['Close']
    else:
        prices = data['Adj Close']
    
    ax.plot(
        data.index,
        prices,
        label=f"{name} ({ticker}) - {currency}",
        linewidth=2,
        color=colors[idx % len(colors)]
    )

# Legenda onder de grafiek
ax.legend(
    loc='upper center',
    bbox_to_anchor=(0.5, -0.16),
    ncol=2,
    fontsize=9,
    frameon=True,
    fancybox=False,
    framealpha=0.9
)

# Amerikaanse tijd onderaan
ax.xaxis.set_major_formatter(
    mdates.DateFormatter(
        '%I:%M %p',
        tz=ZoneInfo("America/New_York")
    )
)

ax.xaxis.set_major_locator(
    mdates.HourLocator(
        interval=2,
        tz=ZoneInfo("America/New_York")
    )
)

# Tijdlabels recht
plt.xticks(rotation=0)

# Y-as met 2 decimalen
ax.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, p: f'{x:.2f}')
)

# Extra ruimte voor de legenda
plt.tight_layout()
plt.subplots_adjust(bottom=0.27)

# Opslaan
plt.savefig(
    'lithium_koersen_vandaag.png',
    dpi=300,
    bbox_inches='tight'
)

print(
    "\n✅ Grafiek opgeslagen als "
    "'lithium_koersen_vandaag.png'"
)

# Tonen
plt.show()

print("\n✨ Alle bedrijven staan in één grafiek!")