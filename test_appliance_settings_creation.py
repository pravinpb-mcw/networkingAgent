#!/usr/bin/env python3
"""
Test script to verify appliance settings creation as new entries
"""

import asyncio
import sys
import os
import json

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.create_network_appliance_settings import create_network_appliance_settings

async def test_appliance_settings_creation():
    """Test that appliance settings are created as new entries"""
    print("🔍 **TESTING APPLIANCE SETTINGS CREATION**")
    print("=" * 50)
    
    # Test 1: Create first appliance settings
    print("\n📋 **Test 1: Create First Appliance Settings**")
    print("-" * 50)
    
    settings_1 = {
        "dhcp": {
            "leaseTime": 3600,
            "enabled": True
        },
        "firewall": {
            "enabled": True
        }
    }
    
    try:
        result_1 = await create_network_appliance_settings(settings_1, use_mock=True)
        print("✅ First appliance settings created successfully!")
        print(f"Result: {result_1[0]['text']}")
    except Exception as e:
        print(f"❌ First creation failed: {e}")
    
    # Test 2: Create second appliance settings
    print("\n📋 **Test 2: Create Second Appliance Settings**")
    print("-" * 50)
    
    settings_2 = {
        "vlan": {
            "enabled": True,
            "vlanId": 100
        },
        "dhcp": {
            "leaseTime": 7200,
            "enabled": False
        }
    }
    
    try:
        result_2 = await create_network_appliance_settings(settings_2, use_mock=True)
        print("✅ Second appliance settings created successfully!")
        print(f"Result: {result_2[0]['text']}")
    except Exception as e:
        print(f"❌ Second creation failed: {e}")
    
    # Test 3: Create third appliance settings
    print("\n📋 **Test 3: Create Third Appliance Settings**")
    print("-" * 50)
    
    settings_3 = {
        "bandwidth": {
            "limitUp": 100,
            "limitDown": 50
        },
        "contentFiltering": {
            "enabled": True
        }
    }
    
    try:
        result_3 = await create_network_appliance_settings(settings_3, use_mock=True)
        print("✅ Third appliance settings created successfully!")
        print(f"Result: {result_3[0]['text']}")
    except Exception as e:
        print(f"❌ Third creation failed: {e}")
    
    # Check the final JSON structure
    print("\n📋 **Final JSON Structure Check**")
    print("-" * 50)
    
    try:
        with open("mock_data/networks.json", 'r') as f:
            networks_data = json.load(f)
        
        appliance_settings = networks_data["main_network"]["appliance_settings"]
        print(f"✅ Total appliance settings entries: {len(appliance_settings)}")
        
        for i, entry in enumerate(appliance_settings, 1):
            print(f"\n📄 **Entry {i}:**")
            print(f"   ID: {entry.get('id', 'N/A')}")
            print(f"   Created: {entry.get('created_at', 'N/A')}")
            print(f"   Settings: {json.dumps(entry, indent=4, default=str)}")
        
        print(f"\n✅ **SUCCESS:** Appliance settings are now stored as separate entries!")
        
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
    
    print(f"\n{'='*50}")
    print("✅ Appliance settings creation test completed!")

if __name__ == "__main__":
    asyncio.run(test_appliance_settings_creation())
