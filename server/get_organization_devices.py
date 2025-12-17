#!/usr/bin/env python3
"""
Get all devices in the organization
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-organization-devices")


async def get_organization_devices(
    organization_id: str = None,
    network_id: str = None,
    use_mock: bool = True
) -> List[TextContent]:
    """
    Get all devices in the organization or filtered by network
    
    Args:
        organization_id: Organization ID (optional, uses env if not provided)
        network_id: Filter devices by network ID (optional)
        use_mock: Whether to use mock server (ignored, routing handled by client)
        
    Returns:
        List[TextContent] containing device information
    """
    try:
        logger.info(f"Getting organization devices for org {organization_id or 'default'}")
        
        # Initialize client (will load from .env)
        client = MerakiAPIClient()
        
        # Get devices
        data = await client.get_organization_devices(organization_id)
        
        if not data:
            logger.warning("No devices found")
            result = {
                "success": False,
                "message": "No devices available"
            }
        else:
            # Filter by network if specified
            if network_id:
                data = [d for d in data if d.get("networkId") == network_id]
                logger.info(f"Filtered to {len(data)} devices in network {network_id}")
            
            # Extract just Access Points (wireless devices)
            aps = [d for d in data if d.get("model", "").startswith("MR")]
            
            result = {
                "success": True,
                "tool": "get_organization_devices",
                "timestamp": datetime.now().isoformat(),
                "organization_id": organization_id or client.organization_id,
                "network_id": network_id,
                "total_devices": len(data),
                "access_points": len(aps),
                "devices": data,
                "ap_serials": [ap.get("serial") for ap in aps],
                "ap_names": [ap.get("name") for ap in aps]
            }
        
        json_output = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=json_output)]
        
    except Exception as e:
        logger.error(f"Error getting organization devices: {e}")
        error_result = {
            "success": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
