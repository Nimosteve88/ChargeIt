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
#create a function to add start and end (integer) attributes to deferables_data
def add_start_end():
    try:
        cursor.execute('ALTER TABLE deferables_data ADD COLUMN "start" INTEGER')
        cursor.execute('ALTER TABLE deferables_data ADD COLUMN "end" INTEGER')
        connection.commit()
        print("Columns added successfully")
    except Exception as e:
        print(f"Error adding columns: {e}")
        connection.rollback()

#delete deferable_data items
def delete_deferable_data():
    try:
        cursor.execute("DELETE FROM deferables_data")
        connection.commit()
        print("All data deleted successfully")
    except Exception as e:
        print(f"Error deleting data: {e}")
        connection.rollback()




#delete_all_data()
#delete_all_tables()
#delete_deferable_data()
#view_all_data()
#add_start_end()
view_data("deferables_data")