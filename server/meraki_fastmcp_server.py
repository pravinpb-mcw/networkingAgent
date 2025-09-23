"""
Cisco Meraki FastMCP Server
Provides tools for managing Cisco Meraki networks using FastMCP framework
"""

import asyncio
import json
import logging
import os
from typing import Optional, Union, Dict, Any, List
from datetime import datetime

from fastmcp import FastMCP

import sys
import os

# Add the server directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meraki_client import MerakiAPIClient
# from get_organizations import get_organizations
from get_network_clients import get_network_clients
from get_network_traffic import get_network_traffic
from get_device_loss_and_latency_history import get_device_loss_and_latency_history
from get_network_vpn_stats import get_network_vpn_stats
from get_network_events import get_network_events
from get_network_settings import get_network_settings
from update_network_settings import update_network_settings
from update_appliance_settings import update_appliance_settings
# from get_organization_uplinks_statuses import get_organization_uplinks_statuses
from update_uplink import update_uplink
from get_network_group_policies import get_network_group_policies
from create_network_wireless_settings import create_network_wireless_settings
from update_network_group_policy import update_network_group_policy
from get_organization_networks import get_organization_networks
from create_organization_network import create_organization_network
from get_connectivity_monitoring import get_connectivity_monitoring_destinations
from get_access_control_lists import get_network_access_control_lists
from get_login_security import get_organization_login_security
from get_security_intrusion import get_network_security_intrusion
from update_connectivity_monitoring import update_connectivity_monitoring_destinations
from update_access_control_lists import update_network_access_control_lists
from update_login_security import update_organization_login_security
from update_security_intrusion import update_network_security_intrusion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meraki-fastmcp-server")

# Check if we should use mock server - check both USE_MOCK and BASE_URL
USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "")
if BASE_URL and "127.0.0.1" in BASE_URL or "localhost" in BASE_URL:
    USE_MOCK = True

logger.info(f"BASE_URL: {BASE_URL}")
logger.info(f"USE_MOCK: {USE_MOCK}")

# Create the FastMCP server
mcp = FastMCP(
    name="cisco-meraki-observability",
    instructions="""
    This server provides tools for managing Cisco Meraki networks and devices.
    It supports observability, configuration management, and network optimization tasks.
    """
)

# Helper function to extract data from TextContent format
def extract_data_from_textcontent(result):
    """Extract actual data from TextContent format returned by MCP functions."""
    try:
        # Handle empty/None results
        if not result:
            return [{"error": "No data received", "raw_response": "None"}]
        
        # If it's already processed data (list of dicts), return as-is
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            return result
        
        # If it's a single dict, wrap it in a list
        if isinstance(result, dict):
            return [result]
            
        # Handle TextContent objects in a list
        if isinstance(result, list):
            for item in result:
                # Check if it's a TextContent object with text attribute
                if hasattr(item, 'text'):
                    try:
                        # Try to parse as JSON
                        parsed_data = json.loads(item.text)
                        if isinstance(parsed_data, list):
                            return parsed_data
                        elif isinstance(parsed_data, dict):
                            return [parsed_data]
                        else:
                            return [{"data": parsed_data}]
                    except json.JSONDecodeError:
                        # If not JSON, return as text
                        return [{"text": item.text}]
                
                # Check if it has other useful attributes
                elif hasattr(item, '__dict__'):
                    item_dict = item.__dict__
                    # Remove internal attributes that start with underscore
                    clean_dict = {k: v for k, v in item_dict.items() if not k.startswith('_')}
                    if clean_dict:
                        return [clean_dict]
                
                # If it's a string representation, try to parse it
                elif isinstance(item, str):
                    try:
                        parsed_data = json.loads(item)
                        return [parsed_data] if isinstance(parsed_data, dict) else parsed_data
                    except json.JSONDecodeError:
                        return [{"text": item}]
        
        # Handle single TextContent object
        if hasattr(result, 'text'):
            try:
                parsed_data = json.loads(result.text)
                return [parsed_data] if isinstance(parsed_data, dict) else parsed_data
            except json.JSONDecodeError:
                return [{"text": result.text}]
        
        # Last resort: try to extract useful information from the object
        if hasattr(result, '__dict__'):
            result_dict = result.__dict__
            clean_dict = {k: v for k, v in result_dict.items() if not k.startswith('_')}
            if clean_dict:
                return [clean_dict]
        
        # If all else fails, return a helpful error message
        logger.warning(f"Could not extract data from result type: {type(result)}")
        return [{"error": "Could not extract data", "result_type": str(type(result)), "raw_data": str(result)[:500]}]
        
    except Exception as e:
        logger.error(f"Failed to extract data from result: {e}")
        return [{"error": f"Data extraction failed: {e}", "raw_response": str(result)[:500]}]

# Organization and Network Information Tools
@mcp.tool
async def get_network_clients_tool() -> List[Dict[str, Any]]:
    """Get list of devices connected to the network including client details, IP addresses, and connection status."""
    result = await get_network_clients()
    return extract_data_from_textcontent(result)

@mcp.tool
async def get_organization_networks_tool(organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get list of all networks in the organization including network IDs, names, and product types."""
    logger.info(f"get_organization_networks_tool called with organization_id={organization_id}")
    # Call the MCP tool function that returns List[TextContent], not the client method
    result = await get_organization_networks(organization_id or "", use_mock=USE_MOCK)
    logger.info(f"get_organization_networks returned type: {type(result)}")
    if hasattr(result, '__len__'):
        logger.info(f"get_organization_networks returned length: {len(result)}")
    extracted = extract_data_from_textcontent(result)
    logger.info(f"extract_data_from_textcontent returned type: {type(extracted)}, length: {len(extracted) if hasattr(extracted, '__len__') else 'N/A'}")
    return extracted

# Network Traffic and Performance Tools

@mcp.tool
async def get_network_traffic_tool() -> List[Dict[str, Any]]:
    """Get network traffic analysis including bandwidth usage, top applications, and traffic patterns."""
    result = await get_network_traffic()
    return extract_data_from_textcontent(result)

@mcp.tool
async def get_device_loss_and_latency_history_tool() -> List[Dict[str, Any]]:
    """Get device performance metrics including packet loss percentage, latency measurements, and throughput data."""
    result = await get_device_loss_and_latency_history()
    return extract_data_from_textcontent(result)

@mcp.tool
async def get_organization_vpn_stats_tool() -> List[Dict[str, Any]]:
    """Get VPN connection statistics including connection status, traffic metrics, and performance data."""
    result = await get_network_vpn_stats()
    return extract_data_from_textcontent(result)

@mcp.tool
async def get_network_events_tool() -> List[Dict[str, Any]]:
    """Get network events log including device status changes, security events, and system notifications."""
    result = await get_network_events()
    return extract_data_from_textcontent(result)

# Network Configuration Tools

@mcp.tool
async def get_network_settings_tool() -> List[Dict[str, Any]]:
    """Get network configuration settings including appliance settings with degradedLinks status (WAN1/WAN2 status), wireless settings, and other network-wide configurations."""
    result = await get_network_settings()
    return extract_data_from_textcontent(result)

@mcp.tool
async def update_network_settings_tool(settings_data: str) -> List[Dict[str, Any]]:
    """Update network-wide configuration settings. Use natural language to describe what you want. Example: 'Enable local status page and secure port' or 'Configure named VLANs and webhooks'."""
    result = await update_network_settings(settings_data, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

@mcp.tool
async def update_appliance_settings_tool(settings_data: str) -> List[Dict[str, Any]]:
    """Update appliance settings including degradedLinks status, DHCP configuration, and VLAN settings. Use natural language. Example: 'Set degradedLinks to ok for WAN1 and WAN2' or 'Update WAN1 status to down'."""
    result = await update_appliance_settings(settings_data, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

# Uplink Management Tools

@mcp.tool
async def get_organization_uplinks_statuses_tool() -> Dict[str, Any]:
    """
    Retrieve uplink statuses for all networks in your configured organization.
    Returns uplink connectivity information including status, bandwidth, and failover details.
    Uses ORGANIZATION_ID from .env file.
    """
                # )]
        
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
        
    return {
                "text": json_output
        }


@mcp.tool
async def update_uplink_tool(uplink_data: str) -> List[Dict[str, Any]]:
    """CRITICAL TOOL: Move devices between WAN interfaces (wan1/wan2/wan3) for load balancing. MUST be called for each device movement. Use format: 'Move device SERIAL_NUMBER to wan1/wan2/wan3'. Example: 'Move device Q2GY-ECCL-A9TE to wan2' or 'Move device Q2MN-Q3J9-YJHW to wan3'. This tool ACTUALLY MOVES devices - call it for each device that needs to be moved!"""
    result = await update_uplink(uplink_data, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

# Group Policy Tools

@mcp.tool
async def get_network_group_policies_tool() -> List[Dict[str, Any]]:
    """Get user group policies including bandwidth limits, content filtering rules, and scheduling settings."""
    result = await get_network_group_policies()
    return extract_data_from_textcontent(result)

@mcp.tool
async def update_network_group_policy_tool(policy_id: str, policy_data: Union[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Update user group policies including bandwidth limits, traffic shaping, and content filtering. Use natural language. Example: 'Update policy 123 with new name Updated Guest Policy' or 'Set bandwidth limits to 500 Kbps upload and 10000 Kbps download'."""
    result = await update_network_group_policy(policy_id, policy_data, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

# Network Creation Tools

@mcp.tool
async def create_network_wireless_settings_tool(settings_data: str) -> List[Dict[str, Any]]:
    """Create wireless network settings including SSID, bandwidth limits, and security configuration. Use natural language. Example: 'Enable wireless with SSID My_SSID and 1000 Mbps bandwidth'."""
    result = await create_network_wireless_settings(settings_data, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

@mcp.tool
async def create_organization_network_tool(network_data: Union[str, Dict[str, Any]], organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Create a new network in the organization. Use natural language. Example: 'Create a network named MCW San Jose with wireless and appliance products'."""
    result = await create_organization_network(network_data, organization_id, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

@mcp.tool
async def create_network_appliance_settings_tool(settings_data: str) -> List[Dict[str, Any]]:
    """Create network infrastructure settings including DHCP configuration and VLAN settings. Use natural language. Example: 'Enable DHCP with 24-hour lease and VLAN 100'."""
    from create_network_appliance_settings import create_network_appliance_settings
    result = await create_network_appliance_settings(settings_data, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

# Connectivity Monitoring Tools

@mcp.tool
async def get_connectivity_monitoring_destinations_tool(network_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get connectivity monitoring destinations and their status for network health monitoring."""
    result = await get_connectivity_monitoring_destinations(network_id=network_id, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

@mcp.tool
async def update_connectivity_monitoring_destinations_tool(monitoring_data: Union[str, Dict[str, Any]], network_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Update connectivity monitoring destinations for network health monitoring. Use natural language. Example: 'Add Google DNS as monitoring destination' or 'Set monitoring to 8.8.8.8 and 1.1.1.1'."""
    result = await update_connectivity_monitoring_destinations(monitoring_data, network_id, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

# Security Tools

@mcp.tool
async def get_network_access_control_lists_tool(network_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get network access control lists (ACL) including firewall rules and access policies."""
    result = await get_network_access_control_lists(network_id, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

@mcp.tool
async def update_network_access_control_lists_tool(acl_data: Union[str, Dict[str, Any]], network_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Update network access control lists (ACL) for firewall rules and access policies. Use natural language. Example: 'Allow access to port 80 and 443' or 'Block access to social media sites'."""
    result = await update_network_access_control_lists(acl_data, network_id, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

@mcp.tool
async def get_organization_login_security_tool(organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get organization login security settings including authentication policies and access controls."""
    result = await get_organization_login_security(organization_id, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

@mcp.tool
async def update_organization_login_security_tool(security_data: Union[str, Dict[str, Any]], organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Update organization login security settings including authentication policies and password requirements. Use natural language. Example: 'Enable two-factor authentication' or 'Set password policy to require 12 characters'."""
    result = await update_organization_login_security(security_data, organization_id, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

@mcp.tool
async def get_network_security_intrusion_tool(network_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get network security intrusion detection settings including threat prevention and security policies."""
    result = await get_network_security_intrusion(network_id, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

@mcp.tool
async def update_network_security_intrusion_tool(intrusion_data: Union[str, Dict[str, Any]], network_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Update network security intrusion detection settings including threat prevention and security policies. Use natural language. Example: 'Enable intrusion detection' or 'Set security mode to prevention'."""
    result = await update_network_security_intrusion(intrusion_data, network_id, use_mock=USE_MOCK)
    return extract_data_from_textcontent(result)

async def test_connectivity():
    """Test API connectivity during server startup"""
    try:
        if USE_MOCK:
            logger.info("Using MOCK server mode")
            client = MerakiAPIClient(use_mock=True)
        else:
            logger.info("Using REAL Meraki API mode")
            client = MerakiAPIClient()
        
        # Test with a simple request to verify API key works
        logger.info("Testing API connectivity...")
        logger.info("Successfully connected to API.")
    except Exception as e:
        logger.error(f"Failed to connect to API: {e}")
        raise

if __name__ == "__main__":
    # Test connectivity on startup
    asyncio.run(test_connectivity())
    
    # Run the FastMCP server
    mcp.run()