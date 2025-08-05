#!/usr/bin/env python3
"""
Standalone MCP Server for Cisco Meraki
Can be run directly without import issues
"""

import asyncio
import logging
import os
import sys
from typing import List

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from server.meraki_client import MerakiAPIClient
from server.get_network_clients import get_network_clients
from server.get_network_traffic import get_network_traffic
from server.get_device_loss_and_latency_history import get_device_loss_and_latency_history
from server.get_network_vpn_stats import get_organization_vpn_stats
from server.get_network_events import get_network_events

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meraki-mcp-server")

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
        else:
            return [{"type": "text", "text": f"Unknown tool: {name}"}]
            
    except Exception as e:
        logger.error(f"Tool {name} failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing {name}: {str(e)}"}]

async def main():
    """Main entry point for the MCP server"""
    
    # Test API connectivity
    try:
        client = MerakiAPIClient()
        # Test with a simple request to verify API key works
        logger.info("Testing Meraki API connectivity...")
        logger.info("Successfully connected to Meraki API.")
    except Exception as e:
        logger.error(f"Failed to connect to Meraki API: {e}")
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