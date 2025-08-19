#!/usr/bin/env python3
"""
Test script to verify input duplication fix is working
"""

import asyncio
import sys
import os

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.update_network_wireless_settings import handle_traffic_shaping_response

async def test_input_duplication_fix():
    """Test that input duplication is handled correctly"""
    print("🔍 **TESTING INPUT DUPLICATION FIX**")
    print("=" * 50)
    
    # Test wireless settings
    wireless_settings = {
        "enabled": True,
        "ssid": "My_SSID",
        "bandwidth": {
            "limitUp": 100,
            "limitDown": 100
        }
    }
    
    # Test cases for duplicated input
    test_cases = [
        ("YES", "Normal YES"),
        ("YESYES", "Duplicated YES"),
        ("NONO", "Duplicated NO"),
        ("policy_2", "Normal policy ID"),
        ("policy_2policy_2", "Duplicated policy ID"),
        ("policy_2:YESpolicy_2:YES", "Duplicated policy response")
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
    print("✅ Input duplication test completed!")

if __name__ == "__main__":
    asyncio.run(test_input_duplication_fix())
