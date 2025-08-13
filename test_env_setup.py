#!/usr/bin/env python3
"""
Test script to verify environment variables and mock mode setup
"""

import os
from dotenv import load_dotenv

def test_env_setup():
    """Test environment variable setup"""
    
    print("Testing Environment Setup")
    print("=" * 50)
    
    # Load .env file
    load_dotenv()
    
    # Check key environment variables
    print("\nEnvironment Variables:")
    print("-" * 30)
    
    base_url = os.getenv("BASE_URL", "")
    network_id = os.getenv("NETWORK_ID", "")
    organization_id = os.getenv("ORGANIZATION_ID", "")
    product_type = os.getenv("PRODUCT_TYPE", "")
    timespan = os.getenv("TIMESPAN", "")
    
    print(f"BASE_URL: {base_url}")
    print(f"NETWORK_ID: {network_id}")
    print(f"ORGANIZATION_ID: {organization_id}")
    print(f"PRODUCT_TYPE: {product_type}")
    print(f"TIMESPAN: {timespan}")
    
    # Check mock mode detection
    print("\nMock Mode Detection:")
    print("-" * 30)
    
    use_mock = os.getenv("USE_MOCK", "false").lower() == "true"
    print(f"USE_MOCK env var: {use_mock}")
    
    # Auto-detect mock mode from BASE_URL
    if base_url and ("127.0.0.1" in base_url or "localhost" in base_url):
        auto_mock = True
        print(f"Auto-detected mock mode from BASE_URL: {auto_mock}")
    else:
        auto_mock = False
        print(f"Auto-detected mock mode from BASE_URL: {auto_mock}")
    
    # Final mock mode
    final_mock = use_mock or auto_mock
    print(f"Final mock mode: {final_mock}")
    
    # Check if required variables are set
    print("\nRequired Variables Check:")
    print("-" * 30)
    
    if not network_id:
        print("❌ NETWORK_ID not set - required for update operations")
    else:
        print("✅ NETWORK_ID is set")
    
    if not base_url:
        print("❌ BASE_URL not set - will use default Meraki API")
    else:
        print("✅ BASE_URL is set")
    
    if final_mock:
        print("✅ Mock mode enabled - will use local server")
    else:
        print("❌ Mock mode disabled - will use real Meraki API")
    
    print("\n" + "=" * 50)
    
    if not network_id:
        print("\n⚠️  WARNING: NETWORK_ID is required for update operations!")
        print("   Add NETWORK_ID=your_network_id to your .env file")
    
    if not final_mock and not base_url:
        print("\n⚠️  WARNING: No BASE_URL set and mock mode disabled!")
        print("   Add BASE_URL=http://127.0.0.1:5000 to use local mock server")
    
    return final_mock, network_id

if __name__ == "__main__":
    test_env_setup() 