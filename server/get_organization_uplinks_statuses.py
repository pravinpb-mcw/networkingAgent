"""
Get Organization Uplinks Statuses Tool
Retrieves device uplink status and failover information for an organization
"""

import json
import logging
from datetime import datetime
from typing import List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-organization-uplinks-statuses-tool")

mcp = FastMCP("get-organization-uplinks-statuses")

@mcp.tool()
async def get_organization_uplinks_statuses() -> List[TextContent]:
    """
    Retrieve device uplink status and failover information for your configured organization.
    Uses ORGANIZATION_ID from .env file.
    """
    try:
        client = MerakiAPIClient()
        data = await client.get_organization_uplinks_statuses()

        result = {
            "tool": "get_organization_uplinks_statuses",
            "timestamp": datetime.now().isoformat(),
            "organization_id": client.organization_id,
            "data": data,
            "summary": f"Retrieved uplink statuses for organization {client.organization_id}"
        }

        json_output = json.dumps(result, indent=2, default=str)
        logger.info(
            "get_organization_uplinks_statuses completed successfully for organization %s",
            client.organization_id,
        )

        return [TextContent(type="text", text=json_output)]

    except Exception as e:
        logger.error("get_organization_uplinks_statuses failed: %s", str(e))
        return [TextContent(type="text", text=f"Error executing get_organization_uplinks_statuses: {str(e)}")]

