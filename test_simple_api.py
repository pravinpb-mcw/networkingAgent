#!/usr/bin/env python3
"""
Simple API Test - Verify API hits are visible
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

async def test_simple_api():
    """Test a simple API call to see if hits are visible."""
    print("🧪 Testing Simple API Call...")
    print("="*50)
    
    try:
        # Load environment
        load_dotenv()
        
        # Import the client
        from meraki_client import MerakiAPIClient
        
        # Create client
        client = MerakiAPIClient()
        print(f"✅ Client created")
        print()
        
        # Test one API call
        print("🔍 Testing get_organizations...")
        result = await client.get_organizations()
        print(f"✅ Test completed: {len(result)} organizations found")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_api())
