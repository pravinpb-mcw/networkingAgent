"""
Get Network Settings Tool
Retrieves settings for a specific network
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-network-settings-tool")

mcp = FastMCP("get-network-settings")

@mcp.tool()
async def get_network_settings() -> List[TextContent]:
    """
    Retrieve settings for your configured network.
    Returns network configuration including local status page, remote status page, and secure port settings.
    Uses NETWORK_ID from .env file.
    """
    try:
        
        # Initialize client (will load API key and network_id from .env file)
        client = MerakiAPIClient()
        data = await client.get_network_settings()
        
        result = {
            "tool": "get_network_settings",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "data": data,
            "summary": f"Retrieved network settings for network {client.network_id}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"get_network_settings completed successfully for network {client.network_id}.")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"❌ Error in get_network_settings: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_network_settings: {str(e)}"
        )]
