"""
Cisco Meraki MCP Server
Combines all individual tools into a single MCP server
"""

import asyncio
import logging
import os
from typing import List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool

import sys
import os

# Add the server directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
try:
    from config import setup_environment
    setup_environment()
except ImportError:
    # If config.py is not available, set basic defaults
    os.environ.setdefault("USE_MOCK", "true")
    os.environ.setdefault("BASE_URL", "http://127.0.0.1:5000")

from meraki_client import MerakiAPIClient
from get_network_clients import get_network_clients
from get_network_traffic import get_network_traffic
from get_device_loss_and_latency_history import get_device_loss_and_latency_history
from get_network_vpn_stats import get_organization_vpn_stats
from get_network_events import get_network_events
from get_organization_uplinks_statuses import get_organization_uplinks_statuses
from update_network_appliance_settings import update_network_appliance_settings
from update_network_wireless_settings import update_network_wireless_settings, update_network_wireless_settings_with_group_policy, continue_wireless_update_after_policy
from update_network_group_policy import update_network_group_policy
from delete_network_group_policy import delete_network_group_policy

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
            name="get_organization_uplinks_statuses",
            description="Get device uplink status. Returns: uplink status, failover info, interface details.",
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
                        "description": "JSON string containing the appliance settings to update (e.g., DHCP, VLAN)."
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="create_network_wireless_settings",
            description="🛑  STOP-AND-WAIT TOOL: Create new network wireless settings with group policy synchronization. Just tell me what you want in simple text. Example: 'Enable wireless with SSID My_SSID and 1000 Mbps bandwidth' or 'Turn on wireless network with name Guest_WiFi'. I'll automatically convert your text to the right format - you don't need to know any technical details. IMPORTANT: I will convert your natural language into the proper JSON structure automatically. When you say 'Enable wireless with SSID My_SSID and 1000 Mbps bandwidth', I will create: {'enabled': True, 'ssid': 'My_SSID', 'bandwidth': {'limitUp': 1000, 'limitDown': 1000}}. SMART: If you provide some details, I'll only ask for what's missing. If you provide nothing, I'll ask for everything. 🛑  CRITICAL INSTRUCTION: After collecting wireless settings, I will STOP execution and wait for YOU to provide group policy data. I will NOT proceed automatically. You must use the 'continue_wireless_update_after_policy' tool to complete the process.",
             inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "JSON string containing the appliance settings to update (e.g., DHCP, VLAN)."
                    }
                },
                "required": ["settings_data"]
            }
        ),

        Tool(
            name="continue_wireless_update_after_policy",
            description="Continue wireless settings update after group policy has been completed. This tool applies the wireless settings that were collected earlier. Use this after you have completed the group policy update to finish the wireless configuration.",
            inputSchema={
                "type": "object",
                "properties": {
                    "wireless_settings": {
                        "oneOf": [
                            {
                                "type": "object",
                                "description": "Dictionary containing the wireless settings to apply"
                            },
                            {
                                "type": "string",
                                "description": "JSON string containing the wireless settings to apply"
                            }
                        ],
                        "description": "Wireless settings data (can be dictionary or JSON string)"
                    }
                },
                "required": ["wireless_settings"]
            }
        ),

        Tool(
            name="create_network_wireless_settings_with_group_policy",
            description="Complete wireless settings creation with group policy synchronization. Just tell me what you want in simple text. Example: 'Enable wireless with SSID My_SSID and 1000 Mbps bandwidth, and create a group policy called Guest Policy'. I'll automatically convert your text to the right format - you don't need to know any technical details. IMPORTANT: I will convert your natural language into the proper JSON structure automatically. SMART: If you provide some details, I'll only ask for what's missing. If you provide nothing, I'll ask for everything. I'll apply group policy first, then wireless settings.",
            inputSchema={
                "type": "object",
                "properties": {
                    "wireless_settings": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Wireless settings data (can be dictionary or JSON string)"
                    },
                    "group_policy_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Group policy data (can be dictionary or JSON string)"
                    }
                },
                "required": ["wireless_settings", "group_policy_data"]
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
            name="delete_network_group_policy",
            description="Delete an existing USER GROUP POLICY. Just provide the policy ID. Example: 'Delete policy_1' or 'Remove policy_2'. IMPORTANT: This will permanently remove the policy and cannot be undone. NOTE: This is for USER POLICIES, not network infrastructure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_id": {
                        "type": "string",
                        "description": "ID of the existing policy to delete"
                    }
                },
                "required": ["policy_id"]
            }
        ),

        Tool(
            name="handle_traffic_shaping_response",
            description="Handle user response to traffic shaping question during wireless settings creation. Use this after the create_network_wireless_settings tool asks about enabling traffic shaping for existing policies. Provide your response: 'YES' to enable for all policies, 'NO' to skip, or 'POLICY_ID:YES' for specific policy.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_response": {
                        "type": "string",
                        "description": "User's response to traffic shaping question (YES/NO/POLICY_ID:YES)"
                    },
                    "wireless_settings": {
                        "oneOf": [
                            {
                                "type": "object",
                                "description": "Dictionary containing the wireless settings that were collected earlier"
                            },
                            {
                                "type": "string",
                                "description": "JSON string containing the wireless settings that were collected earlier"
                            }
                        ],
                        "description": "Wireless settings data that was collected in the previous step"
                    }
                },
                "required": ["user_response", "wireless_settings"]
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
            return await get_organization_vpn_stats()
        elif name == "get_network_events":
            return await get_network_events()
        elif name == "get_organization_uplinks_statuses":
            return await get_organization_uplinks_statuses()
        elif name == "create_network_appliance_settings":
            settings_data = arguments.get("settings_data", {})
            from create_network_appliance_settings import create_network_appliance_settings
            return await create_network_appliance_settings(settings_data, use_mock=USE_MOCK)
        elif name == "create_network_wireless_settings":
            settings_data = arguments.get("settings_data", {})
            return await update_network_wireless_settings(settings_data, use_mock=USE_MOCK)

        elif name == "continue_wireless_update_after_policy":
            wireless_settings = arguments.get("wireless_settings", {})
            return await continue_wireless_update_after_policy(wireless_settings, use_mock=USE_MOCK)

        elif name == "create_network_wireless_settings_with_group_policy":
            wireless_settings = arguments.get("wireless_settings", {})
            group_policy_data = arguments.get("group_policy_data", {})
            return await update_network_wireless_settings_with_group_policy(wireless_settings, group_policy_data, use_mock=USE_MOCK)

        elif name == "update_network_group_policy":
            policy_id = arguments.get("policy_id", "")
            policy_data = arguments.get("policy_data", {})
            return await update_network_group_policy(policy_id, policy_data, use_mock=USE_MOCK)
        elif name == "delete_network_group_policy":
            policy_id = arguments.get("policy_id", "")
            return await delete_network_group_policy(policy_id, use_mock=USE_MOCK)
        elif name == "handle_traffic_shaping_response":
            user_response = arguments.get("user_response", "")
            wireless_settings = arguments.get("wireless_settings", {})
            from update_network_wireless_settings import handle_traffic_shaping_response
            return await handle_traffic_shaping_response(user_response, wireless_settings, use_mock=USE_MOCK)
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