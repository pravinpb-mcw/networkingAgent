"""
Get Network Traffic Tool
Analyzes network traffic patterns and bandwidth usage
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from .meraki_client import MerakiAPIClient

logger = logging.getLogger("get-network-traffic-tool")

mcp = FastMCP("get-network-traffic")

@mcp.tool()
async def get_network_traffic() -> List[TextContent]:
    """
    Analyze network traffic patterns, bandwidth usage, and application breakdown
    for network optimization insights.
    Uses NETWORK_ID and TIMESPAN from .env file.
    """
    try:
        # Initialize client (will load API key, network_id, and timespan from .env file)
        client = MerakiAPIClient()
        data = await client.get_network_traffic()
        
        result = {
            "tool": "get_network_traffic",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "timespan": client.timespan,
            "data": data,
            "summary": f"Retrieved traffic analysis for network {client.network_id} (last {client.timespan} seconds)"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        print(f"\n=== get_network_traffic JSON Output ===\n{json_output}\n")
        logger.info(f"get_network_traffic completed successfully. Retrieved traffic analysis for network {client.network_id}.")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"get_network_traffic failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_network_traffic: {str(e)}"
        )] 