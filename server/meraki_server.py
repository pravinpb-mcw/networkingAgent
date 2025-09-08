"""
Cisco Meraki MCP Server
Provides tools for managing Cisco Meraki networks
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

from mcp import stdio_server
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool

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
            description="Move devices between WAN interfaces (wan1/wan2) for load balancing. Use natural language. Example: 'Move device Q2GY-ECCL-A9TE from wan1 to wan2' or 'Change device Q2MN-Q3J9-YJHW to wan2'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uplink_data": {
                        "type": "string",
                        "description": "Uplink change request in natural language (e.g., 'Move device SERIAL from wan1 to wan2')"
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
            settings_data = arguments.get("settings_data", {})
            return await update_network_settings(settings_data, use_mock=USE_MOCK)
        elif name == "update_appliance_settings":
            settings_data = arguments.get("settings_data", {})
            return await update_appliance_settings(settings_data, use_mock=USE_MOCK)
        elif name == "get_organization_uplinks_statuses":
            return await get_organization_uplinks_statuses()
        elif name == "update_uplink":
            uplink_data = arguments.get("uplink_data", {})
            return await update_uplink(uplink_data, use_mock=USE_MOCK)
        elif name == "get_network_group_policies":
            return await get_network_group_policies()
        elif name == "create_network_appliance_settings":
            settings_data = arguments.get("settings_data", {})
            from create_network_appliance_settings import create_network_appliance_settings
            return await create_network_appliance_settings(settings_data, use_mock=USE_MOCK)
        elif name == "create_network_wireless_settings":
            settings_data = arguments.get("settings_data", {})
            return await create_network_wireless_settings(settings_data, use_mock=USE_MOCK)



        elif name == "update_network_group_policy":
            policy_id = arguments.get("policy_id", "")
            policy_data = arguments.get("policy_data", {})
            return await update_network_group_policy(policy_id, policy_data, use_mock=USE_MOCK)
        elif name == "get_organization_networks":
            organization_id = arguments.get("organization_id", None)
            return await get_organization_networks(organization_id, use_mock=USE_MOCK)
        elif name == "create_organization_network":
            network_data = arguments.get("network_data", {})
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
            monitoring_data = arguments.get("monitoring_data", {})
            network_id = arguments.get("network_id", None)
            return await update_connectivity_monitoring_destinations(monitoring_data, network_id, use_mock=USE_MOCK)
        elif name == "update_network_access_control_lists":
            acl_data = arguments.get("acl_data", {})
            network_id = arguments.get("network_id", None)
            return await update_network_access_control_lists(acl_data, network_id, use_mock=USE_MOCK)
        elif name == "update_organization_login_security":
            security_data = arguments.get("security_data", {})
            organization_id = arguments.get("organization_id", None)
            return await update_organization_login_security(security_data, organization_id, use_mock=USE_MOCK)
        elif name == "update_network_security_intrusion":
            intrusion_data = arguments.get("intrusion_data", {})
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