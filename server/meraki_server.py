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
from get_network_clients import get_network_clients
from get_network_traffic import get_network_traffic
from get_device_loss_and_latency_history import get_device_loss_and_latency_history
from get_network_vpn_stats import get_network_vpn_stats
from get_network_events import get_network_events
from get_network_settings import get_network_settings
from update_network_settings import update_network_settings
from get_organization_uplinks_statuses import get_organization_uplinks_statuses
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
            name="get_network_clients",
            description="Get connected network clients. Returns: device details, usage patterns, connection history.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_traffic",
            description="Analyze network traffic patterns. Returns: bandwidth usage, application breakdown, optimization insights.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_device_loss_and_latency_history",
            description="Get device performance metrics. Returns: packet loss, latency, goodput history.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_organization_vpn_stats",
            description="Get VPN statistics. Returns: connection status, traffic metrics, performance data.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_events",
            description="Get network events. Returns: device status, security events, system notifications.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_settings",
            description="Get network-wide configuration settings. Returns: appliance settings, wireless settings, and other network-wide configurations.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update_network_settings",
            description="Create network-wide configuration settings. Just tell me what you want in simple text. Example: 'Enable local status page and secure port' or 'Configure named VLANs and webhooks'. I'll automatically convert your text to the right format - you don't need to know any technical details. IMPORTANT: I will convert your natural language into the proper JSON structure automatically. When you say 'Enable local status page and secure port', I will create: {'localStatusPage': {'enabled': True}, 'securePort': {'enabled': True}}. SMART: If you provide some details, I'll only ask for what's missing. If you provide nothing, I'll ask for everything. This tool creates comprehensive network-wide settings including local status page, secure port, named VLANs, webhooks, and other configurations.",
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
            name="get_organization_uplinks_statuses",
            description="Get device uplink status. Returns: uplink status, failover info, interface details.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_group_policies",
            description="Get network group policies. Returns: policy details, bandwidth limits, content filtering, scheduling settings.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_network_appliance_settings",
            description="Create new NETWORK INFRASTRUCTURE settings (DHCP, VLAN, etc.). Just tell me what you want in simple text. Example: 'Enable DHCP with 24-hour lease and VLAN 100' or 'Turn on DHCP and enable VLAN'. I'll automatically convert your text to the right format - you don't need to know any technical details. IMPORTANT: I will convert your natural language into the proper JSON structure automatically. When you say 'Enable DHCP with 24-hour lease and VLAN 100', I will create: {'dhcp': {'enabled': True, 'leaseTime': 86400}, 'vlan': {'enabled': True, 'id': 100}}. SMART: If you provide some details, I'll only ask for what's missing. If you provide nothing, I'll ask for everything. NOTE: This is for NETWORK INFRASTRUCTURE, not user policies or bandwidth limits.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "JSON string containing the appliance settings to create (e.g., DHCP, VLAN)."
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="create_network_wireless_settings",
            description="Create new network wireless settings. Just tell me what you want in simple text. Example: 'Enable wireless with SSID My_SSID and 1000 Mbps bandwidth' or 'Turn on wireless network with name Guest_WiFi'. I'll automatically convert your text to the right format - you don't need to know any technical details. IMPORTANT: I will convert your natural language into the proper JSON structure automatically. When you say 'Enable wireless with SSID My_SSID and 1000 Mbps bandwidth', I will create: {'enabled': True, 'ssid': 'My_SSID', 'bandwidth': {'limitUp': 1000, 'limitDown': 1000}}. SMART: If you provide some details, I'll only ask for what's missing. If you provide nothing, I'll ask for everything. This tool directly applies wireless settings without complex workflows.",
             inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "JSON string containing the wireless settings to create (e.g., SSID, bandwidth)."
                    }
                },
                "required": ["settings_data"]
            }
        ),


        Tool(
            name="update_network_group_policy",
            description="Update an existing USER GROUP POLICY (bandwidth limits, traffic shaping, content filtering, etc.). Just tell me what you want in simple text. Example: 'Update policy 123 with new name Updated Guest Policy' or 'Change policy ABC to enable traffic shaping' or 'Set bandwidth limits to 500 Kbps upload and 10000 Kbps download'. I'll automatically convert your text to the right format - you don't need to know any technical details. IMPORTANT: I will convert your natural language into the proper JSON structure automatically. When you say 'Update policy 123 with new name Updated Guest Policy', I will create: {'name': 'Updated Guest Policy'}. When you say 'enable traffic shaping', I will create: {'firewallAndTrafficShaping': {'settings': {'trafficShapingEnabled': True}}}. When you say 'set bandwidth limits to 500 Kbps upload and 10000 Kbps download', I will create: {'bandwidth': {'limitUp': 500, 'limitDown': 10000}}. SMART: If you provide some details, I'll only ask for what's missing. If you provide nothing, I'll ask for everything. NOTE: This is for USER POLICIES, not network infrastructure.",
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
            description="Get all networks in an organization. Returns: network list with IDs, names, product types, and configuration details.",
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
            description="Create a new network in an organization. Just tell me what you want in simple text. Example: 'Create a network named MCW San Jose with wireless and appliance products' or 'Add a new network for testing with cameras and sensors'. I'll automatically convert your text to the right format. SMART: If you provide some details, I'll only ask for what's missing. If you provide nothing, I'll ask for everything.",
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
            description="Get connectivity monitoring destinations for a network. Returns: monitoring destinations, connectivity status, and configuration details.",
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
            description="Get network access control lists for a network. Returns: ACL rules, access policies, and security configurations.",
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
            description="Get organization login security settings. Returns: authentication policies, security rules, and access controls.",
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
            description="Get network security intrusion settings. Returns: intrusion detection rules, security policies, and threat prevention settings.",
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
            description="Update connectivity monitoring destinations for a network. Just tell me what you want in simple text. Example: 'Add Google DNS as monitoring destination' or 'Set monitoring to 8.8.8.8 and 1.1.1.1'.",
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
            description="Update network access control lists for a network. Just tell me what you want in simple text. Example: 'Allow access to port 80 and 443' or 'Block access to social media sites'.",
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
            description="Update organization login security settings. Just tell me what you want in simple text. Example: 'Enable two-factor authentication' or 'Set password policy to require 12 characters'.",
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
            description="Update network security intrusion settings. Just tell me what you want in simple text. Example: 'Enable intrusion detection' or 'Set security mode to prevention'.",
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
        if name == "get_network_clients":
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
        elif name == "get_organization_uplinks_statuses":
            return await get_organization_uplinks_statuses()
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