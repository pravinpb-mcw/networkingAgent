#!/usr/bin/env python3
"""
Cisco Meraki API Data Collector
Collects real-time data from Cisco Meraki API for the last 2 hours including:
- Traffic metrics (latency, jitter, packet loss, data size)
- Network policies and configurations
- Configuration changes and history
- Device performance data
"""

import os
import json
import time
from datetime import datetime, timedelta, timezone
import requests
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MerakiDataCollector:
    def __init__(self, api_key: str, base_url: str = "https://api.meraki.com/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-Cisco-Meraki-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        # Use specific organization and network IDs
        self.target_org_id = "999781"
        self.target_network_id = "L_3947405073390239794"
        
        # Calculate time range (last 2 hours)
        self.end_time = datetime.now(timezone.utc)
        self.start_time = self.end_time - timedelta(hours=24)
        
        # Data storage
        self.collected_data = {
            "metadata": {
                "collection_start": self.start_time.isoformat(),
                "collection_end": self.end_time.isoformat(),
                "api_base_url": base_url,
                "target_organization_id": self.target_org_id,
                "target_network_id": self.target_network_id,
                "total_networks": 0,
                "total_organizations": 0
            },
            "organizations": {},
            "networks": {},
            "devices": {},
            "traffic_data": {},
            "performance_metrics": {},
            "policies": {},
            "configurations": {},
            "changes_history": {}
        }

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Meraki API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit
                logger.warning("Rate limited, waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(endpoint, params)
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Request error for {endpoint}: {e}")
            return None

    def collect_organizations(self):
        """Collect organization data for specific org"""
        logger.info(f"Collecting organization {self.target_org_id}...")
        
        # Get specific organization
        org = self._make_request(f"organizations/{self.target_org_id}")
        
        if org:
            self.collected_data["organizations"][self.target_org_id] = {
                "info": org,
                "networks": [],
                "uplinks": [],
                "vpn_stats": [],
                "login_security": None
            }
            
            # Collect organization-specific data
            self._collect_org_uplinks(self.target_org_id)
            self._collect_org_vpn_stats(self.target_org_id)
            self._collect_org_login_security(self.target_org_id)
            
            self.collected_data["metadata"]["total_organizations"] = 1
            logger.info(f"Collected data for organization {self.target_org_id}")
        else:
            logger.error(f"Failed to collect organization {self.target_org_id}")

    def _collect_org_uplinks(self, org_id: str):
        """Collect organization uplink statuses"""
        uplinks = self._make_request(f"organizations/{org_id}/uplinks/statuses")
        if uplinks:
            self.collected_data["organizations"][org_id]["uplinks"] = uplinks

    def _collect_org_vpn_stats(self, org_id: str):
        """Collect organization VPN statistics"""
        vpn_stats = self._make_request(f"organizations/{org_id}/appliance/vpn/stats")
        if vpn_stats:
            self.collected_data["organizations"][org_id]["vpn_stats"] = vpn_stats

    def _collect_org_login_security(self, org_id: str):
        """Collect organization login security settings"""
        login_security = self._make_request(f"organizations/{org_id}/loginSecurity")
        if login_security:
            self.collected_data["organizations"][org_id]["login_security"] = login_security

    def collect_networks(self):
        """Collect network data for specific network"""
        logger.info(f"Collecting network {self.target_network_id}...")
        
        # Get specific network
        network = self._make_request(f"networks/{self.target_network_id}")
        
        if network:
            self.collected_data["networks"][self.target_network_id] = {
                "info": network,
                "organization_id": self.target_org_id,
                "clients": [],
                "traffic": [],
                "events": [],
                "settings": None,
                "group_policies": [],
                "appliance_settings": None,
                "wireless_settings": None,
                "connectivity_monitoring": None,
                "security_intrusion": None,
                "access_control_lists": None,
                "devices": []
            }
            
            # Add network to organization
            self.collected_data["organizations"][self.target_org_id]["networks"].append(self.target_network_id)
            
            # Collect network-specific data
            self._collect_network_data(self.target_network_id)
            
            self.collected_data["metadata"]["total_networks"] = 1
            logger.info(f"Collected data for network {self.target_network_id}")
        else:
            logger.error(f"Failed to collect network {self.target_network_id}")

    def _collect_network_data(self, network_id: str):
        """Collect comprehensive network data"""
        # Network clients
        clients = self._make_request(f"networks/{network_id}/clients")
        if clients:
            self.collected_data["networks"][network_id]["clients"] = clients

        # Network traffic (last 2 hours) - Fixed parameter issue
        traffic_params = {
            "timespan": 7200  # 2 hours in seconds
        }
        traffic = self._make_request(f"networks/{network_id}/traffic", traffic_params)
        if traffic:
            self.collected_data["networks"][network_id]["traffic"] = traffic

        # Network events (last 2 hours) - Fixed parameter issue
        events_params = {
            "includedEventTypes[]": ["traffic", "policy", "configuration", "security"],
            "timespan": 7200  # Use timespan instead of start/end times
        }
        events = self._make_request(f"networks/{network_id}/events", events_params)
        if events:
            self.collected_data["networks"][network_id]["events"] = events

        # Network settings
        settings = self._make_request(f"networks/{network_id}/settings")
        if settings:
            self.collected_data["networks"][network_id]["settings"] = settings

        # Group policies
        policies = self._make_request(f"networks/{network_id}/groupPolicies")
        if policies:
            self.collected_data["networks"][network_id]["group_policies"] = policies

        # Appliance settings
        appliance_settings = self._make_request(f"networks/{network_id}/appliance/settings")
        if appliance_settings:
            self.collected_data["networks"][network_id]["appliance_settings"] = appliance_settings

        # Wireless settings
        wireless_settings = self._make_request(f"networks/{network_id}/wireless/settings")
        if wireless_settings:
            self.collected_data["networks"][network_id]["wireless_settings"] = wireless_settings

        # Connectivity monitoring
        connectivity = self._make_request(f"networks/{network_id}/appliance/connectivityMonitoringDestinations")
        if connectivity:
            self.collected_data["networks"][network_id]["connectivity_monitoring"] = connectivity

        # Security intrusion
        security = self._make_request(f"networks/{network_id}/appliance/security/intrusion")
        if security:
            self.collected_data["networks"][network_id]["security_intrusion"] = security

        # Access control lists
        acls = self._make_request(f"networks/{network_id}/switch/accessControlLists")
        if acls:
            self.collected_data["networks"][network_id]["access_control_lists"] = acls

        # Network devices
        devices = self._make_request(f"networks/{network_id}/devices")
        if devices:
            self.collected_data["networks"][network_id]["devices"] = devices
            self._collect_device_performance(devices, network_id)

    def _collect_device_performance(self, devices: List[Dict], network_id: str):
        """Collect device performance metrics for the last 2 hours"""
        logger.info(f"Collecting performance data for {len(devices)} devices in network {network_id}")
        
        for device in devices:
            device_id = device.get("serial")
            if not device_id:
                continue
                
            # Device loss and latency history - Fixed parameter issue
            performance_params = {
                "timespan": 7200  # Use timespan instead of t0/t1
            }
            
            performance = self._make_request(f"devices/{device_id}/lossAndLatencyHistory", performance_params)
            if performance:
                if device_id not in self.collected_data["devices"]:
                    self.collected_data["devices"][device_id] = {}
                self.collected_data["devices"][device_id]["performance"] = performance
                self.collected_data["devices"][device_id]["network_id"] = network_id

    def collect_traffic_analytics(self):
        """Collect comprehensive traffic analytics"""
        logger.info("Collecting traffic analytics...")
        
        network_id = self.target_network_id
        
        # Traffic flow data - Fixed parameter issue
        flow_params = {
            "timespan": 7200  # Use timespan instead of t0/t1
        }
        
        flows = self._make_request(f"networks/{network_id}/traffic/flow", flow_params)
        if flows:
            if network_id not in self.collected_data["traffic_data"]:
                self.collected_data["traffic_data"][network_id] = {}
            self.collected_data["traffic_data"][network_id]["flows"] = flows

    def collect_performance_metrics(self):
        """Collect aggregated performance metrics"""
        logger.info("Collecting performance metrics...")
        
        network_id = self.target_network_id
        metrics = {
            "latency": [],
            "jitter": [],
            "packet_loss": [],
            "throughput": [],
            "error_rates": []
        }
        
        # Aggregate device performance data
        for device_id, device_data in self.collected_data["devices"].items():
            if device_data.get("network_id") == network_id and "performance" in device_data:
                for perf in device_data["performance"]:
                    if "lossPercent" in perf:
                        metrics["packet_loss"].append(perf["lossPercent"])
                    if "latencyMs" in perf:
                        metrics["latency"].append(perf["latencyMs"])
                    if "jitter" in perf:
                        metrics["jitter"].append(perf["jitter"])
        
        # Calculate averages and statistics
        if metrics["latency"]:
            metrics["latency_avg"] = sum(metrics["latency"]) / len(metrics["latency"])
            metrics["latency_max"] = max(metrics["latency"])
            metrics["latency_min"] = min(metrics["latency"])
        
        if metrics["packet_loss"]:
            metrics["packet_loss_avg"] = sum(metrics["packet_loss"]) / len(metrics["packet_loss"])
            metrics["packet_loss_max"] = max(metrics["packet_loss"])
        
        self.collected_data["performance_metrics"][network_id] = metrics

    def collect_configuration_changes(self):
        """Collect configuration change history"""
        logger.info("Collecting configuration changes...")
        
        network_id = self.target_network_id
        changes = []
        
        # Look for configuration events in network events
        if "events" in self.collected_data["networks"][network_id]:
            for event in self.collected_data["networks"][network_id]["events"]:
                if event.get("type") in ["configuration", "policy", "security"]:
                    changes.append({
                        "timestamp": event.get("occurredAt"),
                        "type": event.get("type"),
                        "description": event.get("description"),
                        "details": event
                    })
        
        if changes:
            self.collected_data["changes_history"][network_id] = changes

    def save_data(self, filename: str = None):
        """Save collected data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meraki_data_{self.target_org_id}_{self.target_network_id}_{timestamp}.json"
        
        filepath = os.path.join("mock_data", filename)
        os.makedirs("mock_data", exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.collected_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return None

    def run_collection(self):
        """Run complete data collection"""
        logger.info("Starting Meraki data collection...")
        logger.info(f"Target Organization: {self.target_org_id}")
        logger.info(f"Target Network: {self.target_network_id}")
        logger.info(f"Time range: {self.start_time} to {self.end_time}")
        
        try:
            # Collect data in sequence
            self.collect_organizations()
            self.collect_networks()
            self.collect_traffic_analytics()
            self.collect_performance_metrics()
            self.collect_configuration_changes()
            
            logger.info("Data collection completed successfully!")
            
            # Save data
            filepath = self.save_data()
            if filepath:
                logger.info(f"Data saved to: {filepath}")
                
                # Print summary
                self._print_summary()
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            raise

    def _print_summary(self):
        """Print collection summary"""
        print("\n" + "="*60)
        print("MERAKI DATA COLLECTION SUMMARY")
        print("="*60)
        print(f"Target Organization: {self.target_org_id}")
        print(f"Target Network: {self.target_network_id}")
        print(f"Collection Period: {self.start_time} to {self.end_time}")
        print(f"Organizations: {self.collected_data['metadata']['total_organizations']}")
        print(f"Networks: {self.collected_data['metadata']['total_networks']}")
        print(f"Devices: {len(self.collected_data['devices'])}")
        print(f"Traffic Data Sources: {len(self.collected_data['traffic_data'])}")
        print(f"Performance Metrics: {len(self.collected_data['performance_metrics'])}")
        print(f"Configuration Changes: {len(self.collected_data['changes_history'])}")
        print("="*60)


def main():
    """Main function"""
    # Get API key from environment or user input
    api_key = os.getenv("MERAKI_API_KEY")
    
    if not api_key:
        print("Cisco Meraki API Key required!")
        print("Set environment variable: set MERAKI_API_KEY=your_api_key")
        print("Or enter your API key below:")
        api_key = input("API Key: ").strip()
    
    if not api_key:
        print("No API key provided. Exiting.")
        return
    
    # Create collector and run
    collector = MerakiDataCollector(api_key)
    
    try:
        collector.run_collection()
    except KeyboardInterrupt:
        print("\nCollection interrupted by user")
    except Exception as e:
        print(f"Collection failed: {e}")


if __name__ == "__main__":
    main()
