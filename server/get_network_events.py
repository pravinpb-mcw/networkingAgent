"""
Get Network Events Tool
Retrieves events for a specific network
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-network-events-tool")

mcp = FastMCP("get-network-events")

@mcp.tool()
async def get_network_events() -> List[TextContent]:
    """
    Retrieve events for your configured network.
    Returns network events including device status changes, security events, and system notifications.
    Uses NETWORK_ID and PRODUCT_TYPE from .env file.
    """
    try:
        # Initialize client (will load API key, network_id, and product_type from .env file)
        client = MerakiAPIClient()
        data = await client.get_network_events()
        
        result = {
            "tool": "get_network_events",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "product_type": client.product_type,
            "data": data,
            "summary": f"Retrieved {len(data)} events for network {client.network_id} with product type {client.product_type}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"get_network_events completed successfully. Retrieved {len(data)} events for network {client.network_id}.")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"get_network_events failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_network_events: {str(e)}"
        )] 