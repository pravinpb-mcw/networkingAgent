#!/usr/bin/env python3
"""
SCENARIO 2: PARTIAL DEGRADATION - Random Jitter, Likely Recovery
Simulates a minor, transient network issue with random jitter spikes.
Network will likely self-recover within 15-second monitoring window.

Metrics:
- Latency: ~25-35ms (slightly elevated)
- Packet Loss: 0.5-1.0% (minor)
- Jitter: RANDOM spikes 5-15ms (intermittent)
- Goodput: 90-92%
- Channel Utilization: 45-55% (moderate)
- SNR: 28-32dB (acceptable)
- Uplinks: active (minor hiccups)
- Clients: mostly online (1-2 may show latency)

This scenario demonstrates a "warning" state that doesn't require action.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any
import aiohttp

# Configuration
MOCK_SERVER_URL = "http://127.0.0.1:5000"
NETWORK_ID = "L_3947405073390239794"
ORGANIZATION_ID = "999781"
DEVICE_SERIAL = "Q2MN-Q3J9-YJHW"
AP_SERIAL = "Q2XX-ABCD-1234"

# Simulation parameters
DURATION_SECONDS = 30  # Short duration - will likely recover
UPDATE_INTERVAL_SECONDS = 5

# Partial degradation wireless metrics
DEGRADED_WIRELESS = {
    "channelUtilizationPercent": 48.0,
    "airtimeUtilizationPercent": 52.0,
    "retransmissionsPerMinute": 12,
    "avgSignalToNoise": 29.5,
    "avgRssi": -58,
    "clientCount": 18,
    "uplinkSpeedMbps": 780,
    "downlinkSpeedMbps": 650
}


class PartialDegradeScenario:
    """Simulates partial degradation with random jitter"""
    
    def __init__(self):
        self.session = None
        
        # Base values (slightly degraded)
        self.base_values = {
            "latencyMs": 28.0,
            "packetLossPct": 0.7,
            "jitterMs": 8.0,
            "goodput": 91.0
        }
        
        # Jitter range for random spikes
        self.jitter_range = (5.0, 18.0)
        self.latency_range = (22.0, 38.0)
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
        print("🔧 Partial Degradation Scenario Initialized")
        print(f"📊 Duration: {DURATION_SECONDS}s")
        print(f"⏱️  Update Interval: {UPDATE_INTERVAL_SECONDS}s")
        print("="*60)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_random_metrics(self) -> Dict[str, float]:
        """Generate random slightly-degraded metrics"""
        return {
            "latencyMs": round(random.uniform(*self.latency_range), 2),
            "packetLossPct": round(random.uniform(0.3, 1.2), 2),
            "jitterMs": round(random.uniform(*self.jitter_range), 2),
            "goodput": round(random.uniform(89.0, 93.0), 1)
        }
    
    async def update_appliance_settings(self, metrics: Dict[str, float]):
        """Update appliance settings with degraded metrics"""
        settings = {
            "latencyMs": metrics["latencyMs"],
            "packetLossPct": metrics["packetLossPct"],
            "jitterMs": metrics["jitterMs"],
            "degradedLinks": [
                {"uplink": "wan1", "status": "active"},
                {"uplink": "wan2", "status": "active"}
            ],
            "updated_at": datetime.now().isoformat(),
            "note": "SCENARIO_2_PARTIAL_DEGRADE"
        }
        
        url = f"{MOCK_SERVER_URL}/networks/{NETWORK_ID}/appliance/settings"
        
        try:
            async with self.session.post(url, json=settings) as response:
                if response.status == 200:
                    # Show jitter spike indicator
                    jitter_indicator = "⚡ SPIKE" if metrics["jitterMs"] > 12 else "📊 normal"
                    print(f"   └─ Latency: {metrics['latencyMs']}ms, Jitter: {metrics['jitterMs']}ms {jitter_indicator}")
                else:
                    print(f"⚠️  Failed to update: {response.status}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def update_mock_data(self, metrics: Dict[str, float]):
        """Update comprehensive mock data including wireless telemetry"""
        try:
            import os
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mock_file = os.path.join(script_dir, 'mock_data', 'comprehensive_api_data.json')
            with open(mock_file, 'r') as f:
                data = json.load(f)
            
            # Update network appliance settings
            if "networks" in data and NETWORK_ID in data["networks"]:
                network = data["networks"][NETWORK_ID]
                if "appliance_settings" in network and len(network["appliance_settings"]) > 0:
                    network["appliance_settings"][0].update({
                        "latencyMs": metrics["latencyMs"],
                        "packetLossPct": metrics["packetLossPct"],
                        "jitterMs": metrics["jitterMs"],
                        "degradedLinks": [
                            {"uplink": "wan1", "status": "active"},
                            {"uplink": "wan2", "status": "active"}
                        ],
                        "updated_at": datetime.now().isoformat(),
                        "note": "SCENARIO_2_PARTIAL_DEGRADE"
                    })
            
            # Add history entry
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
            
            # Keep last 20 entries
            if len(data["device_loss_and_latency_history"][DEVICE_SERIAL]) > 20:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = \
                    data["device_loss_and_latency_history"][DEVICE_SERIAL][-20:]
            
            # Update wireless usage history (KEY FOR PREDICTIVE AGENT)
            # Shows gradual mild degradation pattern
            base_time = datetime.now() - timedelta(minutes=30)
            wireless_history = []
            
            # Progressive mild degradation pattern (stable → slight increase)
            channel_util_pattern = [32.0, 38.0, 44.0, 48.0, 52.0, 50.0]  # mild increase then slight recovery
            snr_pattern = [33.5, 32.0, 30.5, 29.5, 28.5, 29.0]  # slight decrease then stabilize
            retrans_pattern = [5, 7, 10, 13, 14, 12]  # increase then slight recovery
            rssi_pattern = [-54, -55, -57, -58, -59, -58]
            uplink_pattern = [880, 850, 810, 780, 760, 775]
            downlink_pattern = [820, 780, 720, 660, 640, 655]
            
            for i in range(6):
                bucket_start = base_time + timedelta(minutes=i*5)
                bucket_end = bucket_start + timedelta(minutes=5)
                entry = {
                    "bucketStart": bucket_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "bucketEnd": bucket_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "deviceSerial": AP_SERIAL,
                    "ssid": "MCW-SanJose",
                    "channelUtilizationPercent": round(channel_util_pattern[i] + random.uniform(-2, 2), 1),
                    "airtimeUtilizationPercent": round(channel_util_pattern[i] + 3 + random.uniform(-1, 2), 1),
                    "retransmissionsPerMinute": retrans_pattern[i] + random.randint(-1, 2),
                    "avgSignalToNoise": round(snr_pattern[i] + random.uniform(-0.5, 0.5), 1),
                    "avgRssi": rssi_pattern[i] + random.randint(-1, 1),
                    "clientCount": 14 + i + random.randint(-1, 2),
                    "uplinkSpeedMbps": uplink_pattern[i] + random.randint(-20, 20),
                    "downlinkSpeedMbps": downlink_pattern[i] + random.randint(-15, 15),
                    "note": "SCENARIO_2_PARTIAL_DEGRADE"
                }
                wireless_history.append(entry)
            data["network_wireless_usage_history"] = {NETWORK_ID: wireless_history}
            
            # Update wireless latency history (shows mild degradation pattern)
            latency_history = []
            latency_pattern = [18, 22, 26, 30, 32, 28]  # increase then slight recovery
            jitter_pattern = [3, 5, 7, 9, 10, 8]
            loss_pattern = [0.2, 0.4, 0.6, 0.8, 0.9, 0.7]
            
            for i in range(6):
                slot_start = base_time + timedelta(minutes=i*5)
                slot_end = slot_start + timedelta(minutes=5)
                entry = {
                    "timeslotStart": slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "timeslotEnd": slot_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "latencyMs": latency_pattern[i] + random.randint(-2, 3),
                    "jitterMs": jitter_pattern[i] + random.randint(-1, 2),
                    "packetLossPercent": round(loss_pattern[i] + random.uniform(-0.1, 0.15), 2),
                    "deviceMac": "00:11:22:33:44:55",
                    "note": "SCENARIO_2_PARTIAL_DEGRADE"
                }
                latency_history.append(entry)
            data["network_wireless_latency_history"] = {NETWORK_ID: latency_history}
            
            # Update wireless health
            data["network_wireless_health"] = {
                NETWORK_ID: {
                    "windowStart": (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "windowEnd": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "overallHealthScore": 78,
                    "coverage": {
                        "clientsBelowSNRThreshold": 1,
                        "worstSNR": 26.5,
                        "medianSNR": 29.5
                    },
                    "performance": {
                        "avgLatencyMs": 28,
                        "avgJitterMs": 8,
                        "avgPacketLossPercent": 0.7
                    },
                    "capacity": {
                        "overutilizedRadios": 0,
                        "avgChannelUtilizationPercent": 50.0,
                        "avgAirtimeUtilizationPercent": 54.0
                    },
                    "clientExperience": {
                        "dhcpFailures": 0,
                        "authFailures": 1,
                        "healthScore": 76
                    },
                    "bestApRecommendation": None,
                    "note": "SCENARIO_2_PARTIAL_DEGRADE"
                }
            }
            
            # Update service impact predictions
            data["service_impact_predictions"] = {
                NETWORK_ID: {
                    "sourceAp": "AP-03",
                    "sourceApSerial": AP_SERIAL,
                    "window": f"{(datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')}/{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                    "usersImpacted": 2,
                    "failureProbability": 0.18,
                    "recoveryLikelihood": "HIGH",
                    "recoveryReason": "Intermittent jitter spikes with recovery pattern visible in last bucket",
                    "estimatedTimeToFailure": "Not imminent",
                    "interventionPriority": "LOW",
                    "recommendedFallbackAp": None,
                    "reason": "Minor jitter spikes, likely transient - monitor only",
                    "applications": [
                        {"name": "Teams Video", "activeUserPercent": 62, "impactLevel": "low", "notes": "Minor video quality fluctuation possible"},
                        {"name": "VOIP", "activeUserPercent": 15, "impactLevel": "none", "notes": "Operating normally"},
                        {"name": "SSH Sessions", "activeUserPercent": 8, "impactLevel": "none", "notes": "Operating normally"},
                        {"name": "Email", "activeUserPercent": 20, "impactLevel": "none", "notes": "Operating normally"},
                        {"name": "File Transfers", "activeUserPercent": 12, "impactLevel": "none", "notes": "Operating normally"}
                    ],
                    "trendAnalysis": {
                        "channelUtilization": {"start": 32, "end": 50, "change": 56, "trend": "SLIGHT_INCREASE"},
                        "airtimeUtilization": {"start": 35, "end": 53, "change": 51, "trend": "SLIGHT_INCREASE"},
                        "retransmissions": {"start": 5, "end": 12, "change": 140, "trend": "ELEVATED"},
                        "signalSNR": {"start": 33.5, "end": 29, "change": -13, "trend": "SLIGHT_DECREASE"},
                        "uplinkSpeed": {"start": 880, "end": 775, "change": -12, "trend": "STABLE"},
                        "downlinkSpeed": {"start": 820, "end": 655, "change": -20, "trend": "SLIGHT_DECREASE"},
                        "clientLoad": {"start": 14, "end": 18, "change": 29, "trend": "NORMAL_GROWTH"},
                        "pattern": "INTERMITTENT DEGRADATION - Recovery pattern visible, likely self-correcting"
                    },
                    "currentThresholds": {
                        "latency": {"value": 28, "threshold": 60, "status": "OK"},
                        "jitter": {"value": 8, "threshold": 20, "status": "OK"},
                        "packetLoss": {"value": 0.7, "threshold": 3.0, "status": "OK"}
                    },
                    "failoverCandidates": [
                        {
                            "rank": 1,
                            "apName": "AP-06",
                            "apSerial": "Q2XX-AP06-5678",
                            "score": 92,
                            "reason": "LOW LOAD, GOOD SIGNAL - standby if needed",
                            "distance": 12.3,
                            "channelOverlap": False,
                            "sameFloor": True,
                            "status": "STANDBY"
                        }
                    ],
                    "executionPlan": [
                        {"step": 1, "action": "MONITOR", "description": "Continue monitoring for 15s window"},
                        {"step": 2, "action": "IF_WORSENS", "description": "Escalate to WARNING if metrics don't recover"},
                        {"step": 3, "action": "NO_ACTION_REQUIRED", "description": "Likely to self-correct"}
                    ],
                    "note": "SCENARIO_2_PARTIAL_DEGRADE"
                }
            }
            
            # Update topology
            data["network_topology_link_layer"] = {
                NETWORK_ID: {
                    "nodes": [
                        {"type": "appliance", "id": DEVICE_SERIAL, "name": "San Jose MX64", "uplink": "wan1", "status": "online"},
                        {"type": "wireless", "id": AP_SERIAL, "name": "AP-03", "floorPlanId": "FP-FLR1", "status": "warning"},
                        {"type": "wireless", "id": "Q2XX-AP06-5678", "name": "AP-06", "floorPlanId": "FP-FLR1", "status": "healthy"}
                    ],
                    "links": [
                        {"source": DEVICE_SERIAL, "target": AP_SERIAL, "linkType": "wired", "status": "warning", "latencyMs": 8, "lossPercent": 0.2},
                        {"source": DEVICE_SERIAL, "target": "Q2XX-AP06-5678", "linkType": "wired", "status": "ok", "latencyMs": 4, "lossPercent": 0.05},
                        {"source": AP_SERIAL, "target": "Q2XX-AP06-5678", "linkType": "wireless-mesh", "status": "ok", "latencyMs": 6, "lossPercent": 0.15}
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
                        {"deviceSerial": AP_SERIAL, "x": 12.4, "y": 6.1, "rfCoverageMeters": 24, "historicalStabilityScore": 78},
                        {"deviceSerial": "Q2XX-AP06-5678", "x": 35.2, "y": 8.7, "rfCoverageMeters": 25, "historicalStabilityScore": 92}
                    ]
                }]
            }
            
            # Clear any failed connections (minor issues don't cause failures)
            data["network_wireless_failed_connections"] = {NETWORK_ID: []}
            
            # All clients online (maybe 1 showing slight latency)
            if "network_clients" in data and NETWORK_ID in data["network_clients"]:
                for i, client in enumerate(data["network_clients"][NETWORK_ID]):
                    client["status"] = "Online"
                    client["lastSeen"] = datetime.now().isoformat()
            
            # Write back
            with open(mock_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            print(f"❌ Error updating mock data: {e}")
    
    async def run_scenario(self):
        """Run the partial degradation scenario"""
        print("\n⚠️  SCENARIO 2: PARTIAL DEGRADATION")
        print("="*60)
        print("Simulating random jitter spikes (likely to recover)...")
        print("-"*60)
        
        steps = DURATION_SECONDS // UPDATE_INTERVAL_SECONDS
        
        for step in range(1, steps + 1):
            metrics = self.get_random_metrics()
            
            print(f"\n📊 Step {step}/{steps}")
            await self.update_appliance_settings(metrics)
            await self.update_mock_data(metrics)
            
            if step < steps:
                await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
        
        # End with slightly improved metrics (recovery pattern)
        recovery_metrics = {
            "latencyMs": 22.0,
            "packetLossPct": 0.4,
            "jitterMs": 6.0,
            "goodput": 93.0
        }
        
        print(f"\n📊 Final Step (Recovery Pattern)")
        await self.update_appliance_settings(recovery_metrics)
        await self.update_mock_data(recovery_metrics)
        
        print("\n" + "="*60)
        print("✅ SCENARIO 2 APPLIED: PARTIAL DEGRADATION")
        print("="*60)
        print("\n📋 NETWORK STATE SUMMARY:")
        print("-"*60)
        print(f"  Latency:      22-38ms      ⚠️  SLIGHTLY ELEVATED")
        print(f"  Packet Loss:  0.3-1.2%     ⚠️  MINOR")
        print(f"  Jitter:       5-18ms       ⚡ RANDOM SPIKES")
        print(f"  Goodput:      89-93%       ⚠️  ACCEPTABLE")
        print(f"  Uplinks:      ALL ACTIVE   ✅")
        print(f"  Clients:      ALL ONLINE   ✅")
        print("-"*60)
        print("\n💡 Expected Agent Response: DEGRADING (Risk Score: 31-50)")
        print("   → Should show WARNING but likely to recover")
        print("   → 15-second monitoring window recommended")
        print("="*60)


async def main():
    """Main entry point"""
    scenario = PartialDegradeScenario()
    
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
║        SCENARIO 2: PARTIAL DEGRADATION                       ║
║                                                              ║
║  This script simulates minor, transient network issues:     ║
║    • Latency: ~25-35ms (slightly elevated)                  ║
║    • Packet Loss: 0.5-1.0% (minor)                          ║
║    • Jitter: RANDOM spikes 5-18ms (intermittent)            ║
║    • All uplinks: active                                    ║
║    • All clients: online                                    ║
║                                                              ║
║  Expected Agent Classification: DEGRADING (Low Risk)        ║
║  → Likely to self-recover within 15-second window           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
