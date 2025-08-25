"""
Get Organization Networks Tool
Retrieves all networks in an organization
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-organization-networks-tool")

mcp = FastMCP("get-organization-networks")

@mcp.tool()
async def get_organization_networks(organization_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Get all networks in an organization.
    Uses ORGANIZATION_ID from .env file if not specified.
    
    Args:
        organization_id: Optional organization ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with network information
    """
    try:
        # Initialize Meraki client
        client = MerakiAPIClient(use_mock=use_mock)
        
        # Get organization networks
        logger.info("Retrieving organization networks...")
        networks_result = await client.get_organization_networks(organization_id=organization_id)
        
        result = {
            "tool": "get_organization_networks",
            "timestamp": datetime.now().isoformat(),
            "organization_id": organization_id or client.organization_id,
            "networks_count": len(networks_result) if isinstance(networks_result, list) else 0,
            "networks": networks_result,
            "status": "success",
            "summary": f"Retrieved {len(networks_result) if isinstance(networks_result, list) else 0} networks from organization {organization_id or client.organization_id}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"get_organization_networks completed successfully for organization {organization_id or client.organization_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"get_organization_networks failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_organization_networks: {str(e)}"
        )]
