from flask import Flask, request, jsonify

app = Flask(__name__)

# Store the data in a global variable
data = {}

@app.route('/', methods=['POST'])
def receive_data():
    global data
    data = request.get_json()
    return '', 204  # Return a 204 No Content response

@app.route('/', methods=['GET'])
def send_data():
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)