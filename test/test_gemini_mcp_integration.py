#!/usr/bin/env python3
"""
Test script for Gemini MCP Integration
Tests the integration between Gemini LLM and MCP tools
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path so we can import from llm_integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_integration.gemini_mcp_integration import GeminiMCPIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-gemini-mcp")

async def test_gemini_mcp_integration():
    """Test the Gemini MCP integration"""
    print("🧪 Testing Gemini MCP Integration")
    print("="*50)
    
    try:
        # Initialize the integration
        print("Initializing Gemini MCP Integration...")
        integration = GeminiMCPIntegration()
        print("✅ Integration initialized successfully")
        
        # Test specific insights
        print("\n🔍 Testing specific insight types...")
        insight_types = ["security", "performance", "operational", "comprehensive"]
        
        for insight_type in insight_types:
            print(f"\nTesting {insight_type} analysis...")
            result = await integration.get_specific_insights(insight_type)
            print(f"  Status: {result['status']}")
            if result['status'] == 'success':
                print(f"  Analysis length: {len(result['analysis'])} characters")
        
        # Test custom query
        print("\n🔧 Testing custom query...")
        custom_result = await integration.analyze_network(
            "Check my network for any security vulnerabilities and performance issues"
        )
        print(f"  Status: {custom_result['status']}")
        
        print("\n🎉 Gemini MCP integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Gemini MCP integration test failed: {e}")
        logger.error(f"Test failed: {e}")

async def test_automated_analysis():
    """Test automated analysis"""
    print("\n🚀 Testing Automated Analysis")
    print("="*50)
    
    try:
        integration = GeminiMCPIntegration()
        result = await integration.run_automated_analysis()
        print(f"✅ Automated analysis completed")
        print(f"   Status: {result['status']}")
        
    except Exception as e:
        print(f"❌ Automated analysis failed: {e}")
        logger.error(f"Automated analysis failed: {e}")

async def test_tool_execution():
    """Test individual tool execution"""
    print("\n🔧 Testing Individual Tool Execution")
    print("="*50)
    
    try:
        integration = GeminiMCPIntegration()
        
        # Test each tool
        tools = [
            ("get_network_clients", "Network Clients"),
            ("get_network_traffic", "Network Traffic"),
            ("get_device_loss_and_latency_history", "Device Performance"),
            ("get_organization_vpn_stats", "VPN Statistics"),
            ("get_network_events", "Network Events")
        ]
        
        for tool_name, tool_desc in tools:
            print(f"\nTesting {tool_desc}...")
            tool = next((t for t in integration.tools if t.name == tool_name), None)
            if tool:
                result = await tool._arun()
                print(f"  ✅ {tool_desc} executed successfully")
                print(f"  Result length: {len(result)} characters")
            else:
                print(f"  ❌ Tool {tool_name} not found")
        
    except Exception as e:
        print(f"❌ Tool execution test failed: {e}")
        logger.error(f"Tool execution failed: {e}")

async def main():
    """Main test function"""
    print("Cisco Meraki Gemini MCP Integration Test")
    print("="*50)
    
    # Check environment
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("Please add your Gemini API key to the .env file")
        return
    
    print("✅ Gemini API key found")
    
    # Run tests
    await test_gemini_mcp_integration()
    await test_automated_analysis()
    await test_tool_execution()
    
    print("\n" + "="*50)
    print("✅ All Gemini MCP integration tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 