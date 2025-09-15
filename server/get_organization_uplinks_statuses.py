"""
Get Organization Uplinks Statuses Tool
Retrieves uplink statuses for all networks in an organization
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-organization-uplinks-statuses-tool")

mcp = FastMCP("get-organization-uplinks-statuses")

@mcp.tool()
async def get_organization_uplinks_statuses() -> List[TextContent]:
    """
    Retrieve uplink statuses for all networks in your configured organization.
    Returns uplink connectivity information including status, bandwidth, and failover details.
    Uses ORGANIZATION_ID from .env file.
    """
    try:
        logger.info("I am working on get_organization_uplinks_statuses API tool to get data")
        
        # Check if we should use mock data
        use_mock = os.getenv("USE_MOCK", "False").lower() == "true"
        
        if use_mock:
            # Load mock data
            mock_file = "mock_data/comprehensive_api_data.json"
            if os.path.exists(mock_file):
                with open(mock_file, 'r') as f:
                    mock_data = json.load(f)
                
                if "organization_uplinks_statuses" in mock_data:
                    # Get all uplink statuses for all organizations
                    all_uplinks = []
                    for org_id, uplinks in mock_data["organization_uplinks_statuses"].items():
                        all_uplinks.extend(uplinks)
                    
                    result = {
                        "tool": "get_organization_uplinks_statuses",
                        "timestamp": datetime.now().isoformat(),
                        "organization_id": "999781",
                        "data": all_uplinks,
                        "summary": f"Retrieved uplink statuses for {len(all_uplinks)} networks in organization 999781"
                    }
                    
                    json_output = json.dumps(result, indent=2, default=str)
                    logger.info(f"get_organization_uplinks_statuses completed successfully. Retrieved uplink statuses for {len(all_uplinks)} networks.")
                    
                    return [TextContent(
                        type="text",
                        text=json_output
                    )]
        
        # Initialize client (will load API key and organization_id from .env file)
        client = MerakiAPIClient()
        data = await client.get_organization_uplinks_statuses()
        
        result = {
            "tool": "get_organization_uplinks_statuses",
            "timestamp": datetime.now().isoformat(),
            "organization_id": client.organization_id,
            "data": data,
            "summary": f"Retrieved uplink statuses for {len(data)} networks in organization {client.organization_id}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"get_organization_uplinks_statuses completed successfully. Retrieved uplink statuses for {len(data)} networks.")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"❌ Error in get_organization_uplinks_statuses: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing get_organization_uplinks_statuses: {str(e)}"
        )]

