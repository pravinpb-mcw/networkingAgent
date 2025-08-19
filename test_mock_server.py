#!/usr/bin/env python3
"""
Simple test script to verify mock server endpoints
"""

import requests
import json

def test_mock_server():
    """Test basic mock server functionality"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("Testing Mock Server Endpoints")
    print("=" * 40)
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running: {data.get('message')}")
            print(f"   Status: {data.get('status')}")
        else:
            print(f"❌ Root endpoint failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Server not running")
        print("   Start the server with: python mock_server.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Test endpoint
    print("\n2. Testing /test endpoint")
    try:
        response = requests.get(f"{base_url}/test")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test endpoint working: {data.get('message')}")
        else:
            print(f"❌ Test endpoint failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Wireless settings endpoint
    print("\n3. Testing POST /networks/{network_id}/wireless/settings")
    network_id = "main_network"
    wireless_data = {
        "enabled": True,
        "ssid": "Test_SSID_123"
    }
    
    try:
        response = requests.post(
            f"{base_url}/networks/{network_id}/wireless/settings",
            json=wireless_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Wireless settings updated: {data.get('message')}")
        else:
            print(f"❌ Wireless settings failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Appliance settings endpoint
    print("\n4. Testing POST /networks/{network_id}/appliance/settings")
    appliance_data = {
        "clientTrackingMethod": "MAC address",
        "deploymentMode": "routed"
    }
    
    try:
        response = requests.post(
            f"{base_url}/networks/{network_id}/appliance/settings",
            json=appliance_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Appliance settings updated: {data.get('message')}")
        else:
            print(f"❌ Appliance settings failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Create group policy endpoint
    print("\n5. Testing PUT /networks/{network_id}/groupPolicies")
    policy_data = {
        "name": "Test Policy",
        "bandwidth": {
            "limitUp": 1000,
            "limitDown": 1000
        },
        "scheduling": {
            "enabled": False
        },
        "firewallAndTrafficShaping": {
            "settings": {
                "trafficShapingEnabled": True
            }
        },
        "contentFiltering": {
            "enabled": False
        },
        "splashAuthSettings": "bypass",
        "vlanTagging": {},
        "bonjourForwarding": {}
    }
    
    try:
        response = requests.put(
            f"{base_url}/networks/{network_id}/groupPolicies",
            json=policy_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Group policy created: {data.get('message')}")
            print(f"   Policy ID: {data.get('policyId')}")
        else:
            print(f"❌ Group policy creation failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 40)
    print("Test completed!")
    
    return True

if __name__ == "__main__":
    test_mock_server() 