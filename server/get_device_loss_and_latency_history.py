
from .meraki_client import MerakiAPIClient
from mcp.types import TextContent
import json

async def get_device_loss_and_latency_history():
    client = MerakiAPIClient()
    data = await client.get_device_loss_and_latency_history()
    # Limit to last 50 records to prevent MCP buffer overflow and LLM context exhaustion
    if len(data) > 50:
        data = data[-50:]
    return [TextContent(type="text", text=json.dumps({"data": data}, default=str))]
