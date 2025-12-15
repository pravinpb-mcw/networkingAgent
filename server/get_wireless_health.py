#!/usr/bin/env python3
"""
Get wireless health metrics for Access Points
"""

import json
import logging
from datetime import datetime
from typing import List

from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-wireless-health")


async def get_wireless_health(
    network_id: str = None,
    device_serial: str = None,
    use_mock: bool = True
) -> List[TextContent]:
    """
    Get wireless health metrics including signal quality, client experience, and performance
    
    Args:
        network_id: Network ID (optional, uses env if not provided)
        device_serial: Specific AP serial (optional, gets all if not provided)
        use_mock: Whether to use mock server (ignored, routing handled by client)
        
    Returns:
        List[TextContent] containing wireless health metrics
    """
    try:
        logger.info(f"Getting wireless health for network {network_id or 'default'}")
        
        # Initialize client (will load from .env)
        client = MerakiAPIClient()
        
        # Get wireless health data
        data = await client.get_wireless_health(network_id, device_serial)
        
        if not data:
            logger.warning("No wireless health data available")
            result = {
                "success": False,
                "message": "No wireless health data available"
            }
        else:
            result = {
                "success": True,
                "tool": "get_wireless_health",
                "timestamp": datetime.now().isoformat(),
                "network_id": network_id or client.network_id,
                "device_serial": device_serial,
                "health_data": data
            }
        
        json_output = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=json_output)]
        
    except Exception as e:
        logger.error(f"Error getting wireless health: {e}")
        error_result = {
            "success": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
