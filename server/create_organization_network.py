"""
Create Organization Network Tool
Creates a new network in an organization
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("create-organization-network-tool")

mcp = FastMCP("create-organization-network")

@mcp.tool()
async def create_organization_network(network_data: Union[Dict[str, Any], str], organization_id: str = None, use_mock: bool = False) -> List[TextContent]:
    """
    Create a new network in an organization.
    Uses ORGANIZATION_ID from .env file if not specified.
    
    Args:
        network_data: Network configuration data (dict or natural language string)
        organization_id: Optional organization ID (uses .env if not provided)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with status information
    """
    try:
        # Handle natural language input
        if isinstance(network_data, str):
            from natural_language_converter import convert_natural_language_to_network_data
            network_data = convert_natural_language_to_network_data(network_data)
        
        # Validate network data
        if not isinstance(network_data, dict):
            raise ValueError("network_data must be a dictionary")
        
        # Initialize Meraki client
        client = MerakiAPIClient(use_mock=use_mock)
        
        # Create organization network
        logger.info("Creating organization network...")
        network_result = await client.create_organization_network(
            organization_id=organization_id,
            network_data=network_data
        )
        
        result = {
            "tool": "create_organization_network",
            "timestamp": datetime.now().isoformat(),
            "organization_id": organization_id or client.organization_id,
            "network_created": network_result,
            "status": "success",
            "summary": f"Network created successfully in organization {organization_id or client.organization_id}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"create_organization_network completed successfully for organization {organization_id or client.organization_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"create_organization_network failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing create_organization_network: {str(e)}"
        )]
