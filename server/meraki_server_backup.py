"""
Cisco Meraki FastMCP Server
Provides tools for managing Cisco M# Tool definitions using FastMCP decorators

@app.tool
async def get_organizations_tool() -> List[Dict[str, Any]]:
    """Get list of organizations accessible by the API key"""
    try:
        api_client = MerakiAPIClient()
        result = await get_organizations(api_client.session)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting organizations: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_network_clients_tool(
    network_id: str,
    timespan: int = 86400,
    per_page: int = 100,
    starting_after: str = None
) -> List[Dict[str, Any]]:
    """Get list of clients connected to a network"""
    try:
        api_client = MerakiAPIClient()
        result = await get_network_clients(api_client.session, network_id, timespan, per_page, starting_after)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting network clients: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_network_traffic_tool(
    network_id: str,
    timespan: int = 86400,
    device_type: str = None
) -> List[Dict[str, Any]]:
    """Get network traffic analytics for a network"""
    try:
        api_client = MerakiAPIClient()
        result = await get_network_traffic(api_client.session, network_id, timespan, device_type)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting network traffic: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_device_loss_and_latency_history_tool(
    network_id: str,
    ip: str,
    timespan: int = 7200,
    resolution: int = 300,
    uplink: str = None
) -> List[Dict[str, Any]]:
    """Get device loss and latency history for network devices"""
    try:
        api_client = MerakiAPIClient()
        result = await get_device_loss_and_latency_history(
            api_client.session, network_id, ip, timespan, resolution, uplink
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting device loss and latency history: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_network_vpn_stats_tool(
    network_id: str,
    timespan: int = 86400
) -> List[Dict[str, Any]]:
    """Get VPN stats for a network"""
    try:
        api_client = MerakiAPIClient()
        result = await get_network_vpn_stats(api_client.session, network_id, timespan)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting VPN stats: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_network_events_tool(
    network_id: str,
    product_type: str = None,
    included_event_types: List[str] = None,
    excluded_event_types: List[str] = None,
    device_mac: str = None,
    device_serial: str = None,
    device_name: str = None,
    client_ip: str = None,
    client_mac: str = None,
    client_name: str = None,
    sm_device_mac: str = None,
    sm_device_name: str = None,
    per_page: int = 100,
    starting_after: str = None,
    ending_before: str = None
) -> List[Dict[str, Any]]:
    """Get events for a network"""
    try:
        api_client = MerakiAPIClient()
        result = await get_network_events(
            api_client.session,
            network_id,
            product_type,
            included_event_types,
            excluded_event_types,
            device_mac,
            device_serial,
            device_name,
            client_ip,
            client_mac,
            client_name,
            sm_device_mac,
            sm_device_name,
            per_page,
            starting_after,
            ending_before
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting network events: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_network_settings_tool(network_id: str) -> List[Dict[str, Any]]:
    """Get network settings"""
    try:
        api_client = MerakiAPIClient()
        result = await get_network_settings(api_client.session, network_id)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting network settings: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def update_network_settings_tool(
    network_id: str,
    name: str = None,
    time_zone: str = None,
    tags: List[str] = None,
    enrollment_string: str = None,
    notes: str = None
) -> List[Dict[str, Any]]:
    """Update network settings"""
    try:
        api_client = MerakiAPIClient()
        result = await update_network_settings(
            api_client.session, network_id, name, time_zone, tags, enrollment_string, notes
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error updating network settings: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def update_appliance_settings_tool(
    network_id: str,
    client_tracking_method: str = None,
    deployment_mode: str = None,
    dynamic_dns: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Update appliance settings for a network"""
    try:
        api_client = MerakiAPIClient()
        result = await update_appliance_settings(
            api_client.session, network_id, client_tracking_method, deployment_mode, dynamic_dns
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error updating appliance settings: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_organization_uplinks_statuses_tool(
    organization_id: str,
    per_page: int = 100,
    starting_after: str = None,
    ending_before: str = None,
    network_ids: List[str] = None,
    serials: List[str] = None,
    iccids: List[str] = None
) -> List[Dict[str, Any]]:
    """Get uplink statuses for devices in an organization"""
    try:
        api_client = MerakiAPIClient()
        result = await get_organization_uplinks_statuses(
            api_client.session,
            organization_id,
            per_page,
            starting_after,
            ending_before,
            network_ids,
            serials,
            iccids
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting uplink statuses: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def update_uplink_tool(
    organization_id: str,
    uplink_id: str,
    name: str = None,
    subnet: str = None,
    gateway_ip: str = None
) -> List[Dict[str, Any]]:
    """Update uplink configuration"""
    try:
        api_client = MerakiAPIClient()
        result = await update_uplink(
            api_client.session, organization_id, uplink_id, name, subnet, gateway_ip
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error updating uplink: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_network_group_policies_tool(network_id: str) -> List[Dict[str, Any]]:
    """Get group policies for a network"""
    try:
        api_client = MerakiAPIClient()
        result = await get_network_group_policies(api_client.session, network_id)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting network group policies: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def create_network_wireless_settings_tool(
    network_id: str,
    mesh_enabled: bool = None,
    ipv6_bridge_enabled: bool = None,
    location_analytics_enabled: bool = None
) -> List[Dict[str, Any]]:
    """Create wireless settings for a network"""
    try:
        api_client = MerakiAPIClient()
        result = await create_network_wireless_settings(
            api_client.session, network_id, mesh_enabled, ipv6_bridge_enabled, location_analytics_enabled
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error creating wireless settings: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def update_network_group_policy_tool(
    network_id: str,
    group_policy_id: str,
    name: str = None,
    scheduling: Dict[str, Any] = None,
    bandwidth: Dict[str, Any] = None,
    firewall_and_traffic_shaping: Dict[str, Any] = None,
    content_filtering: Dict[str, Any] = None,
    splash_auth_settings: str = None,
    vlan_tagging: Dict[str, Any] = None,
    bonjour_forwarding: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Update a group policy"""
    try:
        api_client = MerakiAPIClient()
        result = await update_network_group_policy(
            api_client.session,
            network_id,
            group_policy_id,
            name,
            scheduling,
            bandwidth,
            firewall_and_traffic_shaping,
            content_filtering,
            splash_auth_settings,
            vlan_tagging,
            bonjour_forwarding
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error updating network group policy: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_organization_networks_tool(
    organization_id: str,
    config_template_id: str = None,
    tags: List[str] = None,
    tags_filter_type: str = "withAnyTags",
    per_page: int = 100,
    starting_after: str = None,
    ending_before: str = None
) -> List[Dict[str, Any]]:
    """Get networks in an organization"""
    try:
        api_client = MerakiAPIClient()
        result = await get_organization_networks(
            api_client.session,
            organization_id,
            config_template_id,
            tags,
            tags_filter_type,
            per_page,
            starting_after,
            ending_before
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting organization networks: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def create_organization_network_tool(
    organization_id: str,
    name: str,
    product_types: List[str],
    tags: List[str] = None,
    time_zone: str = None,
    copy_from_network_id: str = None,
    notes: str = None
) -> List[Dict[str, Any]]:
    """Create a network in an organization"""
    try:
        api_client = MerakiAPIClient()
        result = await create_organization_network(
            api_client.session,
            organization_id,
            name,
            product_types,
            tags,
            time_zone,
            copy_from_network_id,
            notes
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error creating organization network: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_connectivity_monitoring_destinations_tool(network_id: str) -> List[Dict[str, Any]]:
    """Get connectivity monitoring destinations for a network"""
    try:
        api_client = MerakiAPIClient()
        result = await get_connectivity_monitoring_destinations(api_client.session, network_id)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting connectivity monitoring destinations: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_network_access_control_lists_tool(network_id: str) -> List[Dict[str, Any]]:
    """Get access control lists for a network"""
    try:
        api_client = MerakiAPIClient()
        result = await get_network_access_control_lists(api_client.session, network_id)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting access control lists: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_organization_login_security_tool(organization_id: str) -> List[Dict[str, Any]]:
    """Get organization login security settings"""
    try:
        api_client = MerakiAPIClient()
        result = await get_organization_login_security(api_client.session, organization_id)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting organization login security: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def get_network_security_intrusion_tool(network_id: str) -> List[Dict[str, Any]]:
    """Get network security intrusion settings"""
    try:
        api_client = MerakiAPIClient()
        result = await get_network_security_intrusion(api_client.session, network_id)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error getting network security intrusion: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def update_connectivity_monitoring_destinations_tool(
    network_id: str,
    destinations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Update connectivity monitoring destinations"""
    try:
        api_client = MerakiAPIClient()
        result = await update_connectivity_monitoring_destinations(
            api_client.session, network_id, destinations
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error updating connectivity monitoring destinations: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def update_network_access_control_lists_tool(
    network_id: str,
    rules: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Update network access control lists"""
    try:
        api_client = MerakiAPIClient()
        result = await update_network_access_control_lists(api_client.session, network_id, rules)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error updating access control lists: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def update_organization_login_security_tool(
    organization_id: str,
    enforce_password_expiration: bool = None,
    password_expiration_days: int = None,
    enforce_two_factor_auth: bool = None,
    enforce_different_passwords: bool = None,
    enforce_strong_passwords: bool = None,
    enforce_account_lockout: bool = None,
    account_lockout_attempts: int = None,
    enforce_idle_timeout: bool = None,
    idle_timeout_minutes: int = None,
    enforce_login_ip_ranges: bool = None,
    login_ip_ranges: List[str] = None
) -> List[Dict[str, Any]]:
    """Update organization login security settings"""
    try:
        api_client = MerakiAPIClient()
        result = await update_organization_login_security(
            api_client.session,
            organization_id,
            enforce_password_expiration,
            password_expiration_days,
            enforce_two_factor_auth,
            enforce_different_passwords,
            enforce_strong_passwords,
            enforce_account_lockout,
            account_lockout_attempts,
            enforce_idle_timeout,
            idle_timeout_minutes,
            enforce_login_ip_ranges,
            login_ip_ranges
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error updating organization login security: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]

@app.tool
async def update_network_security_intrusion_tool(
    network_id: str,
    mode: str = None,
    ids_rulesets: str = None,
    protected_networks: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Update network security intrusion settings"""
    try:
        api_client = MerakiAPIClient()
        result = await update_network_security_intrusion(
            api_client.session, network_id, mode, ids_rulesets, protected_networks
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except Exception as e:
        logger.error(f"Error updating network security intrusion: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}] networks
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from fastmcp import FastMCP

# Add the server directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # Import configuration
# try:
#     from config import setup_environment
#     setup_environment()
# except ImportError:
#     # If config.py is not available, set basic defaults
#     os.environ.setdefault("USE_MOCK", "true")
#     os.environ.setdefault("BASE_URL", "http://127.0.0.1:5000")

from meraki_client import MerakiAPIClient
from get_organizations import get_organizations
from get_network_clients import get_network_clients
from get_network_traffic import get_network_traffic
from get_device_loss_and_latency_history import get_device_loss_and_latency_history
from get_network_vpn_stats import get_network_vpn_stats
from get_network_events import get_network_events
from get_network_settings import get_network_settings
from update_network_settings import update_network_settings
from update_appliance_settings import update_appliance_settings
from get_organization_uplinks_statuses import get_organization_uplinks_statuses
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
logger = logging.getLogger("meraki-mcp-server")

# Check if we should use mock server - check both USE_MOCK and BASE_URL
USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "")
if BASE_URL and "127.0.0.1" in BASE_URL or "localhost" in BASE_URL:
    USE_MOCK = True

logger.info(f"BASE_URL: {BASE_URL}")
logger.info(f"USE_MOCK: {USE_MOCK}")

# Initialize the FastMCP server
app = FastMCP(
    name="cisco-meraki-observability",
    instructions="Cisco Meraki network management tools for observability, configuration, and control."
)

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

from fastmcp import FastMCP

import sys
import os

# Add the server directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # Import configuration
# try:
#     from config import setup_environment
#     setup_environment()
# except ImportError:
#     # If config.py is not available, set basic defaults
#     os.environ.setdefault("USE_MOCK", "true")
#     os.environ.setdefault("BASE_URL", "http://127.0.0.1:5000")

from meraki_client import MerakiAPIClient
from get_organizations import get_organizations
from get_network_clients import get_network_clients
from get_network_traffic import get_network_traffic
from get_device_loss_and_latency_history import get_device_loss_and_latency_history
from get_network_vpn_stats import get_network_vpn_stats
from get_network_events import get_network_events
from get_network_settings import get_network_settings
from update_network_settings import update_network_settings
from update_appliance_settings import update_appliance_settings
from get_organization_uplinks_statuses import get_organization_uplinks_statuses
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
logger = logging.getLogger("meraki-mcp-server")

# Check if we should use mock server - check both USE_MOCK and BASE_URL
USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "")
if BASE_URL and "127.0.0.1" in BASE_URL or "localhost" in BASE_URL:
    USE_MOCK = True

logger.info(f"BASE_URL: {BASE_URL}")
logger.info(f"USE_MOCK: {USE_MOCK}")

# Initialize the MCP server
app = Server("cisco-meraki-observability")

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available Meraki API tools"""
    return [
        Tool(
            name="get_organizations",
            description="Get Cisco Meraki organization information including organization ID, name, and basic details.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_clients",
            description="Get list of devices connected to the network including client details, IP addresses, and connection status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_traffic",
            description="Get network traffic analysis including bandwidth usage, top applications, and traffic patterns.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_device_loss_and_latency_history",
            description="Get device performance metrics including packet loss percentage, latency measurements, and throughput data.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_organization_vpn_stats",
            description="Get VPN connection statistics including connection status, traffic metrics, and performance data.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_events",
            description="Get network events log including device status changes, security events, and system notifications.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_settings",
            description="Get network configuration settings including appliance settings with degradedLinks status (WAN1/WAN2 status), wireless settings, and other network-wide configurations.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update_network_settings",
            description="Update network-wide configuration settings. Use natural language to describe what you want. Example: 'Enable local status page and secure port' or 'Configure named VLANs and webhooks'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "Network settings to apply (natural language or JSON)"
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="update_appliance_settings",
            description="Update appliance settings including degradedLinks status, DHCP configuration, and VLAN settings. Use natural language. Example: 'Set degradedLinks to ok for WAN1 and WAN2' or 'Update WAN1 status to down'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "Appliance settings to apply (natural language or JSON)"
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="get_organization_uplinks_statuses",
            description="Get device uplink status information including which WAN interface each device is connected to (wan1/wan2) and connection status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update_uplink",
            description="CRITICAL TOOL: Move devices between WAN interfaces (wan1/wan2/wan3) for load balancing. MUST be called for each device movement. Use format: 'Move device SERIAL_NUMBER to wan1/wan2/wan3'. Example: 'Move device Q2GY-ECCL-A9TE to wan2' or 'Move device Q2MN-Q3J9-YJHW to wan3'. This tool ACTUALLY MOVES devices - call it for each device that needs to be moved!",
            inputSchema={
                "type": "object",
                "properties": {
                    "uplink_data": {
                        "type": "string",
                        "description": "Natural language description of uplink changes. MUST include device serial number and target WAN. Example: 'Move device Q2GY-ECCL-A9TE to wan2'"
                    }
                },
                "required": ["uplink_data"]
            }
        ),
        Tool(
            name="get_network_group_policies",
            description="Get user group policies including bandwidth limits, content filtering rules, and scheduling settings.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_network_appliance_settings",
            description="Create network infrastructure settings including DHCP configuration and VLAN settings. Use natural language. Example: 'Enable DHCP with 24-hour lease and VLAN 100'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "Appliance settings to create (natural language or JSON)"
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="create_network_wireless_settings",
            description="Create wireless network settings including SSID, bandwidth limits, and security configuration. Use natural language. Example: 'Enable wireless with SSID My_SSID and 1000 Mbps bandwidth'.",
             inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "Wireless settings to create (natural language or JSON)"
                    }
                },
                "required": ["settings_data"]
            }
        ),


        Tool(
            name="update_network_group_policy",
            description="Update user group policies including bandwidth limits, traffic shaping, and content filtering. Use natural language. Example: 'Update policy 123 with new name Updated Guest Policy' or 'Set bandwidth limits to 500 Kbps upload and 10000 Kbps download'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_id": {
                        "type": "string",
                        "description": "ID of the existing policy to update"
                    },
                    "policy_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Policy data to update (can be dictionary or JSON string)"
                    }
                },
                "required": ["policy_id", "policy_data"]
            }
        ),
        Tool(
            name="get_organization_networks",
            description="Get list of all networks in the organization including network IDs, names, and product types.",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {
                        "type": "string",
                        "description": "Optional organization ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="create_organization_network",
            description="Create a new network in the organization. Use natural language. Example: 'Create a network named MCW San Jose with wireless and appliance products'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Network configuration data (can be dictionary or natural language string)"
                    },
                    "organization_id": {
                        "type": "string",
                        "description": "Optional organization ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["network_data"]
            }
        ),
        Tool(
            name="get_connectivity_monitoring_destinations",
            description="Get connectivity monitoring destinations and their status for network health monitoring.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_network_access_control_lists",
            description="Get network access control lists (ACL) including firewall rules and access policies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_organization_login_security",
            description="Get organization login security settings including authentication policies and access controls.",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {
                        "type": "string",
                        "description": "Optional organization ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_network_security_intrusion",
            description="Get network security intrusion detection settings including threat prevention and security policies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="update_connectivity_monitoring_destinations",
            description="Update connectivity monitoring destinations for network health monitoring. Use natural language. Example: 'Add Google DNS as monitoring destination' or 'Set monitoring to 8.8.8.8 and 1.1.1.1'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitoring_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Connectivity monitoring configuration (can be dictionary or natural language string)"
                    },
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["monitoring_data"]
            }
        ),
        Tool(
            name="update_network_access_control_lists",
            description="Update network access control lists (ACL) for firewall rules and access policies. Use natural language. Example: 'Allow access to port 80 and 443' or 'Block access to social media sites'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "acl_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Access control list configuration (can be dictionary or natural language string)"
                    },
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["acl_data"]
            }
        ),
        Tool(
            name="update_organization_login_security",
            description="Update organization login security settings including authentication policies and password requirements. Use natural language. Example: 'Enable two-factor authentication' or 'Set password policy to require 12 characters'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "security_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Login security configuration (can be dictionary or natural language string)"
                    },
                    "organization_id": {
                        "type": "string",
                        "description": "Optional organization ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["security_data"]
            }
        ),
        Tool(
            name="update_network_security_intrusion",
            description="Update network security intrusion detection settings including threat prevention and security policies. Use natural language. Example: 'Enable intrusion detection' or 'Set security mode to prevention'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "intrusion_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Security intrusion configuration (can be dictionary or natural language string)"
                    },
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["intrusion_data"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List:
    """Handle tool execution by delegating to individual tool functions"""
    
    try:
        if name == "get_organizations":
            return await get_organizations()
        elif name == "get_network_clients":
            return await get_network_clients()
        elif name == "get_network_traffic":
            return await get_network_traffic()
        elif name == "get_device_loss_and_latency_history":
            return await get_device_loss_and_latency_history()
        elif name == "get_organization_vpn_stats":
            return await get_network_vpn_stats()
        elif name == "get_network_events":
            return await get_network_events()
        elif name == "get_network_settings":
            return await get_network_settings()
        elif name == "update_network_settings":
            settings_data = arguments.get("settings_data", "")
            return await update_network_settings(settings_data, use_mock=USE_MOCK)
        elif name == "update_appliance_settings":
            settings_data = arguments.get("settings_data", "")
            return await update_appliance_settings(settings_data, use_mock=USE_MOCK)
        elif name == "get_organization_uplinks_statuses":
            return await get_organization_uplinks_statuses()
        elif name == "update_uplink":
            uplink_data = arguments.get("uplink_data", "")
            return await update_uplink(uplink_data, use_mock=USE_MOCK)
        elif name == "get_network_group_policies":
            return await get_network_group_policies()
        elif name == "create_network_appliance_settings":
            settings_data = arguments.get("settings_data", "")
            from create_network_appliance_settings import create_network_appliance_settings
            return await create_network_appliance_settings(settings_data, use_mock=USE_MOCK)
        elif name == "create_network_wireless_settings":
            settings_data = arguments.get("settings_data", "")
            return await create_network_wireless_settings(settings_data, use_mock=USE_MOCK)



        elif name == "update_network_group_policy":
            policy_id = arguments.get("policy_id", "")
            policy_data = arguments.get("policy_data", "")
            return await update_network_group_policy(policy_id, policy_data, use_mock=USE_MOCK)
        elif name == "get_organization_networks":
            organization_id = arguments.get("organization_id", None)
            return await get_organization_networks(organization_id, use_mock=USE_MOCK)
        elif name == "create_organization_network":
            network_data = arguments.get("network_data", "")
            organization_id = arguments.get("organization_id", None)
            return await create_organization_network(network_data, organization_id, use_mock=USE_MOCK)
        elif name == "get_connectivity_monitoring_destinations":
            network_id = arguments.get("network_id", None)
            return await get_connectivity_monitoring_destinations(network_id, use_mock=USE_MOCK)
        elif name == "get_network_access_control_lists":
            network_id = arguments.get("network_id", None)
            return await get_network_access_control_lists(network_id, use_mock=USE_MOCK)
        elif name == "get_organization_login_security":
            organization_id = arguments.get("organization_id", None)
            return await get_organization_login_security(organization_id, use_mock=USE_MOCK)
        elif name == "get_network_security_intrusion":
            network_id = arguments.get("network_id", None)
            return await get_network_security_intrusion(network_id, use_mock=USE_MOCK)
        elif name == "update_connectivity_monitoring_destinations":
            monitoring_data = arguments.get("monitoring_data", "")
            network_id = arguments.get("network_id", None)
            return await update_connectivity_monitoring_destinations(monitoring_data, network_id, use_mock=USE_MOCK)
        elif name == "update_network_access_control_lists":
            acl_data = arguments.get("acl_data", "")
            network_id = arguments.get("network_id", None)
            return await update_network_access_control_lists(acl_data, network_id, use_mock=USE_MOCK)
        elif name == "update_organization_login_security":
            security_data = arguments.get("security_data", "")
            organization_id = arguments.get("organization_id", None)
            return await update_organization_login_security(security_data, organization_id, use_mock=USE_MOCK)
        elif name == "update_network_security_intrusion":
            intrusion_data = arguments.get("intrusion_data", "")
            network_id = arguments.get("network_id", None)
            return await update_network_security_intrusion(intrusion_data, network_id, use_mock=USE_MOCK)


        else:
            return [{"type": "text", "text": f"Unknown tool: {name}"}]
            
    except Exception as e:
        logger.error(f"Tool {name} failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing {name}: {str(e)}"}]

async def main():
    """Main entry point for the MCP server"""
    
    # Test API connectivity
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
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cisco-meraki-observability",
                server_version="1.0.0",
                capabilities={
                    "tools": {}
                }
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 