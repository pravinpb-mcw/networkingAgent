"""
Configuration file for the Networking Agent
Set up environment variables and configuration settings
"""

import os

# Set default environment variables if not already set
def setup_environment():
    """Setup environment variables for the networking agent"""
    
    # Meraki API Configuration
    if not os.getenv("MERAKI_API_KEY"):
        os.environ["MERAKI_API_KEY"] = "demo_api_key_for_mock_mode"
    
    if not os.getenv("NETWORK_ID"):
        os.environ["NETWORK_ID"] = "main_network"
    
    if not os.getenv("ORGANIZATION_ID"):
        os.environ["ORGANIZATION_ID"] = "demo_org_id"
    
    # Gemini API Configuration
    if not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = "AIzaSyB_1234567890abcdefghijklmnopqrstuvwxyz"  # Demo key for testing
    
    # Server Configuration
    if not os.getenv("USE_MOCK"):
        os.environ["USE_MOCK"] = "true"
    
    if not os.getenv("BASE_URL"):
        os.environ["BASE_URL"] = "http://127.0.0.1:5000"
    
    if not os.getenv("TIMESPAN"):
        os.environ["TIMESPAN"] = "7200"
    
    if not os.getenv("PRODUCT_TYPE"):
        os.environ["PRODUCT_TYPE"] = "appliance"
    
    # MCP Configuration
    if not os.getenv("MCP_USE_ANONYMIZED_TELEMETRY"):
        os.environ["MCP_USE_ANONYMIZED_TELEMETRY"] = "false"

# Configuration for mock mode
MOCK_CONFIG = {
    "api_key": "demo_api_key_for_mock_mode",
    "network_id": "main_network",
    "organization_id": "demo_org_id",
    "base_url": "http://127.0.0.1:5000",
    "use_mock": True
}

# Configuration for real API mode
REAL_CONFIG = {
    "api_key": os.getenv("MERAKI_API_KEY", ""),
    "network_id": os.getenv("NETWORK_ID", ""),
    "organization_id": os.getenv("ORGANIZATION_ID", ""),
    "base_url": os.getenv("BASE_URL", "https://api.meraki.com/api/v1"),
    "use_mock": False
}

# Get current configuration
def get_config():
    """Get current configuration based on USE_MOCK setting"""
    use_mock = os.getenv("USE_MOCK", "true").lower() == "true"
    return MOCK_CONFIG if use_mock else REAL_CONFIG

# Initialize environment when module is imported
setup_environment()
