from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Store the data in a global variable
data = {}

@app.route('/', methods=['POST'])
def receive_data():
    global data
    data = request.get_json()
    # Notify all clients about the updated data
    socketio.emit('update_data', data)
    return '', 204  # Return a 204 No Content response



@app.route('/', methods=['GET'])
def send_data():
    return jsonify(data)

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/indexled')
def indexled():
    return render_template('indexled.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
