#!/usr/bin/env python3
"""
Test script for LLM integration
Tests the Gemini integration with Meraki data
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path so we can import from llm_integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_integration.meraki_insights import MerakiInsightsCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-llm")

async def test_llm_integration():
    """Test the LLM integration"""
    print("🧪 Testing LLM Integration with Gemini")
    print("="*50)
    
    try:
        # Initialize the insights collector
        print("Initializing MerakiInsightsCollector...")
        collector = MerakiInsightsCollector()
        print("✅ Collector initialized successfully")
        
        # Test data collection
        print("\n📊 Testing data collection...")
        data = await collector.collect_all_data()
        print(f"✅ Data collection completed")
        print(f"   - Network clients: {len(data.get('network_clients', [])) if data.get('network_clients') else 0}")
        print(f"   - Network traffic: {len(data.get('network_traffic', [])) if data.get('network_traffic') else 0}")
        print(f"   - Device performance: {len(data.get('device_performance', [])) if data.get('device_performance') else 0}")
        print(f"   - VPN stats: {len(data.get('vpn_stats', [])) if data.get('vpn_stats') else 0}")
        print(f"   - Network events: {len(data.get('network_events', [])) if data.get('network_events') else 0}")
        
        # Test insights generation
        print("\n🤖 Testing insights generation with Gemini...")
        insights = await collector.get_insights_from_gemini(data)
        print(f"✅ Insights generated successfully")
        print(f"   Status: {insights['status']}")
        print(f"   Timestamp: {insights['timestamp']}")
        
        # Show a preview of the insights
        if insights['status'] == 'success':
            insights_text = insights['insights']
            preview = insights_text[:500] + "..." if len(insights_text) > 500 else insights_text
            print(f"\n📝 Insights Preview:")
            print("-" * 40)
            print(preview)
            print("-" * 40)
        
        print("\n🎉 LLM integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ LLM integration test failed: {e}")
        logger.error(f"Test failed: {e}")

async def test_single_run():
    """Test a single complete run"""
    print("\n🚀 Testing Complete Insights Collection Run")
    print("="*50)
    
    try:
        collector = MerakiInsightsCollector()
        await collector.run_insights_collection()
        print("✅ Complete run test successful!")
        
    except Exception as e:
        print(f"❌ Complete run test failed: {e}")
        logger.error(f"Complete run failed: {e}")

async def main():
    """Main test function"""
    print("Cisco Meraki LLM Integration Test")
    print("="*50)
    
    # Check environment
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("Please add your Gemini API key to the .env file")
        return
    
    print("✅ Gemini API key found")
    
    # Run tests
    await test_llm_integration()
    await test_single_run()
    
    print("\n" + "="*50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 