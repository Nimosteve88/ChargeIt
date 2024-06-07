import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error, mean_absolute_error
import psycopg2
from tabulate import tabulate

# Database connection details
DATABASE_URI = "postgresql+psycopg2://postgres:ChargeIt2024@chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com:5432/initial_db"
engine = create_engine(DATABASE_URI)

# PostgreSQL connection details
PG_HOST = "chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com"
PG_PORT = "5432"
PG_USER = "postgres"
PG_PASSWORD = "ChargeIt2024"
PG_DB = "initial_db"

def get_pg_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        database=PG_DB
    )

def view_data(name):
    try:
        connection = get_pg_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {name}")
        rows = cursor.fetchall()
        print(f"\nContents of {name}:")
        print(tabulate(rows, headers=[desc[0] for desc in cursor.description], tablefmt='psql'))
        return rows, [desc[0] for desc in cursor.description]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None
    finally:
        cursor.close()
        connection.close()

def fetch_demand_data():
    rows, headers = view_data('demand_data')
    if rows:
        demand_data = pd.DataFrame(rows, columns=headers)
        demand_data.sort_values(by='tick', inplace=True)  # Ensure data is in ascending order
        return demand_data
    else:
        return pd.DataFrame()

def validate_data(df):
    # Check for missing values
    if df.isnull().values.any():
        print("Missing values detected. Filling missing values with forward fill.")
        df.fillna(method='ffill', inplace=True)
    
    # Check for duplicate values
    if df.index.duplicated().any():
        print("Duplicate indices detected. Removing duplicates.")
        df = df[~df.index.duplicated(keep='first')]
    
    # Check for zero variance
    if df['demand'].var() == 0:
        raise ValueError("Zero variance detected in the demand data. Cannot fit ARIMA model.")
    
    return df

def plot_demand_forecast(train, test, forecast, xlabel, ylabel, title):
    plt.figure(figsize=(10, 6))
    plt.plot(train.index, train.values, label='Historical Demand')
    plt.plot(test.index, test.values, label='Actual Demand', color='blue')
    plt.plot(forecast.index, forecast.values, label='Forecasted Demand', color='red')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.show()

def main():
    demand_data = fetch_demand_data()

    if demand_data.empty:
        print("No data fetched. Exiting.")
        return

    # Set 'tick' as the index
    demand_data.set_index('tick', inplace=True)

    # Validate data
    demand_data = validate_data(demand_data)

    # Use the last 100 data points for training
    train = demand_data['demand'][-120:-5]  # Use 100 data points for training
    test = demand_data['demand'][-5:]       # Use the last 20 data points for testing

    # Fit the ARIMA model
    model = ARIMA(train, order=(7, 1, 1))  # Adjust order (p,d,q) as needed
    try:
        model_fit = model.fit()
    except Exception as e:
        print(f"Error fitting ARIMA model: {e}")
        return

    # Forecast the next 20 data points
    forecast = model_fit.forecast(steps=5)

    # Create a series for the forecast with the correct index
    forecast_index = range(test.index[0], test.index[0] + len(forecast))
    forecast_series = pd.Series(forecast, index=forecast_index)

    # Ensure there are no NaN values in test and forecast series
    test = test.dropna()
    forecast_series = forecast_series.dropna()

    # Calculate error metrics
    mse = mean_squared_error(test, forecast_series)
    mae = mean_absolute_error(test, forecast_series)
    print(f'Mean Squared Error: {mse}')
    print(f'Mean Absolute Error: {mae}')

    # Plot the results
    plot_demand_forecast(train, test, forecast_series, 'Tick', 'Demand', 'Demand Forecast vs Actual')

if __name__ == "__main__":
    main()
