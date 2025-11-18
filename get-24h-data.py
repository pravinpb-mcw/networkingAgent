#!/usr/bin/env python3
"""
Meraki API - Loss and Latency History Fetcher
Retrieves loss and latency data for all devices in a network over the last 24 hours.
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import time

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
ORGANIZATION_ID = "999781"
NETWORK_ID = "L_3947405073390239794"

def get_api_key():
    """Get API key from user input"""
    api_key = input("Enter your Meraki API key: ").strip()
    if not api_key:
        print("Error: API key cannot be empty")
        sys.exit(1)
    return api_key

def get_network_devices(api_key):
    """Get all devices in the network"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/devices"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching devices: {e}")
        return []

def get_device_loss_latency_history(api_key, serial):
    """Get loss and latency history for a specific device (last 24 hours)"""
    # Calculate timespan for last 24 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    # Convert to Unix timestamps
    t0 = int(start_time.timestamp())
    t1 = int(end_time.timestamp())
    
    url = f"{BASE_URL}/devices/{serial}/lossAndLatencyHistory"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Try multiple destination IPs to get comprehensive data
    destination_ips = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]  # Google DNS, Cloudflare DNS, OpenDNS
    all_data = []
    
    for ip in destination_ips:
        params = {
            "ip": ip,
            "timespan": 86400  # 24 hours in seconds
        }
        
        try:
            print(f"  Fetching data for destination {ip}...")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data:
                # Add destination IP to each data point
                for point in data:
                    point['destination_ip'] = ip
                all_data.extend(data)
                print(f"    Retrieved {len(data)} data points for {ip}")
            else:
                print(f"    No data available for {ip}")
                
        except requests.exceptions.RequestException as e:
            print(f"    Error fetching data for {ip}: {e}")
            if hasattr(e, 'response') and e.response.status_code == 429:
                print("    Rate limit exceeded. Waiting 60 seconds...")
                time.sleep(60)
        
        # Small delay between requests
        time.sleep(0.5)
    
    return all_data if all_data else None

def format_timestamp(timestamp):
    """Convert Unix timestamp to readable format"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def main():
    print("Meraki Loss and Latency History Fetcher")
    print("=" * 50)
    
    # Get API key
    api_key = get_api_key()
    
    # Get all devices in the network
    print(f"\nFetching devices for network {NETWORK_ID}...")
    devices = get_network_devices(api_key)
    
    if not devices:
        print("No devices found or error occurred")
        return
    
    print(f"Found {len(devices)} devices")
    
    # Process each device
    all_data = {}
    
    for device in devices:
        serial = device.get('serial')
        name = device.get('name', 'Unnamed Device')
        model = device.get('model', 'Unknown Model')
        
        print(f"\nProcessing device: {name} ({serial}) - {model}")
        
        # Get loss and latency history
        history_data = get_device_loss_latency_history(api_key, serial)
        
        if history_data:
            all_data[serial] = {
                'device_info': {
                    'name': name,
                    'model': model,
                    'serial': serial
                },
                'history': history_data
            }
            
            # Display summary
            if history_data:
                print(f"  Retrieved {len(history_data)} data points")
                if history_data:
                    latest = history_data[-1]
                    # Check if 'ts' key exists, otherwise use 'datetime' or 'timestamp'
                    timestamp_key = 'ts' if 'ts' in latest else 'datetime' if 'datetime' in latest else 'timestamp'
                    if timestamp_key in latest:
                        print(f"  Latest data: {format_timestamp(latest[timestamp_key])}")
                    else:
                        print(f"  Latest data: {latest}")
                    print(f"  Latest loss: {latest.get('lossPercent', 'N/A')}%")
                    print(f"  Latest latency: {latest.get('latencyMs', 'N/A')}ms")
                    print(f"  Latest jitter: {latest.get('jitterMs', 'N/A')}ms")
            else:
                print("  No historical data available")
        
        # Add small delay to respect rate limits
        time.sleep(0.5)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"meraki_loss_latency_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    print(f"\n" + "=" * 50)
    print(f"Data collection complete!")
    print(f"Results saved to: {filename}")
    print(f"Total devices processed: {len(all_data)}")
    
    # Display summary of what was collected
    if all_data:
        print(f"\nSummary:")
        for serial, data in all_data.items():
            device_name = data['device_info']['name']
            history_count = len(data['history']) if data['history'] else 0
            print(f"  {device_name} ({serial}): {history_count} data points")
    else:
        print("\nNo data was collected. Check the error messages above.")

if __name__ == "__main__":
    main()