#!/usr/bin/env python3
"""
Get wireless usage history including retransmissions, channel utilization, and client metrics
"""

import json
import logging
from datetime import datetime
from typing import List

from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-wireless-usage-history")


async def get_wireless_usage_history(
    network_id: str = None,
    device_serial: str = None,
    timespan: int = 7200,
    use_mock: bool = True
) -> List[TextContent]:
    """
    Get wireless usage history with detailed metrics
    
    Args:
        network_id: Network ID (optional, uses env if not provided)
        device_serial: Specific AP serial (optional, gets all if not provided)
        timespan: Time span in seconds (default 2 hours)
        use_mock: Whether to use mock server (ignored, routing handled by client)
        
    Returns:
        List[TextContent] containing wireless usage history with:
        - Channel utilization
        - Airtime utilization
        - Retransmissions per minute
        - Signal quality (SNR, RSSI)
        - Client count
        - Uplink/downlink speeds
    """
    try:
        logger.info(f"Getting wireless usage history for network {network_id or 'default'}")
        
        # Initialize client (will load from .env)
        client = MerakiAPIClient()
        
        # Get wireless usage history
        data = await client.get_wireless_usage_history(network_id, device_serial, timespan)
        
        if not data:
            logger.warning("No wireless usage data available")
            result = {
                "success": False,
                "message": "No wireless usage data available"
            }
        else:
            # Filter by device if specified and data is a list
            if device_serial and isinstance(data, list):
                data = [entry for entry in data if entry.get("deviceSerial") == device_serial]
            
            result = {
                "success": True,
                "tool": "get_wireless_usage_history",
                "timestamp": datetime.now().isoformat(),
                "network_id": network_id or client.network_id,
                "device_serial": device_serial,
                "timespan": timespan,
                "usage_history": data
            }
        
        json_output = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=json_output)]
        
    except Exception as e:
        logger.error(f"Error getting wireless usage history: {e}")
        error_result = {
            "success": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
