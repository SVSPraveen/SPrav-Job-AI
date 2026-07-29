import requests
import json

payload = {
    "current_roles": [],
    "current_locations": []
}

try:
    res = requests.post('http://localhost:8000/api/scope/suggest', json=payload)
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)
except Exception as e:
    print("ERROR:", e)
