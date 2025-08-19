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
    """Initialize mock data from JSON files"""
    global mock_data
    
    # Load network data
    networks_data = load_from_json_file("networks.json")
    if networks_data:
        mock_data["networks"] = networks_data
    
    # Load other data types
    mock_data["clients"] = load_from_json_file("clients.json").get("clients", [])
    mock_data["traffic"] = load_from_json_file("traffic.json").get("traffic", [])
    mock_data["events"] = load_from_json_file("events.json").get("events", [])
    mock_data["vpn_stats"] = load_from_json_file("vpn_stats.json").get("vpn_stats", [])
    mock_data["uplinks_statuses"] = load_from_json_file("uplinks_statuses.json").get("uplinks_statuses", [])
    
    logger.info("Mock data initialized from JSON files")

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
    name: str
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

@app.get("/organizations/uplinks/statuses")
async def get_organization_uplinks_statuses():
    """Mock endpoint for organization uplinks statuses"""
    logger.info(f"GET /organizations/uplinks/statuses")
    
    # Load data from common JSON file
    common_data = load_from_json_file("common_data.json")
    if common_data and "uplinks_statuses" in common_data:
        return common_data["uplinks_statuses"]
    
    # Return empty list if no data found
    return []

@app.post("/networks/{network_id}/appliance/settings")
async def update_network_appliance_settings(network_id: str, settings: ApplianceSettings):
    """Mock endpoint for updating network appliance settings"""
    try:
        logger.info(f"POST /networks/{network_id}/appliance/settings")
        logger.info(f"Settings: {settings}")
        
        # Store the settings in mock data
        if network_id not in mock_data["networks"]:
            mock_data["networks"][network_id] = {}
        
        mock_data["networks"][network_id]["appliance_settings"] = settings.model_dump()
        
        # Save to JSON file
        save_to_json_file("networks.json", mock_data["networks"])
        
        logger.info(f"Successfully stored appliance settings for network {network_id}")
        
        return {
            "message": "Appliance settings updated successfully",
            "networkId": network_id,
            "timestamp": datetime.now().isoformat(),
            "settings": settings.model_dump()
        }
    except Exception as e:
        logger.error(f"Error updating appliance settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/networks/{network_id}/wireless/settings")
async def update_network_wireless_settings(network_id: str, settings: WirelessSettings):
    """Mock endpoint for updating network wireless settings"""
    try:
        logger.info(f"POST /networks/{network_id}/wireless/settings")
        logger.info(f"Settings: {settings}")

        # Store the settings in mock data
        if network_id not in mock_data["networks"]:
            mock_data["networks"][network_id] = {}

        # Convert to dict before storing
        mock_data["networks"][network_id]["wireless_settings"] = settings.model_dump()
        
        # Save to JSON file
        save_to_json_file("networks.json", mock_data["networks"])
        
        logger.info(f"Successfully stored wireless settings for network {network_id}")

        return {
            "message": "Wireless settings updated successfully",
            "networkId": network_id,
            "timestamp": datetime.now().isoformat(),
            "settings": settings.model_dump()  # Return as dict
        }
    except Exception as e:
        logger.error(f"Error updating wireless settings: {e}")
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
    
    # Save to JSON file
    save_to_json_file("networks.json", mock_data["networks"])
    
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
    
    # Save to JSON file
    save_to_json_file("networks.json", mock_data["networks"])
    
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
    
    # Save to JSON file
    save_to_json_file("networks.json", mock_data["networks"])
    
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
    
    # Load data from common JSON file
    common_data = load_from_json_file("common_data.json")
    if common_data and "clients" in common_data:
        return common_data["clients"]
    
    # Return empty list if no data found
    return []

@app.get("/networks/{network_id}/traffic")
async def get_network_traffic(network_id: str):
    """Mock endpoint for getting network traffic"""
    logger.info(f"GET /networks/{network_id}/traffic")
    
    # Load data from common JSON file
    common_data = load_from_json_file("common_data.json")
    if common_data and "traffic" in common_data:
        return common_data["traffic"]
    
    # Return empty list if no data found
    return []

@app.get("/networks/{network_id}/events")
async def get_network_events(network_id: str):
    """Mock endpoint for getting network events"""
    logger.info(f"GET /networks/{network_id}/events")
    
    # Load data from common JSON file
    common_data = load_from_json_file("common_data.json")
    if common_data and "events" in common_data:
        return common_data["events"]
    
    # Return empty list if no data found
    return []

@app.get("/organizations/appliance/vpn/stats")
async def get_organization_vpn_stats():
    """Mock endpoint for getting organization VPN stats"""
    logger.info(f"GET /organizations/appliance/vpn/stats")
    
    # Load data from common JSON file
    common_data = load_from_json_file("common_data.json")
    if common_data and "vpn_stats" in common_data:
        return common_data["vpn_stats"]
    
    # Return empty list if no data found
    return []

@app.get("/devices/lossAndLatencyHistory")
async def get_device_loss_and_latency_history():
    """Mock endpoint for getting device loss and latency history"""
    logger.info(f"GET /devices/lossAndLatencyHistory")
    
    # Load data from common JSON file
    common_data = load_from_json_file("common_data.json")
    if common_data and "device_history" in common_data:
        return common_data["device_history"]
    
    # Return empty list if no data found
    return []

@app.get("/devices/{serial}/lossAndLatencyHistory")
async def get_device_loss_and_latency_history(serial: str):
    """Mock endpoint for getting device loss and latency history"""
    logger.info(f"GET /devices/{serial}/lossAndLatencyHistory")
    
    # Load data from common JSON file
    common_data = load_from_json_file("common_data.json")
    if common_data and "device_history" in common_data:
        return common_data["device_history"]
    
    # Return empty list if no data found
    return []

@app.get("/organizations/{organization_id}/uplinks/statuses")
async def get_organization_uplinks_statuses(organization_id: str):
    """Mock endpoint for getting organization uplink statuses"""
    logger.info(f"GET /organizations/{organization_id}/uplinks/statuses")
    
    # Load data from common JSON file
    common_data = load_from_json_file("common_data.json")
    if common_data and "uplinks_statuses" in common_data:
        return common_data["uplinks_statuses"]
    
    # Return empty list if no data found
    return []

@app.get("/organizations/{organization_id}/appliance/vpn/stats")
async def get_organization_vpn_stats(organization_id: str):
    """Mock endpoint for getting organization VPN stats"""
    logger.info(f"GET /organizations/{organization_id}/appliance/vpn/stats")
    
    # Load data from common JSON file
    common_data = load_from_json_file("common_data.json")
    if common_data and "vpn_stats" in common_data:
        return common_data["vpn_stats"]
    
    # Return empty list if no data found
    return []

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
    logger.info("Starting Mock Meraki API Server on http://127.0.0.1:5000")
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info") 