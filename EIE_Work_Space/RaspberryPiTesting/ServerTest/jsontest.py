import requests
import json
import time
# Replace with the IP address of the machine running the Flask app
url = 'http://192.168.194.92:5000/power'
starttime = time.time()
# Send GET request to Flask app
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON data
    data = response.json()
    print('Data from Flask server:', data)

    # Modify the JSON data by incrementing the 'power_flywheel' and 'power_extracted' values by 0.1, round them to 2 decimal places
    # Assuming 'data' is your dictionary
    data['power_flywheel'] = str(round(float(data['power_flywheel']) + 0.1, 1))
    data['power_extracted'] = str(round(float(data['power_extracted']) + 0.1, 1))
    
   
    

    # Optionally, you can send the modified data back to the server or do something else with it
    # For example, sending the modified data back to the server
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print("Time taken: ", time.time()-starttime)
        print('Data successfully sent to Flask server')
    else:
        print('Failed to send data to Flask server')
else:
    print('Failed to retrieve data from Flask server')