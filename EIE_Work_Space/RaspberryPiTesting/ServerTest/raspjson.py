import urequests as requests
import ujson as json
import utime as time

# Replace with the IP address of the machine running the Flask app
starttime = time.time()
url = 'http://192.168.0.103:5000/power'

# Send GET request to Flask app
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON data
    data = response.json()
    print('Data from Flask server:', data)

    # Modify the JSON data by incrementing the 'power_flywheel' and 'power_extracted' values by 0.1, round them to 1 decimal place
    # Assuming 'data' is your dictionary
    data['power_flywheel'] = str(round(float(data['power_flywheel']) + 0.1, 1))
    data['power_extracted'] = str(round(float(data['power_extracted']) + 0.1, 1))

    # Convert data back to JSON
    json_data = json.dumps(data)
    
    # Optionally, you can send the modified data back to the server or do something else with it
    # For example, sending the modified data back to the server
    response = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})
    print("Time taken: ", time.time()-starttime)
    if response.status_code == 200:
        
        print('Data successfully sent to Flask server')
        
    else:
        print('Failed to send data to Flask server')
else:
    print('Failed to retrieve data from Flask server')
