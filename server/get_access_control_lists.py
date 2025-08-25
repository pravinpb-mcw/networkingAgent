"""
Get Access Control Lists Tool
Retrieves network access control lists for a network
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-access-control-lists-tool")

mcp = FastMCP("get-access-control-lists")

@mcp.tool()
async def get_network_access_control_lists(network_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Get network access control lists for a network.
    Uses NETWORK_ID from .env file if not specified.
    
    Args:
        network_id: Optional network ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with access control list information
    """
    try:
        client = MerakiAPIClient(use_mock=use_mock)
        logger.info("Retrieving network access control lists...")
        
        result = await client.get_network_access_control_lists(network_id=network_id)
        
        response = {
            "tool": "get_network_access_control_lists",
            "timestamp": datetime.now().isoformat(),
            "network_id": network_id or client.network_id,
            "access_control_lists": result,
            "status": "success",
            "summary": f"Retrieved access control lists for network {network_id or client.network_id}"
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        logger.info(f"get_network_access_control_lists completed successfully for network {network_id or client.network_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"get_network_access_control_lists failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_network_access_control_lists: {str(e)}"
        )]
