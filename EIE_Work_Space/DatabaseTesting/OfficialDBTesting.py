import psycopg2
import requests
import time
import json
from tabulate import tabulate

# Database connection details
host = "chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com"
port = "5432"  # Default PostgreSQL port
dbname = "initial_db"
user = "postgres"
password = "ChargeIt2024"

# Connect to the database
try:
    connection = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    cursor = connection.cursor()
    print("Connected to the database successfully")

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
except Exception as e:
    print(f"Error connecting to the database: {e}")

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

def delete_all_data():
    tables = ["price_data", "sun_data", "demand_data", "deferables_data", "yesterday_data"]
    try:
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        connection.commit()
        print("All data deleted successfully")
    except Exception as e:
        print(f"Error deleting data: {e}")
        connection.rollback()

def view_all_data():
    tables = ["price_data", "sun_data", "demand_data", "deferables_data", "yesterday_data"]
    try:
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            print(f"\nContents of {table}:")
            print(tabulate(rows, headers=[desc[0] for desc in cursor.description], tablefmt='psql'))
    except Exception as e:
        print(f"Error fetching data: {e}")

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
            
            #if tick == 1:
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
        #time.sleep(2)

# Start fetching data continuously
continuously_fetch_data()

# Example usage of the new functions
# Uncomment the following lines to use the delete and view functions

# delete_all_data()
# view_all_data()
