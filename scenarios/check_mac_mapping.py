import json

with open('../mock_data/comprehensive_api_data.json') as f:
    data = json.load(f)

# Get AP devices
devices = data.get('organization_devices', {}).get('999781', [])
aps = [d for d in devices if d.get('model', '').startswith('MR')]

print("AP Serial to MAC Mapping:")
print("-" * 60)
for ap in aps:
    serial = ap.get('serial', 'N/A')
    mac = ap.get('mac', 'N/A')
    print(f"{serial:20} -> {mac}")

print("\nLatency History MACs:")
print("-" * 60)
latency = data.get('network_wireless_latency_history', {}).get('L_3947405073390239794', [])
macs = set([e.get('deviceMac') for e in latency])
for mac in sorted(macs):
    print(f"  {mac}")
