"""
Update Security Intrusion Tool
Updates network security intrusion settings
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-security-intrusion-tool")

mcp = FastMCP("update-security-intrusion")

@mcp.tool()
async def update_network_security_intrusion(intrusion_data: Union[Dict[str, Any], str], network_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Update network security intrusion settings.
    Uses NETWORK_ID from .env file if not specified.
    
    Args:
        intrusion_data: Security intrusion configuration (dict or natural language string)
        network_id: Optional network ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with status information
    """
    try:
        # Handle natural language input
        if isinstance(intrusion_data, str):
            from natural_language_converter import convert_natural_language_to_security_intrusion
            intrusion_data = convert_natural_language_to_security_intrusion(intrusion_data)
        
        # Validate intrusion data
        if not isinstance(intrusion_data, dict):
            raise ValueError("intrusion_data must be a dictionary")
        
        client = MerakiAPIClient(use_mock=use_mock)
        logger.info("Updating network security intrusion settings...")
        
        result = await client.update_network_security_intrusion(
            network_id=network_id,
            intrusion_data=intrusion_data
        )
        
        response = {
            "tool": "update_network_security_intrusion",
            "timestamp": datetime.now().isoformat(),
            "network_id": network_id or client.network_id,
            "intrusion_updated": result,
            "status": "success",
            "summary": f"Updated security intrusion settings for network {network_id or client.network_id}"
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        logger.info(f"update_network_security_intrusion completed successfully for network {network_id or client.network_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"update_network_security_intrusion failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing update_network_security_intrusion: {str(e)}"
        )]
