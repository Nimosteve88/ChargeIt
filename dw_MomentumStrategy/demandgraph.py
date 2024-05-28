import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Data from the JSON
data = [
    {"buy_price": 25, "demand": 1.3445110071796298, "sell_price": 51, "tick": 0},
    {"buy_price": 27, "demand": 1.4970836765824425, "sell_price": 54, "tick": 1},
    {"buy_price": 8, "demand": 0, "sell_price": 17, "tick": 2},
    {"buy_price": 17, "demand": 0.4789110719805346, "sell_price": 34, "tick": 3},
    {"buy_price": 20, "demand": 0.8404296048799726, "sell_price": 41, "tick": 4},
    {"buy_price": 13, "demand": 0.07299422776410491, "sell_price": 26, "tick": 5},
    {"buy_price": 5, "demand": 0, "sell_price": 10, "tick": 6},
    {"buy_price": 25, "demand": 1.2594802091856518, "sell_price": 50, "tick": 7},
    {"buy_price": 22, "demand": 0.9512113866154175, "sell_price": 44, "tick": 8},
    {"buy_price": 16, "demand": 0.42798332124854804, "sell_price": 33, "tick": 9},
    {"buy_price": 7, "demand": 0, "sell_price": 14, "tick": 10},
    {"buy_price": 23, "demand": 0.878463707815587, "sell_price": 46, "tick": 11},
    {"buy_price": 21, "demand": 0.49964838489876406, "sell_price": 43, "tick": 12},
    {"buy_price": 52, "demand": 3.334329238022208, "sell_price": 104, "tick": 13},
    {"buy_price": 24, "demand": 0.3015936444259213, "sell_price": 49, "tick": 14},
    {"buy_price": 27, "demand": 0.3775264791337175, "sell_price": 54, "tick": 15},
    {"buy_price": 42, "demand": 2.1734979357533417, "sell_price": 85, "tick": 16},
    {"buy_price": 38, "demand": 2.088024461179655, "sell_price": 77, "tick": 17},
    {"buy_price": 34, "demand": 1.917459092825307, "sell_price": 69, "tick": 18},
    {"buy_price": 30, "demand": 1.7832625217867617, "sell_price": 60, "tick": 19},
    {"buy_price": 24, "demand": 1.4445398642288891, "sell_price": 49, "tick": 20},
    {"buy_price": 17, "demand": 1.152102699386556, "sell_price": 35, "tick": 21},
    {"buy_price": 49, "demand": 4.727503472664514, "sell_price": 98, "tick": 22},
    {"buy_price": 5, "demand": 0, "sell_price": 10, "tick": 23},
    {"buy_price": 11, "demand": 1.637525189753808, "sell_price": 22, "tick": 24},
    {"buy_price": 17, "demand": 2.550024775804406, "sell_price": 35, "tick": 25},
    {"buy_price": 5, "demand": 0, "sell_price": 10, "tick": 26},
    {"buy_price": 5, "demand": 1.0810411427943531, "sell_price": 10, "tick": 27},
    {"buy_price": 5, "demand": 1.1889936555131275, "sell_price": 10, "tick": 28},
    {"buy_price": 5, "demand": 1.7455336133548538, "sell_price": 10, "tick": 29},
    {"buy_price": 5, "demand": 1.856651489351976, "sell_price": 10, "tick": 30},
    {"buy_price": 5, "demand": 1.4394858515210425, "sell_price": 10, "tick": 31},
    {"buy_price": 16, "demand": 3.0020466861204187, "sell_price": 33, "tick": 32},
    {"buy_price": 5, "demand": 1.3256963165643878, "sell_price": 10, "tick": 33},
    {"buy_price": 5, "demand": 0.6744916797379177, "sell_price": 10, "tick": 34},
    {"buy_price": 39, "demand": 4.707830032830781, "sell_price": 78, "tick": 35},
    {"buy_price": 11, "demand": 1.6649573937890672, "sell_price": 23, "tick": 36},
    {"buy_price": 17, "demand": 1.9884887918277725, "sell_price": 35, "tick": 37},
    {"buy_price": 10, "demand": 0.8247321533678393, "sell_price": 20, "tick": 38},
    {"buy_price": 21, "demand": 1.5376559145314754, "sell_price": 42, "tick": 39},
    {"buy_price": 19, "demand": 0.8929081893386972, "sell_price": 38, "tick": 40},
    {"buy_price": 39, "demand": 2.448151063808961, "sell_price": 78, "tick": 41},
    {"buy_price": 41, "demand": 2.168193720416805, "sell_price": 83, "tick": 42},
    {"buy_price": 56, "demand": 3.1480388805615744, "sell_price": 112, "tick": 43},
    {"buy_price": 53, "demand": 2.308350794465675, "sell_price": 106, "tick": 44},
    {"buy_price": 66, "demand": 3.1671203584097545, "sell_price": 133, "tick": 45},
    {"buy_price": 42, "demand": 0.735275062053661, "sell_price": 84, "tick": 46},
    {"buy_price": 48, "demand": 1.390699041434527, "sell_price": 97, "tick": 47},
    {"buy_price": 49, "demand": 1.4415347601578614, "sell_price": 98, "tick": 48},
    {"buy_price": 60, "demand": 2.511331778248036, "sell_price": 120, "tick": 49},
    {"buy_price": 38, "demand": 0.35028706319835945, "sell_price": 77, "tick": 50},
    {"buy_price": 53, "demand": 2.0862575820205485, "sell_price": 106, "tick": 51},
    {"buy_price": 30, "demand": 0.0009708911837653655, "sell_price": 61, "tick": 52},
    {"buy_price": 48, "demand": 2.0579686171631772, "sell_price": 97, "tick": 53},
    {"buy_price": 49, "demand": 2.3449000917413354, "sell_price": 98, "tick": 54},
    {"buy_price": 39, "demand": 1.6387990286399523, "sell_price": 79, "tick": 55},
    {"buy_price": 48, "demand": 2.6824028190597473, "sell_price": 96, "tick": 56},
    {"buy_price": 36, "demand": 1.7413650234953233, "sell_price": 73, "tick": 57},
    {"buy_price": 17, "demand": 0.00983346794425044, "sell_price": 34, "tick": 58},
    {"buy_price": 26, "demand": 1.2308801139413803, "sell_price": 53, "tick": 59}
]

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
