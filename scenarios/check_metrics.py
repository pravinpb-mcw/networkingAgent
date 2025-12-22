import json

with open('../mock_data/comprehensive_api_data.json') as f:
    data = json.load(f)

usage = data['network_wireless_usage_history']['L_3947405073390239794']

aps = {}
for e in usage:
    serial = e['deviceSerial']
    if serial not in aps:
        aps[serial] = []
    aps[serial].append(e)

print("Latest metrics for each AP:")
print("-" * 80)
for serial in sorted(aps.keys()):
    latest = aps[serial][-1]
    print(f"{serial:20} util={latest['channelUtilizationPercent']:5.1f}%  "
          f"snr={latest['avgSignalToNoise']:5.1f}dB  "
          f"retrans={latest['retransmissionsPerMinute']:3d}/min")
