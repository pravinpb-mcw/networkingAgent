import asyncio
import sys
import os
import logging

# Setup logging to file
log_file = os.path.join(os.path.dirname(__file__), 'server_debug.log')
logging.basicConfig(filename=log_file, level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # Add the parent directory to sys.path to allow imports from server package
    # This assumes the script is located in networkingAgent/server/
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logger.info(f"Added to sys.path: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")

    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    import mcp.types as types

    # Import tools using the package structure
    logger.info("Importing tools...")
    from server.get_device_loss_and_latency_history import get_device_loss_and_latency_history
    from server.get_network_traffic import get_network_traffic
    from server.get_network_events import get_network_events
    from server.get_network_clients import get_network_clients
    from server.get_organizations import get_organizations
    logger.info("Tools imported successfully")

    # Use FastMCP if available (simulated here by using standard Server but keeping structure clean)
    # Note: True FastMCP library is not yet available in this environment, so we stick to standard MCP Server
    # but optimize the tool definitions for speed.
    app = Server("cisco-meraki-observability")
except Exception as e:
    logger.exception("Initialization error")
    sys.exit(1)

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    logger.info("Listing tools")
    return [
        types.Tool(
            name="get_device_loss_and_latency_history",
            description="Get historical data for device packet loss and latency",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_network_traffic",
            description="Get network traffic analysis",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_network_events",
            description="Get recent network events",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_network_clients",
            description="Get list of network clients and their usage",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_organizations",
            description="Get Meraki organizations",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "get_device_loss_and_latency_history":
        return await get_device_loss_and_latency_history()
    elif name == "get_network_traffic":
        return await get_network_traffic()
    elif name == "get_network_events":
        return await get_network_events()
    elif name == "get_network_clients":
        return await get_network_clients()
    elif name == "get_organizations":
        return await get_organizations()
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    try:
        logger.info("Starting server...")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server started, waiting for requests")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        logger.exception("Runtime error")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("Fatal error")
