"""
Get Organization VPN Stats Tool
Retrieves VPN statistics for an organization
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from .meraki_client import MerakiAPIClient

logger = logging.getLogger("get-organization-vpn-stats-tool")

mcp = FastMCP("get-organization-vpn-stats")

@mcp.tool()
async def get_organization_vpn_stats() -> List[TextContent]:
    """
    Retrieve VPN statistics for your configured organization.
    Returns VPN performance data including connection status and traffic metrics.
    Uses ORGANIZATION_ID and TIMESPAN from .env file.
    """
    try:
        # Initialize client (will load API key, organization_id, and timespan from .env file)
        client = MerakiAPIClient()
        data = await client.get_organization_vpn_stats()
        
        result = {
            "tool": "get_organization_vpn_stats",
            "timestamp": datetime.now().isoformat(),
            "organization_id": client.organization_id,
            "timespan": client.timespan,
            "data": data,
            "summary": f"Retrieved VPN statistics for organization {client.organization_id} (last {client.timespan} seconds)"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        print(f"\n=== get_organization_vpn_stats JSON Output ===\n{json_output}\n")
        logger.info(f"get_organization_vpn_stats completed successfully. Retrieved VPN stats for organization {client.organization_id}.")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"get_organization_vpn_stats failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_organization_vpn_stats: {str(e)}"
        )] 