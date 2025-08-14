#!/usr/bin/env python3
"""
Direct test of update_network_wireless_settings function
Bypasses MCP Agent to test the actual function
"""

import asyncio
import sys
import os

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

async def test_direct_call():
    """Test the function directly with the JSON data"""
    
    try:
        from update_network_wireless_settings import update_network_wireless_settings
        
        # The exact JSON you provided
        test_json = '{"enabled": true, "ssid": "My_SSID", "bandwidth": {"limitUp": 1000, "limitDown": 1000}}'
        
        print("Testing update_network_wireless_settings directly...")
        print(f"Input JSON: {test_json}")
        print("-" * 60)
        
        # Call the function directly
        result = await update_network_wireless_settings(test_json, use_mock=True)
        
        print("✅ SUCCESS! Function executed successfully")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_call())
