
from .meraki_client import MerakiAPIClient
from mcp.types import TextContent
import json

async def get_network_traffic():
    client = MerakiAPIClient()
    data = await client.get_network_traffic()
    # Limit to top 20 traffic sources to prevent overload
    if len(data) > 20:
        data = data[:20]
    return [TextContent(type="text", text=json.dumps({"data": data}, default=str))]
