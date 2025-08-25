"""
Update Access Control Lists Tool
Updates network access control lists for a network
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-access-control-lists-tool")

mcp = FastMCP("update-access-control-lists")

@mcp.tool()
async def update_network_access_control_lists(acl_data: Union[Dict[str, Any], str], network_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Update network access control lists for a network.
    Uses NETWORK_ID from .env file if not specified.
    
    Args:
        acl_data: Access control list configuration (dict or natural language string)
        network_id: Optional network ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with status information
    """
    try:
        # Handle natural language input
        if isinstance(acl_data, str):
            from natural_language_converter import convert_natural_language_to_access_control_lists
            acl_data = convert_natural_language_to_access_control_lists(acl_data)
        
        # Validate ACL data
        if not isinstance(acl_data, dict):
            raise ValueError("acl_data must be a dictionary")
        
        client = MerakiAPIClient(use_mock=use_mock)
        logger.info("Updating network access control lists...")
        
        result = await client.update_network_access_control_lists(
            network_id=network_id,
            acl_data=acl_data
        )
        
        response = {
            "tool": "update_network_access_control_lists",
            "timestamp": datetime.now().isoformat(),
            "network_id": network_id or client.network_id,
            "acl_updated": result,
            "status": "success",
            "summary": f"Updated access control lists for network {network_id or client.network_id}"
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        logger.info(f"update_network_access_control_lists completed successfully for network {network_id or client.network_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"update_network_access_control_lists failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing update_network_access_control_lists: {str(e)}"
        )]
