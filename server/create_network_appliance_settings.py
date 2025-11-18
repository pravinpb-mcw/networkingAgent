"""
Create Network Appliance Settings Tool
Creates new appliance settings for a specific network
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from meraki_client import MerakiAPIClient

logger = logging.getLogger("create-network-appliance-settings-tool")

async def create_network_appliance_settings(settings_data: Union[Dict[str, Any], str], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Add new appliance settings to your configured network.
    Uses NETWORK_ID from .env file.
    
    Args:
        settings_data: Dictionary or JSON string containing the appliance settings to add
        use_mock: Whether to use mock server mode
    """
    try:
        # Handle natural language input by converting it to structured data
        if isinstance(settings_data, str):
            # Convert natural language to structured settings data
            settings_data = convert_natural_language_to_settings_data(settings_data)
            logger.info("Successfully converted natural language input to settings data")
        
        # Ensure settings_data is a dict
        if not isinstance(settings_data, dict):
            raise ValueError("settings_data must be a dictionary or valid JSON string")

        client = MerakiAPIClient(use_mock=use_mock)
        
        # Add new appliance settings
        logger.info("Adding new appliance settings")
        
        try:
            # For mock server, we'll actually call the mock server to persist changes
            if use_mock:
                # In mock mode, call the mock server to actually add the settings
                add_result = await client.create_network_appliance_settings(network_id=None, settings_data=settings_data)
            else:
                # For real Meraki API, call the create endpoint
                add_result = await client.create_network_appliance_settings(network_id=None, settings_data=settings_data)
            
            result = {
                "tool": "create_network_appliance_settings",
                "timestamp": datetime.now().isoformat(),
                "network_id": client.network_id,
                "status": "success",
                "message": "Appliance settings added successfully",
                "added_settings": add_result
            }

            logger.info("Successfully added appliance settings")
            
            return [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]

        except Exception as e:
            logger.error(f"Failed to add appliance settings: {e}")
            error_result = {
                "tool": "create_network_appliance_settings",
                "timestamp": datetime.now().isoformat(),
                "network_id": client.network_id,
                "status": "error",
                "message": f"Failed to add appliance settings: {str(e)}"
            }
            return [{"type": "text", "text": json.dumps(error_result, indent=2, default=str)}]

    except Exception as e:
        logger.error(f"create_network_appliance_settings failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing create_network_appliance_settings: {str(e)}"}]

def convert_natural_language_to_settings_data(natural_language: str) -> Dict[str, Any]:
    """
    Convert natural language input to structured appliance settings data.
    
    Args:
        natural_language: Natural language description of settings
        
    Returns:
        Dictionary containing structured settings data
    """
    settings_data = {}
    natural_language_lower = natural_language.lower()
    
    # Parse DHCP lease time
    if "dhcp" in natural_language_lower and "lease" in natural_language_lower:
        dhcp_settings = {}
        
        # Extract lease time value
        import re
        lease_match = re.search(r'(\d+)\s*(?:seconds?|sec)', natural_language_lower)
        if lease_match:
            dhcp_settings["leaseTime"] = float(lease_match.group(1))
        
        if dhcp_settings:
            settings_data["dhcp"] = dhcp_settings
    
    # Parse VLAN settings
    if "vlan" in natural_language_lower:
        vlan_settings = {}
        
        if "enable" in natural_language_lower:
            vlan_settings["enabled"] = True
        elif "disable" in natural_language_lower:
            vlan_settings["enabled"] = False
        
        if vlan_settings:
            settings_data["vlan"] = vlan_settings
    
    # If no specific settings were parsed, create a basic structure
    if not settings_data:
        settings_data = {
            "dhcp": {"leaseTime": 8640.0},
            "vlan": {"enabled": True}
        }
    
    return settings_data
