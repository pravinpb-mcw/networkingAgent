#!/usr/bin/env python3
"""
Enhanced Uplink Device Generator
Allows precise control over WAN1 and WAN2 device generation with specific active/inactive counts
"""

import json
import random
import string
from datetime import datetime, timedelta

def generate_random_serial():
    """Generate a random Meraki device serial number"""
    prefix = random.choice(['Q2GY', 'Q2YN', 'Q3FA', 'Q2MN', 'Q3GX', 'Q2FX', 'Q3GZ'])
    middle = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{middle}-{suffix}"

def generate_random_ip():
    """Generate a random public IP address"""
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

def generate_random_gateway(ip):
    """Generate a gateway IP based on the device IP"""
    ip_parts = ip.split('.')
    return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"

def generate_random_dns():
    """Generate random DNS servers"""
    dns_options = [
        ("8.8.8.8", "8.8.4.4"),
        ("1.1.1.1", "1.0.0.1"),
        ("208.67.222.222", "208.67.220.220"),
        ("9.9.9.9", "149.112.112.112")
    ]
    return random.choice(dns_options)

def generate_uplink_interface(interface_type, status):
    """Generate a single uplink interface with specified status"""
    ip_assigned_by = ['static', 'dhcp']
    
    if status == 'active':
        ip = generate_random_ip()
        gateway = generate_random_gateway(ip)
        public_ip = ip
        primary_dns, secondary_dns = generate_random_dns()
        assigned_by = random.choice(ip_assigned_by)
    else:
        ip = None
        gateway = None
        public_ip = None
        primary_dns = None
        secondary_dns = None
        assigned_by = None
    
    return {
        "interface": interface_type,
        "status": status,
        "ip": ip,
        "gateway": gateway,
        "publicIp": public_ip,
        "primaryDns": primary_dns,
        "secondaryDns": secondary_dns,
        "ipAssignedBy": assigned_by
    }

def generate_device_with_uplinks(wan1_active, wan1_inactive, wan2_active, wan2_inactive):
    """Generate a device with specified uplink configuration"""
    models = ['MX67W', 'MX64W', 'MX85', 'MX75', 'MX100', 'MX250', 'MX450', 'MX650']
    
    # Generate random data
    serial = generate_random_serial()
    model = random.choice(models)
    network_id = f"N_{random.randint(1000000000000000000, 9999999999999999999)}"
    
    # Generate random timestamp (within last 30 days)
    now = datetime.now()
    random_days = random.randint(0, 30)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    random_seconds = random.randint(0, 59)
    
    last_reported = now - timedelta(days=random_days, hours=random_hours, minutes=random_minutes, seconds=random_seconds)
    last_reported_str = last_reported.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Create uplinks based on requirements
    uplinks = []
    
    # Add WAN1 uplinks
    for _ in range(wan1_active):
        uplinks.append(generate_uplink_interface("wan1", "active"))
    
    for _ in range(wan1_inactive):
        uplinks.append(generate_uplink_interface("wan1", "not connected"))
    
    # Add WAN2 uplinks
    for _ in range(wan2_active):
        uplinks.append(generate_uplink_interface("wan2", "active"))
    
    for _ in range(wan2_inactive):
        uplinks.append(generate_uplink_interface("wan2", "not connected"))
    
    device = {
        "networkId": network_id,
        "serial": serial,
        "model": model,
        "highAvailability": {
            "enabled": random.choice([True, False]),
            "role": random.choice(["primary", "secondary"])
        },
        "lastReportedAt": last_reported_str,
        "uplinks": uplinks
    }
    
    return device

def get_user_input():
    """Get user input for device generation"""
    print("🔧 Enhanced Uplink Device Generator")
    print("=" * 50)
    print("This script allows you to specify exactly how many devices you want")
    print("and how many should be active vs inactive for each uplink type.")
    print()
    
    # Get WAN1 configuration
    print("📡 WAN1 Configuration:")
    while True:
        try:
            wan1_total = int(input("How many WAN1 devices do you want? "))
            if wan1_total < 0:
                print("Please enter a non-negative number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    wan1_active = 0
    wan1_inactive = 0
    
    if wan1_total > 0:
        while True:
            try:
                wan1_active = int(input(f"How many WAN1 devices should be ACTIVE? (max {wan1_total}): "))
                if wan1_active < 0 or wan1_active > wan1_total:
                    print(f"Please enter a number between 0 and {wan1_total}.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")
        
        wan1_inactive = wan1_total - wan1_active
    
    # Get WAN2 configuration
    print("\n📡 WAN2 Configuration:")
    while True:
        try:
            wan2_total = int(input("How many WAN2 devices do you want? "))
            if wan2_total < 0:
                print("Please enter a non-negative number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    wan2_active = 0
    wan2_inactive = 0
    
    if wan2_total > 0:
        while True:
            try:
                wan2_active = int(input(f"How many WAN2 devices should be ACTIVE? (max {wan2_total}): "))
                if wan2_active < 0 or wan2_active > wan2_total:
                    print(f"Please enter a number between 0 and {wan2_total}.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")
        
        wan2_inactive = wan2_total - wan2_active
    
    # Get Cellular configuration (optional)
    print("\n📱 Cellular Configuration (optional):")
    while True:
        try:
            cellular_total = int(input("How many Cellular devices do you want? (0 to skip): "))
            if cellular_total < 0:
                print("Please enter a non-negative number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    cellular_active = 0
    cellular_inactive = 0
    
    if cellular_total > 0:
        while True:
            try:
                cellular_active = int(input(f"How many Cellular devices should be ACTIVE? (max {cellular_total}): "))
                if cellular_active < 0 or cellular_active > cellular_total:
                    print(f"Please enter a number between 0 and {cellular_total}.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")
        
        cellular_inactive = cellular_total - cellular_active
    
    return {
        'wan1_active': wan1_active,
        'wan1_inactive': wan1_inactive,
        'wan2_active': wan2_active,
        'wan2_inactive': wan2_inactive,
        'cellular_active': cellular_active,
        'cellular_inactive': cellular_inactive
    }

def generate_devices(config):
    """Generate devices based on configuration"""
    devices = []
    
    # Generate WAN1 devices
    for _ in range(config['wan1_active']):
        device = generate_device_with_uplinks(1, 0, 0, 0)  # 1 WAN1 active, 0 others
        devices.append(device)
        print(f"✅ Generated WAN1 ACTIVE device: {device['serial']} ({device['model']})")
    
    for _ in range(config['wan1_inactive']):
        device = generate_device_with_uplinks(0, 1, 0, 0)  # 1 WAN1 inactive, 0 others
        devices.append(device)
        print(f"✅ Generated WAN1 INACTIVE device: {device['serial']} ({device['model']})")
    
    # Generate WAN2 devices
    for _ in range(config['wan2_active']):
        device = generate_device_with_uplinks(0, 0, 1, 0)  # 1 WAN2 active, 0 others
        devices.append(device)
        print(f"✅ Generated WAN2 ACTIVE device: {device['serial']} ({device['model']})")
    
    for _ in range(config['wan2_inactive']):
        device = generate_device_with_uplinks(0, 0, 0, 1)  # 1 WAN2 inactive, 0 others
        devices.append(device)
        print(f"✅ Generated WAN2 INACTIVE device: {device['serial']} ({device['model']})")
    
    # Generate Cellular devices
    for _ in range(config['cellular_active']):
        device = generate_device_with_uplinks(0, 0, 0, 0)  # No WAN uplinks
        device['uplinks'] = [generate_uplink_interface("cellular", "active")]
        devices.append(device)
        print(f"✅ Generated Cellular ACTIVE device: {device['serial']} ({device['model']})")
    
    for _ in range(config['cellular_inactive']):
        device = generate_device_with_uplinks(0, 0, 0, 0)  # No WAN uplinks
        device['uplinks'] = [generate_uplink_interface("cellular", "not connected")]
        devices.append(device)
        print(f"✅ Generated Cellular INACTIVE device: {device['serial']} ({device['model']})")
    
    return devices

def add_uplink_devices():
    """Main function to add uplink devices"""
    # Get user configuration
    config = get_user_input()
    
    total_devices = (config['wan1_active'] + config['wan1_inactive'] + 
                    config['wan2_active'] + config['wan2_inactive'] + 
                    config['cellular_active'] + config['cellular_inactive'])
    
    if total_devices == 0:
        print("❌ No devices to generate. Exiting.")
        return
    
    print(f"\n📊 Generating {total_devices} devices with specified configuration...")
    print(f"   - WAN1: {config['wan1_active']} active, {config['wan1_inactive']} inactive")
    print(f"   - WAN2: {config['wan2_active']} active, {config['wan2_inactive']} inactive")
    print(f"   - Cellular: {config['cellular_active']} active, {config['cellular_inactive']} inactive")
    print()
    
    # Load existing data
    try:
        with open('mock_data/comprehensive_api_data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: comprehensive_api_data.json not found!")
        return
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON in comprehensive_api_data.json!")
        return
    
    # Generate new devices
    new_devices = generate_devices(config)
    
    # Add to existing data
    if 'organization_uplinks_statuses' not in data:
        data['organization_uplinks_statuses'] = {}
    
    if '999781' not in data['organization_uplinks_statuses']:
        data['organization_uplinks_statuses']['999781'] = []
    
    # Add new devices
    data['organization_uplinks_statuses']['999781'].extend(new_devices)
    
    # Save updated data
    try:
        with open('mock_data/comprehensive_api_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n🎉 Successfully added {total_devices} uplink devices!")
        print(f"📈 Total devices now: {len(data['organization_uplinks_statuses']['999781'])}")
        
        # Show summary
        active_count = sum(1 for device in data['organization_uplinks_statuses']['999781'] 
                          for uplink in device['uplinks'] if uplink['status'] == 'active')
        inactive_count = sum(1 for device in data['organization_uplinks_statuses']['999781'] 
                            for uplink in device['uplinks'] if uplink['status'] != 'active')
        
        print(f"\n📊 Final Summary:")
        print(f"   - Active uplinks: {active_count}")
        print(f"   - Inactive uplinks: {inactive_count}")
        print(f"   - Total devices: {len(data['organization_uplinks_statuses']['999781'])}")
        
        # Show breakdown by interface type
        wan1_active = sum(1 for device in data['organization_uplinks_statuses']['999781'] 
                         for uplink in device['uplinks'] 
                         if uplink['interface'] == 'wan1' and uplink['status'] == 'active')
        wan1_inactive = sum(1 for device in data['organization_uplinks_statuses']['999781'] 
                           for uplink in device['uplinks'] 
                           if uplink['interface'] == 'wan1' and uplink['status'] != 'active')
        wan2_active = sum(1 for device in data['organization_uplinks_statuses']['999781'] 
                         for uplink in device['uplinks'] 
                         if uplink['interface'] == 'wan2' and uplink['status'] == 'active')
        wan2_inactive = sum(1 for device in data['organization_uplinks_statuses']['999781'] 
                           for uplink in device['uplinks'] 
                           if uplink['interface'] == 'wan2' and uplink['status'] != 'active')
        cellular_active = sum(1 for device in data['organization_uplinks_statuses']['999781'] 
                             for uplink in device['uplinks'] 
                             if uplink['interface'] == 'cellular' and uplink['status'] == 'active')
        cellular_inactive = sum(1 for device in data['organization_uplinks_statuses']['999781'] 
                               for uplink in device['uplinks'] 
                               if uplink['interface'] == 'cellular' and uplink['status'] != 'active')
        
        print(f"\n📋 Interface Breakdown:")
        print(f"   - WAN1: {wan1_active} active, {wan1_inactive} inactive")
        print(f"   - WAN2: {wan2_active} active, {wan2_inactive} inactive")
        print(f"   - Cellular: {cellular_active} active, {cellular_inactive} inactive")
        
    except Exception as e:
        print(f"❌ Error saving data: {e}")

if __name__ == "__main__":
    add_uplink_devices()
