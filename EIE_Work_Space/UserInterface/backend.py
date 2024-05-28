from flask import Flask, jsonify, render_template
import psycopg2
import requests
import time
import json
import threading
import socket

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

def run_udp_server():
    # Define the server port
    server_port = 12000

    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the server to the localhost at port server_port
    server_socket.bind(('', server_port))

    print('UDP Server running on port', server_port)

    # Create a set to store client addresses
    client_addresses = set()

    while True:
        # Receive a message from a client and print it
        data, client_address = server_socket.recvfrom(2048)
        data = data.decode()
        if len(data) > 0:
            print("Message from Client at", client_address, ":", data)

            # Send confirmation back to the client that sent the message
            confirmation_message = "Message received! "
            server_socket.sendto(confirmation_message.encode(), client_address)

        # Store the client's address
        client_addresses.add(client_address)

        # Send the received message to all other clients
        for addr in client_addresses:
            if addr != client_address:
                server_socket.sendto(data.encode(), addr)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    cursor.execute("""
        SELECT tick, buy_price, sell_price, day, timestamp
        FROM price_data
        WHERE day >= (SELECT MAX(day) FROM price_data) - 1
        ORDER BY timestamp ASC
    """)
    rows = cursor.fetchall()
    
    # Organize data by day
    data_by_day = {}
    for row in rows:
        day = row[3]
        if day not in data_by_day:
            data_by_day[day] = []
        data_by_day[day].append(row)
    
    # Sort ticks within each day
    sorted_rows = []
    for day in sorted(data_by_day.keys()):
        sorted_rows.extend(sorted(data_by_day[day], key=lambda x: x[0]))  # Sort by tick within each day
    
    cursor.execute("SELECT demand FROM demand_data ORDER BY id DESC LIMIT 1")
    current_demand = cursor.fetchone()[0]
    cursor.execute("SELECT day FROM price_data ORDER BY id DESC LIMIT 1")
    current_day = cursor.fetchone()[0]
    cursor.execute("SELECT sun FROM sun_data ORDER BY id DESC LIMIT 1")
    current_sun = cursor.fetchone()[0]
    
    data = {
        "ticks": [row[0] for row in sorted_rows],
        "buy_prices": [row[1] for row in sorted_rows],
        "sell_prices": [row[2] for row in sorted_rows],
        "current_demand": current_demand,
        "current_day": current_day,
        "current_sun": current_sun
    }
    return jsonify(data)

# @app.route('/alldata')
# def alldata():
#     cursor.execute("""
#         SELECT tick, buy_price, sell_price
#         FROM price_data
#     """)
#     rows = cursor.fetchall()
#     sorted_rows = sorted(rows, key=lambda x: x[0])  # Sort rows based on tick

#     data = {
#         "ticks": [row[0] for row in sorted_rows],
#         "buy_prices": [row[1] for row in sorted_rows],
#         "sell_prices": [row[2] for row in sorted_rows],
#     }
#     return jsonify(data)


if __name__ == "__main__":
    fetch_thread = threading.Thread(target=continuously_fetch_data)
    fetch_thread.start()
    
    udp_thread = threading.Thread(target=run_udp_server)
    udp_thread.start()
    
    app.run(debug=True)
