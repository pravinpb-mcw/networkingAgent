"""
Update Network Settings Tool
Updates network-wide configuration settings for a specific network
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-network-settings-tool")

mcp = FastMCP("update-network-settings")

@mcp.tool()
async def update_network_settings(settings_data: Union[Dict[str, Any], str], use_mock: bool = False) -> List[TextContent]:
    """
    Update network-wide configuration settings for your configured network.
    Uses NETWORK_ID from .env file.
    
    Args:
        settings_data: Network settings to apply (dict or natural language string)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with status information
    """
    try:
        # Handle natural language input
        if isinstance(settings_data, str):
            from natural_language_converter import convert_natural_language_to_network_settings
            settings_data = convert_natural_language_to_network_settings(settings_data)
        
        # Validate settings data
        if not isinstance(settings_data, dict):
            raise ValueError("settings_data must be a dictionary")
        
        # Initialize Meraki client
        client = MerakiAPIClient(use_mock=use_mock)
        
        # Apply network settings
        logger.info("Updating network settings...")
        network_result = await client.update_network_settings(settings_data=settings_data)
        
        result = {
            "tool": "update_network_settings",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "settings_applied": settings_data,
            "status": "success",
            "summary": f"Network settings updated successfully for network {client.network_id}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"update_network_settings completed successfully for network {client.network_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"update_network_settings failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing update_network_settings: {str(e)}"
        )]
