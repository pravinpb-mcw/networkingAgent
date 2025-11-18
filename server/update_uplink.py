"""
Update Uplink Status Tool
Updates existing uplink status data for devices
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-uplink-tool")

async def update_uplink(uplink_data: Union[Dict[str, Any], str], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Update uplink status data for existing devices.
    Uses NETWORK_ID from .env file.
    
    Args:
        uplink_data: Dictionary or JSON string containing the uplink data to update
        use_mock: Whether to use mock server mode
    """
    try:
        # Handle natural language input by converting it to structured data
        if isinstance(uplink_data, str):
            # Convert natural language to structured uplink data
            uplink_data = convert_natural_language_to_uplink_data(uplink_data)
            logger.info("Successfully converted natural language input to uplink data")
        
        # Ensure uplink_data is a dict
        if not isinstance(uplink_data, dict):
            raise ValueError("uplink_data must be a dictionary or valid JSON string")

        client = MerakiAPIClient(use_mock=use_mock)
        
        # Update uplink data
        logger.info("Updating uplink status data")
        
        try:
            # For mock server, we'll actually update the JSON file
            if use_mock:
                # In mock mode, update the JSON file directly
                update_result = await update_mock_uplink_data(uplink_data)
            else:
                # For real Meraki API, call the update endpoint
                update_result = await client.update_uplink_status(network_id=None, uplink_data=uplink_data)
            
            result = {
                "tool": "update_uplink",
                "timestamp": datetime.now().isoformat(),
                "network_id": client.network_id,
                "status": "success",
                "message": "Uplink status updated successfully",
                "updated_data": update_result
            }

            logger.info("Successfully updated uplink status")
            
            return [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]

        except Exception as e:
            logger.error(f"Failed to update uplink status: {e}")
            error_result = {
                "tool": "update_uplink",
                "timestamp": datetime.now().isoformat(),
                "network_id": client.network_id,
                "status": "error",
                "message": f"Failed to update uplink status: {str(e)}"
            }
            return [{"type": "text", "text": json.dumps(error_result, indent=2, default=str)}]

    except Exception as e:
        logger.error(f"update_uplink failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing update_uplink: {str(e)}"}]

def convert_natural_language_to_uplink_data(natural_language: str) -> Dict[str, Any]:
    """
    Convert natural language input to structured uplink data.
    
    Args:
        natural_language: Natural language description of uplink changes
        
    Returns:
        Dictionary containing structured uplink data
    """
    uplink_data = {}
    natural_language_lower = natural_language.lower()
    
    # Parse device serial
    import re
    # Look for device serial patterns like Q2GY-ECCL-A9TE
    serial_match = re.search(r'([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})', natural_language)
    if serial_match:
        uplink_data["serial"] = serial_match.group(1)
    else:
        # Fallback to old pattern
        serial_match = re.search(r'serial[:\s]+([a-z0-9\-]+)', natural_language_lower)
        if serial_match:
            uplink_data["serial"] = serial_match.group(1).upper()
    
    # Parse interface type - look for direction (to wan1, to wan2, etc.)
    if "to wan1" in natural_language_lower or "move to wan1" in natural_language_lower:
        uplink_data["interface"] = "wan1"
    elif "to wan2" in natural_language_lower or "move to wan2" in natural_language_lower:
        uplink_data["interface"] = "wan2"
    elif "to cellular" in natural_language_lower or "move to cellular" in natural_language_lower:
        uplink_data["interface"] = "cellular"
    # Fallback to simple wan1/wan2 detection if no direction specified
    elif "wan1" in natural_language_lower and "wan2" not in natural_language_lower:
        uplink_data["interface"] = "wan1"
    elif "wan2" in natural_language_lower and "wan1" not in natural_language_lower:
        uplink_data["interface"] = "wan2"
    elif "cellular" in natural_language_lower:
        uplink_data["interface"] = "cellular"
    
    # Parse status
    if "active" in natural_language_lower:
        uplink_data["status"] = "active"
    elif "inactive" in natural_language_lower or "not connected" in natural_language_lower:
        uplink_data["status"] = "not connected"
    elif "failed" in natural_language_lower:
        uplink_data["status"] = "failed"
    
    # Parse IP address
    ip_match = re.search(r'ip[:\s]+(\d+\.\d+\.\d+\.\d+)', natural_language_lower)
    if ip_match:
        uplink_data["ip"] = ip_match.group(1)
    
    # Parse gateway
    gateway_match = re.search(r'gateway[:\s]+(\d+\.\d+\.\d+\.\d+)', natural_language_lower)
    if gateway_match:
        uplink_data["gateway"] = gateway_match.group(1)
    
    # Parse public IP
    public_ip_match = re.search(r'public[:\s]+(\d+\.\d+\.\d+\.\d+)', natural_language_lower)
    if public_ip_match:
        uplink_data["publicIp"] = public_ip_match.group(1)
    
    # Parse DNS servers
    dns_match = re.search(r'dns[:\s]+(\d+\.\d+\.\d+\.\d+)', natural_language_lower)
    if dns_match:
        uplink_data["primaryDns"] = dns_match.group(1)
    
    # Parse IP assignment method
    if "static" in natural_language_lower:
        uplink_data["ipAssignedBy"] = "static"
    elif "dhcp" in natural_language_lower:
        uplink_data["ipAssignedBy"] = "dhcp"
    
    logger.info(f"Input natural language: '{natural_language}'")
    logger.info(f"Converted natural language to uplink data: {uplink_data}")
    return uplink_data

async def update_mock_uplink_data(uplink_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the mock JSON file with uplink changes.
    
    Args:
        uplink_data: Dictionary containing the uplink data to update
        
    Returns:
        Dictionary containing the update result
    """
    try:
        import os
        json_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mock_data', 'comprehensive_api_data.json')
        
        # Load existing data
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Get the uplink data
        uplinks = data.get('organization_uplinks_statuses', {}).get('999781', [])
        
        # Find the device to update
        device_serial = uplink_data.get('serial')
        new_interface = uplink_data.get('interface')
        
        if not device_serial or not new_interface:
            raise ValueError("Missing serial or interface in uplink_data")
        
        # Find and update the device
        device_found = False
        for device in uplinks:
            if device.get('serial') == device_serial:
                # Update the interface
                if 'uplinks' in device and len(device['uplinks']) > 0:
                    device['uplinks'][0]['interface'] = new_interface
                    device_found = True
                    logger.info(f"Updated device {device_serial} to interface {new_interface}")
                    break
        
        if not device_found:
            raise ValueError(f"Device with serial {device_serial} not found")
        
        # Save the updated data back to the JSON file
        with open(json_file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Successfully updated device {device_serial} to {new_interface} in JSON file")
        
        return {
            "status": "success",
            "message": f"Device {device_serial} moved to {new_interface}",
            "device_serial": device_serial,
            "new_interface": new_interface
        }
        
    except Exception as e:
        logger.error(f"Failed to update mock uplink data: {e}")
        return {
            "status": "error",
            "message": f"Failed to update mock uplink data: {str(e)}"
        }
