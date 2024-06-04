from flask import Flask, jsonify, render_template, request
import pandas as pd
import requests
import time
import socket
import json, random
import threading
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, select, delete, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from datetime import datetime

app = Flask(__name__)

# Database connection details
DATABASE_URI = "postgresql+psycopg2://postgres:ChargeIt2024@chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com:5432/initial_db"

# Setup SQLAlchemy
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

power = {
    'power_flywheel': '5.5',
    'power_extracted': '6.6'
}

demand = {
    'demand': '0'
}

sunintensity = {
    'sun': '0'
}

energy = {
    'energy_reserve': '80'
}


# Define table structures
class PriceData(Base):
    __tablename__ = 'price_data'
    id = Column(Integer, primary_key=True)
    buy_price = Column(Float)
    sell_price = Column(Float)
    day = Column(Integer)
    tick = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SunData(Base):
    __tablename__ = 'sun_data'
    id = Column(Integer, primary_key=True)
    sun = Column(Float)
    tick = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

class DemandData(Base):
    __tablename__ = 'demand_data'
    id = Column(Integer, primary_key=True)
    demand = Column(Float)
    day = Column(Integer)
    tick = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

class DeferablesData(Base):
    __tablename__ = 'deferables_data'
    id = Column(Integer, primary_key=True)
    demand = Column(Float)
    day = Column(Integer)
    tick = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

class YesterdayData(Base):
    __tablename__ = 'yesterday_data'
    id = Column(Integer, primary_key=True)
    buy_price = Column(Float)
    demand = Column(Float)
    sell_price = Column(Float)
    tick = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables if they don't exist
Base.metadata.create_all(engine)

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

def insert_data_into_db(model_class, data):
    session = Session()
    instance = model_class(**data)
    try:
        session.add(instance)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"Error inserting data into {model_class.__tablename__}: {e}")
    finally:
        session.close()

def update_deferables_data(deferables_data, day, tick):
    session = Session()
    try:
        session.query(DeferablesData).delete()
        for deferable in deferables_data:
            new_data = DeferablesData(demand=deferable['energy'], day=day, tick=tick)
            session.add(new_data)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"Error updating deferables_data: {e}")
    finally:
        session.close()

def calculate_cumulative_average(df, column, window=10):
    return df[column].rolling(window=window, min_periods=1).mean().tolist()

def update_yesterday_data(yesterday_data):
    session = Session()
    try:
        session.query(YesterdayData).delete()
        for entry in yesterday_data:
            new_data = YesterdayData(buy_price=entry['buy_price'], demand=entry['demand'], sell_price=entry['sell_price'], tick=entry['tick'])
            session.add(new_data)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"Error updating yesterday_data: {e}")
    finally:
        session.close()
        
decision = "HOLD"

def fetch_last_n_sell_prices(current_day, current_tick, n):
    session = Session()
    try:
        query = select(PriceData.sell_price).filter(PriceData.day == current_day, PriceData.tick < current_tick).order_by(PriceData.tick.desc()).limit(n)
        result = session.execute(query).scalars().all()
    finally:
        session.close()
    return result

def fetch_last_n_sell_prices_yesterday(n):
    session = Session()
    try:
        query = select(YesterdayData.sell_price).order_by(YesterdayData.tick.desc()).limit(n)
        result = session.execute(query).scalars().all()
    finally:
        session.close()
    return result

def fetch_last_n_buy_prices(current_day, current_tick, n):
    session = Session()
    try:
        query = select(PriceData.buy_price).filter(PriceData.day == current_day, PriceData.tick < current_tick).order_by(PriceData.tick.desc()).limit(n)
        result = session.execute(query).scalars().all()
    finally:
        session.close()
    return result

def fetch_last_n_buy_prices_yesterday(n):
    session = Session()
    try:
        query = select(YesterdayData.buy_price).order_by(YesterdayData.tick.desc()).limit(n)
        result = session.execute(query).scalars().all()
    finally:
        session.close()
    return result

def trading_strategy(current_day, current_tick, current_buy_price, current_sell_price):
    global decision
    try:
        # Fetch the last 4 sell prices
        last_4_sell_prices = fetch_last_n_sell_prices(current_day, current_tick, 4)
        # Fetch the last 4 buy prices
        last_4_buy_prices = fetch_last_n_buy_prices(current_day, current_tick, 4)
        
        if len(last_4_sell_prices) < 4:
            remaining_needed = 4 - len(last_4_sell_prices)
            last_4_sell_prices += fetch_last_n_sell_prices_yesterday(remaining_needed)
        
        if len(last_4_buy_prices) < 4:
            remaining_needed = 4 - len(last_4_buy_prices)
            last_4_buy_prices += fetch_last_n_buy_prices_yesterday(remaining_needed)
        
        all_sell_prices = last_4_sell_prices + [current_sell_price]
        all_buy_prices = last_4_buy_prices + [current_buy_price]
        
        avg_sell_price = sum(all_sell_prices) / len(all_sell_prices)
        avg_buy_price = sum(all_buy_prices) / len(all_buy_prices)
        
        prev_sell_price = last_4_sell_prices[0] if last_4_sell_prices else 0
        prev_buy_price = last_4_buy_prices[0] if last_4_buy_prices else 0
        
        if current_buy_price > prev_buy_price * 1.15:
            if current_buy_price > avg_buy_price * 1.45:
                decision = "SELL"
            else:
                decision = "HOLD"
        elif current_buy_price < prev_buy_price and current_buy_price > avg_buy_price * 1.5:
            decision = "SELL"
        elif current_sell_price < avg_sell_price * 0.85 and current_sell_price < prev_sell_price * 0.85:
            decision = "BUY"
        else:
            decision = "HOLD"
    except Exception as e:
        print(f"Error in trading_strategy: {e}")

def continuously_fetch_data():
    last_tick = None  # Initialize the last_tick variable

    while True:
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
            insert_data_into_db(PriceData, price_data_extracted)
            insert_data_into_db(SunData, sun_data_extracted)
            insert_data_into_db(DemandData, demand_data_extracted)
            
            day = price_data_extracted.get('day', 'N/A')
            tick = price_data_extracted.get('tick', 'N/A')
            demanddata = demand_data_extracted.get('demand', 'N/A')

            if tick == 1:
                update_deferables_data(deferables_data, day, tick)
                update_yesterday_data(yesterday_data)
            
            #update demand dictionary
            global demand, sunintensity
            demand['demand'] = str(demanddata)
            sunintensity['sun'] = str(sun_data_extracted.get('sun'))
            
            current_buy_price = price_data_extracted.get('buy_price', None)
            trading_strategy(day, tick, current_buy_price, price_data_extracted.get('sell_price'))

            # print(f"--------------------DATA FOR DAY {day}, TICK {tick}--------------------")
            # print(f"Buy Price: {price_data_extracted.get('buy_price')}, Sell Price: {price_data_extracted.get('sell_price')}")
            # print(f"Sun: {sun_data_extracted.get('sun')}")
            # print(f"Demand: {demand_data_extracted.get('demand')}")
            # print("----------------------------------------------------------\n")
            # print("Data inserted into the database successfully")
            
            last_tick = current_tick  # Update the last_tick after processing



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    session = Session()
    try:
        result = session.execute(text("""
            SELECT DISTINCT ON (tick) tick, buy_price, sell_price, day, timestamp
            FROM price_data
            WHERE day = (SELECT MAX(day) FROM price_data)
            ORDER BY tick, timestamp ASC
        """)).fetchall()
        
        # rows = [{column: value for column, value in row.items()} for row in result]

        rows = [dict(row._mapping) for row in result]
        
        if not rows:
            return jsonify({"ticks": [], "buy_prices": [], "sell_prices": [], "current_demand": "-", "current_day": "-", "current_sun": "-"})

        # Organize data by day
        data_by_day = {}
        for row in rows:
            day = row['day']
            if day not in data_by_day:
                data_by_day[day] = []
            data_by_day[day].append(row)
        
        # Sort ticks within each day
        sorted_rows = []
        for day in sorted(data_by_day.keys()):
            sorted_rows.extend(sorted(data_by_day[day], key=lambda x: x['tick']))  # Sort by tick within each day
        
        current_demand = session.execute(text("SELECT demand FROM demand_data ORDER BY id DESC LIMIT 1")).scalar() or '-'
        current_day = session.execute(text("SELECT day FROM price_data ORDER BY id DESC LIMIT 1")).scalar() or '-'
        current_sun = session.execute(text("SELECT sun FROM sun_data ORDER BY id DESC LIMIT 1")).scalar() or '-'
        
        data = {
            "ticks": [row['tick'] for row in sorted_rows],
            "buy_prices": [row['buy_price'] for row in sorted_rows],
            "sell_prices": [row['sell_price'] for row in sorted_rows],
            "current_demand": current_demand,
            "current_day": current_day,
            "current_sun": current_sun
        }
        return jsonify(data)
    finally:
        session.close()

@app.route('/alldata')
def alldata():
    session = Session()
    try:
        result = session.execute(text("""
            SELECT tick, buy_price, sell_price, day, timestamp
            FROM price_data
            ORDER BY tick ASC
        """)).fetchall()
        
       # rows = [{column: value for column, value in row.items()} for row in result]

        rows = [dict(row._mapping) for row in result]

        if not rows:
            return jsonify({"ticks": [], "buy_prices": [], "cumulative_buy_avg": [], "cumulative_sell_avg": [], "avg_buy_price_per_tick": [], "sell_prices": []})

        df = pd.DataFrame(rows, columns=['tick', 'buy_price', 'sell_price', 'day', 'timestamp'])

        # Ensure all ticks are present
     

        cumulative_buy_avg = calculate_cumulative_average(df, 'buy_price')
        cumulative_sell_avg = calculate_cumulative_average(df, 'sell_price')

        # Calculate the average buy price per tick
        avg_buy_price_per_tick = df.groupby('tick')['buy_price'].mean().tolist()

        data = {
            "ticks": df['tick'].tolist(),
            #"buy_prices": df['buy_price'].tolist(),
            "cumulative_buy_avg": cumulative_buy_avg,
            "cumulative_sell_avg": cumulative_sell_avg
            #"avg_buy_price_per_tick": avg_buy_price_per_tick,
            #"sell_prices": df['sell_price'].tolist()
        }
        return jsonify(data)
    finally:
        session.close()


@app.route('/decision')
def get_decision():
    global decision
    return jsonify({'decision': decision})

@app.route('/power', methods=['GET', 'POST'])
def get_deferables():
    global power
    if request.method == 'GET':
        # Return the current power
        return jsonify(power)
    elif request.method == 'POST':
        # Update the power with the new data from the request
        data = request.json
        if 'power_flywheel' in data:
            power['power_flywheel'] = data['power_flywheel']
        if 'power_extracted' in data:
            power['power_extracted'] = data['power_extracted']
        return jsonify({'message': 'Data updated', 'data': power}), 200
    
@app.route('/demand', methods=['GET', 'POST'])
def get_demand():
    global demand
    if request.method == 'GET':
        # Return the current demand
        return jsonify(demand)
    elif request.method == 'POST':
        # Update the demand with the new data from the request
        data = request.json
        if 'demand' in data:
            demand['demand'] = data['demand']
        return jsonify({'message': 'Data updated', 'data': demand}), 200
    
@app.route('/sun', methods=['GET', 'POST'])
def get_sun():
    global sunintensity
    if request.method == 'GET':
        # Return the current sun intensity
        return jsonify(sunintensity)
    elif request.method == 'POST':
        # Update the sun intensity with the new data from the request
        data = request.json
        if 'sun' in data:
            sunintensity['sun'] = data['sun']
        return jsonify({'message': 'Data updated', 'data': sunintensity}), 200

@app.route('/energy', methods=['GET', 'POST'])
def get_energy():
    global energy
    if request.method == 'GET':
        # Return the current energy
        return jsonify(energy)
    elif request.method == 'POST':
        # Update the energy with the new data from the request
        data = request.json
        if 'energy_reserve' in data:
            energy['energy_reserve'] = data['energy_reserve']
        return jsonify({'message': 'Data updated', 'data': energy}), 200

@app.route('/energy-data')
def get_energy_data():
    global energy, power
    data = {
        'energy_reserve': energy['energy_reserve'],
        'power_flywheel': power['power_flywheel'],
        'power_extracted': power['power_extracted']
    }
    return jsonify(data)

@app.route('/deferables', methods=['GET'])
def get_deferables_data():
    data = fetch_data(urls["deferables"])
    return jsonify(data)



if __name__ == "__main__":
    fetch_thread = threading.Thread(target=continuously_fetch_data)
    fetch_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
