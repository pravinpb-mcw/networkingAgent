"""
Get Device Loss and Latency History Tool
Retrieves loss and latency history for a specific device
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from .meraki_client import MerakiAPIClient

logger = logging.getLogger("get-device-loss-latency-tool")

mcp = FastMCP("get-device-loss-latency")

@mcp.tool()
async def get_device_loss_and_latency_history() -> List[TextContent]:
    """
    Retrieve loss and latency history for your configured device.
    Returns historical performance data including packet loss and latency metrics.
    Uses SERIAL and IP from .env file.
    """
    try:
        # Initialize client (will load API key, serial, and ip from .env file)
        client = MerakiAPIClient()
        data = await client.get_device_loss_and_latency_history()
        
        result = {
            "tool": "get_device_loss_and_latency_history",
            "timestamp": datetime.now().isoformat(),
            "device_serial": client.serial,
            "device_ip": client.ip,
            "data": data,
            "summary": f"Retrieved loss and latency history for device {client.serial} with IP {client.ip}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        print(f"\n=== get_device_loss_and_latency_history JSON Output ===\n{json_output}\n")
        logger.info(f"get_device_loss_and_latency_history completed successfully. Retrieved data for device {client.serial}.")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"get_device_loss_and_latency_history failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_device_loss_and_latency_history: {str(e)}"
        )] 