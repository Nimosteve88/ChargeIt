import requests

response = requests.get('http://127.0.0.1:4000/rasp1')

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"GET request failed with status code {response.status_code}")