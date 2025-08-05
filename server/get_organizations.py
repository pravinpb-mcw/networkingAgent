"""
Get Organizations Tool
Retrieves all Meraki organizations accessible by the API key
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-organizations-tool")

mcp = FastMCP("get-organizations")

@mcp.tool()
async def get_organizations() -> List[TextContent]:
    """
    Retrieve all Meraki organizations accessible by the API key.
    Returns organization details including ID, name, and URL.
    """
    try:
        # Initialize client (will load API key from .env file)
        client = MerakiAPIClient()
        data = await client.get_organizations()
        
        result = {
            "tool": "get_organizations",
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "summary": f"Retrieved {len(data)} organizations"
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
        
    except Exception as e:
        logger.error(f"get_organizations failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_organizations: {str(e)}"
        )] 