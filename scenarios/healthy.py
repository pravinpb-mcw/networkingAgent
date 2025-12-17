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

# Healthy baseline values
HEALTHY_METRICS = {
    "latencyMs": 15.5,
    "packetLossPct": 0.1,
    "jitterMs": 1.2,
    "goodput": 95.0
}

# Healthy wireless metrics
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
            
            # 3. Reset wireless usage history (KEY FOR PREDICTIVE AGENT)
            data["network_wireless_usage_history"] = {
                NETWORK_ID: []
            }
            base_time = datetime.now() - timedelta(minutes=30)
            for i in range(6):
                bucket_start = base_time + timedelta(minutes=i*5)
                bucket_end = bucket_start + timedelta(minutes=5)
                entry = {
                    "bucketStart": bucket_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "bucketEnd": bucket_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "deviceSerial": AP_SERIAL,
                    "ssid": "MCW-SanJose",
                    "channelUtilizationPercent": round(HEALTHY_WIRELESS["channelUtilizationPercent"] + (i % 3) * 1.5, 1),
                    "airtimeUtilizationPercent": round(HEALTHY_WIRELESS["airtimeUtilizationPercent"] + (i % 3) * 1.2, 1),
                    "retransmissionsPerMinute": HEALTHY_WIRELESS["retransmissionsPerMinute"] + (i % 2),
                    "avgSignalToNoise": round(HEALTHY_WIRELESS["avgSignalToNoise"] - (i % 2) * 0.5, 1),
                    "avgRssi": HEALTHY_WIRELESS["avgRssi"] - (i % 2),
                    "clientCount": HEALTHY_WIRELESS["clientCount"] + (i % 3),
                    "uplinkSpeedMbps": HEALTHY_WIRELESS["uplinkSpeedMbps"] - (i % 3) * 10,
                    "downlinkSpeedMbps": HEALTHY_WIRELESS["downlinkSpeedMbps"] - (i % 3) * 8,
                    "note": "SCENARIO_1_HEALTHY"
                }
                data["network_wireless_usage_history"][NETWORK_ID].append(entry)
            
            # 4. Reset wireless latency history
            data["network_wireless_latency_history"] = {
                NETWORK_ID: []
            }
            for i in range(6):
                slot_start = base_time + timedelta(minutes=i*5)
                slot_end = slot_start + timedelta(minutes=5)
                entry = {
                    "timeslotStart": slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "timeslotEnd": slot_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "latencyMs": 10 + (i % 3),
                    "jitterMs": 1 + (i % 2),
                    "packetLossPercent": round(0.05 + (i % 3) * 0.03, 2),
                    "deviceMac": "00:11:22:33:44:55",
                    "note": "SCENARIO_1_HEALTHY"
                }
                data["network_wireless_latency_history"][NETWORK_ID].append(entry)
            
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
            
            # 6. Clear failed connections
            data["network_wireless_failed_connections"] = {NETWORK_ID: []}
            
            # 7. Reset topology link layer
            data["network_topology_link_layer"] = {
                NETWORK_ID: {
                    "nodes": [
                        {"type": "appliance", "id": DEVICE_SERIAL, "name": "San Jose MX64", "uplink": "wan1", "status": "online"},
                        {"type": "wireless", "id": AP_SERIAL, "name": "AP-03", "floorPlanId": "FP-FLR1", "status": "healthy"},
                        {"type": "wireless", "id": "Q2XX-AP06-5678", "name": "AP-06", "floorPlanId": "FP-FLR1", "status": "healthy"}
                    ],
                    "links": [
                        {"source": DEVICE_SERIAL, "target": AP_SERIAL, "linkType": "wired", "status": "ok", "latencyMs": 3, "lossPercent": 0.05},
                        {"source": DEVICE_SERIAL, "target": "Q2XX-AP06-5678", "linkType": "wired", "status": "ok", "latencyMs": 4, "lossPercent": 0.05},
                        {"source": AP_SERIAL, "target": "Q2XX-AP06-5678", "linkType": "wireless-mesh", "status": "ok", "latencyMs": 5, "lossPercent": 0.1}
                    ]
                }
            }
            
            # 8. Reset floor plans stability score
            data["network_floor_plans"] = {
                NETWORK_ID: [{
                    "floorPlanId": "FP-FLR1",
                    "name": "San Jose HQ - Floor 1",
                    "center": {"lat": 37.4232, "lng": -122.0841},
                    "apCoordinates": [
                        {"deviceSerial": AP_SERIAL, "x": 12.4, "y": 6.1, "rfCoverageMeters": 25, "historicalStabilityScore": 94},
                        {"deviceSerial": "Q2XX-AP06-5678", "x": 35.2, "y": 8.7, "rfCoverageMeters": 25, "historicalStabilityScore": 92}
                    ]
                }]
            }
            
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
            with open('mock_data/comprehensive_api_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print("✅ WIRELESS USAGE HISTORY: RESET TO HEALTHY")
            print(f"   └─ Channel Utilization: ~{HEALTHY_WIRELESS['channelUtilizationPercent']}%")
            print(f"   └─ SNR: ~{HEALTHY_WIRELESS['avgSignalToNoise']}dB")
            print(f"   └─ Retransmissions: ~{HEALTHY_WIRELESS['retransmissionsPerMinute']}/min")
            print("✅ WIRELESS LATENCY HISTORY: RESET TO HEALTHY")
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
        print("\n💡 Expected Agent Response: STABLE (Risk Score: 0-15)")
        print("   → No alerts should be triggered")
        print("   → Network operating normally")
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
