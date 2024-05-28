import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import requests, json


url = "https://icelec50015.azurewebsites.net/yesterday"

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
# Data from the JSON
data = fetch_data(url)

# Extracting demand and tick values
demand_values = [entry['demand'] for entry in data]
ticks = [entry['tick'] for entry in data]

# Calculate summary statistics
mean_demand = np.mean(demand_values)
median_demand = np.median(demand_values)
std_demand = np.std(demand_values)
min_demand = np.min(demand_values)
max_demand = np.max(demand_values)

# Displaying summary statistics
print(f"Mean demand: {mean_demand}")
print(f"Median demand: {median_demand}")
print(f"Standard deviation of demand: {std_demand}")
print(f"Minimum demand: {min_demand}")
print(f"Maximum demand: {max_demand}")

# Plotting time series
plt.figure(figsize=(12, 6))
plt.plot(ticks, demand_values, marker='o')
plt.title('Demand over Time')
plt.xlabel('Tick')
plt.ylabel('Demand')
plt.grid(True)
plt.show()
