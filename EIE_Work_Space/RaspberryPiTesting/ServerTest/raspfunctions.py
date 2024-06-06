import urequests as requests
import ujson as json
import utime as time
from machine import Timer

ip = '192.168.194.92:5000'
def send_data(endpoint):
    # Replace with the IP address of the machine running the Flask app
    url = 'http:'+ip+':5000/'+str(endpoint)
    # Send GET request to Flask app
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        ####################MODIFY DATA HERE####################

        ########################################################

        json_data = json.dumps(data)
        response = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            print('Data successfully sent to server')
        else:
            print('Failed to send data to server')


def get_data(endpoint):
    url = 'http:'+ip+':5000/'+str(endpoint)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print('Failed to retrieve data from server')
        return None


def send_data_to_specific_endpoint(endpoint, data):
    url = 'http:'+ip+':5000/'+str(endpoint)
    json_data = json.dumps(data)
    response = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        print('Data successfully sent to server')
    else:
        print('Failed to send data to server')