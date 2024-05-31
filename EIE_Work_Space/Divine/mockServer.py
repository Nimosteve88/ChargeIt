from flask import Flask, jsonify
from threading import Timer
import random

app = Flask(__name__)

# Initial values
data = {
    'power_flywheel': 0,
    'power_extracted': 0
}

# Function to update values
def update_values():
    data['power_flywheel'] = round(random.uniform(1,2), 5) # generate random number from 1-2, up to 5 decimal places
    data['power_extracted'] = round(random.uniform(1,2), 5)  

    # Call this function again after 5 seconds
    Timer(3.0, update_values).start()

# Start the first update
update_values()

@app.route('/', methods=['GET'])
def get_data():
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
