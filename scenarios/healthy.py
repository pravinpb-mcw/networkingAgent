#!/usr/bin/env python3
"""
SCENARIO 1: HEALTHY NETWORK - All Systems Operational
Resets all network metrics to healthy baseline values.
This is the baseline state for demos and testing.

Metrics:
- Latency: ~12-15ms (excellent)
- Packet Loss: 0.05-0.15% (minimal)
- Jitter: 1-3ms (stable)
- Goodput: 94-96%
- Channel Utilization: 25-32% (comfortable)
- SNR: 33-36dB (excellent)
- All uplinks: active
- All clients: online

This scenario demonstrates a fully healthy network state.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import aiohttp

# Configuration
MOCK_SERVER_URL = "http://127.0.0.1:5000"
NETWORK_ID = "L_3947405073390239794"
ORGANIZATION_ID = "999781"
DEVICE_SERIAL = "Q2MN-Q3J9-YJHW"
AP_SERIAL = "Q2XX-ABCD-1234"

# All APs in the network with excellent healthy states (all below risk 20)
ALL_APS = [
    {"serial": "Q2XX-ABCD-1234", "name": "AP-03", "mac": "00:11:22:33:44:55", "health": "excellent"},      # Risk ~12-14
    {"serial": "Q2XX-AP06-5678", "name": "AP-06", "mac": "00:11:22:33:44:99", "health": "very_good"},     # Risk ~14-16
    {"serial": "Q2XX-AP01-1111", "name": "AP-01", "mac": "00:11:22:33:44:11", "health": "good"},          # Risk ~16-18
    {"serial": "Q2XX-AP04-4444", "name": "AP-04", "mac": "00:11:22:33:44:44", "health": "above_average"}, # Risk ~17-19
    {"serial": "Q2XX-AP08-8888", "name": "AP-08", "mac": "00:11:22:33:44:88", "health": "average"}        # Risk ~18-19
]

# Health profiles - all optimized for scores below 20
HEALTH_PROFILES = {
    "excellent": {
        "channelUtilizationPercent": 18.0,
        "retransmissionsPerMinute": 1,
        "avgSignalToNoise": 38.0,
        "avgRssi": -45,
        "clientCount": 6,
        "latencyMs": 7,
        "jitterMs": 0.8,
        "packetLossPercent": 0.03
    },
    "very_good": {
        "channelUtilizationPercent": 24.0,
        "retransmissionsPerMinute": 2,
        "avgSignalToNoise": 36.5,
        "avgRssi": -50,
        "clientCount": 9,
        "latencyMs": 9,
        "jitterMs": 1.5,
        "packetLossPercent": 0.06
    },
    "good": {
        "channelUtilizationPercent": 30.0,
        "retransmissionsPerMinute": 4,
        "avgSignalToNoise": 35.0,
        "avgRssi": -53,
        "clientCount": 12,
        "latencyMs": 12,
        "jitterMs": 2.0,
        "packetLossPercent": 0.10
    },
    "above_average": {
        "channelUtilizationPercent": 36.0,
        "retransmissionsPerMinute": 6,
        "avgSignalToNoise": 33.5,
        "avgRssi": -56,
        "clientCount": 14,
        "latencyMs": 15,
        "jitterMs": 3.0,
        "packetLossPercent": 0.15
    },
    "average": {
        "channelUtilizationPercent": 40.0,
        "retransmissionsPerMinute": 8,
        "avgSignalToNoise": 32.0,
        "avgRssi": -58,
        "clientCount": 16,
        "latencyMs": 18,
        "jitterMs": 4.0,
        "packetLossPercent": 0.20
    }
}

# Healthy baseline values
HEALTHY_METRICS = {
    "latencyMs": 15.5,
    "packetLossPct": 0.1,
    "jitterMs": 1.2,
    "goodput": 95.0
}

# Healthy wireless metrics (baseline for all APs)
HEALTHY_WIRELESS = {
    "channelUtilizationPercent": 28.0,
    "airtimeUtilizationPercent": 30.5,
    "retransmissionsPerMinute": 3,
    "avgSignalToNoise": 34.5,
    "avgRssi": -52,
    "clientCount": 12,
    "uplinkSpeedMbps": 920,
    "downlinkSpeedMbps": 890
}


class HealthyScenario:
    """Restores network to fully healthy state"""
    
    def __init__(self):
        self.session = None
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
        print("🔧 Healthy Scenario Initialized")
        print("="*60)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    async def update_appliance_settings(self):
        """Update appliance settings to healthy state"""
        settings = {
            "latencyMs": HEALTHY_METRICS["latencyMs"],
            "packetLossPct": HEALTHY_METRICS["packetLossPct"],
            "jitterMs": HEALTHY_METRICS["jitterMs"],
            "degradedLinks": [
                {"uplink": "wan1", "status": "active"},
                {"uplink": "wan2", "status": "active"}
            ],
            "updated_at": datetime.now().isoformat(),
            "note": "SCENARIO_1_HEALTHY"
        }
        
        url = f"{MOCK_SERVER_URL}/networks/{NETWORK_ID}/appliance/settings"
        
        try:
            async with self.session.post(url, json=settings) as response:
                if response.status == 200:
                    print("✅ APPLIANCE SETTINGS: HEALTHY")
                    print(f"   └─ Latency: {settings['latencyMs']}ms ✅")
                    print(f"   └─ Packet Loss: {settings['packetLossPct']}% ✅")
                    print(f"   └─ Jitter: {settings['jitterMs']}ms ✅")
                    print(f"   └─ WAN1: active ✅, WAN2: active ✅")
                else:
                    print(f"⚠️  Failed to update: {response.status}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def update_mock_data(self):
        """Update comprehensive mock data to healthy state"""
        try:
            import os
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mock_file = os.path.join(script_dir, 'mock_data', 'comprehensive_api_data.json')
            with open(mock_file, 'r') as f:
                data = json.load(f)
            
            # 1. Update network appliance settings
            if "networks" in data and NETWORK_ID in data["networks"]:
                network = data["networks"][NETWORK_ID]
                if "appliance_settings" in network and len(network["appliance_settings"]) > 0:
                    network["appliance_settings"][0].update({
                        "latencyMs": HEALTHY_METRICS["latencyMs"],
                        "packetLossPct": HEALTHY_METRICS["packetLossPct"],
                        "jitterMs": HEALTHY_METRICS["jitterMs"],
                        "degradedLinks": [
                            {"uplink": "wan1", "status": "active"},
                            {"uplink": "wan2", "status": "active"}
                        ],
                        "updated_at": datetime.now().isoformat(),
                        "note": "SCENARIO_1_HEALTHY"
                    })
            
            # 2. Reset device loss and latency history
            data["device_loss_and_latency_history"] = {
                DEVICE_SERIAL: []
            }
            for i in range(10):
                entry = {
                    "ts": datetime.now().isoformat(),
                    "latencyMs": HEALTHY_METRICS["latencyMs"],
                    "lossPercent": HEALTHY_METRICS["packetLossPct"],
                    "jitter": HEALTHY_METRICS["jitterMs"],
                    "goodput": HEALTHY_METRICS["goodput"],
                    "destinationIp": "8.8.8.8",
                    "note": "SCENARIO_1_HEALTHY"
                }
                data["device_loss_and_latency_history"][DEVICE_SERIAL].append(entry)
            
            # 3. Ensure ALL APs have healthy baseline data in wireless usage history
            if "network_wireless_usage_history" not in data:
                data["network_wireless_usage_history"] = {}
            if NETWORK_ID not in data["network_wireless_usage_history"]:
                data["network_wireless_usage_history"][NETWORK_ID] = []
            
            # Remove old entries for all APs we're resetting
            existing_history = data["network_wireless_usage_history"][NETWORK_ID]
            ap_serials_to_reset = [ap["serial"] for ap in ALL_APS]
            other_history = [entry for entry in existing_history if entry.get("deviceSerial") not in ap_serials_to_reset]
            
            # Create fresh healthy data for ALL APs with different health profiles
            base_time = datetime.now() - timedelta(minutes=30)
            all_aps_healthy_entries = []
            
            for ap in ALL_APS:
                # Get health profile for this AP
                profile = HEALTH_PROFILES[ap["health"]]
                
                for i in range(6):
                    bucket_start = base_time + timedelta(minutes=i*5)
                    bucket_end = bucket_start + timedelta(minutes=5)
                    
                    # Add slight time-based variation
                    variation = (i % 3) - 1  # -1, 0, 1
                    
                    entry = {
                        "bucketStart": bucket_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "bucketEnd": bucket_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "deviceSerial": ap["serial"],
                        "ssid": "MCW-SanJose",
                        "channelUtilizationPercent": round(profile["channelUtilizationPercent"] + variation * 2, 1),
                        "airtimeUtilizationPercent": round(profile["channelUtilizationPercent"] + variation * 2.5, 1),
                        "retransmissionsPerMinute": max(1, profile["retransmissionsPerMinute"] + variation),
                        "avgSignalToNoise": round(profile["avgSignalToNoise"] + variation * 0.5, 1),
                        "avgRssi": profile["avgRssi"] + variation,
                        "clientCount": max(1, profile["clientCount"] + variation),
                        "uplinkSpeedMbps": 920 - int(profile["channelUtilizationPercent"] * 3),
                        "downlinkSpeedMbps": 890 - int(profile["channelUtilizationPercent"] * 3),
                        "note": "SCENARIO_1_HEALTHY"
                    }
                    all_aps_healthy_entries.append(entry)
            
            # Combine: other data + all APs' healthy data
            data["network_wireless_usage_history"][NETWORK_ID] = other_history + all_aps_healthy_entries
            
            # 4. Ensure ALL APs have healthy latency history
            if "network_wireless_latency_history" not in data:
                data["network_wireless_latency_history"] = {}
            if NETWORK_ID not in data["network_wireless_latency_history"]:
                data["network_wireless_latency_history"][NETWORK_ID] = []
            
            # Remove old entries for all APs we're resetting
            existing_latency = data["network_wireless_latency_history"][NETWORK_ID]
            ap_macs_to_reset = [ap["mac"] for ap in ALL_APS]
            other_latency = [entry for entry in existing_latency if entry.get("deviceMac") not in ap_macs_to_reset]
            
            # Create fresh healthy latency data for ALL APs with different profiles
            all_aps_latency_entries = []
            for ap in ALL_APS:
                profile = HEALTH_PROFILES[ap["health"]]
                
                for i in range(6):
                    slot_start = base_time + timedelta(minutes=i*5)
                    slot_end = slot_start + timedelta(minutes=5)
                    
                    variation = (i % 3) - 1
                    
                    entry = {
                        "timeslotStart": slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "timeslotEnd": slot_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "latencyMs": max(5, profile["latencyMs"] + variation * 2),
                        "jitterMs": max(1, profile["jitterMs"] + variation),
                        "packetLossPercent": round(max(0.01, profile["packetLossPercent"] + variation * 0.05), 2),
                        "deviceMac": ap["mac"],
                        "note": "SCENARIO_1_HEALTHY"
                    }
                    all_aps_latency_entries.append(entry)
            
            # Combine: other data + all APs' healthy data
            data["network_wireless_latency_history"][NETWORK_ID] = other_latency + all_aps_latency_entries
            
            # 5. Reset wireless health
            data["network_wireless_health"] = {
                NETWORK_ID: {
                    "windowStart": (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "windowEnd": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "overallHealthScore": 95,
                    "coverage": {
                        "clientsBelowSNRThreshold": 0,
                        "worstSNR": 32.5,
                        "medianSNR": 35.1
                    },
                    "performance": {
                        "avgLatencyMs": 12,
                        "avgJitterMs": 2,
                        "avgPacketLossPercent": 0.1
                    },
                    "capacity": {
                        "overutilizedRadios": 0,
                        "avgChannelUtilizationPercent": 28.0,
                        "avgAirtimeUtilizationPercent": 30.5
                    },
                    "clientExperience": {
                        "dhcpFailures": 0,
                        "authFailures": 0,
                        "healthScore": 96
                    },
                    "bestApRecommendation": None,
                    "note": "SCENARIO_1_HEALTHY"
                }
            }
            
            # 6. Clear failed connections for ALL APs
            if "network_wireless_failed_connections" not in data:
                data["network_wireless_failed_connections"] = {}
            if NETWORK_ID in data["network_wireless_failed_connections"]:
                # Remove failed connections for all APs we're resetting
                ap_serials_to_reset = [ap["serial"] for ap in ALL_APS]
                existing_failures = data["network_wireless_failed_connections"][NETWORK_ID]
                data["network_wireless_failed_connections"][NETWORK_ID] = [
                    entry for entry in existing_failures 
                    if entry.get("deviceSerial") not in ap_serials_to_reset
                ]
            else:
                data["network_wireless_failed_connections"][NETWORK_ID] = []
            
            # 7. Reset topology link layer with ALL APs
            data["network_topology_link_layer"] = {
                NETWORK_ID: {
                    "nodes": [
                        {"type": "appliance", "id": DEVICE_SERIAL, "name": "San Jose MX64", "uplink": "wan1", "status": "online"}
                    ],
                    "links": []
                }
            }
            
            # Add all APs as nodes
            for ap in ALL_APS:
                data["network_topology_link_layer"][NETWORK_ID]["nodes"].append({
                    "type": "wireless",
                    "id": ap["serial"],
                    "name": ap["name"],
                    "floorPlanId": "FP-FLR1",
                    "status": "healthy"
                })
            
            # Add links from appliance to each AP
            for ap in ALL_APS:
                data["network_topology_link_layer"][NETWORK_ID]["links"].append({
                    "source": DEVICE_SERIAL,
                    "target": ap["serial"],
                    "linkType": "wired",
                    "status": "ok",
                    "latencyMs": 3,
                    "lossPercent": 0.05
                })
            
            # Add mesh links between APs
            for i in range(len(ALL_APS) - 1):
                data["network_topology_link_layer"][NETWORK_ID]["links"].append({
                    "source": ALL_APS[i]["serial"],
                    "target": ALL_APS[i+1]["serial"],
                    "linkType": "wireless-mesh",
                    "status": "ok",
                    "latencyMs": 5,
                    "lossPercent": 0.1
                })
            
            # 8. Reset floor plans stability score for ALL APs
            data["network_floor_plans"] = {
                NETWORK_ID: [{
                    "floorPlanId": "FP-FLR1",
                    "name": "San Jose HQ - Floor 1",
                    "center": {"lat": 37.4232, "lng": -122.0841},
                    "apCoordinates": []
                }]
            }
            
            # Add coordinates for all APs
            for i, ap in enumerate(ALL_APS):
                data["network_floor_plans"][NETWORK_ID][0]["apCoordinates"].append({
                    "deviceSerial": ap["serial"],
                    "x": 12.4 + i * 10,  # Space them out horizontally
                    "y": 6.1 + (i % 2) * 5,  # Alternate vertically
                    "rfCoverageMeters": 25,
                    "historicalStabilityScore": 94 - i  # Slight variation
                })
            
            # 9. Reset service impact predictions
            data["service_impact_predictions"] = {
                NETWORK_ID: {
                    "sourceAp": None,
                    "sourceApSerial": None,
                    "window": f"{(datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')}/{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                    "usersImpacted": 0,
                    "failureProbability": 0.02,
                    "recoveryLikelihood": "N/A",
                    "recoveryReason": "Network operating at optimal levels - no issues detected",
                    "estimatedTimeToFailure": "Not applicable",
                    "interventionPriority": "NONE",
                    "recommendedFallbackAp": None,
                    "reason": "Network operating normally - all metrics within healthy thresholds",
                    "applications": [
                        {"name": "Teams Video", "activeUserPercent": 62, "impactLevel": "none", "notes": "Operating normally - excellent quality"},
                        {"name": "VOIP", "activeUserPercent": 15, "impactLevel": "none", "notes": "Operating normally - crystal clear"},
                        {"name": "SSH Sessions", "activeUserPercent": 8, "impactLevel": "none", "notes": "Operating normally - responsive"},
                        {"name": "Email", "activeUserPercent": 20, "impactLevel": "none", "notes": "Operating normally"},
                        {"name": "File Transfers", "activeUserPercent": 12, "impactLevel": "none", "notes": "Operating normally - fast transfers"}
                    ],
                    "trendAnalysis": {
                        "channelUtilization": {"start": 26, "end": 28, "change": 8, "trend": "STABLE"},
                        "airtimeUtilization": {"start": 29, "end": 30.5, "change": 5, "trend": "STABLE"},
                        "retransmissions": {"start": 3, "end": 3, "change": 0, "trend": "STABLE"},
                        "signalSNR": {"start": 34.5, "end": 34.5, "change": 0, "trend": "STABLE"},
                        "uplinkSpeed": {"start": 920, "end": 920, "change": 0, "trend": "STABLE"},
                        "downlinkSpeed": {"start": 890, "end": 890, "change": 0, "trend": "STABLE"},
                        "clientLoad": {"start": 12, "end": 12, "change": 0, "trend": "STABLE"},
                        "pattern": "HEALTHY BASELINE - All metrics stable within optimal ranges"
                    },
                    "currentThresholds": {
                        "latency": {"value": 15, "threshold": 60, "status": "EXCELLENT"},
                        "jitter": {"value": 1.2, "threshold": 20, "status": "EXCELLENT"},
                        "packetLoss": {"value": 0.1, "threshold": 3.0, "status": "EXCELLENT"}
                    },
                    "failoverCandidates": [],
                    "executionPlan": [
                        {"step": 1, "action": "NO_ACTION_REQUIRED", "description": "Network healthy, continue normal monitoring"}
                    ],
                    "note": "SCENARIO_1_HEALTHY"
                }
            }
            
            # 10. Set all clients online
            if "network_clients" in data and NETWORK_ID in data["network_clients"]:
                for client in data["network_clients"][NETWORK_ID]:
                    client["status"] = "Online"
                    client["lastSeen"] = datetime.now().isoformat()
            
            # 11. Set all uplinks active
            if "organization_uplinks_statuses" in data and ORGANIZATION_ID in data["organization_uplinks_statuses"]:
                for device in data["organization_uplinks_statuses"][ORGANIZATION_ID]:
                    if device.get("networkId") == NETWORK_ID:
                        for uplink in device.get("uplinks", []):
                            uplink["status"] = "active"
                        device["lastReportedAt"] = datetime.now().isoformat()
            
            # Write back
            with open(mock_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print("✅ WIRELESS USAGE HISTORY: RESET TO HEALTHY")
            print(f"   └─ All {len(ALL_APS)} APs reset with excellent healthy baselines")
            print(f"      • AP-03: Excellent (18% util, 38dB SNR, 1 retrans/min) → Risk ~13")
            print(f"      • AP-06: Very Good (24% util, 36.5dB SNR, 2 retrans/min) → Risk ~15")
            print(f"      • AP-01: Good (30% util, 35dB SNR, 4 retrans/min) → Risk ~17")
            print(f"      • AP-04: Above Average (36% util, 33.5dB SNR, 6 retrans/min) → Risk ~18")
            print(f"      • AP-08: Average (40% util, 32dB SNR, 8 retrans/min) → Risk ~19")
            print("✅ WIRELESS LATENCY HISTORY: RESET TO HEALTHY")
            print(f"   └─ All {len(ALL_APS)} APs have baseline latency data")
            print(f"   └─ Latency: ~10-13ms")
            print(f"   └─ Jitter: ~1-3ms")
            print(f"   └─ Packet Loss: ~0.05-0.15%")
            print("✅ WIRELESS HEALTH: RESET TO HEALTHY")
            print(f"   └─ Health Score: 95")
            print("✅ SERVICE IMPACT: CLEARED")
            print(f"   └─ Failure Probability: 2%")
            print("✅ CLIENTS: ALL ONLINE")
            print("✅ UPLINKS: ALL ACTIVE")
            
        except Exception as e:
            print(f"❌ Error updating mock data: {e}")
            import traceback
            traceback.print_exc()
    
    async def run_scenario(self):
        """Run the healthy scenario"""
        print("\n🟢 SCENARIO 1: HEALTHY NETWORK")
        print("="*60)
        print("Resetting all metrics to healthy baseline...")
        print("-"*60)
        
        await self.update_appliance_settings()
        await self.update_mock_data()
        
        print("\n" + "="*60)
        print("✅ SCENARIO 1 APPLIED: HEALTHY NETWORK")
        print("="*60)
        print("\n📋 NETWORK STATE SUMMARY:")
        print("-"*60)
        print(f"  Latency:           {HEALTHY_METRICS['latencyMs']}ms     ✅ EXCELLENT")
        print(f"  Packet Loss:       {HEALTHY_METRICS['packetLossPct']}%      ✅ MINIMAL")
        print(f"  Jitter:            {HEALTHY_METRICS['jitterMs']}ms      ✅ STABLE")
        print(f"  Goodput:           {HEALTHY_METRICS['goodput']}%     ✅ OPTIMAL")
        print(f"  Channel Util:      ~28%         ✅ COMFORTABLE")
        print(f"  SNR:               ~34.5dB      ✅ EXCELLENT")
        print(f"  Retransmissions:   ~3/min       ✅ MINIMAL")
        print(f"  Uplinks:           ALL ACTIVE   ✅")
        print(f"  Clients:           ALL ONLINE   ✅")
        print(f"  Health Score:      95           ✅")
        print("-"*60)
        print("\n💡 Expected Agent Response: ALL APs HEALTHY (Risk Scores: 13-19)")
        print("   → All APs below risk 20 threshold")
        print("   → Network operating optimally with excellent health")
        print("="*60)


async def main():
    """Main entry point"""
    scenario = HealthyScenario()
    
    try:
        await scenario.initialize()
        await scenario.run_scenario()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scenario interrupted by user")
    except Exception as e:
        print(f"\n❌ Scenario failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scenario.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           SCENARIO 1: HEALTHY NETWORK                        ║
║                                                              ║
║  This script resets the network to healthy baseline:        ║
║    • Latency: ~12-15ms (excellent)                          ║
║    • Packet Loss: 0.05-0.15% (minimal)                      ║
║    • Jitter: 1-3ms (stable)                                 ║
║    • Channel Utilization: ~28% (comfortable)                ║
║    • SNR: ~34.5dB (excellent)                               ║
║    • All uplinks: active                                    ║
║    • All clients: online                                    ║
║                                                              ║
║  Expected Agent Classification: STABLE (Low Risk)           ║
║  → Use this to reset after running failure scenarios        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
