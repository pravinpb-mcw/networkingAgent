
from .meraki_client import MerakiAPIClient
from mcp.types import TextContent
import json

async def get_organizations():
    client = MerakiAPIClient()
    data = await client.get_organizations()
    return [TextContent(type="text", text=json.dumps({"data": data}, default=str))]
