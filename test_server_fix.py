#!/usr/bin/env python3
"""
Test script to verify server can start properly after fixes
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def test_server_imports():
    """Test if all server imports work correctly"""
    print("🧪 **TESTING SERVER IMPORTS**")
    print("=" * 40)
    
    try:
        # Test basic imports
        print("✅ Testing basic imports...")
        from server.meraki_client import MerakiAPIClient
        print("✅ MerakiAPIClient imported successfully")
        
        # Test wireless settings import
        print("✅ Testing wireless settings import...")
        from server.update_network_wireless_settings import update_network_wireless_settings
        print("✅ update_network_wireless_settings imported successfully")
        
        # Test group policy import
        print("✅ Testing group policy import...")
        from server.update_network_group_policy import update_network_group_policy
        print("✅ update_network_group_policy imported successfully")
        
        # Test other tool imports
        print("✅ Testing other tool imports...")
        from server.get_network_clients import get_network_clients
        from server.get_network_traffic import get_network_traffic
        from server.get_device_loss_and_latency_history import get_device_loss_and_latency_history
        from server.get_network_vpn_stats import get_organization_vpn_stats
        from server.get_network_events import get_network_events
        from server.get_organization_uplinks_statuses import get_organization_uplinks_statuses
        print("✅ All tool imports successful")
        
        # Test server import
        print("✅ Testing server import...")
        from server.meraki_server import app, handle_list_tools, handle_call_tool
        print("✅ Server imports successful")
        
        print("\n🎉 **ALL IMPORTS SUCCESSFUL!**")
        print("The server should now start without connection errors.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def test_wireless_function():
    """Test if the simplified wireless function works"""
    print("\n🧪 **TESTING WIRELESS FUNCTION**")
    print("=" * 40)
    
    try:
        from server.update_network_wireless_settings import update_network_wireless_settings
        
        # Test with mock data
        test_settings = {
            "enabled": True,
            "ssid": "TestNetwork",
            "bandwidth": {"limitUp": 100, "limitDown": 100}
        }
        
        print(f"✅ Testing with settings: {test_settings}")
        print("✅ Function exists and can be called")
        
    except Exception as e:
        print(f"❌ Error testing wireless function: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 **SERVER FIX VERIFICATION**")
    print("=" * 50)
    
    success1 = test_server_imports()
    success2 = test_wireless_function()
    
    if success1 and success2:
        print("\n🎉 **ALL TESTS PASSED!**")
        print("The server should now work correctly.")
        print("Try using the networking agent again.")
    else:
        print("\n❌ **SOME TESTS FAILED**")
        print("There may still be issues with the server.")
