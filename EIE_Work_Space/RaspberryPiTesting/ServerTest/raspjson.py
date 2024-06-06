import urequests as requests
import ujson as json
import utime as time
from machine import Timer

# Replace with the IP address of the machine running the Flask app
url = 'http://192.168.0.105:5000/power'
energyurl = 'http://192.168.0.105:5000/energy'

# Send GET request to Flask app
response = requests.get(url)
energyresponse = requests.get(energyurl)



# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON data
    data = response.json()
    energydata = energyresponse.json()
    print('Data from Flask server:', data)
    print('Energy data from Flask server:', energydata)

    # Modify the JSON data by incrementing the 'power_flywheel' and 'power_extracted' values by 0.1, round them to 1 decimal place
    data['power_flywheel'] = str(round(float(data['power_flywheel']) + 0.1, 1))
    data['power_extracted'] = str(round(float(data['power_extracted']) + 0.1, 1))
    energydata['energy_reserve'] = str(round(float(energydata['energy_reserve']) + 0.1, 1))

    # Convert data back to JSON
    json_data = json.dumps(data)
    json_energydata = json.dumps(energydata)
    

    # Send the modified data back to the server
    response = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})
    response = requests.post(energyurl, data=json_energydata, headers={'Content-Type': 'application/json'})


    if response.status_code == 200:
        print('Data successfully sent to Flask server')
    else:
        print('Failed to send data to Flask server')
else:
    print('Failed to retrieve data from Flask server')
