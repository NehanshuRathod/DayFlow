import requests
import json

try:
    print("Testing Login API...")
    url = "http://localhost:8000/auth/login"
    payload = {
        "identifier": "admin@odoo.in",
        "password": "admin123"
    }
    
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:", response.json())
    except:
        print("Response Text:", response.text)

except Exception as e:
    print(f"Error: {e}")
