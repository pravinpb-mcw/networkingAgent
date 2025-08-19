#!/usr/bin/env python3
"""
Simple test to verify mock server is working
"""

import requests
import json

def test_mock_server():
    """Test basic mock server functionality"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("Testing Mock Server")
    print("=" * 30)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Server is running: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Get current networks data
    try:
        response = requests.get(f"{base_url}/networks")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Networks data loaded: {list(data.keys())}")
            
            # Check if main_network exists
            if "main_network" in data:
                print(f"✅ main_network found")
                if "policies" in data["main_network"]:
                    policies = list(data["main_network"]["policies"].keys())
                    print(f"✅ Policies found: {policies}")
                    
                    # Show current policy_2 data
                    if "policy_2" in data["main_network"]["policies"]:
                        policy_2 = data["main_network"]["policies"]["policy_2"]
                        print(f"✅ policy_2 current data:")
                        print(f"   Bandwidth: {policy_2.get('bandwidth', 'Not set')}")
                        print(f"   Traffic Shaping: {policy_2.get('firewallAndTrafficShaping', 'Not set')}")
                else:
                    print(f"❌ No policies found in main_network")
            else:
                print(f"❌ main_network not found")
        else:
            print(f"❌ Failed to get networks: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting networks: {e}")

if __name__ == "__main__":
    test_mock_server()
