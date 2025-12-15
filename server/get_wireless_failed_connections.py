#!/usr/bin/env python3
"""
Get wireless failed connection attempts
"""

import json
import logging
from datetime import datetime
from typing import List

from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-wireless-failed-connections")


async def get_wireless_failed_connections(
    network_id: str = None,
    device_serial: str = None,
    timespan: int = 7200,
    use_mock: bool = True
) -> List[TextContent]:
    """
    Get wireless failed connection attempts (auth failures, DHCP timeouts, etc.)
    
    Args:
        network_id: Network ID (optional, uses env if not provided)
        device_serial: Specific AP serial (optional)
        timespan: Time span in seconds (default 2 hours)
        use_mock: Whether to use mock server (ignored, routing handled by client)
        
    Returns:
        List[TextContent] containing failed connection events
    """
    try:
        logger.info(f"Getting wireless failed connections for network {network_id or 'default'}")
        
        # Initialize client (will load from .env)
        client = MerakiAPIClient()
        
        # Get failed connections
        data = await client.get_wireless_failed_connections(network_id, device_serial, timespan)
        
        if not data:
            logger.warning("No failed connection data available")
            result = {
                "success": False,
                "message": "No failed connection data available"
            }
        else:
            # Filter by device if specified and data is a list
            if device_serial and isinstance(data, list):
                data = [entry for entry in data if entry.get("deviceSerial") == device_serial]
            
            result = {
                "success": True,
                "tool": "get_wireless_failed_connections",
                "timestamp": datetime.now().isoformat(),
                "network_id": network_id or client.network_id,
                "device_serial": device_serial,
                "timespan": timespan,
                "failed_connections": data
            }
        
        json_output = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=json_output)]
        
    except Exception as e:
        logger.error(f"Error getting wireless failed connections: {e}")
        error_result = {
            "success": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
