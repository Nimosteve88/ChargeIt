import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import mean_squared_error, mean_absolute_error
import itertools
import warnings
import psycopg2
from tabulate import tabulate

warnings.filterwarnings("ignore")

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

def grid_search_arima(data, test, p_values, d_values, q_values):
    best_aic = float("inf")
    best_order = None
    best_mse = None
    best_mae = None
    best_model = None

    for p in p_values:
        for d in d_values:
            for q in q_values:
                try:
                    model = ARIMA(data, order=(p, d, q))
                    model_fit = model.fit()
                    aic = model_fit.aic
                    forecast = model_fit.get_forecast(steps=len(test))
                    forecast_mean = forecast.predicted_mean
                    mse = mean_squared_error(test, forecast_mean)
                    mae = mean_absolute_error(test, forecast_mean)

                    if aic < best_aic:
                        best_aic = aic
                        best_order = (p, d, q)
                        best_mse = mse
                        best_mae = mae
                        best_model = model_fit
                except Exception as e:
                    print(f"Error fitting ARIMA({p},{d},{q}): {e}")
                    continue

    return best_order, best_aic, best_mse, best_mae, best_model

def main():
    demand_data = fetch_demand_data()

    if demand_data.empty:
        print("No data fetched. Exiting.")
        return

    # Set 'tick' as the index
    demand_data.set_index('tick', inplace=True)

    # Validate data
    demand_data = validate_data(demand_data)

    # Use the last 100-200 data points for training
    train = demand_data['demand'][-100:-15]  # Use the last 200 data points for training
    test = demand_data['demand'][-15:]    # Use the last 15 data points for testing

    # Define the parameter ranges for grid search
    p_values = range(0, 5)
    d_values = range(0, 3)
    q_values = range(0, 5)

    best_order, best_aic, best_mse, best_mae, best_model = grid_search_arima(train, test, p_values, d_values, q_values)

    if best_model is None:
        print("No suitable ARIMA model found.")
        return

    print(f"Best ARIMA order: {best_order}")
    print(f"Best AIC: {best_aic}")
    print(f"Best MSE: {best_mse}")
    print(f"Best MAE: {best_mae}")

    # Forecast the next 15 data points
    forecast = best_model.get_forecast(steps=15)
    forecast_mean = forecast.predicted_mean

    # Create a series for the forecast with the correct index
    forecast_index = range(test.index[-1] + 1, test.index[-1] + 1 + len(forecast_mean))
    forecast_series = pd.Series(forecast_mean, index=forecast_index)

    # Ensure there are no NaN values in test and forecast series
    test = test.dropna()
    forecast_series = forecast_series.dropna()

    # Plot the results
    plot_demand_forecast(train, test, forecast_series, 'Tick', 'Demand', 'Demand Forecast vs Actual')

if __name__ == "__main__":
    main()
