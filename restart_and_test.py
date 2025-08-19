#!/usr/bin/env python3
"""
Restart and Test Script for Networking Agent
This script will help diagnose and fix connection issues
"""

import os
import sys
import subprocess
import time
import json

def setup_environment():
    """Setup environment variables"""
    print("Setting up environment variables...")
    
    # Set default environment variables
    env_vars = {
        "USE_MOCK": "true",
        "BASE_URL": "http://127.0.0.1:5000",
        "TIMESPAN": "7200",
        "PRODUCT_TYPE": "appliance",
        "MERAKI_API_KEY": "demo_api_key_for_mock_mode",
        "NETWORK_ID": "main_network",
        "ORGANIZATION_ID": "demo_org_id",
        "GEMINI_API_KEY": "demo_gemini_key",
        "MCP_USE_ANONYMIZED_TELEMETRY": "false"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  Set {key}={value}")
    
    print("✅ Environment variables configured")

def check_files():
    """Check if required files exist"""
    print("\nChecking required files...")
    
    required_files = [
        "server/meraki_server.py",
        "mock_data/networks.json",
        "mock_data/common_data.json",
        "mcp-inspector-config.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files found")
        return True

def test_server_import():
    """Test if server can be imported"""
    print("\nTesting server import...")
    
    try:
        # Add server directory to path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))
        
        # Test import
        from server.meraki_server import app
        print("✅ Server imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        return False

def test_mock_data():
    """Test mock data access"""
    print("\nTesting mock data...")
    
    try:
        with open("mock_data/networks.json", 'r') as f:
            data = json.load(f)
        print("✅ Mock data loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Mock data test failed: {e}")
        return False

def create_env_file():
    """Create a .env file with proper configuration"""
    print("\nCreating environment configuration...")
    
    env_content = """# Meraki API Configuration
MERAKI_API_KEY=demo_api_key_for_mock_mode
NETWORK_ID=main_network
ORGANIZATION_ID=demo_org_id

# Gemini API Configuration
GEMINI_API_KEY=demo_gemini_key

# Server Configuration
USE_MOCK=true
BASE_URL=http://127.0.0.1:5000
TIMESPAN=7200
PRODUCT_TYPE=appliance

# MCP Configuration
MCP_USE_ANONYMIZED_TELEMETRY=false
"""
    
    try:
        with open(".env", 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("NETWORKING AGENT RESTART & TEST")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Check files
    if not check_files():
        print("\n❌ Some required files are missing. Please check the file structure.")
        return False
    
    # Test server import
    if not test_server_import():
        print("\n❌ Server import failed. Check for import errors.")
        return False
    
    # Test mock data
    if not test_mock_data():
        print("\n❌ Mock data test failed. Check mock_data directory.")
        return False
    
    # Create .env file
    create_env_file()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    print("✅ Environment configured")
    print("✅ Files checked")
    print("✅ Server import tested")
    print("✅ Mock data verified")
    print("✅ .env file created")
    
    print("\n🎉 The networking agent should now work properly!")
    print("\nTo start the agent:")
    print("1. Run: python client/mcp_client.py")
    print("2. Or run: streamlit run dashboard.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n✅ Setup completed successfully!")
