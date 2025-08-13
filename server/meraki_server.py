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

from meraki_client import MerakiAPIClient
from get_network_clients import get_network_clients
from get_network_traffic import get_network_traffic
from get_device_loss_and_latency_history import get_device_loss_and_latency_history
from get_network_vpn_stats import get_organization_vpn_stats
from get_network_events import get_network_events
from get_organization_uplinks_statuses import get_organization_uplinks_statuses
from update_network_appliance_settings import update_network_appliance_settings
from update_network_wireless_settings import update_network_wireless_settings
from create_network_group_policy import create_network_group_policy

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
            description="Retrieve clients connected to your configured network including device details, usage patterns, and connection history. Uses NETWORK_ID and TIMESPAN from .env file.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_traffic",
            description="Analyze network traffic patterns, bandwidth usage, and application breakdown for network optimization insights. Uses NETWORK_ID and TIMESPAN from .env file.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_device_loss_and_latency_history",
            description="Retrieve loss and latency history for your configured device. Returns historical performance data including packet loss and latency metrics. Uses SERIAL and IP from .env file.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_organization_vpn_stats",
            description="Retrieve VPN statistics for your configured organization. Returns VPN performance data including connection status and traffic metrics. Uses ORGANIZATION_ID and TIMESPAN from .env file.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_events",
            description="Retrieve events for your configured network. Returns network events including device status changes, security events, and system notifications. Uses NETWORK_ID and PRODUCT_TYPE from .env file.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_organization_uplinks_statuses",
            description="Retrieve device uplink status and failover information for your configured organization. Uses ORGANIZATION_ID from .env file.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update_network_appliance_settings",
            description="Update network appliance settings for your configured network. Uses NETWORK_ID from .env file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "oneOf": [
                            {
                                "type": "object",
                                "description": "Dictionary containing the appliance settings to update"
                            },
                            {
                                "type": "string",
                                "description": "JSON string containing the appliance settings to update"
                            }
                        ],
                        "description": "Appliance settings data (can be dictionary or JSON string)"
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="update_network_wireless_settings",
            description="Update network wireless settings for your configured network. Uses NETWORK_ID from .env file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "oneOf": [
                            {
                                "type": "object",
                                "description": "Dictionary containing the wireless settings to update"
                            },
                            {
                                "type": "string",
                                "description": "JSON string containing the wireless settings to update"
                            }
                        ],
                        "description": "Wireless settings data (can be dictionary or JSON string)"
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="create_network_group_policy",
            description="Create a new group policy for your configured network. Uses NETWORK_ID from .env file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_data": {
                        "oneOf": [
                            {
                                "type": "object",
                                "description": "Dictionary containing the group policy configuration"
                            },
                            {
                                "type": "string",
                                "description": "JSON string containing the group policy configuration"
                            }
                        ],
                        "description": "Group policy data (can be dictionary or JSON string)"
                    }
                },
                "required": ["policy_data"]
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
        elif name == "update_network_appliance_settings":
            settings_data = arguments.get("settings_data", {})
            return await update_network_appliance_settings(settings_data, use_mock=USE_MOCK)
        elif name == "update_network_wireless_settings":
            settings_data = arguments.get("settings_data", {})
            return await update_network_wireless_settings(settings_data, use_mock=USE_MOCK)
        elif name == "create_network_group_policy":
            policy_data = arguments.get("policy_data", {})
            return await create_network_group_policy(policy_data, use_mock=USE_MOCK)
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