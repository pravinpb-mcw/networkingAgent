"""
Get Connectivity Monitoring Destinations Tool
Retrieves connectivity monitoring destinations for a network
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-connectivity-monitoring-tool")

mcp = FastMCP("get-connectivity-monitoring")

@mcp.tool()
async def get_connectivity_monitoring_destinations(network_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Get connectivity monitoring destinations for a network.
    Uses NETWORK_ID from .env file if not specified.
    
    Args:
        network_id: Optional network ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with connectivity monitoring information
    """
    try:
        logger.info("I am working on get_connectivity_monitoring_destinations API tool to get data")
        
        client = MerakiAPIClient(use_mock=use_mock)
        logger.info("Retrieving connectivity monitoring destinations...")
        
        result = await client.get_connectivity_monitoring_destinations(network_id=network_id)
        
        response = {
            "tool": "get_connectivity_monitoring_destinations",
            "timestamp": datetime.now().isoformat(),
            "network_id": network_id or client.network_id,
            "connectivity_monitoring": result,
            "status": "success",
            "summary": f"Retrieved connectivity monitoring destinations for network {network_id or client.network_id}"
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        logger.info(f"get_connectivity_monitoring_destinations completed successfully for network {network_id or client.network_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"❌ Error in get_connectivity_monitoring_destinations: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_connectivity_monitoring_destinations: {str(e)}"
        )]
