#!/usr/bin/env python3
"""
SCENARIO 4: FULL FAILURE - Everything Degraded
Simulates complete network failure with critical metrics across all dimensions.
This scenario represents imminent or active failure requiring immediate action.

Metrics:
- Latency: 150-500ms (critical)
- Packet Loss: 8-15% (severe)
- Jitter: 40-60ms (critical)
- Goodput: 35-50%
- Channel Utilization: 92-98% (saturated)
- SNR: 15-18dB (critical - below threshold)
- Uplinks: failed or flapping
- Clients: 50%+ offline or unreachable

This scenario demonstrates "LIKELY FAILURE" requiring immediate intervention.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import aiohttp

# Configuration
MOCK_SERVER_URL = "http://127.0.0.1:5000"
NETWORK_ID = "L_3947405073390239794"
ORGANIZATION_ID = "999781"
DEVICE_SERIAL = "Q2MN-Q3J9-YJHW"
AP_SERIAL = "Q2XX-ABCD-1234"

# Critical failure wireless metrics
FAILURE_WIRELESS = {
    "channelUtilizationPercent": 96.0,
    "airtimeUtilizationPercent": 98.5,
    "retransmissionsPerMinute": 55,
    "avgSignalToNoise": 16.5,
    "avgRssi": -71,
    "clientCount": 38,
    "uplinkSpeedMbps": 280,
    "downlinkSpeedMbps": 180
}


class FullFailureScenario:
    """Simulates complete network failure"""
    
    def __init__(self):
        self.session = None
        
        # Critical failure values
        self.failure_values = {
            "latencyMs": 350.0,
            "packetLossPct": 12.0,
            "jitterMs": 55.0,
            "goodput": 42.0
        }
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
        print("🔧 Full Failure Scenario Initialized")
        print("="*60)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    async def update_appliance_settings(self):
        """Update appliance settings with critical failure metrics"""
        settings = {
            "latencyMs": self.failure_values["latencyMs"],
            "packetLossPct": self.failure_values["packetLossPct"],
            "jitterMs": self.failure_values["jitterMs"],
            "degradedLinks": [
                {"uplink": "wan1", "status": "failed"},
                {"uplink": "wan2", "status": "failed"}
            ],
            "updated_at": datetime.now().isoformat(),
            "note": "SCENARIO_4_FULL_FAILURE"
        }
        
        url = f"{MOCK_SERVER_URL}/networks/{NETWORK_ID}/appliance/settings"
        
        try:
            async with self.session.post(url, json=settings) as response:
                if response.status == 200:
                    print(f"🔴 Appliance Settings: CRITICAL FAILURE")
                    print(f"   └─ Latency: {settings['latencyMs']}ms ❌ CRITICAL")
                    print(f"   └─ Packet Loss: {settings['packetLossPct']}% ❌ SEVERE")
                    print(f"   └─ Jitter: {settings['jitterMs']}ms ❌ CRITICAL")
                    print(f"   └─ WAN1: FAILED ❌, WAN2: FAILED ❌")
                else:
                    print(f"⚠️  Failed to update appliance settings: {response.status}")
        except Exception as e:
            print(f"❌ Error updating appliance settings: {e}")
    
    async def update_mock_data(self):
        """Update comprehensive mock data with failure state including wireless telemetry"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            # Update network appliance settings
            if "networks" in data and NETWORK_ID in data["networks"]:
                network = data["networks"][NETWORK_ID]
                if "appliance_settings" in network and len(network["appliance_settings"]) > 0:
                    network["appliance_settings"][0].update({
                        "latencyMs": self.failure_values["latencyMs"],
                        "packetLossPct": self.failure_values["packetLossPct"],
                        "jitterMs": self.failure_values["jitterMs"],
                        "degradedLinks": [
                            {"uplink": "wan1", "status": "failed"},
                            {"uplink": "wan2", "status": "failed"}
                        ],
                        "updated_at": datetime.now().isoformat(),
                        "note": "SCENARIO_4_FULL_FAILURE"
                    })
            
            # Clear history and add failure trend entries
            if "device_loss_and_latency_history" not in data:
                data["device_loss_and_latency_history"] = {}
            
            # Create a degradation history showing progressive failure
            failure_history = []
            base_latency = 50.0
            base_loss = 2.0
            base_jitter = 15.0
            base_goodput = 85.0
            
            # 15 entries showing progressive degradation over time
            for i in range(15):
                progress = i / 14  # 0.0 to 1.0
                
                entry = {
                    "ts": datetime.now().isoformat(),
                    "latencyMs": round(base_latency + (self.failure_values["latencyMs"] - base_latency) * progress + random.uniform(-10, 20), 2),
                    "lossPercent": round(base_loss + (self.failure_values["packetLossPct"] - base_loss) * progress + random.uniform(-0.5, 1), 2),
                    "jitter": round(base_jitter + (self.failure_values["jitterMs"] - base_jitter) * progress + random.uniform(-2, 5), 2),
                    "goodput": round(base_goodput - (base_goodput - self.failure_values["goodput"]) * progress + random.uniform(-3, 2), 1),
                    "destinationIp": "8.8.8.8"
                }
                failure_history.append(entry)
            
            data["device_loss_and_latency_history"][DEVICE_SERIAL] = failure_history
            
            # Update wireless usage history (KEY FOR PREDICTIVE AGENT - shows critical degradation)
            base_time = datetime.now() - timedelta(minutes=30)
            wireless_history = []
            # Progressive failure pattern
            channel_util_progression = [48.0, 65.0, 78.0, 88.0, 94.0, 96.5]
            snr_progression = [31.0, 27.0, 23.0, 20.0, 17.5, 16.0]
            retrans_progression = [12, 22, 34, 44, 52, 58]
            rssi_progression = [-58, -62, -65, -68, -70, -72]
            uplink_progression = [850, 680, 520, 400, 320, 260]
            downlink_progression = [780, 580, 420, 320, 240, 170]
            
            for i in range(6):
                bucket_start = base_time + timedelta(minutes=i*5)
                bucket_end = bucket_start + timedelta(minutes=5)
                entry = {
                    "bucketStart": bucket_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "bucketEnd": bucket_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "deviceSerial": AP_SERIAL,
                    "ssid": "MCW-SanJose",
                    "channelUtilizationPercent": round(channel_util_progression[i] + random.uniform(-1, 2), 1),
                    "airtimeUtilizationPercent": round(channel_util_progression[i] + 2 + random.uniform(-1, 2), 1),
                    "retransmissionsPerMinute": retrans_progression[i] + random.randint(-2, 4),
                    "avgSignalToNoise": round(snr_progression[i] + random.uniform(-0.5, 0.5), 1),
                    "avgRssi": rssi_progression[i] + random.randint(-1, 1),
                    "clientCount": 22 + i * 3 + random.randint(-1, 2),
                    "uplinkSpeedMbps": uplink_progression[i] + random.randint(-30, 20),
                    "downlinkSpeedMbps": downlink_progression[i] + random.randint(-20, 15),
                    "note": "SCENARIO_4_FULL_FAILURE"
                }
                wireless_history.append(entry)
            data["network_wireless_usage_history"] = {NETWORK_ID: wireless_history}
            
            # Update wireless latency history (shows critical degradation)
            latency_history = []
            latency_progression = [28, 48, 72, 98, 125, 155]
            jitter_progression = [6, 14, 24, 36, 48, 58]
            loss_progression = [0.8, 2.2, 4.0, 6.5, 9.0, 12.0]
            
            for i in range(6):
                slot_start = base_time + timedelta(minutes=i*5)
                slot_end = slot_start + timedelta(minutes=5)
                entry = {
                    "timeslotStart": slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "timeslotEnd": slot_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "latencyMs": latency_progression[i] + random.randint(-5, 10),
                    "jitterMs": jitter_progression[i] + random.randint(-3, 5),
                    "packetLossPercent": round(loss_progression[i] + random.uniform(-0.5, 1.0), 2),
                    "deviceMac": "00:11:22:33:44:55",
                    "note": "SCENARIO_4_FULL_FAILURE"
                }
                latency_history.append(entry)
            data["network_wireless_latency_history"] = {NETWORK_ID: latency_history}
            
            # Update wireless health - CRITICAL
            data["network_wireless_health"] = {
                NETWORK_ID: {
                    "windowStart": (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "windowEnd": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "overallHealthScore": 28,
                    "coverage": {
                        "clientsBelowSNRThreshold": 12,
                        "worstSNR": 14.5,
                        "medianSNR": 17.0
                    },
                    "performance": {
                        "avgLatencyMs": 125,
                        "avgJitterMs": 48,
                        "avgPacketLossPercent": 9.5
                    },
                    "capacity": {
                        "overutilizedRadios": 2,
                        "avgChannelUtilizationPercent": 94.0,
                        "avgAirtimeUtilizationPercent": 96.5
                    },
                    "clientExperience": {
                        "dhcpFailures": 8,
                        "authFailures": 12,
                        "healthScore": 24
                    },
                    "bestApRecommendation": {
                        "sourceAp": "AP-03",
                        "recommendedAp": "AP-06",
                        "reason": "CRITICAL: Immediate failover required",
                        "expectedRssi": -58,
                        "expectedChannelUtilization": 24.0
                    },
                    "note": "SCENARIO_4_FULL_FAILURE"
                }
            }
            
            # Add multiple failed connections
            data["network_wireless_failed_connections"] = {
                NETWORK_ID: [
                    {"eventTime": (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:01", "failureReason": "auth_failure", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                    {"eventTime": (datetime.now() - timedelta(minutes=12)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:02", "failureReason": "dhcp_timeout", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                    {"eventTime": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:03", "failureReason": "association_rejected", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                    {"eventTime": (datetime.now() - timedelta(minutes=8)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:04", "failureReason": "auth_failure", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                    {"eventTime": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:05", "failureReason": "dhcp_timeout", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                    {"eventTime": (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:06", "failureReason": "deauthentication", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"}
                ]
            }
            
            # Update service impact predictions - CRITICAL
            data["service_impact_predictions"] = {
                NETWORK_ID: {
                    "sourceAp": "AP-03",
                    "window": f"{(datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')}/{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                    "usersImpacted": 22,
                    "failureProbability": 0.92,
                    "recommendedFallbackAp": "AP-06",
                    "reason": "CRITICAL: Multiple correlated failures - immediate intervention required",
                    "applications": [
                        {"name": "Teams", "activeUserPercent": 62, "impactLevel": "critical", "notes": "UNAVAILABLE - latency >150ms, jitter >40ms"},
                        {"name": "VOIP", "activeUserPercent": 15, "impactLevel": "critical", "notes": "UNAVAILABLE - jitter >30ms, loss >5%"},
                        {"name": "Email", "activeUserPercent": 20, "impactLevel": "high", "notes": "SEVERELY DEGRADED - loss >8%"},
                        {"name": "SMB/SFTP", "activeUserPercent": 12, "impactLevel": "critical", "notes": "FAILED - timeouts on all transfers"}
                    ],
                    "note": "SCENARIO_4_FULL_FAILURE"
                }
            }
            
            # Update topology - FAILURE
            data["network_topology_link_layer"] = {
                NETWORK_ID: {
                    "nodes": [
                        {"type": "appliance", "id": DEVICE_SERIAL, "name": "San Jose MX64", "uplink": "wan1", "status": "degraded"},
                        {"type": "wireless", "id": AP_SERIAL, "name": "AP-03", "floorPlanId": "FP-FLR1", "status": "failing"},
                        {"type": "wireless", "id": "Q2XX-AP06-5678", "name": "AP-06", "floorPlanId": "FP-FLR1", "status": "healthy"}
                    ],
                    "links": [
                        {"source": DEVICE_SERIAL, "target": AP_SERIAL, "linkType": "wired", "status": "critical", "latencyMs": 45, "lossPercent": 4.5},
                        {"source": DEVICE_SERIAL, "target": "Q2XX-AP06-5678", "linkType": "wired", "status": "ok", "latencyMs": 4, "lossPercent": 0.05},
                        {"source": AP_SERIAL, "target": "Q2XX-AP06-5678", "linkType": "wireless-mesh", "status": "critical", "latencyMs": 35, "lossPercent": 3.2}
                    ]
                }
            }
            
            # Update floor plans stability score - CRITICAL
            data["network_floor_plans"] = {
                NETWORK_ID: [{
                    "floorPlanId": "FP-FLR1",
                    "name": "San Jose HQ - Floor 1",
                    "center": {"lat": 37.4232, "lng": -122.0841},
                    "apCoordinates": [
                        {"deviceSerial": AP_SERIAL, "x": 12.4, "y": 6.1, "rfCoverageMeters": 15, "historicalStabilityScore": 18},
                        {"deviceSerial": "Q2XX-AP06-5678", "x": 35.2, "y": 8.7, "rfCoverageMeters": 25, "historicalStabilityScore": 92}
                    ]
                }]
            }
            
            # Set most clients to offline
            online_count = 0
            offline_count = 0
            if "network_clients" in data and NETWORK_ID in data["network_clients"]:
                for i, client in enumerate(data["network_clients"][NETWORK_ID]):
                    # 60% offline
                    if i % 5 < 3:
                        client["status"] = "Offline"
                        offline_count += 1
                    else:
                        client["status"] = "Online"
                        online_count += 1
                    client["lastSeen"] = datetime.now().isoformat()
            
            # Set all uplinks to failed
            if "organization_uplinks_statuses" in data and ORGANIZATION_ID in data["organization_uplinks_statuses"]:
                for device in data["organization_uplinks_statuses"][ORGANIZATION_ID]:
                    if device.get("networkId") == NETWORK_ID:
                        for uplink in device.get("uplinks", []):
                            uplink["status"] = "failed"
                        device["lastReportedAt"] = datetime.now().isoformat()
            
            # Write back
            with open('mock_data/comprehensive_api_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"🔴 WIRELESS TELEMETRY: CRITICAL FAILURE")
            print(f"   └─ Channel Util: 48% → 96.5% ❌ SATURATED")
            print(f"   └─ SNR: 31dB → 16dB ❌ BELOW THRESHOLD")
            print(f"   └─ Retransmissions: 12/min → 58/min ❌ CRITICAL")
            print(f"   └─ Latency: 28ms → 155ms ❌ CRITICAL")
            print(f"   └─ Packet Loss: 0.8% → 12% ❌ SEVERE")
            print(f"🔴 CLIENT STATUS:")
            print(f"   └─ {online_count} online, {offline_count} OFFLINE ❌")
            print(f"🔴 UPLINKS: ALL FAILED ❌")
            print(f"🔴 HEALTH SCORE: 28 ❌ CRITICAL")
            
        except Exception as e:
            print(f"❌ Error updating mock data: {e}")
    
    async def run_scenario(self):
        """Apply the full failure scenario"""
        print("\n🔴 SCENARIO 4: FULL NETWORK FAILURE")
        print("="*60)
        print("Setting all metrics to CRITICAL failure values...")
        print("-"*60)
        
        await self.update_appliance_settings()
        await self.update_mock_data()
        
        print("\n" + "="*60)
        print("🔴 SCENARIO 4 APPLIED: NETWORK FAILURE")
        print("="*60)
        print("\n📋 NETWORK STATE SUMMARY:")
        print("-"*60)
        print(f"  Latency:         {self.failure_values['latencyMs']}ms     ❌ CRITICAL")
        print(f"  Packet Loss:     {self.failure_values['packetLossPct']}%      ❌ SEVERE")
        print(f"  Jitter:          {self.failure_values['jitterMs']}ms       ❌ CRITICAL")
        print(f"  Goodput:         {self.failure_values['goodput']}%       ❌ FAILED")
        print(f"  Channel Util:    96.5%        ❌ SATURATED")
        print(f"  SNR:             16dB         ❌ BELOW THRESHOLD")
        print(f"  Retransmissions: 58/min       ❌ CRITICAL")
        print(f"  WAN1:            FAILED       ❌")
        print(f"  WAN2:            FAILED       ❌")
        print(f"  Clients:         ~40% online  ❌ MAJORITY OFFLINE")
        print(f"  Health Score:    28           ❌ CRITICAL")
        print("-"*60)
        print("\n🚨 SERVICE IMPACT:")
        print("-"*60)
        print("  Teams Video:   ❌ UNAVAILABLE (latency >150ms, jitter >30ms)")
        print("  VOIP Calls:    ❌ UNAVAILABLE (jitter >30ms, loss >1%)")
        print("  Email:         ⚠️  SEVERELY DEGRADED (loss >5%)")
        print("  SMB Transfers: ❌ FAILED (loss >0.5%, latency >100ms)")
        print("-"*60)
        print("\n💡 Expected Agent Response: LIKELY FAILURE (Risk Score: 85-100)")
        print("   → Should send CRITICAL alert immediately")
        print("   → Must recommend immediate failover")
        print("   → Identify all affected clients")
        print("   → Provide specific AP switching instructions")
        print("="*60)


async def main():
    """Main entry point"""
    scenario = FullFailureScenario()
    
    try:
        await scenario.initialize()
        await scenario.run_scenario()
    except Exception as e:
        print(f"\n❌ Scenario failed: {e}")
    finally:
        await scenario.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           SCENARIO 4: FULL NETWORK FAILURE                   ║
║                                                              ║
║  This script simulates complete network failure:            ║
║    • Latency: ~350ms (CRITICAL)                             ║
║    • Packet Loss: ~12% (SEVERE)                             ║
║    • Jitter: ~55ms (CRITICAL)                               ║
║    • Goodput: ~42% (FAILED)                                 ║
║    • Channel Utilization: 96%+ (SATURATED)                  ║
║    • SNR: ~16dB (BELOW THRESHOLD)                           ║
║    • Both uplinks: FAILED                                   ║
║    • 60% clients: OFFLINE                                   ║
║                                                              ║
║  Expected Agent Classification: LIKELY FAILURE              ║
║  → Risk Score: 85-100                                       ║
║  → Requires IMMEDIATE intervention                          ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
