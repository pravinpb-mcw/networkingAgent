#!/usr/bin/env python3
"""
Mock Meraki API Server for Local Testing
Handles the same endpoints as the real Meraki API for development and testing
"""

import json
import logging
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
            "GET /organizations/{org_id}/uplinks/statuses",
            "POST /networks/{network_id}/appliance/settings",
            "POST /networks/{network_id}/wireless/settings", 
            "PUT /networks/{network_id}/groupPolicies",
            "GET /networks/{network_id}/clients",
            "GET /networks/{network_id}/traffic",
            "GET /networks/{network_id}/events",
            "GET /organizations/{org_id}/appliance/vpn/stats",
            "GET /devices/{serial}/lossAndLatencyHistory"
        ]
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Mock server is working!", "timestamp": datetime.now().isoformat()}

@app.get("/organizations/{organization_id}/uplinks/statuses")
async def get_organization_uplinks_statuses(organization_id: str):
    """Mock endpoint for organization uplinks statuses"""
    logger.info(f"GET /organizations/{organization_id}/uplinks/statuses")
    
    # Return mock uplink status data
    mock_uplinks = [
        {
            "serial": "Q2MN-Q3J9-YJHW",
            "networkId": "L_3947405073390239794",
            "uplinks": [
                {
                    "interface": "wan1",
                    "status": "active",
                    "ip": "192.168.1.100",
                    "gateway": "192.168.1.1",
                    "publicIp": "203.0.113.1",
                    "dns": ["8.8.8.8", "8.8.4.4"],
                    "usingStaticIp": False,
                    "ipAssignedBy": "dhcp"
                },
                {
                    "interface": "wan2", 
                    "status": "ready",
                    "ip": "192.168.2.100",
                    "gateway": "192.168.2.1",
                    "publicIp": "203.0.113.2",
                    "dns": ["8.8.8.8", "8.8.4.4"],
                    "usingStaticIp": False,
                    "ipAssignedBy": "dhcp"
                }
            ]
        }
    ]
    
    return mock_uplinks

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
    policy_id = f"policy_{len(mock_data.get('networks', {}).get(network_id, {}).get('policies', [])) + 1}"
    
    # Store the policy in mock data
    if network_id not in mock_data["networks"]:
        mock_data["networks"][network_id] = {}
    if "policies" not in mock_data["networks"][network_id]:
        mock_data["networks"][network_id]["policies"] = {}
    
    mock_data["networks"][network_id]["policies"][policy_id] = {
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
    
    return {
        "message": "Group policy created successfully",
        "networkId": network_id,
        "policyId": policy_id,
        "timestamp": datetime.now().isoformat(),
        "policy": mock_data["networks"][network_id]["policies"][policy_id]
    }

@app.get("/networks/{network_id}/clients")
async def get_network_clients(network_id: str, timespan: int = 7200):
    """Mock endpoint for getting network clients"""
    logger.info(f"GET /networks/{network_id}/clients?timespan={timespan}")
    
    # Return mock client data
    mock_clients = [
        {
            "id": "client_001",
            "mac": "00:11:22:33:44:55",
            "description": "Test Client 1",
            "ip": "192.168.1.100",
            "user": "testuser1",
            "vlan": "100",
            "switchport": "1",
            "wirelessCapabilities": "802.11ac",
            "ssid": "TestSSID",
            "recentDeviceMac": "00:11:22:33:44:55"
        },
        {
            "id": "client_002", 
            "mac": "AA:BB:CC:DD:EE:FF",
            "description": "Test Client 2",
            "ip": "192.168.1.101",
            "user": "testuser2",
            "vlan": "100",
            "switchport": "2",
            "wirelessCapabilities": "802.11ac",
            "ssid": "TestSSID",
            "recentDeviceMac": "AA:BB:CC:DD:EE:FF"
        }
    ]
    
    return mock_clients

@app.get("/networks/{network_id}/traffic")
async def get_network_traffic(network_id: str, timespan: int = 7200):
    """Mock endpoint for getting network traffic"""
    logger.info(f"GET /networks/{network_id}/traffic?timespan={timespan}")
    
    # Return mock traffic data
    mock_traffic = [
        {
            "application": "HTTP",
            "destination": "www.google.com",
            "port": 80,
            "protocol": "TCP",
            "sent": 1024,
            "recv": 2048
        },
        {
            "application": "HTTPS",
            "destination": "www.github.com", 
            "port": 443,
            "protocol": "TCP",
            "sent": 2048,
            "recv": 4096
        }
    ]
    
    return mock_traffic

@app.get("/networks/{network_id}/events")
async def get_network_events(network_id: str, productType: str = "appliance"):
    """Mock endpoint for getting network events"""
    logger.info(f"GET /networks/{network_id}/events?productType={productType}")
    
    # Return mock event data
    mock_events = [
        {
            "occurredAt": "2024-01-01T12:00:00Z",
            "networkId": network_id,
            "type": "device_online",
            "description": "Device Q2MN-Q3J9-YJHW came online",
            "category": "device",
            "eventId": "event_001"
        },
        {
            "occurredAt": "2024-01-01T11:00:00Z",
            "networkId": network_id,
            "type": "device_offline", 
            "description": "Device Q2MN-Q3J9-YJHW went offline",
            "category": "device",
            "eventId": "event_002"
        }
    ]
    
    return mock_events

@app.get("/organizations/{organization_id}/appliance/vpn/stats")
async def get_organization_vpn_stats(organization_id: str, timespan: int = 7200):
    """Mock endpoint for getting organization VPN stats"""
    logger.info(f"GET /organizations/{organization_id}/appliance/vpn/stats?timespan={timespan}")
    
    # Return mock VPN stats
    mock_vpn_stats = [
        {
            "networkId": "L_3947405073390239794",
            "networkName": "Test Network",
            "uplink": "wan1",
            "time": "2024-01-01T12:00:00Z",
            "txBytes": 1024,
            "rxBytes": 2048,
            "numFlows": 100
        }
    ]
    
    return mock_vpn_stats

@app.get("/devices/{serial}/lossAndLatencyHistory")
async def get_device_loss_and_latency_history(serial: str, ip: str):
    """Mock endpoint for getting device loss and latency history"""
    logger.info(f"GET /devices/{serial}/lossAndLatencyHistory?ip={ip}")
    
    # Return mock loss and latency data
    mock_history = [
        {
            "startTime": "2024-01-01T12:00:00Z",
            "endTime": "2024-01-01T12:05:00Z",
            "lossPercent": 0.1,
            "latencyMs": 15.5,
            "goodput": 95.0
        },
        {
            "startTime": "2024-01-01T12:05:00Z",
            "endTime": "2024-01-01T12:10:00Z", 
            "lossPercent": 0.2,
            "latencyMs": 18.2,
            "goodput": 92.0
        }
    ]
    
    return mock_history

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
    return {"message": "Mock data cleared successfully"}

if __name__ == "__main__":
    logger.info("Starting Mock Meraki API Server on http://127.0.0.1:5000")
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info") 