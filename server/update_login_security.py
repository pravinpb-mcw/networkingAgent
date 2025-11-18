"""
Update Login Security Tool
Updates organization login security settings
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-login-security-tool")

mcp = FastMCP("update-login-security")

@mcp.tool()
async def update_organization_login_security(security_data: Union[Dict[str, Any], str], organization_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Update organization login security settings.
    Uses ORGANIZATION_ID from .env file if not specified.
    
    Args:
        security_data: Login security configuration (dict or natural language string)
        organization_id: Optional organization ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with status information
    """
    try:
        # Handle natural language input
        if isinstance(security_data, str):
            from natural_language_converter import convert_natural_language_to_login_security
            security_data = convert_natural_language_to_login_security(security_data)
        
        # Validate security data
        if not isinstance(security_data, dict):
            raise ValueError("security_data must be a dictionary")
        
        client = MerakiAPIClient(use_mock=use_mock)
        logger.info("Updating organization login security settings...")
        
        result = await client.update_organization_login_security(
            organization_id=organization_id,
            security_data=security_data
        )
        
        response = {
            "tool": "update_organization_login_security",
            "timestamp": datetime.now().isoformat(),
            "organization_id": organization_id or client.organization_id,
            "security_updated": result,
            "status": "success",
            "summary": f"Updated login security settings for organization {organization_id or client.organization_id}"
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        logger.info(f"update_organization_login_security completed successfully for organization {organization_id or client.organization_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"update_organization_login_security failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing update_organization_login_security: {str(e)}"
        )]
