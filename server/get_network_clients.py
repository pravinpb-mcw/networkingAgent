"""
Get Network Clients Tool
Retrieves clients connected to a specific network
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-network-clients-tool")

mcp = FastMCP("get-network-clients")

@mcp.tool()
async def get_network_clients() -> List[TextContent]:
    """
    Retrieve clients connected to your configured network including device details,
    usage patterns, and connection history.
    Uses NETWORK_ID and TIMESPAN from .env file.
    """
    try:

        # Initialize client (will load API key, network_id, and timespan from .env file)
        client = MerakiAPIClient()
        data = await client.get_network_clients()
        
        result = {
            "tool": "get_network_clients",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "timespan": client.timespan,
            "data": data,
            "summary": f"Retrieved {len(data)} clients from network {client.network_id} (last {client.timespan} seconds)"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"get_network_clients completed successfully. Retrieved {len(data)} clients.")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"❌ Error in get_network_clients: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_network_clients: {str(e)}"
        )] 