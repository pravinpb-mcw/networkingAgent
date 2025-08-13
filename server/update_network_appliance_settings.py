"""
Update Network Appliance Settings Tool
Updates appliance settings for a specific network
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-network-appliance-settings-tool")

async def update_network_appliance_settings(settings_data: Union[Dict[str, Any], str], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Update network appliance settings for your configured network.
    Uses NETWORK_ID from .env file.
    
    Args:
        settings_data: Dictionary or JSON string containing the appliance settings to update
        use_mock: Whether to use mock server mode
    """
    try:
        # Handle both dictionary and JSON string inputs
        if isinstance(settings_data, str):
            try:
                # Parse JSON string to dictionary
                settings_data = json.loads(settings_data)
                logger.info("Successfully parsed JSON string input to dictionary")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string: {e}")
        
        # Ensure settings_data is a dict
        if not isinstance(settings_data, dict):
            raise ValueError("settings_data must be a dictionary or valid JSON string")
        
        client = MerakiAPIClient(use_mock=use_mock)
        data = await client.update_network_appliance_settings(settings_data=settings_data)
        
        result = {
            "tool": "update_network_appliance_settings",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "settings_data": settings_data,
            "response": data,
            "summary": f"Successfully updated appliance settings for network {client.network_id}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"update_network_appliance_settings completed successfully for network {client.network_id}")
        
        return [{"type": "text", "text": json_output}]
        
    except Exception as e:
        logger.error(f"update_network_appliance_settings failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing update_network_appliance_settings: {str(e)}"}] 