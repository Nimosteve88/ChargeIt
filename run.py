import requests
import time

# URLs of the external web servers
urls = {
    "price": "https://icelec50015.azurewebsites.net/price",
    "sun": "https://icelec50015.azurewebsites.net/sun",
    "demand": "https://icelec50015.azurewebsites.net/demand",
    "deferables": "https://icelec50015.azurewebsites.net/deferables",
    "yesterday": "https://icelec50015.azurewebsites.net/yesterday"
}

def fetch_data(url):
    response = requests.get(url)
    data = response.json()
    return data

def extract_data(data, keys):
    if isinstance(data, list):
        return {key: data[i] if i < len(data) else 'N/A' for i, key in enumerate(keys)}
    elif isinstance(data, dict):
        return {key: data.get(key, 'N/A') for key in keys}
    else:
        return {key: 'N/A' for key in keys}

def continuously_fetch_data():
    while True:
        try:
            price_data = fetch_data(urls["price"])
            sun_data = fetch_data(urls["sun"])
            demand_data = fetch_data(urls["demand"])
            deferables_data = fetch_data(urls["deferables"])
            yesterday_data = fetch_data(urls["yesterday"])
            
            keys_price = ['buy_price', 'sell_price', 'day', 'tick']
            keys_sun = ['sunrise', 'sunset', 'day', 'tick']
            keys_demand = ['demand', 'day', 'tick']
            keys_deferables = ['deferables', 'day', 'tick']
            keys_yesterday = ['yesterday', 'day', 'tick']

            price_data_extracted = extract_data(price_data, keys_price)
            sun_data_extracted = extract_data(sun_data, keys_sun)
            demand_data_extracted = extract_data(demand_data, keys_demand)
            deferables_data_extracted = extract_data(deferables_data, keys_deferables)
            yesterday_data_extracted = extract_data(yesterday_data, keys_yesterday)
            
            day = price_data_extracted['day']
            tick = price_data_extracted['tick']
            
            print(f"--------------------DATA FOR DAY {day}, TICK {tick}--------------------")
            print(f"Buy Price: {price_data_extracted['buy_price']}, Sell Price: {price_data_extracted['sell_price']}")
            print(f"Sunrise: {sun_data_extracted['sunrise']}, Sunset: {sun_data_extracted['sunset']}")
            print(f"Demand: {demand_data_extracted['demand']}")
            print(f"Deferables: {deferables_data_extracted['deferables']}")
            print(f"Yesterday: {yesterday_data_extracted['yesterday']}")
            print("----------------------------------------------------------\n")
        except Exception as e:
            print(f"Error fetching data: {e}")
        
        # Sleep for 5 seconds to ensure fetching data every tick
        time.sleep(5)

# Start fetching data continuously
continuously_fetch_data()

