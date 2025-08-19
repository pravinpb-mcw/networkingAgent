#!/usr/bin/env python3
"""
Test script to verify policy update functionality
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def test_policy_update():
    """Test the policy update functionality"""
    print("Testing policy update functionality...")
    
    try:
        # Import the function
        from server.update_network_group_policy import update_network_group_policy
        
        # Test data
        policy_id = "policy_2"
        policy_data = {
            "bandwidth": {
                "limitUp": 500,
                "limitDown": 10000
            },
            "firewallAndTrafficShaping": {
                "settings": {
                    "trafficShapingEnabled": True
                }
            }
        }
        
        print(f"Testing with policy_id: {policy_id}")
        print(f"Policy data: {policy_data}")
        
        # Run the test
        result = asyncio.run(update_network_group_policy(policy_id, policy_data, use_mock=True))
        
        print("✅ Policy update test completed successfully!")
        print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Policy update test failed: {e}")
        return False

def test_server_tool_definition():
    """Test that the server tool definition is correct"""
    print("\nTesting server tool definition...")
    
    try:
        # Import the server
        from server.meraki_server import app
        
        # Check if the tool is properly defined
        tools = asyncio.run(app.list_tools())
        
        # Find the update_network_group_policy tool
        policy_tool = None
        for tool in tools:
            if tool.name == "update_network_group_policy":
                policy_tool = tool
                break
        
        if policy_tool:
            print("✅ update_network_group_policy tool found")
            
            # Check the input schema
            schema = policy_tool.inputSchema
            if "policy_id" in schema.get("properties", {}) and "policy_data" in schema.get("properties", {}):
                print("✅ Tool schema has correct properties")
                return True
            else:
                print("❌ Tool schema missing required properties")
                return False
        else:
            print("❌ update_network_group_policy tool not found")
            return False
            
    except Exception as e:
        print(f"❌ Server tool definition test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("POLICY UPDATE FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("Server Tool Definition", test_server_tool_definition),
        ("Policy Update Function", test_policy_update),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
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
        print("🎉 All tests passed! The policy update functionality should work properly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
