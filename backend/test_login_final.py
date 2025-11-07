"""
Final test for login functionality
"""
import requests

API_BASE_URL = 'http://localhost:8000'

def test_login(username, password):
    print(f"\n🔐 Testing login: {username}")
    print(f"Password: {password}")
    
    response = requests.post(
        f'{API_BASE_URL}/api/v1/auth/login',
        json={
            'username': username,
            'password': password
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Login successful!")
        data = response.json()
        if data.get('success'):
            print(f"Access Token: {data['data']['access_token'][:50]}...")
            print(f"User: {data['data']['user']['username']} ({data['data']['user']['role']})")
    else:
        print("❌ Login failed!")

if __name__ == '__main__':
    print("=" * 60)
    print("Testing Login After Fresh Migration + Seed")
    print("=" * 60)
    
    # Test admin
    test_login('admin', 'admin123')
    
    # Test user
    test_login('user', 'user123')
    
    # Test wrong password
    test_login('admin', 'wrongpassword')
