"""
Get Login Security Tool
Retrieves organization login security settings
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-login-security-tool")

mcp = FastMCP("get-login-security")

@mcp.tool()
async def get_organization_login_security(organization_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Get organization login security settings.
    Uses ORGANIZATION_ID from .env file if not specified.
    
    Args:
        organization_id: Optional organization ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with login security information
    """
    try:
        logger.info("I am working on get_organization_login_security API tool to get data")
        
        client = MerakiAPIClient(use_mock=use_mock)
        logger.info("Retrieving organization login security settings...")
        
        result = await client.get_organization_login_security(organization_id=organization_id)
        
        response = {
            "tool": "get_organization_login_security",
            "timestamp": datetime.now().isoformat(),
            "organization_id": organization_id or client.organization_id,
            "login_security": result,
            "status": "success",
            "summary": f"Retrieved login security settings for organization {organization_id or client.organization_id}"
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        logger.info(f"get_organization_login_security completed successfully for organization {organization_id or client.organization_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"❌ Error in get_organization_login_security: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_organization_login_security: {str(e)}"
        )]
