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
import xgboost as xgb  # Added for machine learning

app = Flask(__name__)

# Database connection details
DATABASE_URI = "postgresql+psycopg2://postgres:ChargeIt2024@chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com:5432/initial_db"

# Setup SQLAlchemy
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

power = {
    'gridpower': '0.0'
}

demand = {
    'demand': '0.0'
}

sunintensity = {
    'sun': '0'
}

resevoir = {
    'resevoirpower': '0.0',
    'resevoirenergy': '0.0'
}


energy = {
    'flywheel_energy': '0.0',
    'pv_power': '0.0'
}

balance_reserve = 0.00
deferable_power = 0.0


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
    start = Column(Integer)
    end = Column(Integer)
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

# ML Model Placeholder
model = None

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
            new_data = DeferablesData(
                demand=deferable['energy'],
                day=day,
                start=deferable['start'],
                end=deferable['end'],
                tick=tick
            )
            session.add(new_data)
        session.commit()
        session.execute(text("""
            DELETE FROM deferables_data a USING deferables_data b 
            WHERE a.id < b.id AND a.demand = b.demand AND a.day = b.day AND a.tick = b.tick
        """))
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

def prepare_features(data):
    df = pd.DataFrame(data, columns=['tick', 'buy_price', 'sell_price', 'day', 'timestamp'])
    df['price_diff'] = df['sell_price'] - df['buy_price']
    df['buy_ma'] = df['buy_price'].rolling(window=5).mean()
    df['sell_ma'] = df['sell_price'].rolling(window=5).mean()
    df.dropna(inplace=True)
    return df


def fetch_historical_data():
    session = Session()
    try:
        result = session.execute(text("""
            SELECT tick, buy_price, sell_price, day, timestamp
            FROM price_data
            ORDER BY tick ASC
        """)).fetchall()

        rows = [dict(row._mapping) for row in result]
        return rows
    finally:
        session.close()

FEATURE_NAMES = ['buy_price', 'sell_price', 'price_diff', 'buy_ma', 'sell_ma']

def train_model():
    global model
    while True:
        data = fetch_historical_data()
        if data:
            df = prepare_features(data)
            if not df.empty:
                X = df[FEATURE_NAMES]
                y = (df['sell_price'].shift(-1) > df['sell_price']).astype(int) 
                dtrain = xgb.DMatrix(X, label=y, feature_names=FEATURE_NAMES)
                param = {'max_depth': 3, 'eta': 0.1, 'objective': 'binary:logistic'}
                num_round = 100
                model = xgb.train(param, dtrain, num_round)
                print("Model trained with features:", FEATURE_NAMES)



def combined_strategy(current_day, current_tick, current_buy_price, current_sell_price):
    global power, demand, energy, balance_reserve, decision, indicator, deferable_power, model
    remaining_power = float(energy['pv_power']) - (float(demand['demand']) + deferable_power) 
    #remaining_power = 5.0     # Use this if you want to test ML model
    initial_decision = None
    # Initial demand strategy logic
    if remaining_power < 0: #not enough power from pv
        if float(resevoir['resevoirenergy']) <= 0.3: #if storage is empty
            initial_decision = "BUY"
            decision = "BUY"
            balance_reserve -= current_buy_price * abs(remaining_power)
            balance_reserve = round(balance_reserve)
            indicator = 1
        else: #storage not empty
            if (abs(remaining_power) * 5)> float(resevoir['resevoirenergy']): #required power more than storage
                discharge_flywheel(-float(resevoir['resevoirenergy'])/5)
                initial_decision = "BUY"
                decision = "BUY"
                balance_reserve -= current_buy_price * (abs(remaining_power) - (float(resevoir['resevoirenergy'])/5))
                balance_reserve = round(balance_reserve)
                indicator = 1
            else:
                initial_decision = None
                discharge_flywheel(float(remaining_power))
    # if model is not None:
    #     print("model exists")
    # Secondary decision based on price trends using ML model
    if initial_decision is None and model is not None:
        print("Using ML model for decision making...")
        try:
            last_10_sell_prices = fetch_last_n_sell_prices(current_day, current_tick, 10)
            last_10_buy_prices = fetch_last_n_buy_prices(current_day, current_tick, 10)
                
            if len(last_10_sell_prices) < 10:
                remaining_needed = 10 - len(last_10_sell_prices)
                last_10_sell_prices += fetch_last_n_sell_prices_yesterday(remaining_needed)
                
            if len(last_10_buy_prices) < 10:
                remaining_needed = 10 - len(last_10_buy_prices)
                last_10_buy_prices += fetch_last_n_buy_prices_yesterday(remaining_needed)
                
            all_sell_prices = last_10_sell_prices + [current_sell_price]
            all_buy_prices = last_10_buy_prices + [current_buy_price]

            data = [{'tick': i, 'buy_price': buy, 'sell_price': sell, 
                     'day': current_day, 'timestamp': datetime.utcnow()} for i, 
                     (buy, sell) in enumerate(zip(all_buy_prices, all_sell_prices))]
            df = prepare_features(data)

            if not df.empty:
                X = df[FEATURE_NAMES].iloc[-1]
                print("Features for prediction:", X.to_dict())  # Debugging statement
                dmatrix = xgb.DMatrix(X.values.reshape(1, -1), feature_names=FEATURE_NAMES)
                prediction = model.predict(dmatrix) 
                # Use a threshold to decide
                if prediction >= 0.8:
                    decision = "BUY"
                    print(f"ML model decision: {decision}, model prediction: {prediction}")
                    balance_reserve -= float(current_sell_price) * 1.48  # Incremental buy
                    balance_reserve = round(balance_reserve)
                    charge_flywheel(1.48)
                elif prediction <= 0.6:
                    decision = "SELL"
                    print(f"ML model decision: {decision}, model prediction: {prediction}")
                    balance_reserve += float(current_buy_price) * float(resevoir['resevoirenergy']) / 5
                    balance_reserve = round(balance_reserve)
                    discharge_flywheel(-float(resevoir['resevoirenergy']) / 10)  # Incremental discharge
                else:
                    decision = "HOLD"
                    print(f"ML model decision: {decision}, model prediction: {prediction}")

        except Exception as e:
            print(f"Error in trading_strategy: {e}")

    elif model is None:
        print("Using last option for decision making...")

        last_10_sell_prices = fetch_last_n_sell_prices(current_day, current_tick, 10)
        last_10_buy_prices = fetch_last_n_buy_prices(current_day, current_tick, 10)
                
        if len(last_10_sell_prices) < 10:
            remaining_needed = 10 - len(last_10_sell_prices)
            last_10_sell_prices += fetch_last_n_sell_prices_yesterday(remaining_needed)
                
        if len(last_10_buy_prices) < 10:
            remaining_needed = 10 - len(last_10_buy_prices)
            last_10_buy_prices += fetch_last_n_buy_prices_yesterday(remaining_needed)
                
        all_sell_prices = last_10_sell_prices + [current_sell_price]
        all_buy_prices = last_10_buy_prices + [current_buy_price]

        avg_sell_price = sum(all_sell_prices) / len(all_sell_prices)
        avg_buy_price = sum(all_buy_prices) / len(all_buy_prices)

        localsell = sum(all_sell_prices[-3:]) / 3
        localbuy = sum(all_buy_prices[-3:]) / 3


        if current_sell_price < avg_sell_price:
            if current_sell_price < localsell * 0.85:
                decision = "BUY"
                balance_reserve = round(balance_reserve - float(current_sell_price) * 1.48)
                charge_flywheel(1.48)

        elif current_buy_price > avg_buy_price:
            if current_buy_price > localbuy * 1.15:
                decision = "SELL"
                balance_reserve += float(current_buy_price) * float(resevoir['resevoirenergy']) / 5
                balance_reserve = round(balance_reserve)
                discharge_flywheel(-float(resevoir['resevoirenergy']) / 10)  # Incremental discharge


    print(f"Combined strategy decision: {decision}")
def discharge_flywheel(amount):
    # logic to discharge flywheel/capacitor
    resevoir['resevoirpower'] = str(amount)
    pass
def charge_flywheel(amount):
    # logic to charge flywheel/capacitor
    resevoir['resevoirpower'] = str(amount)
    pass

indicator = 0

def handle_deferables(tick, deferables_data):
    global deferable_power
    if deferables_data:
        for i in range(len(deferables_data)):
            deferables_data[i]['power'] = deferables_data[i]['energy'] / ((deferables_data[i]['end'] - deferables_data[i]['start'] + 1) * 5)
            if tick >= deferables_data[i]['start'] and tick <= deferables_data[i]['end']:
                deferable_power += deferables_data[i]['power']
            elif tick > deferables_data[i]['end']:
                deferables_data.pop(i)
                #Uncomment this when ready to test deferables
    #             session = Session()
    #             try:
    #                 session.query(DeferablesData).filter(DeferablesData.start == deferables_data[i]['start'], DeferablesData.end == deferables_data[i]['end'], DeferablesData.demand == deferables_data[i]['energy']).delete()
    #                 session.commit()
    #             except Exception as e:
    #                 session.rollback()
    #                 print(f"Error deleting deferables_data: {e}")
    #             finally:
    #                 session.close()
    else:
        #if array is empty meaning all deferables are satisfied
        pass
liveday = None
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
            global liveday
            liveday = price_data_extracted.get('day', 'N/A')
            day = price_data_extracted.get('day', 'N/A')
            tick = price_data_extracted.get('tick', 'N/A')
            demanddata = demand_data_extracted.get('demand', 'N/A')

            if tick == 1 or tick ==0:
                update_deferables_data(deferables_data, day, tick)
                update_yesterday_data(yesterday_data)

            #update demand dictionary
            global demand, sunintensity, deferable_power, balance_reserve
            demand['demand'] = str(demanddata)
            sunintensity['sun'] = str(sun_data_extracted.get('sun'))
            
            # power['grid_power'] = str(random.uniform(0.0, 10.0))
            # power['pv_power'] = str(random.uniform(0.0, 10.0))
            #energy['flywheel_energy'] = str(random.uniform(0.0, 10.0))

            current_buy_price = price_data_extracted.get('buy_price', None)
            current_sell_price = price_data_extracted.get('sell_price', None)
            handle_deferables(tick, deferables_data)
            combined_strategy(day, tick, current_buy_price, current_sell_price)
            #print the current balance reserve
            print(f"Balance Reserve: {balance_reserve}")
            deferable_power = 0
            #print(f"Tick: {tick}, Decision: {decision}, Balance Reserve: {balance_reserve}, Flywheel Energy: {energy['flywheel_energy']}, Deferable Power: {deferable_power}")
            last_tick = current_tick  # Update the last_tick after processing

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    global liveday
    session = Session()
    try:
        result = session.execute(text("""
            SELECT DISTINCT ON (tick) tick, buy_price, sell_price, day, timestamp
            FROM price_data
            WHERE day = :day
            ORDER BY tick, timestamp ASC
        """),{'day':liveday}).fetchall()
        
        rows = [dict(row._mapping) for row in result]
        
        if not rows:
            return jsonify({"ticks": [], "buy_prices": [], "sell_prices": [], "current_demand": "-", "current_day": "-", "current_sun": "-"})

        data_by_day = {}
        for row in rows:
            day = row['day']
            if day not in data_by_day:
                data_by_day[day] = []
            data_by_day[day].append(row)
        
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

# @app.route('/alldata')
# def alldata():
#     session = Session()
#     try:
#         result = session.execute(text("""
#             SELECT tick, buy_price, sell_price, day, timestamp
#             FROM price_data
#             ORDER BY tick ASC
#         """)).fetchall()
        
#         rows = [dict(row._mapping) for row in result]

#         if not rows:
#             return jsonify({"ticks": [], "buy_prices": [], "cumulative_buy_avg": [], "cumulative_sell_avg": [], "avg_buy_price_per_tick": [], "sell_prices": []})

#         df = pd.DataFrame(rows, columns=['tick', 'buy_price', 'sell_price', 'day', 'timestamp'])
#         cumulative_buy_avg = calculate_cumulative_average(df, 'buy_price')
#         cumulative_sell_avg = calculate_cumulative_average(df, 'sell_price')
#         avg_buy_price_per_tick = df.groupby('tick')['buy_price'].mean().tolist()

#         data = {
#             "ticks": df['tick'].tolist(),
#             "cumulative_buy_avg": cumulative_buy_avg,
#             "cumulative_sell_avg": cumulative_sell_avg
#         }
#         return jsonify(data)
#     finally:
#         session.close()

@app.route('/decision')
def get_decision():
    global decision
    return jsonify({'decision': decision})

@app.route('/deferables', methods=['GET'])
def get_deferables_data():
    session = Session()
    try:
        result = session.execute(text("""
            SELECT demand, day, "start", "end", tick
            FROM deferables_data
            ORDER BY tick ASC
        """)).fetchall()

        rows = [dict(row._mapping) for row in result]
        data = {
            "deferables": rows
        }
        return jsonify(data)
    finally:
        session.close()

    
@app.route('/demand', methods=['GET', 'POST'])
def get_demand():
    global demand
    if request.method == 'GET':
        return jsonify(demand)
    elif request.method == 'POST':
        data = request.json
        if 'demand' in data:
            demand['demand'] = data['demand']
        return jsonify({'message': 'Data updated', 'data': demand}), 200
    
@app.route('/gridpower', methods=['GET', 'POST'])
def get_grid():
    if request.method == 'GET':
        return jsonify(power)
    elif request.method == 'POST':
        data = request.json
        if 'gridpower' in data:
            power['gridpower'] = data['gridpower']
        return jsonify({'message': 'Data updated', 'data': power}), 200
    
@app.route('/sun', methods=['GET', 'POST'])
def get_sun():
    global sunintensity
    if request.method == 'GET':
        return jsonify(sunintensity)
    elif request.method == 'POST':
        data = request.json
        if 'sun' in data:
            sunintensity['sun'] = data['sun']
        return jsonify({'message': 'Data updated', 'data': sunintensity}), 200

@app.route('/energy', methods=['GET', 'POST'])
def get_energy():
    global energy
    if request.method == 'GET':
        return jsonify(energy)
    elif request.method == 'POST':
        data = request.json
        if 'pv_power' in data:
            energy['pv_power'] = data['pv_power']
            # energy['flywheel_energy'] = data['flywheel_energy']
        return jsonify({'message': 'Data updated', 'data': energy}), 200

@app.route('/energy-data')
def get_energy_data():
    global energy, power
    data = {
        'flywheel_energy': resevoir['resevoirenergy'],
        'grid_power': power['gridpower'],
        'pv_power': energy['pv_power']
    }
    return jsonify(data)

@app.route('/resevoirpower', methods=['GET', 'POST'])
def get_resevoirpower():
    global resevoirpower
    if request.method == 'GET':
        # Return the current resevoir power
        return jsonify(resevoir)
    elif request.method == 'POST':
        # Update the resevoir power with the new data from the request
        data = request.json
        if 'resevoirenergy' in data:
            resevoir['resevoirenergy'] = data['resevoirenergy']
        return jsonify({'message': 'Data updated', 'data': resevoir}), 200

def update_deferables_data(deferables_data, day, tick):
    session = Session()
    try:
        session.query(DeferablesData).delete()
        for deferable in deferables_data:
            new_data = DeferablesData(
                demand=deferable['energy'],
                day=day,
                start=deferable['start'],
                end=deferable['end'],
                tick=tick
            )
            session.add(new_data)
        session.commit()
        session.execute(text("""
            DELETE FROM deferables_data a USING deferables_data b 
            WHERE a.id < b.id AND a.demand = b.demand AND a.day = b.day AND a.tick = b.tick
        """))
    except IntegrityError as e:
        session.rollback()
        print(f"Error updating deferables_data: {e}")
    finally:
        session.close()

    

@app.route('/balance-data')
def balance_data():
    global balance_reserve
    balance_data = {
        'balance_reserve': str(balance_reserve)  
    }
    return jsonify(balance_data)



@app.route('/sun-data')
def sun_data():
    session = Session()
    try:
        result = session.execute(text("""
            SELECT tick, sun
            FROM sun_data
            ORDER BY tick ASC
        """)).fetchall()

        rows = [dict(row._mapping) for row in result]
        data = {
            "ticks": [row['tick'] for row in rows],
            "sun_values": [row['sun'] for row in rows]
        }
        return jsonify(data)
    finally:
        session.close()

@app.route('/demand-data')
def demand_data():
    session = Session()
    try:
        result = session.execute(text("""
            SELECT tick, demand
            FROM demand_data
            ORDER BY tick ASC
        """)).fetchall()

        rows = [dict(row._mapping) for row in result]
        data = {
            "ticks": [row['tick'] for row in rows],
            "demand_values": [row['demand'] for row in rows]
        }
        return jsonify(data)
    finally:
        session.close()

from collections import deque


tick_queue = deque(maxlen=60)
flywheel_energy_queue = deque(maxlen=60)
grid_power_queue = deque(maxlen=60)
pv_power_queue = deque(maxlen=60)

@app.route('/live-energy-data')
def live_energy_data():
    global energy, power, tick_queue, flywheel_energy_queue, grid_power_queue, pv_power_queue
    current_tick = fetch_data(urls["price"])['tick']
    tick_queue.append(current_tick)
    flywheel_energy_queue.append(float(resevoir['resevoirenergy']))
    grid_power_queue.append(float(power['gridpower']))
    pv_power_queue.append(float(energy['pv_power']))
    
    data = {
        'ticks': list(tick_queue),
        'flywheel_energy': list(flywheel_energy_queue),
        'grid_power': list(grid_power_queue),
        'pv_power': list(pv_power_queue)
    }
    return jsonify(data)


if __name__ == "__main__":
    train_thread = threading.Thread(target=train_model)
    train_thread.start()
    
    fetch_thread = threading.Thread(target=continuously_fetch_data)
    fetch_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
