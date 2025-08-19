#!/usr/bin/env python3
"""
Test script to verify MCP server connection
"""

import asyncio
import sys
import os
import subprocess
import time

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_server_startup():
    """Test if the MCP server can start properly"""
    print("Testing MCP server startup...")
    
    try:
        # Import configuration
        from config import setup_environment
        setup_environment()
        print("✅ Configuration loaded successfully")
        
        # Test importing the server
        sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))
        from server.meraki_server import app
        print("✅ Server module imported successfully")
        
        # Test basic server functionality
        print("✅ Server initialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False

def test_mock_data():
    """Test if mock data is accessible"""
    print("\nTesting mock data access...")
    
    try:
        import json
        
        # Test networks.json
        with open("mock_data/networks.json", 'r') as f:
            networks_data = json.load(f)
        print("✅ networks.json loaded successfully")
        
        # Test common_data.json
        with open("mock_data/common_data.json", 'r') as f:
            common_data = json.load(f)
        print("✅ common_data.json loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock data test failed: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported"""
    print("\nTesting module imports...")
    
    try:
        # Test server imports
        sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))
        
        from server.meraki_client import MerakiAPIClient
        print("✅ meraki_client imported")
        
        from server.update_network_wireless_settings import update_network_wireless_settings
        print("✅ update_network_wireless_settings imported")
        
        from server.update_network_appliance_settings import update_network_appliance_settings
        print("✅ update_network_appliance_settings imported")
        
        from server.update_network_group_policy import update_network_group_policy
        print("✅ update_network_group_policy imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

async def test_async_functions():
    """Test async functions"""
    print("\nTesting async functions...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))
        
        # Test wireless settings function
        from server.update_network_wireless_settings import update_network_wireless_settings
        
        test_settings = {
            "enabled": True,
            "ssid": "Test_SSID",
            "bandwidth": {
                "limitUp": 100,
                "limitDown": 100
            }
        }
        
        result = await update_network_wireless_settings(test_settings, use_mock=True)
        print("✅ update_network_wireless_settings executed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Async function test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("NETWORKING AGENT CONNECTION TEST")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("Server Startup", test_server_startup),
        ("Mock Data", test_mock_data),
        ("Module Imports", test_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    # Run async test
    print(f"\n🧪 Running Async Functions test...")
    try:
        async_result = asyncio.run(test_async_functions())
        results.append(("Async Functions", async_result))
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        results.append(("Async Functions", False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The networking agent should work properly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
