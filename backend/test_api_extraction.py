#!/usr/bin/env python3
"""
Test API extraction directly
"""
import requests
import json

# Login first
login_response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'username': 'madulinux', 'password': 'justice#404'}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

response_data = login_response.json()
token = response_data['data']['tokens']['access_token']
print(f"✅ Login successful")

# Try extraction
files = {
    'file': open('/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend/uploads/20251110_213245_2025-11-10_213243_18875_0.pdf', 'rb')
}

data = {
    'template_id': '1'
}

headers = {
    'Authorization': f'Bearer {token}'
}

print(f"\n🔍 Testing extraction...")
response = requests.post(
    'http://localhost:8000/api/v1/extraction/extract',
    files=files,
    data=data,
    headers=headers
)

print(f"\n📊 Response Status: {response.status_code}")
print(f"📊 Response Body:")
print(json.dumps(response.json(), indent=2))
