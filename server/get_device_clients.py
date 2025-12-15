#!/usr/bin/env python3
"""
Get clients connected to a specific device (AP)
"""

import json
import logging
from datetime import datetime
from typing import List

from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-device-clients")


async def get_device_clients(
    device_serial: str,
    network_id: str = None,
    use_mock: bool = True
) -> List[TextContent]:
    """
    Get clients connected to a specific device
    
    Args:
        device_serial: Device serial number
        network_id: Network ID (optional, uses env if not provided)
        use_mock: Whether to use mock server (ignored, routing handled by client)
        
    Returns:
        List[TextContent] containing list of clients with their details
    """
    try:
        logger.info(f"Getting clients for device {device_serial}")
        
        # Initialize client (will load from .env)
        client = MerakiAPIClient()
        
        # Get device clients
        data = await client.get_device_clients(device_serial)
        
        if not data:
            logger.warning(f"No clients found for device {device_serial}")
            result = {
                "success": False,
                "message": "No clients connected"
            }
        else:
            result = {
                "success": True,
                "tool": "get_device_clients",
                "timestamp": datetime.now().isoformat(),
                "device_serial": device_serial,
                "network_id": network_id or client.network_id,
                "client_count": len(data) if isinstance(data, list) else 0,
                "clients": data
            }
        
        json_output = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=json_output)]
        
    except Exception as e:
        logger.error(f"Error getting device clients: {e}")
        error_result = {
            "success": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
