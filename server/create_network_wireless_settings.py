"""
Create Network Wireless Settings Tool
Creates wireless settings for a specific network directly
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Union

from meraki_client import MerakiAPIClient

logger = logging.getLogger("create-network-wireless-settings-tool")

async def create_network_wireless_settings(settings_data: Union[Dict[str, Any], str], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Create network wireless settings for your configured network.
    Uses NETWORK_ID from .env file.
    
    This function directly applies wireless settings without complex workflows.
    
    Args:
        settings_data: Wireless settings to apply (dict or natural language string)
        use_mock: Whether to use mock server mode
    
    Returns:
        List of response objects with status information
    """
    try:
        # Handle natural language input by converting it to structured data
        if isinstance(settings_data, str):
            # Convert natural language to structured wireless settings
            from natural_language_converter import convert_natural_language_to_wireless_settings
            settings_data = convert_natural_language_to_wireless_settings(settings_data)
            logger.info("Successfully converted natural language input to wireless settings")
        
        # Validate settings data
        if not isinstance(settings_data, dict):
            raise ValueError("settings_data must be a dictionary")
        
        # Initialize Meraki client
        client = MerakiAPIClient(use_mock=use_mock)
        
        # Initialize response tracking
        response_parts = []
        response_parts.append("📶 **WIRELESS NETWORK SETTINGS CREATION**")
        response_parts.append("=" * 50)
        response_parts.append(f"📝 **Settings to Apply:** {json.dumps(settings_data, indent=2)}")
        response_parts.append("")
        
        # Apply wireless settings
        logger.info("Creating wireless settings...")
        try:
            wireless_result = await client.create_network_wireless_settings(settings_data=settings_data)
            
            response_parts.append("✅ **WIRELESS SETTINGS CREATED SUCCESSFULLY**")
            response_parts.append("")
            response_parts.append("📋 **Created Settings:**")
            
            # Display applied settings
            if settings_data.get("enabled") is not None:
                status = "ENABLED" if settings_data["enabled"] else "DISABLED"
                response_parts.append(f"   • Wireless: {status}")
            
            if settings_data.get("ssid"):
                response_parts.append(f"   • SSID: {settings_data['ssid']}")
            
            if settings_data.get("bandwidth"):
                bandwidth = settings_data["bandwidth"]
                if bandwidth.get("limitUp"):
                    response_parts.append(f"   • Upload Limit: {bandwidth['limitUp']} Mbps")
                if bandwidth.get("limitDown"):
                    response_parts.append(f"   • Download Limit: {bandwidth['limitDown']} Mbps")
            
            response_parts.append("")
            response_parts.append("🎉 **OPERATION COMPLETED SUCCESSFULLY!**")
            response_parts.append("• Wireless network configuration created")
            
        except Exception as e:
            logger.error(f"Failed to create wireless settings: {e}")
            response_parts.append(f"❌ **ERROR CREATING WIRELESS SETTINGS:** {str(e)}")
            response_parts.append("")
            response_parts.append("🔧 **Recommendations:**")
            response_parts.append("   • Check network connectivity")
            response_parts.append("   • Verify settings format")
            response_parts.append("   • Review error logs")
        
        response_parts.append("")
        response_parts.append("📅 **Timestamp:** " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return [{"type": "text", "text": "\n".join(response_parts)}]
        
    except Exception as e:
        logger.error(f"Error in create_network_wireless_settings: {e}")
        return [{
            "type": "text",
            "text": f"❌ **WIRELESS SETTINGS CREATION FAILED**\n\nError: {str(e)}\n\nPlease check your settings and try again."
        }]
