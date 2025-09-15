"""
Update Appliance Settings Tool
Updates appliance settings for a specific network, including degradedLinks status
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-appliance-settings-tool")

mcp = FastMCP("update-appliance-settings")

@mcp.tool()
async def update_appliance_settings(settings_data: Union[Dict[str, Any], str] = None, use_mock: bool = False) -> List[TextContent]:
    """
    Update appliance settings for your configured network.
    Uses NETWORK_ID from .env file.
    
    Args:
        settings_data: Dictionary or JSON string containing the appliance settings to update
        use_mock: Whether to use mock server mode
    """
    try:
        # Handle missing settings_data
        if not settings_data:
            logger.error("settings_data is required")
            return [TextContent(type="text", text=f"Error executing update_appliance_settings: settings_data is required")]
        
        # Parse settings_data if it's a string
        if isinstance(settings_data, str):
            try:
                settings_data = json.loads(settings_data)
            except json.JSONDecodeError:
                # If it's not JSON, treat it as natural language and convert
                settings_data = convert_natural_language_to_appliance_settings(settings_data)
        
        client = MerakiAPIClient(use_mock=use_mock)
        
        # Update appliance settings
        logger.info("Updating appliance settings...")
        network_result = await client.update_appliance_settings(settings_data=settings_data)
        
        result = {
            "tool": "update_appliance_settings",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "settings_applied": settings_data,
            "status": "success",
            "response": network_result
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"update_appliance_settings completed successfully for network {client.network_id}")
        
        return [TextContent(
            type="text",
            text=json_output
        )]
        
    except Exception as e:
        logger.error(f"update_appliance_settings failed: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing update_appliance_settings: {e}"
        )]

def convert_natural_language_to_appliance_settings(natural_language: str) -> Dict[str, Any]:
    """
    Convert natural language input to structured appliance settings data.
    
    Args:
        natural_language: Natural language description of settings
        
    Returns:
        Dictionary containing the structured appliance settings
    """
    settings_data = {}
    natural_language = natural_language.lower()
    
    # Parse degradedLinks status
    if "degradedlinks" in natural_language or "degraded links" in natural_language:
        degraded_links = []
        
        # Check for WAN1 status
        if "wan1" in natural_language:
            if "down" in natural_language:
                degraded_links.append({"uplink": "wan1", "status": "down"})
            elif "ok" in natural_language or "up" in natural_language:
                degraded_links.append({"uplink": "wan1", "status": "ok"})
        
        # Check for WAN2 status
        if "wan2" in natural_language:
            if "down" in natural_language:
                degraded_links.append({"uplink": "wan2", "status": "down"})
            elif "ok" in natural_language or "up" in natural_language:
                degraded_links.append({"uplink": "wan2", "status": "ok"})
        
        # Check for WAN3 status
        if "wan3" in natural_language:
            if "down" in natural_language:
                degraded_links.append({"uplink": "wan3", "status": "down"})
            elif "ok" in natural_language or "up" in natural_language:
                degraded_links.append({"uplink": "wan3", "status": "ok"})
        
        if degraded_links:
            settings_data["degradedLinks"] = degraded_links
    
    logger.info(f"Converted natural language to appliance settings: {settings_data}")
    return settings_data

if __name__ == "__main__":
    # Test the tool
    import asyncio
    
    async def test():
        # Test with natural language
        result = await update_appliance_settings("Set degradedLinks to ok for WAN1 and WAN2", use_mock=True)
        print("Natural language test:", result[0].text)
        
        # Test with JSON
        json_data = {
            "degradedLinks": [
                {"uplink": "wan1", "status": "ok"},
                {"uplink": "wan2", "status": "ok"}
            ]
        }
        result = await update_appliance_settings(json_data, use_mock=True)
        print("JSON test:", result[0].text)
    
    asyncio.run(test())