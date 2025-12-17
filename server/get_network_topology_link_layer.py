#!/usr/bin/env python3
"""
Get network topology link layer information
Returns LLDP and CDP information for all discovered devices and connections
"""

import json
import logging
from datetime import datetime
from typing import List

from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("get-network-topology-link-layer")


async def get_network_topology_link_layer(
    network_id: str = None,
    use_mock: bool = True
) -> List[TextContent]:
    """
    Get network topology link layer with LLDP and CDP information
    
    Returns the physical network topology showing:
    - All devices (APs, switches, appliances, wireless controllers)
    - Device locations and connections
    - LLDP and CDP discovery data
    - Links between devices
    
    Args:
        network_id: Network ID (optional, uses env if not provided)
        use_mock: Whether to use mock server (ignored, routing handled by client)
        
    Returns:
        List[TextContent] containing topology data with nodes and links
    """
    try:
        logger.info(f"Getting network topology link layer for network {network_id or 'default'}")
        
        # Initialize client
        client = MerakiAPIClient()
        
        # Get topology data
        data = await client.get_network_topology_link_layer(network_id)
        
        if not data:
            logger.warning("No topology data available")
            result = {
                "success": False,
                "message": "No topology data available"
            }
        else:
            # Extract AP devices specifically
            ap_devices = []
            all_devices = []
            
            nodes = data.get("nodes", [])
            for node in nodes:
                node_type = node.get("type")
                
                if node_type == "device":
                    device = node.get("device", {})
                    product_type = device.get("productType", "")
                    
                    device_info = {
                        "derived_id": node.get("derivedId"),
                        "mac": node.get("mac"),
                        "serial": device.get("serial"),
                        "name": device.get("name"),
                        "model": device.get("model"),
                        "product_type": product_type,
                        "status": device.get("status"),
                        "last_reported": device.get("lastReportedAt")
                    }
                    
                    all_devices.append(device_info)
                    
                    # Filter for wireless APs
                    if product_type in ["wireless", "wirelessController"]:
                        ap_devices.append(device_info)
                
                elif node_type == "stack":
                    # Handle stack members
                    stack = node.get("stack", {})
                    for member in stack.get("members", []):
                        if member.get("type") == "device":
                            device = member.get("device", {})
                            product_type = device.get("productType", "")
                            
                            device_info = {
                                "derived_id": member.get("derivedId"),
                                "mac": member.get("mac"),
                                "serial": device.get("serial"),
                                "name": device.get("name"),
                                "model": device.get("model"),
                                "product_type": product_type,
                                "status": device.get("status"),
                                "last_reported": device.get("lastReportedAt"),
                                "in_stack": stack.get("name")
                            }
                            
                            all_devices.append(device_info)
                            
                            if product_type in ["wireless", "wirelessController"]:
                                ap_devices.append(device_info)
            
            result = {
                "success": True,
                "tool": "get_network_topology_link_layer",
                "timestamp": datetime.now().isoformat(),
                "network_id": network_id or client.network_id,
                "topology_summary": {
                    "total_nodes": len(nodes),
                    "total_devices": len(all_devices),
                    "wireless_devices": len(ap_devices),
                    "total_links": len(data.get("links", []))
                },
                "wireless_devices": ap_devices,
                "all_devices": all_devices,
                "full_topology": data
            }
        
        json_output = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=json_output)]
        
    except Exception as e:
        logger.error(f"Error getting topology: {e}")
        error_result = {
            "success": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
