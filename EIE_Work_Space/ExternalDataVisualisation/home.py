from flask import Flask, jsonify, render_template
import requests
import threading
import time

app = Flask(__name__)

# URLs of the external web servers
urls = {
    "price": "https://icelec50015.azurewebsites.net/price",
    "sun": "https://icelec50015.azurewebsites.net/sun",
    "demand": "https://icelec50015.azurewebsites.net/demand",
    "deferables": "https://icelec50015.azurewebsites.net/deferables",
    "yesterday": "https://icelec50015.azurewebsites.net/yesterday"
}

latest_data = {}

def fetch_data(url):
    response = requests.get(url)
    data = response.json()
    return data

def extract_data(data, keys, key_for_list=None):
    if isinstance(data, list) and key_for_list:
        return {key_for_list: data}
    elif isinstance(data, dict):
        return {key: data.get(key, 'N/A') for key in keys}
    else:
        return {key: 'N/A' for key in keys}

def continuously_fetch_data():
    global latest_data
    while True:
        try:
            price_data = fetch_data(urls["price"])
            sun_data = fetch_data(urls["sun"])
            demand_data = fetch_data(urls["demand"])
            deferables_data = fetch_data(urls["deferables"])
            yesterday_data = fetch_data(urls["yesterday"])
            
            keys_price = ['buy_price', 'sell_price', 'day', 'tick']
            keys_sun = ['sun', 'tick']
            keys_demand = ['demand', 'day', 'tick']
            keys_deferables = []  # No specific keys, since we want the whole list
            # No keys for yesterday since we want the entire list

            price_data_extracted = extract_data(price_data, keys_price)
            sun_data_extracted = extract_data(sun_data, keys_sun)
            demand_data_extracted = extract_data(demand_data, keys_demand)
            deferables_data_extracted = extract_data(deferables_data, keys_deferables, key_for_list='deferables')
            yesterday_data_extracted = {"yesterday": yesterday_data}  # Store the entire list
            
            latest_data = {
                "price_data": price_data_extracted,
                "sun_data": sun_data_extracted,
                "demand_data": demand_data_extracted,
                "deferables_data": deferables_data_extracted,
                "yesterday_data": yesterday_data_extracted,
            }
        except Exception as e:
            print(f"Error fetching data: {e}")
        
        time.sleep(3.5)

# Start fetching data continuously in a separate thread
threading.Thread(target=continuously_fetch_data, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    return jsonify(latest_data)

if __name__ == '__main__':
    app.run(debug=True)
