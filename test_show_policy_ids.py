#!/usr/bin/env python3
"""
Test script to verify that policy IDs are shown to users
"""

import asyncio
import sys
import os

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.update_network_wireless_settings import update_network_wireless_settings

async def test_show_policy_ids():
    """Test that policy IDs are shown to users"""
    print("🔍 **TESTING POLICY ID DISPLAY**")
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
    
    print("\n📋 **Testing update_network_wireless_settings**")
    print("This should show available policy IDs and names:")
    print("-" * 50)
    
    try:
        result = await update_network_wireless_settings(wireless_settings, use_mock=True)
        print("✅ Function executed successfully!")
        print("\n📄 **RESPONSE:**")
        print(result[0]['text'])
        
        # Check if policy IDs are shown
        if "AVAILABLE POLICIES" in result[0]['text']:
            print("\n✅ **SUCCESS:** Policy IDs are being shown!")
        else:
            print("\n❌ **ISSUE:** Policy IDs are not being shown")
            
    except Exception as e:
        print(f"❌ Function failed: {e}")
    
    print(f"\n{'='*50}")
    print("✅ Policy ID display test completed!")

if __name__ == "__main__":
    asyncio.run(test_show_policy_ids())
