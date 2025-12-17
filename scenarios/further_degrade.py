#!/usr/bin/env python3
"""
SCENARIO 3: FURTHER DEGRADATION - Sustained Issues
Simulates sustained network degradation with worsening trends.
This scenario shows clear degradation patterns that won't self-recover.

Metrics:
- Latency: 50-80ms (elevated, trending up)
- Packet Loss: 2-4% (significant)
- Jitter: 18-28ms (consistently high)
- Goodput: 75-82%
- Channel Utilization: 70-85% (high, trending up)
- SNR: 20-26dB (degrading)
- Uplinks: wan1 connecting/degraded, wan2 active
- Clients: 70% online, 30% experiencing issues

This scenario demonstrates a "serious warning" requiring attention.
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

# Simulation parameters
DURATION_SECONDS = 60
UPDATE_INTERVAL_SECONDS = 10
STEPS = DURATION_SECONDS // UPDATE_INTERVAL_SECONDS

# Wireless degradation stages (progressively worse)
WIRELESS_DEGRADATION_STAGES = [
    {"channelUtilization": 65.0, "snr": 27.0, "retransmissions": 18, "rssi": -60, "uplink": 680, "downlink": 520},
    {"channelUtilization": 72.0, "snr": 25.0, "retransmissions": 24, "rssi": -62, "uplink": 580, "downlink": 450},
    {"channelUtilization": 78.0, "snr": 23.0, "retransmissions": 30, "rssi": -64, "uplink": 490, "downlink": 380},
    {"channelUtilization": 82.0, "snr": 21.5, "retransmissions": 36, "rssi": -66, "uplink": 420, "downlink": 320},
    {"channelUtilization": 86.0, "snr": 20.0, "retransmissions": 42, "rssi": -68, "uplink": 360, "downlink": 270},
    {"channelUtilization": 88.0, "snr": 19.0, "retransmissions": 46, "rssi": -69, "uplink": 320, "downlink": 240},
]


class FurtherDegradeScenario:
    """Simulates sustained network degradation"""
    
    def __init__(self):
        self.session = None
        
        # Degradation progression values
        self.degradation_stages = [
            {"latencyMs": 45.0, "packetLossPct": 1.8, "jitterMs": 16.0, "goodput": 84.0},
            {"latencyMs": 55.0, "packetLossPct": 2.3, "jitterMs": 19.0, "goodput": 81.0},
            {"latencyMs": 62.0, "packetLossPct": 2.8, "jitterMs": 22.0, "goodput": 78.0},
            {"latencyMs": 70.0, "packetLossPct": 3.2, "jitterMs": 24.0, "goodput": 76.0},
            {"latencyMs": 78.0, "packetLossPct": 3.6, "jitterMs": 26.0, "goodput": 74.0},
            {"latencyMs": 85.0, "packetLossPct": 4.0, "jitterMs": 28.0, "goodput": 72.0},
        ]
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
        print("🔧 Further Degradation Scenario Initialized")
        print(f"📊 Duration: {DURATION_SECONDS}s")
        print(f"⏱️  Update Interval: {UPDATE_INTERVAL_SECONDS}s")
        print(f"📈 Total Steps: {STEPS}")
        print("="*60)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_metrics_for_step(self, step: int) -> Dict[str, float]:
        """Get progressively worsening metrics"""
        stage_index = min(step - 1, len(self.degradation_stages) - 1)
        base = self.degradation_stages[stage_index]
        
        # Add small random variance
        return {
            "latencyMs": round(base["latencyMs"] + random.uniform(-3, 5), 2),
            "packetLossPct": round(base["packetLossPct"] + random.uniform(-0.2, 0.3), 2),
            "jitterMs": round(base["jitterMs"] + random.uniform(-1, 2), 2),
            "goodput": round(base["goodput"] + random.uniform(-2, 1), 1)
        }
    
    def get_uplink_status(self, step: int) -> List[Dict[str, str]]:
        """Get uplink statuses based on degradation stage"""
        if step <= 2:
            return [
                {"uplink": "wan1", "status": "active"},
                {"uplink": "wan2", "status": "active"}
            ]
        elif step <= 4:
            return [
                {"uplink": "wan1", "status": "connecting"},
                {"uplink": "wan2", "status": "active"}
            ]
        else:
            return [
                {"uplink": "wan1", "status": "connecting"},
                {"uplink": "wan2", "status": "connecting"}
            ]
    
    def get_client_status(self, client_index: int, step: int) -> str:
        """Determine client status - more go offline as degradation progresses"""
        if step <= 2:
            return "Online"
        elif step <= 4:
            # 20% offline
            return "Offline" if client_index % 5 == 0 else "Online"
        else:
            # 30% offline
            return "Offline" if client_index % 3 == 0 else "Online"
    
    async def update_appliance_settings(self, step: int, metrics: Dict[str, float]):
        """Update appliance settings"""
        uplinks = self.get_uplink_status(step)
        
        settings = {
            "latencyMs": metrics["latencyMs"],
            "packetLossPct": metrics["packetLossPct"],
            "jitterMs": metrics["jitterMs"],
            "degradedLinks": uplinks,
            "updated_at": datetime.now().isoformat(),
            "note": "SCENARIO_3_FURTHER_DEGRADE"
        }
        
        url = f"{MOCK_SERVER_URL}/networks/{NETWORK_ID}/appliance/settings"
        
        try:
            async with self.session.post(url, json=settings) as response:
                if response.status == 200:
                    wan1_status = uplinks[0]["status"]
                    wan2_status = uplinks[1]["status"]
                    print(f"   └─ Latency: {metrics['latencyMs']}ms ↑, Loss: {metrics['packetLossPct']}% ↑")
                    print(f"   └─ Jitter: {metrics['jitterMs']}ms, WAN1: {wan1_status}, WAN2: {wan2_status}")
                else:
                    print(f"⚠️  Failed to update: {response.status}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def update_mock_data(self, step: int, metrics: Dict[str, float]):
        """Update comprehensive mock data including wireless telemetry"""
        try:
            import os
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mock_file = os.path.join(script_dir, 'mock_data', 'comprehensive_api_data.json')
            with open(mock_file, 'r') as f:
                data = json.load(f)
            
            uplinks = self.get_uplink_status(step)
            stage_index = min(step - 1, len(WIRELESS_DEGRADATION_STAGES) - 1)
            wireless_stage = WIRELESS_DEGRADATION_STAGES[stage_index]
            
            # Update network appliance settings
            if "networks" in data and NETWORK_ID in data["networks"]:
                network = data["networks"][NETWORK_ID]
                if "appliance_settings" in network and len(network["appliance_settings"]) > 0:
                    network["appliance_settings"][0].update({
                        "latencyMs": metrics["latencyMs"],
                        "packetLossPct": metrics["packetLossPct"],
                        "jitterMs": metrics["jitterMs"],
                        "degradedLinks": uplinks,
                        "updated_at": datetime.now().isoformat(),
                        "note": "SCENARIO_3_FURTHER_DEGRADE"
                    })
            
            # Add history entry showing degradation trend
            if "device_loss_and_latency_history" not in data:
                data["device_loss_and_latency_history"] = {}
            
            if DEVICE_SERIAL not in data["device_loss_and_latency_history"]:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = []
            
            entry = {
                "ts": datetime.now().isoformat(),
                "latencyMs": metrics["latencyMs"],
                "lossPercent": metrics["packetLossPct"],
                "jitter": metrics["jitterMs"],
                "goodput": metrics["goodput"],
                "destinationIp": "8.8.8.8"
            }
            data["device_loss_and_latency_history"][DEVICE_SERIAL].append(entry)
            
            # Keep last 30 entries
            if len(data["device_loss_and_latency_history"][DEVICE_SERIAL]) > 30:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = \
                    data["device_loss_and_latency_history"][DEVICE_SERIAL][-30:]
            
            # Update wireless usage history (KEY FOR PREDICTIVE AGENT - shows degradation trend)
            base_time = datetime.now() - timedelta(minutes=30)
            wireless_history = []
            for i in range(6):
                bucket_start = base_time + timedelta(minutes=i*5)
                bucket_end = bucket_start + timedelta(minutes=5)
                # Progressive degradation
                stage_for_bucket = min(i, len(WIRELESS_DEGRADATION_STAGES) - 1)
                ws = WIRELESS_DEGRADATION_STAGES[stage_for_bucket]
                entry = {
                    "bucketStart": bucket_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "bucketEnd": bucket_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "deviceSerial": AP_SERIAL,
                    "ssid": "MCW-SanJose",
                    "channelUtilizationPercent": round(ws["channelUtilization"] + random.uniform(-2, 3), 1),
                    "airtimeUtilizationPercent": round(ws["channelUtilization"] + 4 + random.uniform(-1, 2), 1),
                    "retransmissionsPerMinute": ws["retransmissions"] + random.randint(-2, 4),
                    "avgSignalToNoise": round(ws["snr"] + random.uniform(-1, 0.5), 1),
                    "avgRssi": ws["rssi"] + random.randint(-1, 1),
                    "clientCount": 22 + i * 2 + random.randint(-1, 2),
                    "uplinkSpeedMbps": ws["uplink"] + random.randint(-30, 20),
                    "downlinkSpeedMbps": ws["downlink"] + random.randint(-20, 15),
                    "note": "SCENARIO_3_FURTHER_DEGRADE"
                }
                wireless_history.append(entry)
            data["network_wireless_usage_history"] = {NETWORK_ID: wireless_history}
            
            # Update wireless latency history (shows degradation)
            latency_history = []
            latency_progression = [35, 42, 52, 62, 72, 80]
            jitter_progression = [10, 14, 18, 22, 26, 28]
            loss_progression = [1.2, 1.8, 2.5, 3.2, 3.8, 4.2]
            for i in range(6):
                slot_start = base_time + timedelta(minutes=i*5)
                slot_end = slot_start + timedelta(minutes=5)
                entry = {
                    "timeslotStart": slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "timeslotEnd": slot_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "latencyMs": latency_progression[i] + random.randint(-3, 5),
                    "jitterMs": jitter_progression[i] + random.randint(-2, 3),
                    "packetLossPercent": round(loss_progression[i] + random.uniform(-0.3, 0.4), 2),
                    "deviceMac": "00:11:22:33:44:55",
                    "note": "SCENARIO_3_FURTHER_DEGRADE"
                }
                latency_history.append(entry)
            data["network_wireless_latency_history"] = {NETWORK_ID: latency_history}
            
            # Update wireless health
            data["network_wireless_health"] = {
                NETWORK_ID: {
                    "windowStart": (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "windowEnd": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "overallHealthScore": 58,
                    "coverage": {
                        "clientsBelowSNRThreshold": 4,
                        "worstSNR": 18.5,
                        "medianSNR": 22.0
                    },
                    "performance": {
                        "avgLatencyMs": 65,
                        "avgJitterMs": 22,
                        "avgPacketLossPercent": 3.2
                    },
                    "capacity": {
                        "overutilizedRadios": 1,
                        "avgChannelUtilizationPercent": 78.0,
                        "avgAirtimeUtilizationPercent": 82.0
                    },
                    "clientExperience": {
                        "dhcpFailures": 3,
                        "authFailures": 4,
                        "healthScore": 54
                    },
                    "bestApRecommendation": {
                        "sourceAp": "AP-03",
                        "recommendedAp": "AP-06",
                        "reason": "Lower load and better SNR",
                        "expectedRssi": -58,
                        "expectedChannelUtilization": 24.0
                    },
                    "note": "SCENARIO_3_FURTHER_DEGRADE"
                }
            }
            
            # Add failed connections
            data["network_wireless_failed_connections"] = {
                NETWORK_ID: [
                    {
                        "eventTime": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "deviceSerial": AP_SERIAL,
                        "clientMac": "AA:BB:CC:DD:EE:01",
                        "failureReason": "auth_failure",
                        "ssid": "MCW-SanJose",
                        "apMac": "00:11:22:33:44:55"
                    },
                    {
                        "eventTime": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "deviceSerial": AP_SERIAL,
                        "clientMac": "AA:BB:CC:DD:EE:02",
                        "failureReason": "dhcp_timeout",
                        "ssid": "MCW-SanJose",
                        "apMac": "00:11:22:33:44:55"
                    }
                ]
            }
            
            # Update service impact predictions
            data["service_impact_predictions"] = {
                NETWORK_ID: {
                    "sourceAp": "AP-03",
                    "sourceApSerial": AP_SERIAL,
                    "window": f"{(datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')}/{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                    "usersImpacted": 8,
                    "failureProbability": 0.55,
                    "recoveryLikelihood": "LOW",
                    "recoveryReason": "Sustained degradation with no recovery pattern in last 3 buckets",
                    "estimatedTimeToFailure": "15-30 minutes",
                    "interventionPriority": "HIGH",
                    "recommendedFallbackAp": "AP-06",
                    "reason": "Sustained degradation pattern detected - prepare for failover",
                    "applications": [
                        {"name": "Teams Video", "activeUserPercent": 62, "impactLevel": "high", "notes": "Video quality degraded, audio may cut out"},
                        {"name": "VOIP", "activeUserPercent": 15, "impactLevel": "medium", "notes": "Call quality impacted, jitter >15ms"},
                        {"name": "SSH Sessions", "activeUserPercent": 8, "impactLevel": "medium", "notes": "Terminal lag noticeable"},
                        {"name": "Email", "activeUserPercent": 20, "impactLevel": "low", "notes": "Slight delays possible"},
                        {"name": "File Transfers", "activeUserPercent": 12, "impactLevel": "medium", "notes": "File transfers may timeout"}
                    ],
                    "trendAnalysis": {
                        "channelUtilization": {"start": 45, "end": 78, "change": 73, "trend": "WORSENING"},
                        "airtimeUtilization": {"start": 48, "end": 82, "change": 71, "trend": "WORSENING"},
                        "retransmissions": {"start": 8, "end": 30, "change": 275, "trend": "WORSENING"},
                        "signalSNR": {"start": 32, "end": 23, "change": -28, "trend": "DEGRADING"},
                        "uplinkSpeed": {"start": 850, "end": 490, "change": -42, "trend": "DEGRADING"},
                        "downlinkSpeed": {"start": 780, "end": 380, "change": -51, "trend": "DEGRADING"},
                        "clientLoad": {"start": 18, "end": 26, "change": 44, "trend": "INCREASING"},
                        "pattern": "SUSTAINED DEGRADATION - Metrics worsening without recovery signs"
                    },
                    "currentThresholds": {
                        "latency": {"value": 55, "threshold": 60, "status": "WARNING"},
                        "jitter": {"value": 19, "threshold": 20, "status": "WARNING"},
                        "packetLoss": {"value": 2.8, "threshold": 3.0, "status": "WARNING"}
                    },
                    "failoverCandidates": [
                        {
                            "rank": 1,
                            "apName": "AP-06",
                            "apSerial": "Q2XX-AP06-5678",
                            "score": 92,
                            "reason": "LOW LOAD (1 client), GOOD SIGNAL (-58dBm), same floor",
                            "distance": 12.3,
                            "channelOverlap": False,
                            "sameFloor": True
                        },
                        {
                            "rank": 2,
                            "apName": "AP-04",
                            "apSerial": "Q2XX-AP04-4444",
                            "score": 89,
                            "reason": "EXCELLENT SIGNAL (-52dBm), LOW LOAD (1 client)",
                            "distance": 8.5,
                            "channelOverlap": False,
                            "sameFloor": True
                        },
                        {
                            "rank": 3,
                            "apName": "AP-01",
                            "apSerial": "Q2XX-AP01-1111",
                            "score": 75,
                            "reason": "MEDIUM LOAD (3 clients), CHANNEL OVERLAP possible"
                        }
                    ],
                    "executionPlan": [
                        {"step": 1, "action": "PREPARE", "description": "Monitor closely for next 5 minutes"},
                        {"step": 2, "action": "IF_WORSENS", "target": "Anton-Laptop", "targetAp": "AP-06"},
                        {"step": 3, "action": "IF_WORSENS", "target": "Teams-Room", "targetAp": "AP-06"},
                        {"step": 4, "action": "FALLBACK", "description": "If AP-06 unavailable, use AP-04"}
                    ],
                    "note": "SCENARIO_3_FURTHER_DEGRADE"
                }
            }
            
            # Update topology
            data["network_topology_link_layer"] = {
                NETWORK_ID: {
                    "nodes": [
                        {"type": "appliance", "id": DEVICE_SERIAL, "name": "San Jose MX64", "uplink": "wan1", "status": "online"},
                        {"type": "wireless", "id": AP_SERIAL, "name": "AP-03", "floorPlanId": "FP-FLR1", "status": "degrading"},
                        {"type": "wireless", "id": "Q2XX-AP06-5678", "name": "AP-06", "floorPlanId": "FP-FLR1", "status": "healthy"}
                    ],
                    "links": [
                        {"source": DEVICE_SERIAL, "target": AP_SERIAL, "linkType": "wired", "status": "warning", "latencyMs": 15, "lossPercent": 0.8},
                        {"source": DEVICE_SERIAL, "target": "Q2XX-AP06-5678", "linkType": "wired", "status": "ok", "latencyMs": 4, "lossPercent": 0.05},
                        {"source": AP_SERIAL, "target": "Q2XX-AP06-5678", "linkType": "wireless-mesh", "status": "warning", "latencyMs": 12, "lossPercent": 0.6}
                    ]
                }
            }
            
            # Update floor plans stability score
            data["network_floor_plans"] = {
                NETWORK_ID: [{
                    "floorPlanId": "FP-FLR1",
                    "name": "San Jose HQ - Floor 1",
                    "center": {"lat": 37.4232, "lng": -122.0841},
                    "apCoordinates": [
                        {"deviceSerial": AP_SERIAL, "x": 12.4, "y": 6.1, "rfCoverageMeters": 20, "historicalStabilityScore": 52},
                        {"deviceSerial": "Q2XX-AP06-5678", "x": 35.2, "y": 8.7, "rfCoverageMeters": 25, "historicalStabilityScore": 92}
                    ]
                }]
            }
            
            # Update client statuses
            online_count = 0
            offline_count = 0
            if "network_clients" in data and NETWORK_ID in data["network_clients"]:
                for i, client in enumerate(data["network_clients"][NETWORK_ID]):
                    status = self.get_client_status(i, step)
                    client["status"] = status
                    client["lastSeen"] = datetime.now().isoformat()
                    if status == "Online":
                        online_count += 1
                    else:
                        offline_count += 1
            
            # Update uplink statuses
            if "organization_uplinks_statuses" in data and ORGANIZATION_ID in data["organization_uplinks_statuses"]:
                for device in data["organization_uplinks_statuses"][ORGANIZATION_ID]:
                    if device.get("networkId") == NETWORK_ID:
                        device["uplinks"] = uplinks
                        device["lastReportedAt"] = datetime.now().isoformat()
            
            # Write back
            with open(mock_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            if offline_count > 0:
                print(f"   └─ Clients: {online_count} online, {offline_count} offline ⚠️")
            
        except Exception as e:
            print(f"❌ Error updating mock data: {e}")
    
    async def run_scenario(self):
        """Run the further degradation scenario"""
        print("\n🔶 SCENARIO 3: FURTHER DEGRADATION")
        print("="*60)
        print("Simulating sustained degradation with worsening trend...")
        print("-"*60)
        
        for step in range(1, STEPS + 1):
            metrics = self.get_metrics_for_step(step)
            progress = (step / STEPS) * 100
            
            print(f"\n📊 Step {step}/{STEPS} ({progress:.0f}%) - DEGRADING ↓")
            await self.update_appliance_settings(step, metrics)
            await self.update_mock_data(step, metrics)
            
            if step < STEPS:
                await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
        
        final_metrics = self.get_metrics_for_step(STEPS)
        
        print("\n" + "="*60)
        print("✅ SCENARIO 3 APPLIED: FURTHER DEGRADATION")
        print("="*60)
        print("\n📋 NETWORK STATE SUMMARY:")
        print("-"*60)
        print(f"  Latency:      {final_metrics['latencyMs']}ms      🔶 HIGH (↑ trending)")
        print(f"  Packet Loss:  {final_metrics['packetLossPct']}%       🔶 SIGNIFICANT")
        print(f"  Jitter:       {final_metrics['jitterMs']}ms       🔶 ELEVATED")
        print(f"  Goodput:      {final_metrics['goodput']}%       🔶 DEGRADED")
        print(f"  WAN1:         connecting     ⚠️  UNSTABLE")
        print(f"  WAN2:         connecting     ⚠️  UNSTABLE")
        print(f"  Clients:      ~70% online    ⚠️  SOME OFFLINE")
        print("-"*60)
        print("\n💡 Expected Agent Response: DEGRADING (Risk Score: 51-70)")
        print("   → Should send WARNING alert")
        print("   → Recommend monitoring closely")
        print("   → Consider failover preparation")
        print("="*60)


async def main():
    """Main entry point"""
    scenario = FurtherDegradeScenario()
    
    try:
        await scenario.initialize()
        await scenario.run_scenario()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scenario interrupted by user")
    except Exception as e:
        print(f"\n❌ Scenario failed: {e}")
    finally:
        await scenario.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         SCENARIO 3: FURTHER DEGRADATION                      ║
║                                                              ║
║  This script simulates sustained network degradation:       ║
║    • Latency: 50-85ms (trending up ↑)                       ║
║    • Packet Loss: 2-4% (significant)                        ║
║    • Jitter: 18-28ms (consistently high)                    ║
║    • WAN1: connecting/degraded                              ║
║    • WAN2: active → connecting                              ║
║    • ~30% clients experiencing issues                       ║
║                                                              ║
║  Expected Agent Classification: DEGRADING (High Risk)       ║
║  → Will NOT self-recover, requires attention                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
