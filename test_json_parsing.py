#!/usr/bin/env python3
"""
Test script to verify JSON string parsing in update tools
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

async def test_json_parsing():
    """Test JSON string parsing in update tools"""
    
    print("Testing JSON String Parsing in Update Tools")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    try:
        # Import the functions
        from update_network_wireless_settings import update_network_wireless_settings
        from update_network_appliance_settings import update_network_appliance_settings
        # Note: create_network_group_policy tool has been removed
        
        print("✅ Successfully imported update functions")
        
        # Test 1: JSON string input for wireless settings
        print("\n1. Testing update_network_wireless_settings with JSON string")
        print("-" * 60)
        
        wireless_json = '{"enabled": true, "ssid": "Test_SSID_JSON", "bandwidth": {"limitUp": 1000, "limitDown": 1000}}'
        
        try:
            result = await update_network_wireless_settings(wireless_json, use_mock=True)
            print("✅ Wireless settings update with JSON string successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Wireless settings update with JSON string failed: {e}")
        
        # Test 2: JSON string input for appliance settings
        print("\n2. Testing update_network_appliance_settings with JSON string")
        print("-" * 60)
        
        appliance_json = '{"clientTrackingMethod": "MAC address", "deploymentMode": "routed"}'
        
        try:
            result = await update_network_appliance_settings(appliance_json, use_mock=True)
            print("✅ Appliance settings update with JSON string successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Appliance settings update with JSON string failed: {e}")
        
        # Test 3: JSON string input for group policy creation
        print("\n3. Testing create_network_group_policy with JSON string")
        print("-" * 60)
        print("Note: create_network_group_policy tool has been removed")
        print("Use update_network_group_policy instead")
        print("Skipping this test...")
        
        # Test 4: Dictionary input (should still work)
        print("\n4. Testing update_network_wireless_settings with dictionary")
        print("-" * 60)
        
        wireless_dict = {
            "enabled": True,
            "ssid": "Test_SSID_Dict",
            "bandwidth": {"limitUp": 2000, "limitDown": 2000}
        }
        
        try:
            result = await update_network_wireless_settings(wireless_dict, use_mock=True)
            print("✅ Wireless settings update with dictionary successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Wireless settings update with dictionary failed: {e}")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_json_parsing()) 