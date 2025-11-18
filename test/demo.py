#!/usr/bin/env python3
"""
Demo script showing how to use individual Meraki tools
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path so we can import from server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.meraki_client import MerakiAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("demo")

async def demo_network_clients():
    """Demo: Get network clients"""
    print("\n🔍 Demo: Getting Network Clients")
    print("="*40)
    
    try:
        client = MerakiAPIClient()
        data = await client.get_network_clients()
        
        print(f"Found {len(data)} clients:")
        for i, client_data in enumerate(data[:5]):  # Show first 5
            print(f"  {i+1}. {client_data.get('description', 'Unknown')} - {client_data.get('ip', 'No IP')}")
        
        if len(data) > 5:
            print(f"  ... and {len(data) - 5} more clients")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def demo_network_traffic():
    """Demo: Get network traffic"""
    print("\n📊 Demo: Getting Network Traffic")
    print("="*40)
    
    try:
        client = MerakiAPIClient()
        data = await client.get_network_traffic()
        
        print(f"Found {len(data)} traffic records:")
        for i, traffic in enumerate(data[:3]):  # Show first 3
            print(f"  {i+1}. Application: {traffic.get('application', 'Unknown')}")
            print(f"     Protocol: {traffic.get('protocol', 'Unknown')}")
            print(f"     Port: {traffic.get('port', 'Unknown')}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def demo_network_events():
    """Demo: Get network events"""
    print("\n📅 Demo: Getting Network Events")
    print("="*40)
    
    try:
        client = MerakiAPIClient()
        data = await client.get_network_events()
        
        print(f"Found {len(data)} events:")
        for i, event in enumerate(data[:3]):  # Show first 3
            print(f"  {i+1}. Type: {event.get('type', 'Unknown')}")
            print(f"     Category: {event.get('category', 'Unknown')}")
            print(f"     Description: {event.get('description', 'No description')}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def demo_custom_parameters():
    """Demo: Using tools with custom parameters"""
    print("\n⚙️ Demo: Custom Parameters")
    print("="*40)
    
    try:
        client = MerakiAPIClient()
        
        # Example: Get clients for last 1 hour instead of default
        print("Getting clients for last 1 hour (3600 seconds)...")
        data = await client.get_network_clients(timespan=3600)
        print(f"Found {len(data)} clients in the last hour")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Main demo function"""
    print("Cisco Meraki Tools Demo")
    print("="*50)
    
    # Check if we have basic configuration
    try:
        client = MerakiAPIClient()
        print(f"✅ Connected to Meraki API")
        print(f"   Network: {client.network_id}")
        print(f"   Organization: {client.organization_id}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file")
        return
    
    # Run demos
    await demo_network_clients()
    await demo_network_traffic()
    await demo_network_events()
    await demo_custom_parameters()
    
    print("\n🎉 Demo completed!")
    print("\nTo see full JSON output, run: python test_tools.py")

if __name__ == "__main__":
    asyncio.run(main()) 