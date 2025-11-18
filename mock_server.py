#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Mock Meraki API Server for Local Testing
Handles the same endpoints as the real Meraki API for development and testing
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-meraki-server")

app = FastAPI(title="Mock Meraki API Server", version="1.0.0")

# Mock data storage
mock_data = {
    "networks": {},
    "organizations": {},
    "devices": {},
    "clients": [],
    "traffic": [],
    "events": [],
    "vpn_stats": [],
    "uplinks_statuses": []
}

# Data directory for JSON files
DATA_DIR = "mock_data"
os.makedirs(DATA_DIR, exist_ok=True)

def save_to_json_file(filename: str, data: Dict[str, Any]):
    """Save data to a JSON file"""
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Data saved to {filepath}")
    except Exception as e:
        logger.error(f"Error saving to {filepath}: {e}")

def save_to_comprehensive_json(data: Dict[str, Any]):
    """Save data to the comprehensive API data file"""
    filepath = os.path.join(DATA_DIR, "comprehensive_api_data.json")
    try:
        # Load existing comprehensive data
        existing_data = load_from_json_file("comprehensive_api_data.json")
        if not existing_data:
            existing_data = {}
        
        # Update with new data
        existing_data.update(data)
        
        # Save back to comprehensive file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Data saved to comprehensive file: {filepath}")
    except Exception as e:
        logger.error(f"Error saving to comprehensive file: {e}")

def load_from_json_file(filename: str) -> Dict[str, Any]:
    """Load data from a JSON file"""
    filepath = os.path.join(DATA_DIR, filename)
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Data loaded from {filepath}")
                return data
        else:
            logger.info(f"File {filepath} does not exist, using empty data")
            return {}
    except Exception as e:
        logger.error(f"Error loading from {filepath}: {e}")
        return {}

# Load existing data from JSON files on startup
def initialize_mock_data():
    """Initialize mock data from comprehensive JSON file"""
    global mock_data
    
    # Load comprehensive API data
    comprehensive_data = load_from_json_file("comprehensive_api_data.json")
    if comprehensive_data:
        # Map the comprehensive data to our mock_data structure
        mock_data["organizations"] = comprehensive_data.get("organizations", [])
        mock_data["networks"] = comprehensive_data.get("networks", {})
        mock_data["network_clients"] = comprehensive_data.get("network_clients", {})
        mock_data["network_traffic"] = comprehensive_data.get("network_traffic", {})
        mock_data["network_events"] = comprehensive_data.get("network_events", {})
        mock_data["network_settings"] = comprehensive_data.get("network_settings", {})
        mock_data["organization_uplinks_statuses"] = comprehensive_data.get("organization_uplinks_statuses", {})
        mock_data["network_vpn_stats"] = comprehensive_data.get("network_vpn_stats", {})
        mock_data["device_loss_and_latency_history"] = comprehensive_data.get("device_loss_and_latency_history", {})
        mock_data["connectivity_monitoring_destinations"] = comprehensive_data.get("connectivity_monitoring_destinations", {})
        mock_data["network_group_policies"] = comprehensive_data.get("network_group_policies", {})
        mock_data["network_access_control_lists"] = comprehensive_data.get("network_access_control_lists", {})
        mock_data["organization_login_security"] = comprehensive_data.get("organization_login_security", {})
        mock_data["network_security_intrusion"] = comprehensive_data.get("network_security_intrusion", {})
        mock_data["appliance_settings"] = comprehensive_data.get("appliance_settings", {})
        mock_data["wireless_settings"] = comprehensive_data.get("wireless_settings", {})
        
        # Backward compatibility with old structure
        mock_data["clients"] = comprehensive_data.get("clients", [])
        mock_data["traffic"] = comprehensive_data.get("traffic", [])
        mock_data["events"] = comprehensive_data.get("events", [])
        mock_data["vpn_stats"] = comprehensive_data.get("vpn_stats", [])
        mock_data["uplinks_statuses"] = comprehensive_data.get("uplinks_statuses", [])
        
        logger.info("Mock data initialized from comprehensive API data file")
    else:
        # Fallback to old individual files
        networks_data = load_from_json_file("networks.json")
        if networks_data:
            mock_data["networks"] = networks_data
        
        # Load other data types
        mock_data["clients"] = load_from_json_file("clients.json").get("clients", [])
        mock_data["traffic"] = load_from_json_file("traffic.json").get("traffic", [])
        mock_data["events"] = load_from_json_file("events.json").get("events", [])
        mock_data["vpn_stats"] = load_from_json_file("vpn_stats.json").get("vpn_stats", [])
        mock_data["uplinks_statuses"] = load_from_json_file("uplinks_statuses.json").get("uplinks_statuses", [])
        
        logger.info("Mock data initialized from individual JSON files (fallback)")

# Initialize data on startup
initialize_mock_data()

class ApplianceSettings(BaseModel):
    """Flexible model for appliance settings"""
    class Config:
        extra = "allow"  # Allow any additional fields

class WirelessSettings(BaseModel):
    """Flexible model for wireless settings"""
    class Config:
        extra = "allow"  # Allow any additional fields

class GroupPolicy(BaseModel):
    """Model for group policy matching Cisco Meraki API structure"""
    name: str = None  # Make name optional for partial updates
    scheduling: Dict[str, Any] = {}
    bandwidth: Dict[str, Any] = {}
    firewallAndTrafficShaping: Dict[str, Any] = {}
    contentFiltering: Dict[str, Any] = {}
    splashAuthSettings: str = "bypass"
    vlanTagging: Dict[str, Any] = {}
    bonjourForwarding: Dict[str, Any] = {}
    
    class Config:
        extra = "allow"  # Allow any additional fields

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Mock Meraki API Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "GET /organizations/uplinks/statuses",
            "POST /networks/{network_id}/appliance/settings",
            "POST /networks/{network_id}/wireless/settings", 
            "PUT /networks/{network_id}/groupPolicies",
            "PUT /networks/{network_id}/groupPolicies/{policy_id}",
            "GET /networks/clients",
            "GET /networks/traffic",
            "GET /networks/events",
            "GET /organizations/appliance/vpn/stats",
            "GET /devices/lossAndLatencyHistory",
            "GET /mock/json-files",
            "GET /mock/json-files/{filename}",
            "DELETE /mock/data"
        ]
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Mock server is working!", "timestamp": datetime.now().isoformat()}

@app.get("/organizations")
async def get_organizations():
    """Mock endpoint for getting organizations"""
    logger.info(f"GET /organizations")
    
    # Return data from comprehensive API data structure
    if "organizations" in mock_data:
        return mock_data["organizations"]
    
    # Fallback to empty list
    return []

@app.get("/organizations/uplinks/statuses")
async def get_organization_uplinks_statuses():
    """Mock endpoint for organization uplinks statuses"""
    logger.info(f"GET /organizations/uplinks/statuses")
    
    # Return data from comprehensive API data structure
    if "organization_uplinks_statuses" in mock_data:
        # Return all uplink statuses for all organizations
        all_uplinks = []
        for org_id, uplinks in mock_data["organization_uplinks_statuses"].items():
            all_uplinks.extend(uplinks)
        return all_uplinks
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "uplinks_statuses" in common_data:
        return common_data["uplinks_statuses"]
    
    # Return empty list if no data found
    return []

@app.put("/networks/{network_id}/uplinks/statuses")
async def update_uplink_status(network_id: str, uplink_data: dict):
    """Mock endpoint for updating uplink status"""
    try:
        logger.info(f"PUT /networks/{network_id}/uplinks/statuses")
        logger.info(f"Uplink data: {uplink_data}")
        
        # Load comprehensive data
        comprehensive_data = load_from_json_file("comprehensive_api_data.json")
        if not comprehensive_data:
            comprehensive_data = {"organization_uplinks_statuses": {}}
        
        # Update the uplink data in both mock_data and comprehensive_data
        if "organization_uplinks_statuses" in mock_data:
            # Find and update the specific device uplink in mock_data
            updated_devices = []
            for org_id, uplinks in mock_data["organization_uplinks_statuses"].items():
                for device in uplinks:
                    # If serial is provided, match by serial; otherwise update all devices with matching interface
                    if (uplink_data.get("serial") and device.get("serial") == uplink_data.get("serial")) or \
                       (not uplink_data.get("serial") and uplink_data.get("interface")):
                        # Update the uplink interface
                        for uplink in device.get("uplinks", []):
                            # Update the interface to the new one
                            uplink["interface"] = uplink_data.get("interface")
                            # Update other uplink data
                            uplink.update(uplink_data)
                            updated_devices.append(device['serial'])
                            logger.info(f"Updated uplink for device {device['serial']} in mock_data")
                            break
                        if uplink_data.get("serial"):  # If serial was provided, stop after finding the match
                            break
            
            # Also update in comprehensive_data
            if "organization_uplinks_statuses" in comprehensive_data:
                for org_id, uplinks in comprehensive_data["organization_uplinks_statuses"].items():
                    for device in uplinks:
                        # If serial is provided, match by serial; otherwise update all devices with matching interface
                        if (uplink_data.get("serial") and device.get("serial") == uplink_data.get("serial")) or \
                           (not uplink_data.get("serial") and uplink_data.get("interface")):
                            # Update the uplink interface
                            for uplink in device.get("uplinks", []):
                                # Update the interface to the new one
                                uplink["interface"] = uplink_data.get("interface")
                                # Update other uplink data
                                uplink.update(uplink_data)
                                logger.info(f"Updated uplink for device {device['serial']} in comprehensive_data")
                                break
                            if uplink_data.get("serial"):  # If serial was provided, stop after finding the match
                                break
        
        # Save back to comprehensive file
        save_to_comprehensive_json(comprehensive_data)
        
        return {
            "message": "Uplink status updated successfully", 
            "updated_data": uplink_data,
            "updated_devices": updated_devices if 'updated_devices' in locals() else []
        }
        
    except Exception as e:
        logger.error(f"Error updating uplink status: {e}")
        return {"error": str(e)}

@app.post("/networks/{network_id}/appliance/settings")
async def create_network_appliance_settings(network_id: str, settings: ApplianceSettings):
    """Mock endpoint for creating/updating network appliance settings"""
    try:
        logger.info(f"POST /networks/{network_id}/appliance/settings")
        logger.info(f"Settings: {settings}")
        
        # Initialize network if it doesn't exist
        if network_id not in mock_data["networks"]:
            mock_data["networks"][network_id] = {}
        
        # Initialize appliance_settings as a list if it doesn't exist
        if "appliance_settings" not in mock_data["networks"][network_id]:
            mock_data["networks"][network_id]["appliance_settings"] = []
        
        # Check if we should update existing settings or create new ones
        # If there are existing settings, update the latest one
        if len(mock_data["networks"][network_id]["appliance_settings"]) > 0:
            # Update the latest entry
            latest_entry = mock_data["networks"][network_id]["appliance_settings"][-1]
            new_settings = settings.model_dump()
            
            updated_entry = {
                **latest_entry,
                **new_settings,
                "updated_at": datetime.now().isoformat()
            }
            
            # Replace the latest entry with the updated one
            mock_data["networks"][network_id]["appliance_settings"][-1] = updated_entry
            
            # Save to comprehensive JSON file
            save_to_comprehensive_json({"networks": mock_data["networks"]})
            
            logger.info(f"Successfully updated appliance settings for network {network_id}")
            
            return {
                "message": "Appliance settings updated successfully",
                "networkId": network_id,
                "timestamp": datetime.now().isoformat(),
                "updated_entry": updated_entry,
                "total_entries": len(mock_data["networks"][network_id]["appliance_settings"])
            }
        else:
            # Create a new appliance settings entry
            new_settings = settings.model_dump()
            new_entry = {
                "id": f"appliance_settings_{len(mock_data['networks'][network_id]['appliance_settings']) + 1}",
                "created_at": datetime.now().isoformat(),
                **new_settings
            }
            
            # Add the new entry to the list
            mock_data["networks"][network_id]["appliance_settings"].append(new_entry)
            
            # Save to comprehensive JSON file
            save_to_comprehensive_json({"networks": mock_data["networks"]})
            
            logger.info(f"Successfully added new appliance settings for network {network_id}")
            
            return {
                "message": "Appliance settings created successfully",
                "networkId": network_id,
                "timestamp": datetime.now().isoformat(),
                "new_entry": new_entry,
                "total_entries": len(mock_data["networks"][network_id]["appliance_settings"])
            }
    except Exception as e:
        logger.error(f"Error adding appliance settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/networks/{network_id}/appliance/settings")
async def update_network_appliance_settings(network_id: str, settings: ApplianceSettings):
    """Mock endpoint for updating existing network appliance settings"""
    try:
        logger.info(f"PUT /networks/{network_id}/appliance/settings")
        logger.info(f"Settings: {settings}")
        
        # Check if network and appliance settings exist
        if (network_id not in mock_data["networks"] or 
            "appliance_settings" not in mock_data["networks"][network_id] or
            len(mock_data["networks"][network_id]["appliance_settings"]) == 0):
            raise HTTPException(status_code=404, detail=f"No appliance settings found for network {network_id}")
        
        # Get the latest appliance settings entry
        latest_entry = mock_data["networks"][network_id]["appliance_settings"][-1]
        
        # Update the existing entry with new settings
        new_settings = settings.model_dump()
        updated_entry = {
            **latest_entry,
            **new_settings,
            "updated_at": datetime.now().isoformat()
        }
        
        # Replace the latest entry with the updated one
        mock_data["networks"][network_id]["appliance_settings"][-1] = updated_entry
        
        # Save to comprehensive JSON file
        save_to_comprehensive_json({"networks": mock_data["networks"]})
        
        logger.info(f"Successfully updated appliance settings for network {network_id}")
        
        return {
            "message": "Appliance settings updated successfully",
            "networkId": network_id,
            "timestamp": datetime.now().isoformat(),
            "updated_entry": updated_entry,
            "total_entries": len(mock_data["networks"][network_id]["appliance_settings"])
        }
    except Exception as e:
        logger.error(f"Error updating appliance settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/networks/{network_id}/wireless/settings")
async def create_network_wireless_settings(network_id: str, settings: WirelessSettings):
    """Mock endpoint for creating new network wireless settings"""
    try:
        logger.info(f"POST /networks/{network_id}/wireless/settings")
        logger.info(f"Settings: {settings}")

        # Initialize network if it doesn't exist
        if network_id not in mock_data["networks"]:
            mock_data["networks"][network_id] = {}

        # Initialize wireless_settings as a list if it doesn't exist
        if "wireless_settings" not in mock_data["networks"][network_id]:
            mock_data["networks"][network_id]["wireless_settings"] = []

        # Create a new wireless settings entry
        new_settings = settings.model_dump()
        new_entry = {
            "id": f"wireless_settings_{len(mock_data['networks'][network_id]['wireless_settings']) + 1}",
            "created_at": datetime.now().isoformat(),
            **new_settings
        }

        # Add the new entry to the list
        mock_data["networks"][network_id]["wireless_settings"].append(new_entry)
        
        # Save to comprehensive JSON file
        save_to_comprehensive_json({"networks": mock_data["networks"]})
        
        logger.info(f"Successfully created new wireless settings for network {network_id}")

        return {
            "message": "Wireless settings created successfully",
            "networkId": network_id,
            "timestamp": datetime.now().isoformat(),
            "new_entry": new_entry,
            "total_entries": len(mock_data["networks"][network_id]["wireless_settings"])
        }
    except Exception as e:
        logger.error(f"Error creating wireless settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/networks/{network_id}/settings")
async def get_network_settings(network_id: str):
    """Mock endpoint for getting network settings"""
    logger.info(f"GET /networks/{network_id}/settings")
    
    try:
        # Check if network exists
        if network_id not in mock_data["networks"]:
            raise HTTPException(status_code=404, detail=f"Network {network_id} not found")
        
        # Get network settings from mock data
        network_settings = mock_data["networks"][network_id].get("network_settings", {})
        
        # Also include appliance settings if available
        # Get appliance settings from the network data (contains degradedLinks)
        appliance_settings = mock_data["networks"][network_id].get("appliance_settings", [])
        
        # Combine network settings and appliance settings
        combined_data = {
            **network_settings,
            "appliance_settings": appliance_settings
        }
        
        return {
            "message": "Network settings retrieved successfully",
            "networkId": network_id,
            "timestamp": datetime.now().isoformat(),
            "data": combined_data
        }
    except Exception as e:
        logger.error(f"Error getting network settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/networks/{network_id}/settings")
async def update_network_settings(network_id: str, settings: dict):
    """Mock endpoint for updating network settings"""
    logger.info(f"PUT /networks/{network_id}/settings")
    logger.info(f"Settings: {settings}")
    
    try:
        # Check if network exists
        if network_id not in mock_data["networks"]:
            raise HTTPException(status_code=404, detail=f"Network {network_id} not found")
        
        # Store the settings in mock data
        mock_data["networks"][network_id]["network_settings"] = settings
        
        # Save to comprehensive JSON file
        save_to_comprehensive_json({"networks": mock_data["networks"]})
        
        return {
            "message": "Network settings updated successfully",
            "networkId": network_id,
            "timestamp": datetime.now().isoformat(),
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Error updating network settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/networks/{network_id}/groupPolicies")
async def create_network_group_policy(network_id: str, policy: GroupPolicy):
    """Mock endpoint for creating network group policies"""
    logger.info(f"PUT /networks/{network_id}/groupPolicies")
    logger.info(f"Policy: {policy}")
    
    # Generate a mock policy ID
    policy_id = f"policy_{len(mock_data.get('networks', {}).get(network_id, {}).get('groupPolicies', [])) + 1}"
    
    # Store the policy in mock data
    if network_id not in mock_data["networks"]:
        mock_data["networks"][network_id] = {}
    if "groupPolicies" not in mock_data["networks"][network_id]:
        mock_data["networks"][network_id]["groupPolicies"] = {}
    
    mock_data["networks"][network_id]["groupPolicies"][policy_id] = {
        "id": policy_id,
        "name": policy.name,
        "scheduling": policy.scheduling,
        "bandwidth": policy.bandwidth,
        "firewallAndTrafficShaping": policy.firewallAndTrafficShaping,
        "contentFiltering": policy.contentFiltering,
        "splashAuthSettings": policy.splashAuthSettings,
        "vlanTagging": policy.vlanTagging,
        "bonjourForwarding": policy.bonjourForwarding
    }
    
    # Save to comprehensive JSON file
    save_to_comprehensive_json({"networks": mock_data["networks"]})
    
    return {
        "message": "Group policy created successfully",
        "networkId": network_id,
        "policyId": policy_id,
        "timestamp": datetime.now().isoformat(),
        "policy": mock_data["networks"][network_id]["groupPolicies"][policy_id]
    }

@app.put("/networks/{network_id}/groupPolicies/{policy_id}")
async def update_network_group_policy(network_id: str, policy_id: str, policy: GroupPolicy):
    """Mock endpoint for updating existing network group policies"""
    logger.info(f"PUT /networks/{network_id}/groupPolicies/{policy_id}")
    logger.info(f"Policy updates: {policy}")
    
    # Check if the policy exists
    if (network_id not in mock_data["networks"] or 
        "groupPolicies" not in mock_data["networks"][network_id] or
        policy_id not in mock_data["networks"][network_id]["groupPolicies"]):
        raise HTTPException(status_code=404, detail=f"Group policy {policy_id} not found")
    
    # Update the existing policy
    existing_policy = mock_data["networks"][network_id]["groupPolicies"][policy_id]
    
    # Update only the fields that are provided
    if policy.name is not None:
        existing_policy["name"] = policy.name
    if policy.scheduling is not None:
        existing_policy["scheduling"] = policy.scheduling
    if policy.bandwidth is not None:
        existing_policy["bandwidth"] = policy.bandwidth
    if policy.firewallAndTrafficShaping is not None:
        existing_policy["firewallAndTrafficShaping"] = policy.firewallAndTrafficShaping
    if policy.contentFiltering is not None:
        existing_policy["contentFiltering"] = policy.contentFiltering
    if policy.splashAuthSettings is not None:
        existing_policy["splashAuthSettings"] = policy.splashAuthSettings
    if policy.vlanTagging is not None:
        existing_policy["vlanTagging"] = policy.vlanTagging
    if policy.bonjourForwarding is not None:
        existing_policy["bonjourForwarding"] = policy.bonjourForwarding
    
    # Add updated timestamp
    existing_policy["updated_at"] = datetime.now().isoformat()
    
    # Save to comprehensive JSON file
    save_to_comprehensive_json({"networks": mock_data["networks"]})
    
    return {
        "message": "Group policy updated successfully",
        "networkId": network_id,
        "policyId": policy_id,
        "timestamp": datetime.now().isoformat(),
        "updated_policy": existing_policy
    }

@app.delete("/networks/{network_id}/groupPolicies/{policy_id}")
async def delete_network_group_policy(network_id: str, policy_id: str):
    """Mock endpoint for deleting existing network group policies"""
    logger.info(f"DELETE /networks/{network_id}/groupPolicies/{policy_id}")
    
    # Check if the policy exists
    if (network_id not in mock_data["networks"] or 
        "groupPolicies" not in mock_data["networks"][network_id] or
        policy_id not in mock_data["networks"][network_id]["groupPolicies"]):
        raise HTTPException(status_code=404, detail=f"Group policy {policy_id} not found")
    
    # Delete the existing policy
    deleted_policy = mock_data["networks"][network_id]["groupPolicies"].pop(policy_id)
    
    # Save to comprehensive JSON file
    save_to_comprehensive_json({"networks": mock_data["networks"]})
    
    return {
        "message": "Group policy deleted successfully",
        "networkId": network_id,
        "policyId": policy_id,
        "timestamp": datetime.now().isoformat(),
        "deleted_policy": deleted_policy
    }

@app.get("/networks")
async def get_networks():
    """Mock endpoint for getting all networks data"""
    logger.info(f"GET /networks")
    
    # Return the networks data from mock_data
    return mock_data["networks"]

@app.get("/networks/{network_id}/clients")
async def get_network_clients(network_id: str):
    """Mock endpoint for getting network clients"""
    logger.info(f"GET /networks/{network_id}/clients")
    
    # RELOAD data from JSON file to pick up simulation changes
    comprehensive_data = load_from_json_file("comprehensive_api_data.json")
    if comprehensive_data and "network_clients" in comprehensive_data:
        if network_id in comprehensive_data["network_clients"]:
            return comprehensive_data["network_clients"][network_id]
    
    # Return data from cached mock_data structure
    if "network_clients" in mock_data and network_id in mock_data["network_clients"]:
        return mock_data["network_clients"][network_id]
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "clients" in common_data:
        return common_data["clients"]
    
    # Return empty list if no data found
    return []

@app.get("/networks/{network_id}/traffic")
async def get_network_traffic(network_id: str):
    """Mock endpoint for getting network traffic"""
    logger.info(f"GET /networks/{network_id}/traffic")
    
    # Return data from comprehensive API data structure
    if "network_traffic" in mock_data and network_id in mock_data["network_traffic"]:
        return mock_data["network_traffic"][network_id]
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "traffic" in common_data:
        return common_data["traffic"]
    
    # Return empty list if no data found
    return []

@app.get("/networks/{network_id}/events")
async def get_network_events(network_id: str):
    """Mock endpoint for getting network events"""
    logger.info(f"GET /networks/{network_id}/events")
    
    # Return data from comprehensive API data structure
    if "network_events" in mock_data and network_id in mock_data["network_events"]:
        return mock_data["network_events"][network_id]
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "events" in common_data:
        return common_data["events"]
    
    # Return empty list if no data found
    return []

@app.get("/organizations/appliance/vpn/stats")
async def get_organization_vpn_stats():
    """Mock endpoint for getting organization VPN stats"""
    logger.info(f"GET /organizations/appliance/vpn/stats")
    
    # Return data from comprehensive API data structure
    if "network_vpn_stats" in mock_data:
        # Return all VPN stats for all networks
        all_vpn_stats = []
        for network_id, vpn_stats in mock_data["network_vpn_stats"].items():
            all_vpn_stats.extend(vpn_stats)
        return all_vpn_stats
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "vpn_stats" in common_data:
        return common_data["vpn_stats"]
    
    # Return empty list if no data found
    return []

@app.get("/devices/lossAndLatencyHistory")
async def get_device_loss_and_latency_history():
    """Mock endpoint for getting device loss and latency history"""
    logger.info(f"GET /devices/lossAndLatencyHistory")
    
    # Return data from comprehensive API data structure
    if "device_loss_and_latency_history" in mock_data:
        # Return all device history for all devices
        all_device_history = []
        for serial, device_history in mock_data["device_loss_and_latency_history"].items():
            all_device_history.extend(device_history)
        return all_device_history
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "device_history" in common_data:
        return common_data["device_history"]
    
    # Return empty list if no data found
    return []

@app.get("/devices/{serial}/lossAndLatencyHistory")
async def get_device_loss_and_latency_history(serial: str):
    """Mock endpoint for getting device loss and latency history"""
    logger.info(f"GET /devices/{serial}/lossAndLatencyHistory")
    
    # RELOAD data from JSON file to pick up simulation changes
    comprehensive_data = load_from_json_file("comprehensive_api_data.json")
    if comprehensive_data and "device_loss_and_latency_history" in comprehensive_data:
        if serial in comprehensive_data["device_loss_and_latency_history"]:
            return comprehensive_data["device_loss_and_latency_history"][serial]
    
    # Return data from cached mock_data structure
    if "device_loss_and_latency_history" in mock_data and serial in mock_data["device_loss_and_latency_history"]:
        return mock_data["device_loss_and_latency_history"][serial]
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "device_history" in common_data:
        return common_data["device_history"]
    
    # Return empty list if no data found
    return []

@app.get("/organizations/{organization_id}/uplinks/statuses")
async def get_organization_uplinks_statuses(organization_id: str):
    """Mock endpoint for getting organization uplink statuses"""
    logger.info(f"GET /organizations/{organization_id}/uplinks/statuses")
    
    # RELOAD data from JSON file to pick up simulation changes
    comprehensive_data = load_from_json_file("comprehensive_api_data.json")
    if comprehensive_data and "organization_uplinks_statuses" in comprehensive_data:
        if organization_id in comprehensive_data["organization_uplinks_statuses"]:
            return comprehensive_data["organization_uplinks_statuses"][organization_id]
    
    # Return data from cached mock_data structure
    if "organization_uplinks_statuses" in mock_data and organization_id in mock_data["organization_uplinks_statuses"]:
        return mock_data["organization_uplinks_statuses"][organization_id]
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "uplinks_statuses" in common_data:
        return common_data["uplinks_statuses"]
    
    # Return empty list if no data found
    return []

@app.get("/networks/{network_id}/groupPolicies")
async def get_network_group_policies(network_id: str):
    """Mock endpoint for getting network group policies"""
    logger.info(f"GET /networks/{network_id}/groupPolicies")
    
    # Return data from comprehensive API data structure
    if "network_group_policies" in mock_data and network_id in mock_data["network_group_policies"]:
        return mock_data["network_group_policies"][network_id]
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "group_policies" in common_data:
        return common_data["group_policies"]
    
    # Return empty list if no data found
    return []

@app.get("/organizations/{organization_id}/appliance/vpn/stats")
async def get_organization_vpn_stats(organization_id: str):
    """Mock endpoint for getting organization VPN stats"""
    logger.info(f"GET /organizations/{organization_id}/appliance/vpn/stats")
    
    # Return data from comprehensive API data structure
    if "network_vpn_stats" in mock_data:
        # Return all VPN stats for all networks in the organization
        all_vpn_stats = []
        for network_id, vpn_stats in mock_data["network_vpn_stats"].items():
            all_vpn_stats.extend(vpn_stats)
        return all_vpn_stats
    
    # Fallback to old common_data.json
    common_data = load_from_json_file("common_data.json")
    if common_data and "vpn_stats" in common_data:
        return common_data["vpn_stats"]
    
    # Return empty list if no data found
    return []

@app.get("/organizations/{organization_id}/networks")
async def get_organization_networks(organization_id: str):
    """Mock endpoint for getting organization networks"""
    logger.info(f"GET /organizations/{organization_id}/networks")
    
    # Return data from comprehensive API data structure
    if "networks" in mock_data:
        # Convert the networks data structure to a list format
        networks_list = []
        for network_id, network_info in mock_data["networks"].items():
            if network_info.get("organizationId") == organization_id:
                network_entry = {
                    "id": network_id,
                    "organizationId": organization_id,
                    "name": network_info.get("name", f"Network {network_id}"),
                    "productTypes": network_info.get("productTypes", ["appliance", "camera", "cellularGateway", "sensor", "switch", "wireless"]),
                    "timeZone": network_info.get("timeZone", "America/Los_Angeles"),
                    "tags": network_info.get("tags", []),
                    "enrollmentString": network_info.get("enrollmentString", None),
                    "notes": network_info.get("notes", ""),
                    "isBoundToConfigTemplate": network_info.get("isBoundToConfigTemplate", False),
                    "isVirtual": network_info.get("isVirtual", False)
                }
                networks_list.append(network_entry)
        
        logger.info(f"Returning {len(networks_list)} networks for organization {organization_id}")
        return networks_list
    
    # Fallback to comprehensive JSON file
    comprehensive_data = load_from_json_file("comprehensive_api_data.json")
    
    # Convert the networks data structure to a list format
    networks_list = []
    if comprehensive_data and "networks" in comprehensive_data:
        for network_id, network_info in comprehensive_data["networks"].items():
            if network_info.get("organizationId") == organization_id:
                network_entry = {
                    "id": network_id,
                    "organizationId": organization_id,
                    "name": network_info.get("name", f"Network {network_id}"),
                    "productTypes": network_info.get("productTypes", ["appliance", "camera", "cellularGateway", "sensor", "switch", "wireless"]),
                    "timeZone": network_info.get("timeZone", "America/Los_Angeles"),
                    "tags": network_info.get("tags", []),
                    "enrollmentString": network_info.get("enrollmentString", None),
                    "notes": network_info.get("notes", ""),
                    "isBoundToConfigTemplate": network_info.get("isBoundToConfigTemplate", False),
                    "isVirtual": network_info.get("isVirtual", False)
                }
                networks_list.append(network_entry)
    
    logger.info(f"Returning {len(networks_list)} networks for organization {organization_id}")
    return networks_list

@app.post("/organizations/{organization_id}/networks")
async def create_organization_network(organization_id: str, request: Request):
    """Mock endpoint for creating organization networks"""
    logger.info(f"POST /organizations/{organization_id}/networks")
    
    try:
        # Get request body
        network_data = await request.json()
        logger.info(f"Creating network with data: {network_data}")
        
        # Generate a unique network ID
        import uuid
        network_id = f"L_{uuid.uuid4().hex[:16]}"
        
        # Add the network ID and organization ID to the data
        network_data["id"] = network_id
        network_data["organizationId"] = organization_id
        
        # Load existing comprehensive data
        comprehensive_data = load_from_json_file("comprehensive_api_data.json")
        if not comprehensive_data:
            comprehensive_data = {"networks": {}}
        
        # Add the new network
        comprehensive_data["networks"][network_id] = network_data
        
        # Save updated data back to comprehensive file
        save_to_comprehensive_json(comprehensive_data)
        
        logger.info(f"Successfully created new network {network_id} for organization {organization_id}")
        return network_data
        
    except Exception as e:
        logger.error(f"Error creating organization network: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Connectivity Monitoring Destinations
@app.get("/networks/{network_id}/appliance/connectivityMonitoringDestinations")
async def get_connectivity_monitoring_destinations(network_id: str):
    """Get connectivity monitoring destinations for a network"""
    logger.info(f"Getting connectivity monitoring destinations for network {network_id}")
    
    # Return data from comprehensive API data structure
    if "connectivity_monitoring_destinations" in mock_data and network_id in mock_data["connectivity_monitoring_destinations"]:
        return mock_data["connectivity_monitoring_destinations"][network_id]
    
    # Fallback to comprehensive JSON file
    comprehensive_data = load_from_json_file("comprehensive_api_data.json")
    
    if comprehensive_data and "networks" in comprehensive_data and network_id in comprehensive_data["networks"]:
        connectivity_data = comprehensive_data["networks"][network_id].get("connectivity_monitoring", {
            "destinations": ["8.8.8.8", "1.1.1.1"]
        })
        return connectivity_data
    else:
        raise HTTPException(status_code=404, detail="Network not found")

@app.put("/networks/{network_id}/appliance/connectivityMonitoringDestinations")
async def update_connectivity_monitoring_destinations(network_id: str, request: Request):
    """Update connectivity monitoring destinations for a network"""
    logger.info(f"Updating connectivity monitoring destinations for network {network_id}")
    
    try:
        monitoring_data = await request.json()
        logger.info(f"Monitoring data: {monitoring_data}")
        
        # Load comprehensive data
        comprehensive_data = load_from_json_file("comprehensive_api_data.json")
        if not comprehensive_data:
            comprehensive_data = {"networks": {}}
        
        if network_id in comprehensive_data["networks"]:
            # Update the connectivity monitoring data
            comprehensive_data["networks"][network_id]["connectivity_monitoring"] = monitoring_data
            
            # Save back to comprehensive file
            save_to_comprehensive_json(comprehensive_data)
            
            logger.info(f"Updated connectivity monitoring for network {network_id}")
            return monitoring_data
        else:
            raise HTTPException(status_code=404, detail="Network not found")
    except Exception as e:
        logger.error(f"Error updating connectivity monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Access Control Lists
@app.get("/networks/{network_id}/switch/accessControlLists")
async def get_network_access_control_lists(network_id: str):
    """Get network access control lists"""
    logger.info(f"Getting access control lists for network {network_id}")
    
    # Return data from comprehensive API data structure
    if "network_access_control_lists" in mock_data and network_id in mock_data["network_access_control_lists"]:
        return mock_data["network_access_control_lists"][network_id]
    
    # Fallback to comprehensive JSON file
    comprehensive_data = load_from_json_file("comprehensive_api_data.json")
    
    if comprehensive_data and "networks" in comprehensive_data and network_id in comprehensive_data["networks"]:
        acl_data = comprehensive_data["networks"][network_id].get("access_control_lists", {
            "rules": [
                {
                    "policy": "allow",
                    "protocol": "tcp",
                    "srcPort": "any",
                    "srcCidr": "any",
                    "destPort": "any",
                    "destCidr": "any",
                    "syslogEnabled": False
                }
            ]
        })
        return acl_data
    else:
        raise HTTPException(status_code=404, detail="Network not found")

@app.put("/networks/{network_id}/switch/accessControlLists")
async def update_network_access_control_lists(network_id: str, request: Request):
    """Update network access control lists"""
    logger.info(f"Updating access control lists for network {network_id}")
    
    try:
        acl_data = await request.json()
        logger.info(f"ACL data: {acl_data}")
        
        # Load comprehensive data
        comprehensive_data = load_from_json_file("comprehensive_api_data.json")
        if not comprehensive_data:
            comprehensive_data = {"networks": {}}
        
        if network_id in comprehensive_data["networks"]:
            # Update the ACL data
            comprehensive_data["networks"][network_id]["access_control_lists"] = acl_data
            
            # Save back to comprehensive file
            save_to_comprehensive_json(comprehensive_data)
            
            logger.info(f"Updated access control lists for network {network_id}")
            return acl_data
        else:
            raise HTTPException(status_code=404, detail="Network not found")
    except Exception as e:
        logger.error(f"Error updating access control lists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Login Security
@app.get("/organizations/{organization_id}/loginSecurity")
async def get_organization_login_security(organization_id: str):
    """Get organization login security settings"""
    logger.info(f"Getting login security settings for organization {organization_id}")
    
    # Return data from comprehensive API data structure
    if "organization_login_security" in mock_data and organization_id in mock_data["organization_login_security"]:
        return mock_data["organization_login_security"][organization_id]
    
    # Fallback to default login security data
    login_security_data = {
        "enforcePasswordExpiration": False,
        "passwordExpirationDays": 365,
        "enforceDifferentPasswords": False,
        "numDifferentPasswords": 5,
        "enforceStrongPasswords": False,
        "enforceAccountLockout": False,
        "accountLockoutAttempts": 10,
        "enforceIdleTimeout": False,
        "idleTimeoutMinutes": 60,
        "enforceTwoFactorAuth": False,
        "enforceLoginIpRanges": False,
        "loginIpRanges": []
    }
    
    return login_security_data

@app.put("/organizations/{organization_id}/loginSecurity")
async def update_organization_login_security(organization_id: str, request: Request):
    """Update organization login security settings"""
    logger.info(f"Updating login security settings for organization {organization_id}")
    
    try:
        security_data = await request.json()
        logger.info(f"Security data: {security_data}")
        
        # Load comprehensive data and update login security
        comprehensive_data = load_from_json_file("comprehensive_api_data.json")
        if not comprehensive_data:
            comprehensive_data = {"organization_login_security": {}}
        
        # Update the login security data
        if "organization_login_security" not in comprehensive_data:
            comprehensive_data["organization_login_security"] = {}
        
        comprehensive_data["organization_login_security"][organization_id] = security_data
        
        # Save back to comprehensive file
        save_to_comprehensive_json(comprehensive_data)
        
        logger.info(f"Updated login security for organization {organization_id}")
        return security_data
    except Exception as e:
        logger.error(f"Error updating login security: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Security Intrusion
@app.get("/networks/{network_id}/appliance/security/intrusion")
async def get_network_security_intrusion(network_id: str):
    """Get network security intrusion settings"""
    logger.info(f"Getting security intrusion settings for network {network_id}")
    
    # Return data from comprehensive API data structure
    if "network_security_intrusion" in mock_data and network_id in mock_data["network_security_intrusion"]:
        return mock_data["network_security_intrusion"][network_id]
    
    # Fallback to comprehensive JSON file
    comprehensive_data = load_from_json_file("comprehensive_api_data.json")
    
    if comprehensive_data and "networks" in comprehensive_data and network_id in comprehensive_data["networks"]:
        intrusion_data = comprehensive_data["networks"][network_id].get("security_intrusion", {
            "mode": "prevention",
            "idsRulesets": "connectivity"
        })
        return intrusion_data
    else:
        raise HTTPException(status_code=404, detail="Network not found")

@app.put("/networks/{network_id}/appliance/security/intrusion")
async def update_network_security_intrusion(network_id: str, request: Request):
    """Update network security intrusion settings"""
    logger.info(f"Updating security intrusion settings for network {network_id}")
    
    try:
        intrusion_data = await request.json()
        logger.info(f"Intrusion data: {intrusion_data}")
        
        # Load comprehensive data
        comprehensive_data = load_from_json_file("comprehensive_api_data.json")
        if not comprehensive_data:
            comprehensive_data = {"networks": {}}
        
        if network_id in comprehensive_data["networks"]:
            # Update the intrusion data
            comprehensive_data["networks"][network_id]["security_intrusion"] = intrusion_data
            
            # Save back to comprehensive file
            save_to_comprehensive_json(comprehensive_data)
            
            logger.info(f"Updated security intrusion for network {network_id}")
            return intrusion_data
        else:
            raise HTTPException(status_code=404, detail="Network not found")
    except Exception as e:
        logger.error(f"Error updating security intrusion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mock/data")
async def get_mock_data():
    """Get all stored mock data for debugging"""
    return mock_data

@app.delete("/mock/data")
async def clear_mock_data():
    """Clear all stored mock data"""
    global mock_data
    mock_data = {
        "networks": {},
        "organizations": {},
        "devices": {},
        "clients": [],
        "traffic": [],
        "events": [],
        "vpn_stats": [],
        "uplinks_statuses": []
    }
    
    # Clear JSON files
    try:
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(DATA_DIR, filename)
                os.remove(filepath)
                logger.info(f"Deleted {filepath}")
    except Exception as e:
        logger.error(f"Error clearing JSON files: {e}")
    
    return {"message": "Mock data and JSON files cleared successfully"}

@app.get("/mock/json-files")
async def list_json_files():
    """List all available JSON data files"""
    try:
        files = []
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(DATA_DIR, filename)
                file_size = os.path.getsize(filepath)
                files.append({
                    "filename": filename,
                    "size_bytes": file_size,
                    "size_kb": round(file_size / 1024, 2)
                })
        return {
            "data_directory": DATA_DIR,
            "files": files,
            "total_files": len(files)
        }
    except Exception as e:
        logger.error(f"Error listing JSON files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mock/json-files/{filename}")
async def get_json_file_content(filename: str):
    """Get the content of a specific JSON file"""
    try:
        if not filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only .json files are allowed")
        
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        return {
            "filename": filename,
            "content": content,
            "last_modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
        }
    except Exception as e:
        logger.error(f"Error reading JSON file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting Mock Meraki API Server on http://127.0.0.5000")
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info") 
    # uvicorn.run(app, host="0.0.0.0", port=5000)
    # uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")

