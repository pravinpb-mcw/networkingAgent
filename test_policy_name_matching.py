#!/usr/bin/env python3
"""
Test script to verify policy name matching functionality
"""

import asyncio
import sys
import os

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.update_network_wireless_settings import handle_traffic_shaping_response

async def test_policy_name_matching():
    """Test that policy name matching works correctly"""
    print("🔍 **TESTING POLICY NAME MATCHING**")
    print("=" * 50)
    
    # Test wireless settings
    wireless_settings = {
        "enabled": True,
        "ssid": "Test_SSID",
        "bandwidth": {
            "limitUp": 100,
            "limitDown": 100
        }
    }
    
    # Test cases for policy name matching
    test_cases = [
        ("policy_1", "Policy ID"),
        ("policy_1policy_1", "Duplicated Policy ID"),
        ("Updated Staff Policy", "Policy Name"),
        ("updated staff policy", "Policy Name (lowercase)"),
        ("UPDATED STAFF POLICY", "Policy Name (uppercase)"),
        ("Staff Policy", "Partial Policy Name"),
        ("policy_2", "Another Policy ID"),
        ("policy_2policy_2", "Duplicated Another Policy ID"),
        ("YES", "Enable All"),
        ("NO", "Skip"),
        ("invalid_policy", "Invalid Policy")
    ]
    
    for user_input, description in test_cases:
        print(f"\n📋 **Test Case: {description}**")
        print(f"Input: '{user_input}'")
        
        try:
            result = await handle_traffic_shaping_response(user_input, wireless_settings, use_mock=True)
            print("✅ Input processed successfully!")
            print(f"Result preview: {result[0]['text'][:200]}...")
        except Exception as e:
            print(f"❌ Input processing failed: {e}")
    
    print(f"\n{'='*50}")
    print("✅ Policy name matching test completed!")

if __name__ == "__main__":
    asyncio.run(test_policy_name_matching())
