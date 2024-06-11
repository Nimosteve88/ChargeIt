import psycopg2
import requests
import time
import json
from tabulate import tabulate

# # Database connection details
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

    
except Exception as e:
    print(f"Error connecting to the database: {e}")


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


def view_data(name):
    try:
        cursor.execute(f"SELECT * FROM {name}")
        rows = cursor.fetchall()
        print(f"\nContents of {name}:")
        print(tabulate(rows, headers=[desc[0] for desc in cursor.description], tablefmt='psql'))
    except Exception as e:
        print(f"Error fetching data: {e}")

#view first 5 rows of each of a certain table
def view_first_5_rows(name):
    try:
        cursor.execute(f"SELECT * FROM {name} LIMIT 5")
        rows = cursor.fetchall()
        print(f"\nFirst 5 rows of {name}:")
        print(tabulate(rows, headers=[desc[0] for desc in cursor.description], tablefmt='psql'))
    except Exception as e:
        print(f"Error fetching data: {e}")

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

def delete_all_tables():
    tables = ["price_data", "sun_data", "demand_data", "deferables_data", "yesterday_data"]
    try:
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        connection.commit()
        print("All tables deleted successfully")
    except Exception as e:
        print(f"Error deleting tables: {e}")
        connection.rollback()

#delete_all_data()
#delete_all_tables()
#view_all_data()
#view_data("price_data")
view_first_5_rows("price_data")