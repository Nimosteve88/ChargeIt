from flask import Flask, jsonify
import random

app = Flask(__name__)

# Initial values
data = {
    'power_flywheel': 0,
    'power_extracted': 0
}


@app.route('/rasp1', methods=['GET'])
def get_data():
    data['power_flywheel'] = round(random.uniform(1,2), 5) # generate random number from 1-2, up to 5 decimal places
    data['power_extracted'] = round(random.uniform(1,2), 5)  

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=4000)
