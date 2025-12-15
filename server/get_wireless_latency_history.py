#!/usr/bin/env python3
"""
Get wireless latency history for predictive analysis
"""

import json
import logging
from datetime import datetime
from typing import List

from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-wireless-latency-history")


async def get_wireless_latency_history(
    network_id: str = None,
    device_serial: str = None,
    timespan: int = 7200,
    use_mock: bool = True
) -> List[TextContent]:
    """
    Get wireless latency history with jitter and packet loss
    
    Args:
        network_id: Network ID (optional, uses env if not provided)
        device_serial: Specific AP serial or device MAC
        timespan: Time span in seconds (default 2 hours)
        use_mock: Whether to use mock server (ignored, routing handled by client)
        
    Returns:
        List[TextContent] containing time-series latency, jitter, and packet loss data
    """
    try:
        logger.info(f"Getting wireless latency history for network {network_id or 'default'}")
        
        # Initialize client (will load from .env)
        client = MerakiAPIClient()
        
        # Get wireless latency history
        data = await client.get_wireless_latency_history(network_id, device_serial, timespan)
        
        if not data:
            logger.warning("No wireless latency data available")
            result = {
                "success": False,
                "message": "No wireless latency data available"
            }
        else:
            # Filter by device if specified and data is a list
            if device_serial and isinstance(data, list):
                data = [entry for entry in data if entry.get("deviceMac") == device_serial or entry.get("deviceSerial") == device_serial]
            
            result = {
                "success": True,
                "tool": "get_wireless_latency_history",
                "timestamp": datetime.now().isoformat(),
                "network_id": network_id or client.network_id,
                "device_serial": device_serial,
                "timespan": timespan,
                "latency_history": data
            }
        
        json_output = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=json_output)]
        
    except Exception as e:
        logger.error(f"Error getting wireless latency history: {e}")
        error_result = {
            "success": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
