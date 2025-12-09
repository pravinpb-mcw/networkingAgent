
from .meraki_client import MerakiAPIClient
from mcp.types import TextContent
import json

async def get_network_events():
    client = MerakiAPIClient()
    data = await client.get_network_events()
    return [TextContent(type="text", text=json.dumps({"data": data}, default=str))]
