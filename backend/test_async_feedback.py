"""
Test async feedback submission performance
"""
import time
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "madulinux"
PASSWORD = "justice#404"

def test_feedback_response_time():
    """Test that feedback submission returns quickly"""
    
    # 1. Login
    print("🔐 Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful")
    
    # 2. Get a document to test with
    print("\n📄 Getting test document...")
    docs_response = requests.get(
        f"{BASE_URL}/api/v1/extraction/documents",
        headers=headers
    )
    
    if docs_response.status_code != 200 or not docs_response.json()["data"]:
        print("❌ No documents found")
        return
    
    document_id = docs_response.json()["data"][0]["id"]
    print(f"✅ Using document ID: {document_id}")
    
    # 3. Submit feedback and measure response time
    print("\n⚡ Testing feedback submission speed...")
    
    feedback_data = {
        "document_id": document_id,
        "corrections": {
            "nama_lengkap": "Test Name",
            "nik": "1234567890123456"
        }
    }
    
    start_time = time.time()
    
    feedback_response = requests.post(
        f"{BASE_URL}/api/v1/extraction/feedback",
        headers=headers,
        json=feedback_data
    )
    
    elapsed_time = time.time() - start_time
    
    # 4. Check results
    print(f"\n📊 Results:")
    print(f"   Status Code: {feedback_response.status_code}")
    print(f"   Response Time: {elapsed_time:.3f} seconds")
    
    if feedback_response.status_code == 200:
        response_data = feedback_response.json()
        
        # Check auto-training status
        auto_training = response_data.get("data", {}).get("auto_training", {})
        print(f"   Auto-training Status: {auto_training.get('status', 'N/A')}")
        print(f"   Auto-training Message: {auto_training.get('message', 'N/A')}")
        
        # Verify response is fast
        if elapsed_time < 2.0:
            print(f"\n✅ SUCCESS: Response time is excellent ({elapsed_time:.3f}s < 2.0s)")
            print("   Training is running in background (non-blocking)")
        else:
            print(f"\n⚠️  WARNING: Response time is slow ({elapsed_time:.3f}s >= 2.0s)")
            print("   Training might still be blocking")
    else:
        print(f"\n❌ FAILED: {feedback_response.text}")
    
    # 5. Monitor background training
    print("\n📝 Background training is running...")
    print("   Check server logs with: tail -f server.log | grep 'Background auto-training'")
    print("\n   You should see:")
    print("   ✅ Background auto-training completed for template X: Y samples, Z% accuracy")

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 ASYNC FEEDBACK SUBMISSION TEST")
    print("=" * 80)
    
    try:
        test_feedback_response_time()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        print("   Make sure the server is running:")
        print("   python manage.py runserver")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
