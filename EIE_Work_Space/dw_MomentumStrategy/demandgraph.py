import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import requests, json


url = "https://icelec50015.azurewebsites.net/yesterday"

def fetch_data(url):
    response = requests.get(url)
    data = response.json()
    return data

# Data from the JSON
data = fetch_data(url)

# Extracting demand and tick values
demand_values = [entry['demand'] for entry in data]
ticks = [entry['tick'] for entry in data]

# Plotting time series
plt.figure(figsize=(12, 6))
plt.plot(ticks, demand_values, marker='o')
plt.title('Demand over Time')
plt.xlabel('Tick')
plt.ylabel('Demand')
plt.grid(True)
plt.show()
