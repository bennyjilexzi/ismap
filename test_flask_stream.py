import requests
import json
import time

email = f"test_{int(time.time())}@example.com"
password = "admin"

res = requests.post("http://localhost:5000/api/register", json={"username": "test", "email": email, "password": password})
res = requests.post("http://localhost:5000/api/login", json={"email": email, "password": password})
token = res.json()["token"]

url = "http://localhost:5000/api/discover/example.com"
headers = {"Authorization": f"Bearer {token}"}
print("Connecting...")
start_time = time.time()
try:
    with requests.get(url, headers=headers, stream=True) as response:
        print("Status:", response.status_code)
        for line in response.iter_lines():
            if line:
                print(f"[{time.time() - start_time:.2f}s] {line.decode('utf-8')}")
except Exception as e:
    print("Error:", e)
