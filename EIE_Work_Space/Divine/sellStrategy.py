import psycopg2
import pandas as pd
import requests
import time
import json

url = "https://icelec50015.azurewebsites.net/price"

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

host = "chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com"
port = "5432"  # Default PostgreSQL port
dbname = "initial_db"
user = "postgres"
password = "ChargeIt2024"

# Database connection parameters
db_params = {
    'dbname': dbname,
    'user': user,
    'password': password,
    'host': host,
    'port': port
}

# Function to fetch the last N sell prices from the current day
def fetch_last_n_sell_prices(conn, current_day, current_tick, n):
    query = f"""
    SELECT sell_price FROM price_data
    WHERE day = {current_day} AND tick < {current_tick}
    ORDER BY tick DESC
    LIMIT {n}
    """
    return pd.read_sql(query, conn)['sell_price'].tolist()

# Function to fetch the last N sell prices from the previous day
def fetch_last_n_sell_prices_yesterday(conn, n):
    query = f"""
    SELECT sell_price FROM yesterday_data
    ORDER BY tick DESC
    LIMIT {n}
    """
    return pd.read_sql(query, conn)['sell_price'].tolist()

# Function to implement the trading strategy
def selling_strategy(conn, current_day, current_tick, current_sell_price):
    try:
        last_4_sell_prices = fetch_last_n_sell_prices(conn, current_day, current_tick, 4)
        
        # If there are not enough values, fetch the remaining from yesterday's data
        if len(last_4_sell_prices) < 4:
            remaining_needed = 4 - len(last_4_sell_prices)
            last_4_sell_prices += fetch_last_n_sell_prices_yesterday(conn, remaining_needed)
        
        # Check if we have at least 4 previous values
        # if len(last_4_sell_prices) < 4:
        #     print(f"Not enough data to make a decision at day {current_day}, tick {current_tick}.")
        #     print("HOLD")

        # Include the current sell price in the average calculation
        all_sell_prices = last_4_sell_prices + [current_sell_price]
        avg_sell_price = sum(all_sell_prices) / len(all_sell_prices)
        prev_sell_price = last_4_sell_prices[0]  # The most recent previous sell price

        if current_sell_price > prev_sell_price * 1.15:
            if current_sell_price > avg_sell_price * 1.45:
                print(f"tick: {current_tick},  SELL")
            else:
                print(f"tick: {current_tick},  HOLD")
        elif current_sell_price < prev_sell_price and current_sell_price > avg_sell_price * 1.5:
            print(f"tick: {current_tick},  SELL")
        else:
            print(f"tick: {current_tick},  HOLD")
    except Exception as e:
        print(f"Error fetching data: {e}")

# Main function to run the trading algorithm
def main():
    conn = psycopg2.connect(**db_params)
    while True:
        # Example data: replace this with actual fetch from your live data source
        price_data = fetch_data(url)
        
        keys_price = ['buy_price', 'sell_price', 'day', 'tick']
        
        price_data_extracted = extract_data(price_data, keys_price)
        
        day = price_data_extracted.get('day')
        tick = price_data_extracted.get('tick')
        current_sell_price = price_data_extracted.get('sell_price')
        selling_strategy(conn, day, tick, current_sell_price)
        time.sleep(4.7)
    conn.close()

if __name__ == "__main__":
    main()
