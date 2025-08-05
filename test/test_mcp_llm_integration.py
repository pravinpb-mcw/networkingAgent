#!/usr/bin/env python3
"""
Test script for MCP-LLM Integration
Tests the integration between MCP tools and Gemini LLM
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path so we can import from llm_integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_integration.mcp_llm_integration import MCPLLMIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-mcp-llm")

async def test_mcp_llm_integration():
    """Test the MCP-LLM integration"""
    print("🧪 Testing MCP-LLM Integration")
    print("="*50)
    
    try:
        # Initialize the integration
        print("Initializing MCP-LLM Integration...")
        integration = MCPLLMIntegration()
        print("✅ Integration initialized successfully")
        
        # Test individual MCP tool execution
        print("\n🔧 Testing individual MCP tools...")
        for tool_name in integration.mcp_tools.keys():
            print(f"Testing {tool_name}...")
            result = await integration.execute_mcp_tool(tool_name)
            status = result.get("status", "unknown")
            print(f"  {tool_name}: {status}")
        
        # Test complete analysis
        print("\n🤖 Testing complete MCP-LLM analysis...")
        await integration.run_mcp_llm_analysis()
        print("✅ Complete analysis test successful!")
        
    except Exception as e:
        print(f"❌ MCP-LLM integration test failed: {e}")
        logger.error(f"Test failed: {e}")

async def test_single_tool_analysis():
    """Test analysis of a single MCP tool"""
    print("\n🔍 Testing Single Tool Analysis")
    print("="*50)
    
    try:
        integration = MCPLLMIntegration()
        
        # Test with network clients tool
        print("Testing analysis of get_network_clients tool...")
        tool_result = await integration.execute_mcp_tool("get_network_clients")
        
        # Create mock MCP data structure
        mcp_data = {
            "timestamp": "2024-01-15T10:30:00",
            "mcp_tools_data": {
                "get_network_clients": tool_result
            },
            "tools_executed": ["get_network_clients"]
        }
        
        # Get LLM analysis
        analysis = await integration.get_llm_analysis(mcp_data)
        print(f"✅ Single tool analysis completed")
        print(f"   Status: {analysis['status']}")
        
        # Show preview
        if analysis['status'] == 'success':
            preview = analysis['analysis'][:300] + "..." if len(analysis['analysis']) > 300 else analysis['analysis']
            print(f"\n📝 Analysis Preview:")
            print("-" * 40)
            print(preview)
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Single tool analysis failed: {e}")
        logger.error(f"Single tool analysis failed: {e}")

async def main():
    """Main test function"""
    print("Cisco Meraki MCP-LLM Integration Test")
    print("="*50)
    
    # Check environment
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("Please add your Gemini API key to the .env file")
        return
    
    print("✅ Gemini API key found")
    
    # Run tests
    await test_mcp_llm_integration()
    await test_single_tool_analysis()
    
    print("\n" + "="*50)
    print("✅ All MCP-LLM integration tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 