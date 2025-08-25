"""
Get Security Intrusion Tool
Retrieves network security intrusion settings
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-security-intrusion-tool")

mcp = FastMCP("get-security-intrusion")

@mcp.tool()
async def get_network_security_intrusion(network_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Get network security intrusion settings.
    Uses NETWORK_ID from .env file if not specified.
    
    Args:
        network_id: Optional network ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with security intrusion information
    """
    try:
        client = MerakiAPIClient(use_mock=use_mock)
        logger.info("Retrieving network security intrusion settings...")
        
        result = await client.get_network_security_intrusion(network_id=network_id)
        
        response = {
            "tool": "get_network_security_intrusion",
            "timestamp": datetime.now().isoformat(),
            "network_id": network_id or client.network_id,
            "security_intrusion": result,
            "status": "success",
            "summary": f"Retrieved security intrusion settings for network {network_id or client.network_id}"
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        logger.info(f"get_network_security_intrusion completed successfully for network {network_id or client.network_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"get_network_security_intrusion failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_network_security_intrusion: {str(e)}"
        )]
