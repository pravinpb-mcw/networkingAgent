"""
Update Connectivity Monitoring Destinations Tool
Updates connectivity monitoring destinations for a network
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-connectivity-monitoring-tool")

mcp = FastMCP("update-connectivity-monitoring")

@mcp.tool()
async def update_connectivity_monitoring_destinations(monitoring_data: Union[Dict[str, Any], str], network_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Update connectivity monitoring destinations for a network.
    Uses NETWORK_ID from .env file if not specified.
    
    Args:
        monitoring_data: Connectivity monitoring configuration (dict or natural language string)
        network_id: Optional network ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with status information
    """
    try:
        # Handle natural language input
        if isinstance(monitoring_data, str):
            from natural_language_converter import convert_natural_language_to_connectivity_monitoring
            monitoring_data = convert_natural_language_to_connectivity_monitoring(monitoring_data)
        
        # Validate monitoring data
        if not isinstance(monitoring_data, dict):
            raise ValueError("monitoring_data must be a dictionary")
        
        client = MerakiAPIClient(use_mock=use_mock)
        logger.info("Updating connectivity monitoring destinations...")
        
        result = await client.update_connectivity_monitoring_destinations(
            network_id=network_id,
            monitoring_data=monitoring_data
        )
        
        response = {
            "tool": "update_connectivity_monitoring_destinations",
            "timestamp": datetime.now().isoformat(),
            "network_id": network_id or client.network_id,
            "monitoring_updated": result,
            "status": "success",
            "summary": f"Updated connectivity monitoring destinations for network {network_id or client.network_id}"
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        logger.info(f"update_connectivity_monitoring_destinations completed successfully for network {network_id or client.network_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"update_connectivity_monitoring_destinations failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing update_connectivity_monitoring_destinations: {str(e)}"
        )]
