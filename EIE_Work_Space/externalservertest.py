import requests
import psycopg2
import pandas as pd
import json

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

def fetch_last_n_sell_prices(conn, current_day, current_tick, n):
    query = f"""
    SELECT sell_price FROM price_data
    WHERE day = {current_day} AND tick < {current_tick}
    ORDER BY tick DESC
    LIMIT {n}
    """
    return pd.read_sql(query, conn)['sell_price'].tolist()

def fetch_last_n_sell_prices_yesterday(conn, n):
    query = f"""
    SELECT sell_price FROM yesterday_data
    ORDER BY tick DESC
    LIMIT {n}
    """
    return pd.read_sql(query, conn)['sell_price'].tolist()

def trading_strategy(conn, current_day, current_tick, current_sell_price):
    global decision
    try:
        last_4_sell_prices = fetch_last_n_sell_prices(conn, current_day, current_tick, 4)
        
        if len(last_4_sell_prices) < 4:
            remaining_needed = 4 - len(last_4_sell_prices)
            last_4_sell_prices += fetch_last_n_sell_prices_yesterday(conn, remaining_needed)
        
        all_sell_prices = last_4_sell_prices + [current_sell_price]
        avg_sell_price = sum(all_sell_prices) / len(all_sell_prices)
        prev_sell_price = last_4_sell_prices[0]

        if current_sell_price > prev_sell_price * 1.15:
            if current_sell_price > avg_sell_price * 1.45:
                decision = "SELL"
            else:
                decision = "HOLD"
        elif current_sell_price < prev_sell_price and current_sell_price > avg_sell_price * 1.5:
            decision = "SELL"
        else:
            decision = "HOLD"
    except Exception as e:
        print(f"Error fetching data: {e}")

def continuously_fetch_data():
    last_tick = None  # Initialize the last_tick variable

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
            
            current_tick = price_data_extracted.get('tick', None)

            if current_tick != last_tick:  # Only perform tasks if the tick is different
                # Insert data into the respective tables
                insert_data_into_db("price_data", price_data_extracted)
                insert_data_into_db("sun_data", sun_data_extracted)
                insert_data_into_db("demand_data", demand_data_extracted)
                
                day = price_data_extracted.get('day', 'N/A')
                tick = price_data_extracted.get('tick', 'N/A')
                
                if tick == 1:
                    update_deferables_data(deferables_data, day, tick)
                    update_yesterday_data(yesterday_data)
                
                trading_strategy(connection, day, tick, price_data_extracted.get('sell_price'))

                print(f"--------------------DATA FOR DAY {day}, TICK {tick}--------------------")
                print(f"Buy Price: {price_data_extracted.get('buy_price')}, Sell Price: {price_data_extracted.get('sell_price')}")
                print(f"Sun: {sun_data_extracted.get('sun')}")
                print(f"Demand: {demand_data_extracted.get('demand')}")
                print("----------------------------------------------------------\n")
                print("Data inserted into the database successfully")
                
                last_tick = current_tick  # Update the last_tick after processing
        except Exception as e:
            print(f"Error fetching data: {e}")
        
        # Remove time.sleep(4.5)

if __name__ == "__main__":
    continuously_fetch_data()
