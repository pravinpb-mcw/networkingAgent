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
async def get_organization_networks(organization_id: str = "", use_mock: bool = False) -> List[TextContent]:
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
        logger.info("I am working on get_organization_networks API tool to get data")
        
        # Initialize Meraki client
        client = MerakiAPIClient(use_mock=use_mock)
        
        # Get organization networks
        logger.info("Retrieving organization networks...")
        org_id = organization_id if organization_id else None
        networks_result = await client.get_organization_networks(organization_id=org_id)

        # Defensive handling if API returns non-list
        full_list = networks_result if isinstance(networks_result, list) else []
        total_count = len(full_list)

        # Truncate and project fields to keep context small
        MAX_ITEMS = 50
        projected = []
        for item in full_list[:MAX_ITEMS]:
            if isinstance(item, dict):
                projected.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "productTypes": item.get("productTypes"),
                    "timeZone": item.get("timeZone"),
                    "tags": item.get("tags"),
                })
            else:
                projected.append(item)

        result = {
            "tool": "get_organization_networks",
            "timestamp": datetime.now().isoformat(),
            "organization_id": org_id or client.organization_id,
            "networks_total_count": total_count,
            "networks_returned_count": len(projected),
            "returned_is_truncated": total_count > len(projected),
            "networks": projected,
            "status": "success",
            "summary": f"Retrieved {len(projected)} of {total_count} networks (truncated for brevity)"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"get_organization_networks completed successfully for organization {org_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        # Avoid unicode symbols to prevent Windows console encoding issues
        logger.error(f"Error in get_organization_networks: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_organization_networks: {str(e)}"
        )]
