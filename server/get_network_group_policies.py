"""
Get Network Group Policies Tool
Retrieves group policies for a specific network
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-network-group-policies-tool")

mcp = FastMCP("get-network-group-policies")

@mcp.tool()
async def get_network_group_policies() -> List[TextContent]:
    """
    Retrieve group policies for your configured network.
    Returns policy information including bandwidth limits, scheduling, and content filtering rules.
    Uses NETWORK_ID from .env file.
    """
    try:
        
        # Initialize client (will load API key and network_id from .env file)
        client = MerakiAPIClient()
        data = await client.get_network_group_policies()
        
        result = {
            "tool": "get_network_group_policies",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "data": data,
            "summary": f"Retrieved {len(data)} group policies for network {client.network_id}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"get_network_group_policies completed successfully. Retrieved {len(data)} policies for network {client.network_id}.")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"❌ Error in get_network_group_policies: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_network_group_policies: {str(e)}"
        )]
