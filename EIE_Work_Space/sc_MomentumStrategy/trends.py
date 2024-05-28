from flask import Flask, jsonify, render_template
import psycopg2
import requests
import time
import json
import threading
import pandas as pd

app = Flask(__name__)

# Database connection details
host = "chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com"
port = "5432"  # Default PostgreSQL port
dbname = "initial_db"
user = "postgres"
password = "ChargeIt2024"

# Connect to the database
connection = psycopg2.connect(
    host=host,
    port=port,
    dbname=dbname,
    user=user,
    password=password
)
cursor = connection.cursor()

# Create tables if they don't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS price_data (
    id SERIAL PRIMARY KEY,
    buy_price FLOAT,
    sell_price FLOAT,
    day INT,
    tick INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sun_data (
    id SERIAL PRIMARY KEY,
    sun FLOAT,
    tick INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS demand_data (
    id SERIAL PRIMARY KEY,
    demand FLOAT,
    day INT,
    tick INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS deferables_data (
    id SERIAL PRIMARY KEY,
    demand FLOAT,
    day INT,
    tick INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS yesterday_data (
    id SERIAL PRIMARY KEY,
    buy_price FLOAT,
    demand FLOAT,
    sell_price FLOAT,
    tick INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
connection.commit()

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

def extract_data(data, keys, key_for_list=None):
    if isinstance(data, list) and key_for_list:
        return {key_for_list: json.dumps(data)}
    elif isinstance(data, dict):
        return {key: data.get(key, None) for key in keys}
    else:
        return {key: None for key in keys}

def insert_data_into_db(table_name, data):
    columns = ', '.join(data.keys())
    values = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
    try:
        cursor.execute(query, list(data.values()))
        connection.commit()
    except Exception as e:
        print(f"Error inserting data into {table_name}: {e}")
        connection.rollback()

def update_deferables_data(deferables_data, day, tick):
    try:
        cursor.execute("DELETE FROM deferables_data")
        for deferable in deferables_data:
            cursor.execute(
                "INSERT INTO deferables_data (demand, day, tick) VALUES (%s, %s, %s)",
                (deferable['energy'], day, tick)
            )
        connection.commit()
    except Exception as e:
        print(f"Error updating deferables_data: {e}")
        connection.rollback()

def update_yesterday_data(yesterday_data):
    try:
        cursor.execute("DELETE FROM yesterday_data")
        for entry in yesterday_data:
            cursor.execute(
                "INSERT INTO yesterday_data (buy_price, demand, sell_price, tick) VALUES (%s, %s, %s, %s)",
                (entry['buy_price'], entry['demand'], entry['sell_price'], entry['tick'])
            )
        connection.commit()
    except Exception as e:
        print(f"Error updating yesterday_data: {e}")
        connection.rollback()

def calculate_cumulative_average(df, column):
    df[f'cumulative_avg_{column}'] = df[column].expanding().mean()
    return df[f'cumulative_avg_{column}'].tolist()

def continuously_fetch_data():
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
            keys_deferables = ['demand']  # Extracting energy as demand
            keys_yesterday = ['buy_price', 'demand', 'sell_price', 'tick']

            price_data_extracted = extract_data(price_data, keys_price)
            sun_data_extracted = extract_data(sun_data, keys_sun)
            demand_data_extracted = extract_data(demand_data, keys_demand)
            
            # Insert data into the respective tables
            insert_data_into_db("price_data", price_data_extracted)
            insert_data_into_db("sun_data", sun_data_extracted)
            insert_data_into_db("demand_data", demand_data_extracted)
            
            day = price_data_extracted.get('day', 'N/A')
            tick = price_data_extracted.get('tick', 'N/A')
            
            if tick == 1:
                update_deferables_data(deferables_data, day, tick)
                update_yesterday_data(yesterday_data)
            
            print(f"--------------------DATA FOR DAY {day}, TICK {tick}--------------------")
            print(f"Buy Price: {price_data_extracted.get('buy_price')}, Sell Price: {price_data_extracted.get('sell_price')}")
            print(f"Sun: {sun_data_extracted.get('sun')}")
            print(f"Demand: {demand_data_extracted.get('demand')}")
            print("----------------------------------------------------------\n")
            print("Data inserted into the database successfully")
        except Exception as e:
            print(f"Error fetching data: {e}")
        
        # Sleep for 3.5 seconds to ensure fetching data every interval
        time.sleep(3.5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    try:
        cursor.execute("SELECT tick, buy_price, sell_price FROM price_data ORDER BY tick ASC")
        rows = cursor.fetchall()
        if not rows:
            return jsonify({"error": "No data available"}), 500

        df = pd.DataFrame(rows, columns=['tick', 'buy_price', 'sell_price'])

        # Ensure all ticks are present
        all_ticks = pd.DataFrame({'tick': range(df['tick'].min(), df['tick'].max() + 1)})
        df = all_ticks.merge(df, on='tick', how='left').fillna(method='ffill')

        cumulative_buy_avg = calculate_cumulative_average(df, 'buy_price')
        cumulative_sell_avg = calculate_cumulative_average(df, 'sell_price')

        cursor.execute("SELECT demand FROM demand_data ORDER BY id DESC LIMIT 1")
        demand_row = cursor.fetchone()
        current_demand = demand_row[0] if demand_row else None

        cursor.execute("SELECT day FROM price_data ORDER BY id DESC LIMIT 1")
        day_row = cursor.fetchone()
        current_day = day_row[0] if day_row else None

        cursor.execute("SELECT sun FROM sun_data ORDER BY id DESC LIMIT 1")
        sun_row = cursor.fetchone()
        current_sun = sun_row[0] if sun_row else None
        
        data = {
            "ticks": df['tick'].tolist(),
            "cumulative_buy_avg": cumulative_buy_avg,
            "cumulative_sell_avg": cumulative_sell_avg,
            "current_demand": current_demand,
            "current_day": current_day,
            "current_sun": current_sun
        }
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    fetch_thread = threading.Thread(target=continuously_fetch_data)
    fetch_thread.start()
    app.run(debug=True)
