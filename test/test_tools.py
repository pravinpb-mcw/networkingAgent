#!/usr/bin/env python3
"""
Test script to demonstrate how to use the Meraki tools directly
This is for testing and development purposes
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path so we can import from server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.meraki_client import MerakiAPIClient
from server.get_network_clients import get_network_clients
from server.get_network_traffic import get_network_traffic
from server.get_device_loss_and_latency_history import get_device_loss_and_latency_history
from server.get_network_vpn_stats import get_organization_vpn_stats
from server.get_network_events import get_network_events
from server.get_organization_uplinks_statuses import get_organization_uplinks_statuses

from server.create_network_wireless_settings import create_network_wireless_settings
# Note: create_network_group_policy tool has been removed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-tools")

async def test_meraki_api_connection():
    """Test basic API connectivity"""
    try:
        print("Testing Meraki API connection...")
        client = MerakiAPIClient()
        print(f"✅ Successfully connected to Meraki API")
        print(f"   Network ID: {client.network_id}")
        print(f"   Organization ID: {client.organization_id}")
        print(f"   Device Serial: {client.serial}")
        print(f"   Device IP: {client.ip}")
        print(f"   Product Type: {client.product_type}")
        print(f"   Timespan: {client.timespan} seconds")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Meraki API: {e}")
        return False

async def test_all_tools():
    """Test all available tools"""
    tools = [
        ("get_network_clients", get_network_clients),
        ("get_network_traffic", get_network_traffic),
        ("get_device_loss_and_latency_history", get_device_loss_and_latency_history),
        ("get_organization_vpn_stats", get_organization_vpn_stats),
        ("get_network_events", get_network_events),
        ("get_organization_uplinks_statuses", get_organization_uplinks_statuses),
    
        ("create_network_wireless_settings", lambda: create_network_wireless_settings({"test": "settings"})),
        # Note: create_network_group_policy tool has been removed
    ]
    
    for tool_name, tool_func in tools:
        print(f"\n{'='*50}")
        print(f"Testing {tool_name}...")
        print(f"{'='*50}")
        
        try:
            result = await tool_func()
            print(f"✅ {tool_name} completed successfully")
            # The tool already prints its JSON output
        except Exception as e:
            print(f"❌ {tool_name} failed: {e}")

async def main():
    """Main test function"""
    print("Cisco Meraki Tools Test Script")
    print("="*50)
    
    # First test API connection
    if not await test_meraki_api_connection():
        print("\n❌ Cannot proceed without valid API connection.")
        print("Please check your .env file and ensure all required variables are set.")
        return
    
    # Test all tools
    await test_all_tools()
    
    print(f"\n{'='*50}")
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 