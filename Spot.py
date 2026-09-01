import requests
import re
import csv
from datetime import datetime
import os

def get_lithium_data():
    url = "https://metalcharts.org/lithium-price"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        text = response.text
        
        # ============================================
        # 1. PRICE - ALWAYS AVAILABLE
        # ============================================
        price_match = re.search(r'/metals/lc[^$]*\$([\d,]+\.\d{2})', text)
        if not price_match:
            price_match = re.search(r'lithium price is \$([\d,]+\.\d{2})', text)
        
        price = float(price_match.group(1).replace(',', '')) if price_match else None
        
        # ============================================
        # 2. CHANGE USD - ALWAYS AVAILABLE
        # ============================================
        change_match = re.search(r'([+-])\$([\d,]+\.\d{2})', text)
        change_usd = None
        if change_match:
            sign = change_match.group(1)
            value = change_match.group(2).replace(',', '')
            change_usd = float(f"{sign}{value}")
        
        # ============================================
        # 3. PERCENTAGE - ALWAYS AVAILABLE
        # ============================================
        percent_match = re.search(r'([+-]\d+\.\d{2})%', text)
        percent_change = percent_match.group(1) if percent_match else None
        
        # ============================================
        # 4. UPDATE TIME - ALWAYS AVAILABLE
        # ============================================
        time_match = re.search(r'Updated ([A-Za-z]+ \d{1,2}, \d{4}, \d{1,2}:\d{2} [AP]M [A-Z+-]+)', text)
        update_time = time_match.group(1) if time_match else None
        
        # ============================================
        # 5. 24h RANGE - ALWAYS AVAILABLE
        # ============================================
        range_match = re.search(r'\$([\d,]+\.\d{2}) to \$([\d,]+\.\d{2})', text)
        range_low = None
        range_high = None
        if range_match:
            range_low = float(range_match.group(1).replace(',', ''))
            range_high = float(range_match.group(2).replace(',', ''))
        
        # ============================================
        # 6. BID / ASK - ALWAYS AVAILABLE
        # ============================================
        bid_ask_match = re.search(r'\$([\d,]+\.\d{2}) / \$([\d,]+\.\d{2})', text)
        bid = None
        ask = None
        if bid_ask_match:
            bid = float(bid_ask_match.group(1).replace(',', ''))
            ask = float(bid_ask_match.group(2).replace(',', ''))
        
        # ============================================
        # 7. ALL-TIME HIGH - ALWAYS AVAILABLE
        # ============================================
        ath_match = re.search(r'All-Time High[\s\n]*\$([\d,]+\.\d{2})\(([A-Za-z]+ \d{1,2}, \d{4})\)', text)
        ath_price = None
        ath_date = None
        if ath_match:
            ath_price = float(ath_match.group(1).replace(',', ''))
            ath_date = ath_match.group(2)
        
        return {
            'price': price,
            'change_usd': change_usd,
            'percent_change': percent_change,
            'update_time': update_time,
            'range_low': range_low,
            'range_high': range_high,
            'bid': bid,
            'ask': ask,
            'ath_price': ath_price,
            'ath_date': ath_date,
            'scrape_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'scrape_date': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def todays_data_exists(filename="lithium_data.csv"):
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not os.path.isfile(filename):
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row and row[0] == today:
                    return True
        return False
    except:
        return False

def save_to_csv(data, filename="lithium_data.csv"):
    today = datetime.now().strftime('%Y-%m-%d')
    file_exists = os.path.isfile(filename)
    
    if todays_data_exists(filename):
        print(f"⚠️ Data for {today} already exists. Skipping save.")
        return False
    
    try:
        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    'Date',
                    'Price_USD',
                    'Change_USD',
                    'Change_Percent',
                    'Update_Time',
                    'Scrape_Time',
                    'Range_Low',
                    'Range_High',
                    'Bid',
                    'Ask',
                    'ATH_Price',
                    'ATH_Date'
                ])
            
            writer.writerow([
                data['scrape_date'],
                data['price'],
                data['change_usd'],
                data['percent_change'],
                data['update_time'],
                data['scrape_time'],
                data['range_low'],
                data['range_high'],
                data['bid'],
                data['ask'],
                data['ath_price'],
                data['ath_date']
            ])
            
            print(f"✅ Saved: ${data['price']:,.2f} | Change: {data['change_usd']} ({data['percent_change']}%)")
            return True
            
    except Exception as e:
        print(f"ERROR saving: {e}")
        return False

# Run
if __name__ == "__main__":
    print("=" * 70)
    print("🔋 LITHIUM PRICE SCRAPER")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if todays_data_exists():
        print(f"ℹ️ Data for {today} already exists.")
        print(f"   Run this script tomorrow to get new data.")
    else:
        print("📡 Fetching fresh data...")
        data = get_lithium_data()
        
        if data and data['price']:
            print("\n📈 DATA RETRIEVED:")
            print(f"   Price: ${data['price']:,.2f}")
            print(f"   Change: {data['change_usd']} ({data['percent_change']}%)")
            print(f"   Updated: {data['update_time']}")
            print(f"   Range: ${data['range_low']:,.2f} - ${data['range_high']:,.2f}")
            print(f"   Bid/Ask: ${data['bid']:,.2f} / ${data['ask']:,.2f}")
            print(f"   ATH: ${data['ath_price']:,.2f} ({data['ath_date']})")
            
            if save_to_csv(data):
                print("\n✅ New data saved successfully!")
                
                # Show what was saved
                print("\n📊 Saved to CSV:")
                print(f"   Date: {data['scrape_date']}")
                print(f"   Price: ${data['price']:,.2f}")
                print(f"   Change: {data['change_usd']} ({data['percent_change']}%)")
                print(f"   Updated: {data['update_time']}")
                print(f"   Range: ${data['range_low']:,.2f} - ${data['range_high']:,.2f}")
                print(f"   Bid/Ask: ${data['bid']:,.2f} / ${data['ask']:,.2f}")
                print(f"   ATH: ${data['ath_price']:,.2f} ({data['ath_date']})")
            else:
                print("\n❌ Failed to save data")
        else:
            print("\n❌ Scraping failed - no data retrieved")
    
    print("\n" + "=" * 70)