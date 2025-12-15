"""
MCP Server Tool: Get AP Topology
Returns nearby APs with distance, signal strength, and channel overlap information
"""

import json
from typing import List
from mcp.types import TextContent
from server.meraki_client import MerakiAPIClient


async def get_ap_topology(network_id: str, ap_serial: str) -> List[TextContent]:
    """
    Get AP topology information including nearby APs
    
    Args:
        network_id: Network ID to query
        ap_serial: Serial number of the source AP
        
    Returns:
        List[TextContent]: AP topology data with nearby APs ranked by proximity
    """
    client = MerakiAPIClient()
    
    try:
        result = await client.get_ap_topology(network_id, ap_serial)
        
        # Format the response
        output = {
            "network_id": network_id,
            "source_ap": ap_serial,
            "topology": result
        }
        
        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2)
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Failed to get AP topology: {str(e)}",
                    "network_id": network_id,
                    "ap_serial": ap_serial
                }, indent=2)
            )
        ]
