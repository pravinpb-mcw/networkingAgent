#!/usr/bin/env python3
"""
Meraki API - 24-Hour Bandwidth Data Fetcher
Retrieves network traffic and bandwidth data for the last 24 hours using the real Meraki API.
Uses the /networks/{networkId}/traffic endpoint for comprehensive bandwidth analysis.
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
ORGANIZATION_ID = "999781"
NETWORK_ID = "L_3947405073390239794"

def get_api_key():
    """Get API key from environment or user input"""
    api_key = os.getenv("MERAKI_API_KEY")
    
    if not api_key:
        api_key = input("Enter your Meraki API key: ").strip()
        if not api_key:
            print("Error: API key cannot be empty")
            sys.exit(1)
    
    return api_key

def get_network_traffic_data(api_key, timespan_hours=24):
    """Get network traffic data for the specified timespan"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/traffic"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Convert hours to seconds
    timespan_seconds = timespan_hours * 3600
    
    params = {
        "timespan": timespan_seconds
    }
    
    try:
        print(f"Fetching network traffic data for last {timespan_hours} hours...")
        print(f"Endpoint: {url}")
        print(f"Timespan: {timespan_seconds} seconds ({timespan_hours} hours)")
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        print(f"Successfully retrieved traffic data")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching traffic data: {e}")
        if hasattr(e, 'response'):
            print(f"Status code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return None

def get_network_clients_bandwidth_usage(api_key, timespan_hours=24):
    """Get bandwidth usage history for all clients in the network"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/clients/bandwidthUsageHistory"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Convert hours to seconds
    timespan_seconds = timespan_hours * 3600
    
    params = {
        "timespan": timespan_seconds
    }
    
    try:
        print(f"Fetching client bandwidth usage history for last {timespan_hours} hours...")
        print(f"Endpoint: {url}")
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        print(f"Successfully retrieved bandwidth usage data")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bandwidth usage data: {e}")
        if hasattr(e, 'response'):
            print(f"Status code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return None

def get_network_devices_performance(api_key):
    """Get performance data for all devices in the network"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/devices"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        print("Fetching network devices...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        devices = response.json()
        print(f"Found {len(devices)} devices")
        
        # Get performance data for each device
        device_performance = {}
        for device in devices:
            serial = device.get('serial')
            name = device.get('name', 'Unnamed Device')
            
            if serial:
                perf_data = get_device_performance(api_key, serial)
                if perf_data:
                    device_performance[serial] = {
                        'device_info': {
                            'name': name,
                            'serial': serial,
                            'model': device.get('model', 'Unknown')
                        },
                        'performance': perf_data
                    }
        
        return device_performance
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching devices: {e}")
        return {}

def get_device_performance(api_key, serial):
    """Get performance data for a specific device"""
    url = f"{BASE_URL}/devices/{serial}/appliance/performance"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching performance for {serial}: {e}")
        return None

def format_timestamp(timestamp):
    """Convert Unix timestamp to readable format"""
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return str(timestamp)

def analyze_bandwidth_data(traffic_data, bandwidth_data, device_performance):
    """Analyze and summarize the bandwidth data"""
    print("\n" + "="*60)
    print("BANDWIDTH DATA ANALYSIS")
    print("="*60)
    
    # Analyze traffic data
    if traffic_data:
        print(f"\n📊 Network Traffic Analysis:")
        print(f"  Data points: {len(traffic_data) if isinstance(traffic_data, list) else 'N/A'}")
        
        if isinstance(traffic_data, list) and traffic_data:
            # Calculate total bandwidth usage
            total_bytes = sum(item.get('bytes', 0) for item in traffic_data)
            total_mbps = (total_bytes * 8) / (1024 * 1024)  # Convert to Mbps
            print(f"  Total data transferred: {total_bytes:,} bytes ({total_mbps:.2f} Mbps)")
            
            # Find peak usage
            peak_bytes = max(item.get('bytes', 0) for item in traffic_data)
            peak_mbps = (peak_bytes * 8) / (1024 * 1024)
            print(f"  Peak usage: {peak_bytes:,} bytes ({peak_mbps:.2f} Mbps)")
    
    # Analyze bandwidth usage data
    if bandwidth_data:
        print(f"\n📈 Client Bandwidth Usage:")
        print(f"  Data points: {len(bandwidth_data) if isinstance(bandwidth_data, list) else 'N/A'}")
        
        if isinstance(bandwidth_data, list) and bandwidth_data:
            # Calculate average bandwidth
            total_bandwidth = sum(item.get('bandwidth', 0) for item in bandwidth_data)
            avg_bandwidth = total_bandwidth / len(bandwidth_data) if bandwidth_data else 0
            print(f"  Average bandwidth: {avg_bandwidth:.2f} Mbps")
            
            # Find peak bandwidth
            peak_bandwidth = max(item.get('bandwidth', 0) for item in bandwidth_data)
            print(f"  Peak bandwidth: {peak_bandwidth:.2f} Mbps")
    
    # Analyze device performance
    if device_performance:
        print(f"\n🖥️ Device Performance:")
        print(f"  Devices analyzed: {len(device_performance)}")
        
        for serial, data in device_performance.items():
            device_name = data['device_info']['name']
            perf = data.get('performance', {})
            
            if perf:
                print(f"  {device_name}:")
                print(f"    Performance score: {perf.get('performanceScore', 'N/A')}")
                print(f"    CPU utilization: {perf.get('cpuUtilization', 'N/A')}%")
                print(f"    Memory utilization: {perf.get('memoryUtilization', 'N/A')}%")

def main():
    print("Meraki 24-Hour Bandwidth Data Fetcher")
    print("="*50)
    print("This script fetches comprehensive bandwidth data from real Meraki API")
    print("="*50)
    
    # Get API key
    api_key = get_api_key()
    
    # Collect all bandwidth-related data
    all_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'timespan_hours': 24,
            'network_id': NETWORK_ID,
            'organization_id': ORGANIZATION_ID
        },
        'traffic_data': None,
        'bandwidth_usage': None,
        'device_performance': None
    }
    
    # 1. Get network traffic data
    print(f"\n1. Fetching Network Traffic Data...")
    traffic_data = get_network_traffic_data(api_key, 24)
    all_data['traffic_data'] = traffic_data
    
    # Small delay to respect rate limits
    time.sleep(1)
    
    # 2. Get client bandwidth usage history
    print(f"\n2. Fetching Client Bandwidth Usage History...")
    bandwidth_data = get_network_clients_bandwidth_usage(api_key, 24)
    all_data['bandwidth_usage'] = bandwidth_data
    
    # Small delay to respect rate limits
    time.sleep(1)
    
    # 3. Get device performance data
    print(f"\n3. Fetching Device Performance Data...")
    device_performance = get_network_devices_performance(api_key)
    all_data['device_performance'] = device_performance
    
    # Analyze the data
    analyze_bandwidth_data(traffic_data, bandwidth_data, device_performance)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"meraki_24h_bandwidth_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        print(f"\n" + "="*60)
        print(f"✅ Data collection complete!")
        print(f"📁 Results saved to: {filename}")
        print(f"📊 Data collected:")
        print(f"   - Network traffic: {'Yes' if traffic_data else 'No'}")
        print(f"   - Bandwidth usage: {'Yes' if bandwidth_data else 'No'}")
        print(f"   - Device performance: {'Yes' if device_performance else 'No'}")
        
    except Exception as e:
        print(f"Error saving data: {e}")
        print("Data collected but not saved to file")

if __name__ == "__main__":
    main()
