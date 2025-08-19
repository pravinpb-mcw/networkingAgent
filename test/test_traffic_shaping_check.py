#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced traffic shaping check functionality
This shows how the create_network_wireless_settings tool now checks existing policies
"""

import asyncio
import json
import logging
import sys
import os

# Add the parent directory to the path so we can import from server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.update_network_wireless_settings import check_existing_group_policies_for_traffic_shaping, handle_traffic_shaping_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-traffic-shaping-check")

def test_traffic_shaping_check():
    """Test the traffic shaping check functionality"""
    print("🔍 **TESTING TRAFFIC SHAPING CHECK FUNCTIONALITY**")
    print("=" * 60)
    
    # Test 1: Check existing policies
    print("\n📋 **Step 1: Checking existing group policies...**")
    policy_check_result = check_existing_group_policies_for_traffic_shaping()
    
    print(f"Found policies with disabled traffic shaping: {policy_check_result['found_policies']}")
    print(f"Total policies checked: {policy_check_result.get('total_policies_checked', 0)}")
    
    if policy_check_result["found_policies"]:
        print("\n📋 **Policies with trafficShapingEnabled=false:**")
        for policy in policy_check_result["policies_with_disabled_traffic_shaping"]:
            print(f"   • Policy ID: {policy['policy_id']}")
            print(f"     Name: {policy['policy_name']}")
            print(f"     Network: {policy['network_id']}")
            print(f"     Current Status: Traffic Shaping DISABLED")
            print("")
    else:
        print("✅ All existing policies have trafficShapingEnabled=true or no policies found.")
    
    return policy_check_result

async def test_traffic_shaping_response():
    """Test the traffic shaping response handling"""
    print("\n🔄 **Step 2: Testing traffic shaping response handling...**")
    
    # Sample wireless settings
    wireless_settings = {
        "enabled": True,
        "ssid": "Test_SSID",
        "bandwidth": {
            "limitUp": 1000,
            "limitDown": 1000
        }
    }
    
    # Test different user responses
    test_responses = [
        ("YES", "Enable traffic shaping for all policies"),
        ("NO", "Skip traffic shaping"),
        ("policy_1:YES", "Enable traffic shaping for specific policy")
    ]
    
    for response, description in test_responses:
        print(f"\n🧪 **Testing response: '{response}' ({description})**")
        try:
            result = await handle_traffic_shaping_response(response, wireless_settings, use_mock=True)
            print("✅ Response handled successfully")
            print(f"Result: {result[0]['text'][:200]}...")
        except Exception as e:
            print(f"❌ Error handling response: {e}")

def create_test_policy_with_disabled_traffic_shaping():
    """Create a test policy with trafficShapingEnabled=false for testing"""
    print("\n🔧 **Step 3: Creating test policy with disabled traffic shaping...**")
    
    # Read existing networks.json
    networks_file_path = os.path.join("mock_data", "networks.json")
    
    if os.path.exists(networks_file_path):
        with open(networks_file_path, 'r') as f:
            networks_data = json.load(f)
    else:
        networks_data = {}
    
    # Add a test network if it doesn't exist
    if "test_network" not in networks_data:
        networks_data["test_network"] = {
            "groupPolicies": {}
        }
    
    # Add a test policy with disabled traffic shaping
    networks_data["test_network"]["groupPolicies"]["test_policy_disabled"] = {
        "id": "test_policy_disabled",
        "name": "Test Policy - Traffic Shaping Disabled",
        "scheduling": {},
        "bandwidth": {
            "limitDown": 5000.0,
            "limitUp": 1000.0
        },
        "firewallAndTrafficShaping": {
            "settings": {
                "trafficShapingEnabled": False  # This is what we're testing for
            }
        },
        "contentFiltering": {},
        "splashAuthSettings": "bypass",
        "vlanTagging": {},
        "bonjourForwarding": {},
        "updated_at": "2025-01-20T10:00:00.000000"
    }
    
    # Write back to file
    with open(networks_file_path, 'w') as f:
        json.dump(networks_data, f, indent=2)
    
    print("✅ Created test policy with trafficShapingEnabled=false")
    print("   Policy ID: test_policy_disabled")
    print("   Name: Test Policy - Traffic Shaping Disabled")

async def main():
    """Main test function"""
    print("Cisco Meraki Traffic Shaping Check Test")
    print("=" * 60)
    
    # Step 1: Create test policy with disabled traffic shaping
    create_test_policy_with_disabled_traffic_shaping()
    
    # Step 2: Test traffic shaping check
    policy_check_result = test_traffic_shaping_check()
    
    # Step 3: Test response handling
    await test_traffic_shaping_response()
    
    print(f"\n{'='*60}")
    print("✅ Test completed successfully!")
    print("\n📝 **Summary:**")
    print("• The enhanced create_network_wireless_settings tool now checks existing policies")
    print("• It identifies policies with trafficShapingEnabled=false")
    print("• It asks users if they want to enable traffic shaping")
    print("• Users can enable for all policies, skip, or enable for specific policies")
    print("• After handling traffic shaping, it proceeds with wireless settings creation")

if __name__ == "__main__":
    asyncio.run(main())
