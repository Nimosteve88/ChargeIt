import threading
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import requests
import json
from time import sleep

# Database connection details
DATABASE_URI = "postgresql+psycopg2://postgres:ChargeIt2024@chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com:5432/initial_db"

# Setup SQLAlchemy
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

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
    finally:
        session.close()

def update_yesterday_data(yesterday_data):
    session = Session()
    try:
        session.query(YesterdayData).delete()
        for entry in yesterday_data:
            new_data = YesterdayData(buy_price=entry['buy_price'], demand=entry['demand'], sell_price=entry['sell_price'], tick=entry['tick'])
            session.add(new_data)
        session.commit()
    finally:
        session.close()


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
            
            if tick == 1:
                update_deferables_data(deferables_data, day, tick)
                update_yesterday_data(yesterday_data)
            

            print(f"--------------------DATA FOR DAY {day}, TICK {tick}--------------------")
            print(f"Buy Price: {price_data_extracted.get('buy_price')}, Sell Price: {price_data_extracted.get('sell_price')}")
            print(f"Sun: {sun_data_extracted.get('sun')}")
            print(f"Demand: {demand_data_extracted.get('demand')}")
            print("----------------------------------------------------------\n")
            print("Data inserted into the database successfully")
            
            last_tick = current_tick  # Update the last_tick after processing


if __name__ == "__main__":
    continuously_fetch_data()
