"""
Test X API Permission Requirements and Alternative Following Check Methods
"""

from api import XAPIClient
from config import CLIENT_ID, CLIENT_SECRET, CALLBACK_URL
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_following_permissions():
    """Test different X API endpoints to see what works with current permissions."""
    
    print("🔍 Testing X API Following Permission Alternatives")
    print("="*60)
    
    # Initialize client
    client = XAPIClient(CLIENT_ID, CLIENT_SECRET, CALLBACK_URL)
    
    # Test user ID (you'll need to replace with your actual user ID)
    # You can get this from the /users/me endpoint
    print("\n1. Testing /users/me endpoint (should work with basic permissions)")
    try:
        response = client._make_api_request('GET', '/users/me', api_endpoint_type='user_lookup')
        if response.status_code == 200:
            data = response.json()
            user_id = data['data']['id']
            username = data['data']['username']
            print(f"✅ Success: Your user ID is {user_id} (@{username})")
            
            # Test Scott's user ID: 931286316
            scott_id = "931286316"
            
            print(f"\n2. Testing direct following relationship check")
            print(f"   Endpoint: GET /users/{user_id}/following/{scott_id}")
            try:
                response = client._make_api_request('GET', f'/users/{user_id}/following/{scott_id}', api_endpoint_type='user_lookup')
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
                
                if response.status_code == 403:
                    print("   ❌ RESULT: Requires elevated permissions")
                elif response.status_code == 200:
                    print("   ✅ RESULT: Works with current permissions!")
                else:
                    print(f"   ⚠️ RESULT: Unexpected response")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
            
            print(f"\n3. Testing following list endpoint (alternative)")
            print(f"   Endpoint: GET /users/{user_id}/following?max_results=100")
            try:
                response = client._make_api_request('GET', f'/users/{user_id}/following?max_results=100', api_endpoint_type='user_lookup')
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    following_count = len(data.get('data', []))
                    print(f"   ✅ SUCCESS: Retrieved {following_count} following users")
                    
                    # Check if Scott is in the list
                    following_users = data.get('data', [])
                    scott_in_list = any(user.get('id') == scott_id for user in following_users)
                    print(f"   Scott (@ScottPresler) in list: {scott_in_list}")
                    
                    if following_count == 100:
                        print("   ⚠️ NOTE: Only first 100 users returned (pagination limit)")
                else:
                    print(f"   ❌ FAILED: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                
        else:
            print(f"❌ Failed to get user info: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def print_permission_info():
    """Print information about X API permission levels."""
    
    print("\n" + "="*60)
    print("📋 X API PERMISSION LEVELS INFORMATION")
    print("="*60)
    
    print("""
🔓 ESSENTIAL ACCESS (Free, Basic)
   - Read public tweets
   - Post tweets  
   - Basic user information
   - Current permissions: read, write, direct message

🔐 ELEVATED ACCESS (Free, Requires Approval)
   - Everything in Essential
   - Following relationships (GET /users/{id}/following/{target_id})
   - More API calls per month
   - Additional endpoints

🎓 ACADEMIC ACCESS (Free, For Researchers)
   - Everything in Elevated
   - Higher rate limits
   - Advanced search capabilities

💼 ENTERPRISE ACCESS (Paid)
   - Everything in Academic
   - Highest rate limits
   - Premium features
   - 24/7 support

RECOMMENDATION:
To get following relationship access, you need to:
1. Apply for Elevated Access in your X Developer Portal
2. Explain your use case (building an unfollow tool)
3. Wait for approval (usually 1-2 days)

ALTERNATIVE:
Use the following list method (limited to first 100 following)
or accept false positives for speed benefits.
""")

if __name__ == '__main__':
    test_following_permissions()
    print_permission_info()