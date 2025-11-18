import meraki
import json
import time

# ================================
# CONFIG
# ================================
API_KEY = "79c93183a13575a8a8f60c791c8530e6eacbc54a"
ORG_ID = "999781"    # your org ID

dashboard = meraki.DashboardAPI(API_KEY, print_console=False)

# ================================
# Helper Function
# ================================
def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")

# ================================
# 1. Get All Devices
# ================================
print("Fetching organization devices...")
devices = dashboard.organizations.getOrganizationDevices(ORG_ID)
print(f"Found {len(devices)} devices\n")

# ================================
# 2. Choose Device: Prefer MR → fallback MX
# ================================
selected_serial = None
network_id = None
device_type = None

# First priority: wireless AP (MR)
for d in devices:
    if d.get("productType") == "wireless":
        selected_serial = d["serial"]
        device_type = "wireless"
        network_id = d.get("network", {}).get("id")
        break

# Second priority: appliance (MX)
if not selected_serial:
    for d in devices:
        if d.get("productType") == "appliance":
            selected_serial = d["serial"]
            device_type = "appliance"
            network_id = d.get("network", {}).get("id")
            break

# If still nothing, use first device
if not selected_serial:
    d = devices[0]
    selected_serial = d["serial"]
    device_type = d.get("productType", "unknown")
    network_id = d.get("network", {}).get("id")

print_section("Selected Device")
print(json.dumps({
    "serial": selected_serial,
    "device_type": device_type,
    "network_id": network_id
}, indent=2))

time.sleep(1)

# ================================================================
# 3. Wireless Metrics (if MR)
# ================================================================
if device_type == "wireless":
    print_section("1. Device Wireless Status")
    try:
        wireless_status = dashboard.wireless.getDeviceWirelessStatus(selected_serial)
        print(json.dumps(wireless_status, indent=2))
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(1)

    # Jitter, latency, packet loss history
    print_section("2. Wireless Latency & Jitter History")
    try:
        metrics = dashboard.wireless.getNetworkWirelessLatencyHistory(
            network_id,
            timespan=3600,  # last 1 hour
            resolution=300  # 5 min buckets
        )
        print(json.dumps(metrics[:5], indent=2))
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(1)

    # Wireless connection failures
    print_section("3. Wireless Connection Failures")
    try:
        failures = dashboard.wireless.getNetworkWirelessFailedConnections(
            network_id,
            timespan=3600
        )
        print(json.dumps(failures[:5], indent=2))
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(1)

else:
    print_section("Device is not wireless → Skipping wireless metrics")

# ================================================================
# 4. Network Clients
# ================================================================
print_section("4. Network Clients")
try:
    clients = dashboard.networks.getNetworkClients(
        network_id,
        total_pages='all'
    )
    print(json.dumps(clients[:5], indent=2))
    print(f"\nTotal clients: {len(clients)}")
except Exception as e:
    print(f"Error: {e}")

time.sleep(1)

# ================================================================
# 5. Network Events (Correct productType)
# ================================================================
print_section("5. Network Events")

# Choose correct productType for events
event_type = "wireless" if device_type == "wireless" else "appliance"

try:
    events = dashboard.networks.getNetworkEvents(
        network_id,
        productType=event_type,
        perPage=10
    )
    print(json.dumps(events.get("events", [])[:10], indent=2))
except Exception as e:
    print(f"Error: {e}")

time.sleep(1)

# ================================================================
# 6. Uplink (WAN) status for MX
# ================================================================
print_section("6. Device Uplink Status (MX only)")

try:
    uplink = dashboard.devices.getDeviceUplink(selected_serial)
    print(json.dumps(uplink, indent=2))
except:
    print("No uplink data (likely an MR device)")

time.sleep(1)

# ================================================================
# 7. WAN Loss & Latency History (MX only)
# ================================================================
print_section("7. Uplink Loss & Latency History")

try:
    loss_latency = dashboard.appliance.getDeviceLossAndLatencyHistory(
        selected_serial,
        uplink='wan1',
        timespan=3600,
        resolution=300
    )
    print(json.dumps(loss_latency[:5], indent=2))
except Exception as e:
    print(f"Error: {e}")

time.sleep(1)

print("\n" + "="*60)
print("Collection Complete")
print("="*60)
