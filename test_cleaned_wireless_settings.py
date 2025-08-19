#!/usr/bin/env python3
"""
Test script to verify the cleaned wireless settings functionality
"""

import asyncio
import sys
import os
import json

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.update_network_wireless_settings import (
    check_existing_group_policies_for_traffic_shaping,
    show_available_policies,
    update_network_wireless_settings,
    handle_traffic_shaping_response
)

async def test_cleaned_wireless_settings():
    """Test the cleaned wireless settings functionality"""
    print("🔍 **TESTING CLEANED WIRELESS SETTINGS**")
    print("=" * 50)
    
    # Test 1: Check available policies
    print("\n📋 **Test 1: Show Available Policies**")
    print("-" * 50)
    
    try:
        policies_info = show_available_policies()
        print("✅ Available policies retrieved successfully!")
        print(policies_info)
    except Exception as e:
        print(f"❌ Error showing policies: {e}")
    
    # Test 2: Check traffic shaping status
    print("\n📋 **Test 2: Check Traffic Shaping Status**")
    print("-" * 50)
    
    try:
        traffic_shaping_check = check_existing_group_policies_for_traffic_shaping()
        print("✅ Traffic shaping check completed!")
        print(f"Found policies: {traffic_shaping_check['found_policies']}")
        print(f"Policies with disabled traffic shaping: {len(traffic_shaping_check['policies_with_disabled_traffic_shaping'])}")
        
        if traffic_shaping_check['policies_with_disabled_traffic_shaping']:
            print("📋 **Policies with disabled traffic shaping:**")
            for policy in traffic_shaping_check['policies_with_disabled_traffic_shaping']:
                print(f"   • {policy['policy_id']} ({policy['policy_name']}) - Network: {policy['network_id']}")
    except Exception as e:
        print(f"❌ Error checking traffic shaping: {e}")
    
    # Test 3: Test wireless settings creation (without traffic shaping prompt)
    print("\n📋 **Test 3: Create Wireless Settings**")
    print("-" * 50)
    
    settings = {
        "enabled": True,
        "ssid": "Test_Cleaned_SSID",
        "bandwidth": {
            "limitUp": 150,
            "limitDown": 100
        }
    }
    
    try:
        result = await update_network_wireless_settings(settings, use_mock=True)
        print("✅ Wireless settings creation initiated!")
        print(f"Result: {result[0]['text']}")
    except Exception as e:
        print(f"❌ Error creating wireless settings: {e}")
    
    # Test 4: Test traffic shaping response handling
    print("\n📋 **Test 4: Handle Traffic Shaping Response**")
    print("-" * 50)
    
    try:
        # Test with "YES" response
        response = await handle_traffic_shaping_response("YES", settings, use_mock=True)
        print("✅ Traffic shaping response handled successfully!")
        print(f"Response: {response[0]['text']}")
    except Exception as e:
        print(f"❌ Error handling traffic shaping response: {e}")
    
    print(f"\n{'='*50}")
    print("✅ Cleaned wireless settings test completed!")

if __name__ == "__main__":
    asyncio.run(test_cleaned_wireless_settings())
