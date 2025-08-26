"""
Get Network VPN Stats Tool
Retrieves VPN statistics for a specific network
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-network-vpn-stats-tool")

mcp = FastMCP("get-network-vpn-stats")

@mcp.tool()
async def get_network_vpn_stats() -> List[TextContent]:
    """
    Retrieve VPN statistics for your configured network.
    Returns VPN performance data including connection status, bandwidth usage, and latency metrics.
    Uses NETWORK_ID and TIMESPAN from .env file.
    """
    try:
        logger.info("I am working on get_network_vpn_stats API tool to get data")
        
        # Initialize client (will load API key, network_id, and timespan from .env file)
        client = MerakiAPIClient()
        data = await client.get_network_vpn_stats()
        
        result = {
            "tool": "get_network_vpn_stats",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "timespan": client.timespan,
            "data": data,
            "summary": f"Retrieved VPN statistics for network {client.network_id} (last {client.timespan} seconds)"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"get_network_vpn_stats completed successfully. Retrieved VPN statistics for network {client.network_id}.")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"❌ Error in get_network_vpn_stats: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_network_vpn_stats: {str(e)}"
        )] 