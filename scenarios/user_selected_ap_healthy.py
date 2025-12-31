#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USER-SELECTED AP RECOVERY - Interactive Scenario
Allows user to select which specific AP should be restored to healthy state.
This restores only the selected AP while keeping all others in their current state.
"""

import sys
import os

# Fix Windows console encoding for emojis
if os.name == 'nt':  # Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp

# Configuration
MOCK_SERVER_URL = "http://127.0.0.1:5000"
NETWORK_ID = "L_3947405073390239794"
ORGANIZATION_ID = "999781"
DEVICE_SERIAL = "Q2MN-Q3J9-YJHW"

# All available APs in the network
ALL_APS = [
    {"serial": "Q2XX-ABCD-1234", "name": "AP-03", "mac": "00:11:22:33:44:55"},
    {"serial": "Q2XX-AP06-5678", "name": "AP-06", "mac": "00:11:22:33:44:99"},
    {"serial": "Q2XX-AP01-1111", "name": "AP-01", "mac": "00:11:22:33:44:11"},
    {"serial": "Q2XX-AP04-4444", "name": "AP-04", "mac": "00:11:22:33:44:44"},
    {"serial": "Q2XX-AP08-8888", "name": "AP-08", "mac": "00:11:22:33:44:88"}
]

# Healthy metrics for the selected AP
HEALTHY_METRICS = {
    "latencyMs": 15.5,
    "packetLossPct": 0.1,
    "jitterMs": 1.2,
    "goodput": 95.0
}

# Excellent healthy wireless profile
HEALTHY_PROFILE = {
    "channelUtilizationPercent": 18.0,
    "retransmissionsPerMinute": 1,
    "avgSignalToNoise": 38.0,
    "avgRssi": -45,
    "clientCount": 6,
    "latencyMs": 7,
    "jitterMs": 0.8,
    "packetLossPercent": 0.03
}


class UserSelectedAPHealthy:
    """Restores selected AP to healthy state only"""
    
    def __init__(self, selected_ap: Dict[str, str]):
        self.session = None
        self.selected_ap = selected_ap
        self.ap_serial = selected_ap["serial"]
        self.ap_name = selected_ap["name"]
        self.ap_mac = selected_ap["mac"]
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 User-Selected AP Recovery Scenario Initialized")
        print(f"🎯 Target: {self.ap_name} ({self.ap_serial})")
        print("="*60)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    async def update_appliance_settings(self):
        """Update appliance settings with healthy metrics"""
        settings = {
            "latencyMs": HEALTHY_METRICS["latencyMs"],
            "packetLossPct": HEALTHY_METRICS["packetLossPct"],
            "jitterMs": HEALTHY_METRICS["jitterMs"],
            "degradedLinks": [
                {"uplink": "wan1", "status": "active"},
                {"uplink": "wan2", "status": "active"}
            ],
            "updated_at": datetime.now().isoformat(),
            "note": f"USER_SELECTED_HEALTHY_{self.ap_name}"
        }
        
        url = f"{MOCK_SERVER_URL}/networks/{NETWORK_ID}/appliance/settings"
        
        try:
            async with self.session.post(url, json=settings) as response:
                if response.status == 200:
                    print(f"✅ Appliance Settings: HEALTHY")
                    print(f"   └─ Latency: {settings['latencyMs']}ms ✅")
                    print(f"   └─ Packet Loss: {settings['packetLossPct']}% ✅")
                    print(f"   └─ Jitter: {settings['jitterMs']}ms ✅")
                    print(f"   └─ WAN1: active ✅, WAN2: active ✅")
                else:
                    print(f"⚠️  Failed to update appliance settings: {response.status}")
        except Exception as e:
            print(f"❌ Error updating appliance settings: {e}")
    
    async def update_mock_data(self):
        """Update comprehensive mock data with healthy state for selected AP only"""
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
                        "latencyMs": HEALTHY_METRICS["latencyMs"],
                        "packetLossPct": HEALTHY_METRICS["packetLossPct"],
                        "jitterMs": HEALTHY_METRICS["jitterMs"],
                        "degradedLinks": [
                            {"uplink": "wan1", "status": "active"},
                            {"uplink": "wan2", "status": "active"}
                        ],
                        "updated_at": datetime.now().isoformat(),
                        "note": f"USER_SELECTED_HEALTHY_{self.ap_name}"
                    })
            
            # Update device loss and latency history
            if "device_loss_and_latency_history" not in data:
                data["device_loss_and_latency_history"] = {}
            
            if DEVICE_SERIAL not in data["device_loss_and_latency_history"]:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = []
            
            # Add healthy history entries
            for i in range(10):
                entry = {
                    "ts": datetime.now().isoformat(),
                    "latencyMs": HEALTHY_METRICS["latencyMs"],
                    "lossPercent": HEALTHY_METRICS["packetLossPct"],
                    "jitter": HEALTHY_METRICS["jitterMs"],
                    "goodput": HEALTHY_METRICS["goodput"],
                    "destinationIp": "8.8.8.8",
                    "note": f"USER_SELECTED_HEALTHY_{self.ap_name}"
                }
                data["device_loss_and_latency_history"][DEVICE_SERIAL].append(entry)
            
            # Keep last 30 entries
            if len(data["device_loss_and_latency_history"][DEVICE_SERIAL]) > 30:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = \
                    data["device_loss_and_latency_history"][DEVICE_SERIAL][-30:]
            
            # Update wireless usage history - ONLY for selected AP
            if "network_wireless_usage_history" not in data:
                data["network_wireless_usage_history"] = {}
            if NETWORK_ID not in data["network_wireless_usage_history"]:
                data["network_wireless_usage_history"][NETWORK_ID] = []
            
            # Remove only selected AP's old entries, keep all others intact
            existing_history = data["network_wireless_usage_history"][NETWORK_ID]
            other_history = [entry for entry in existing_history if entry.get("deviceSerial") != self.ap_serial]
            
            base_time = datetime.now() - timedelta(minutes=30)
            wireless_history = []
            
            # Create healthy metrics for selected AP only
            for i in range(6):
                bucket_start = base_time + timedelta(minutes=i*5)
                bucket_end = bucket_start + timedelta(minutes=5)
                
                # Add slight time-based variation
                variation = (i % 3) - 1  # -1, 0, 1
                
                entry = {
                    "bucketStart": bucket_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "bucketEnd": bucket_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "deviceSerial": self.ap_serial,
                    "ssid": "MCW-SanJose",
                    "channelUtilizationPercent": round(HEALTHY_PROFILE["channelUtilizationPercent"] + variation * 2, 1),
                    "airtimeUtilizationPercent": round(HEALTHY_PROFILE["channelUtilizationPercent"] + variation * 2.5, 1),
                    "retransmissionsPerMinute": max(1, HEALTHY_PROFILE["retransmissionsPerMinute"] + variation),
                    "avgSignalToNoise": round(HEALTHY_PROFILE["avgSignalToNoise"] + variation * 0.5, 1),
                    "avgRssi": HEALTHY_PROFILE["avgRssi"] + variation,
                    "clientCount": max(1, HEALTHY_PROFILE["clientCount"] + variation),
                    "uplinkSpeedMbps": 920 - int(HEALTHY_PROFILE["channelUtilizationPercent"] * 3),
                    "downlinkSpeedMbps": 890 - int(HEALTHY_PROFILE["channelUtilizationPercent"] * 3),
                    "note": f"USER_SELECTED_HEALTHY_{self.ap_name}"
                }
                wireless_history.append(entry)
            
            # Combine: other APs (unchanged) + selected AP (healthy)
            data["network_wireless_usage_history"][NETWORK_ID] = other_history + wireless_history
            
            # Update wireless latency history - ONLY for selected AP
            if "network_wireless_latency_history" not in data:
                data["network_wireless_latency_history"] = {}
            if NETWORK_ID not in data["network_wireless_latency_history"]:
                data["network_wireless_latency_history"][NETWORK_ID] = []
            
            # Remove only selected AP's old entries, keep all others intact
            existing_latency = data["network_wireless_latency_history"][NETWORK_ID]
            other_latency = [entry for entry in existing_latency if entry.get("deviceMac") != self.ap_mac]
            
            latency_history = []
            
            # Create healthy latency data for selected AP only
            for i in range(6):
                slot_start = base_time + timedelta(minutes=i*5)
                slot_end = slot_start + timedelta(minutes=5)
                
                variation = (i % 3) - 1
                
                entry = {
                    "timeslotStart": slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "timeslotEnd": slot_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "latencyMs": max(5, HEALTHY_PROFILE["latencyMs"] + variation * 2),
                    "jitterMs": max(1, HEALTHY_PROFILE["jitterMs"] + variation),
                    "packetLossPercent": round(max(0.01, HEALTHY_PROFILE["packetLossPercent"] + variation * 0.05), 2),
                    "deviceMac": self.ap_mac,
                    "note": f"USER_SELECTED_HEALTHY_{self.ap_name}"
                }
                latency_history.append(entry)
            
            # Combine: other APs (unchanged) + selected AP (healthy)
            data["network_wireless_latency_history"][NETWORK_ID] = other_latency + latency_history
            
            # Update wireless health (overall network health improves)
            if "network_wireless_health" not in data:
                data["network_wireless_health"] = {}
            
            data["network_wireless_health"][NETWORK_ID] = {
                "windowStart": (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "windowEnd": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "overallHealthScore": 85,
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
                    "healthScore": 88
                },
                "bestApRecommendation": None,
                "note": f"USER_SELECTED_HEALTHY_{self.ap_name}"
            }
            
            # Clear failed connections for selected AP only
            if "network_wireless_failed_connections" not in data:
                data["network_wireless_failed_connections"] = {}
            if NETWORK_ID not in data["network_wireless_failed_connections"]:
                data["network_wireless_failed_connections"][NETWORK_ID] = []
            
            # Remove failed connections for selected AP only, keep others
            existing_failures = data["network_wireless_failed_connections"][NETWORK_ID]
            data["network_wireless_failed_connections"][NETWORK_ID] = [
                f for f in existing_failures if f.get("deviceSerial") != self.ap_serial
            ]
            
            # Update service impact predictions (improve for selected AP)
            if "service_impact_predictions" not in data:
                data["service_impact_predictions"] = {}
            
            data["service_impact_predictions"][NETWORK_ID] = {
                "sourceAp": None,
                "sourceApSerial": None,
                "window": f"{(datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')}/{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                "usersImpacted": 0,
                "failureProbability": 0.05,
                "recoveryLikelihood": "N/A",
                "recoveryReason": f"{self.ap_name} restored to healthy operation",
                "estimatedTimeToFailure": "Not applicable",
                "interventionPriority": "NONE",
                "recommendedFallbackAp": None,
                "reason": f"{self.ap_name} operating normally - excellent metrics",
                "applications": [
                    {"name": "Teams Video", "activeUserPercent": 62, "impactLevel": "none", "notes": "Operating normally - excellent quality"},
                    {"name": "VOIP", "activeUserPercent": 15, "impactLevel": "none", "notes": "Operating normally - crystal clear"},
                    {"name": "SSH Sessions", "activeUserPercent": 8, "impactLevel": "none", "notes": "Operating normally - responsive"},
                    {"name": "Email", "activeUserPercent": 20, "impactLevel": "none", "notes": "Operating normally"},
                    {"name": "File Transfers", "activeUserPercent": 12, "impactLevel": "none", "notes": "Operating normally - fast transfers"}
                ],
                "trendAnalysis": {
                    "channelUtilization": {"start": 18, "end": 18, "change": 0, "trend": "STABLE"},
                    "airtimeUtilization": {"start": 20, "end": 20, "change": 0, "trend": "STABLE"},
                    "retransmissions": {"start": 1, "end": 1, "change": 0, "trend": "STABLE"},
                    "signalSNR": {"start": 38, "end": 38, "change": 0, "trend": "STABLE"},
                    "uplinkSpeed": {"start": 920, "end": 920, "change": 0, "trend": "STABLE"},
                    "downlinkSpeed": {"start": 890, "end": 890, "change": 0, "trend": "STABLE"},
                    "clientLoad": {"start": 6, "end": 6, "change": 0, "trend": "STABLE"},
                    "pattern": f"HEALTHY - {self.ap_name} metrics stable within optimal ranges"
                },
                "currentThresholds": {
                    "latency": {"value": 7, "threshold": 60, "status": "EXCELLENT"},
                    "jitter": {"value": 0.8, "threshold": 20, "status": "EXCELLENT"},
                    "packetLoss": {"value": 0.03, "threshold": 3.0, "status": "EXCELLENT"}
                },
                "failoverCandidates": [],
                "executionPlan": [
                    {"step": 1, "action": "NO_ACTION_REQUIRED", "description": f"{self.ap_name} healthy, continue normal monitoring"}
                ],
                "note": f"USER_SELECTED_HEALTHY_{self.ap_name}"
            }
            
            # Update topology - mark selected AP as healthy
            if "network_topology_link_layer" in data and NETWORK_ID in data["network_topology_link_layer"]:
                topology = data["network_topology_link_layer"][NETWORK_ID]
                
                # Update node status for selected AP
                for node in topology.get("nodes", []):
                    if node.get("id") == self.ap_serial:
                        node["status"] = "healthy"
                
                # Update link status for selected AP
                for link in topology.get("links", []):
                    if link.get("source") == self.ap_serial or link.get("target") == self.ap_serial:
                        link["status"] = "ok"
                        if link.get("source") == DEVICE_SERIAL or link.get("target") == DEVICE_SERIAL:
                            link["latencyMs"] = 3
                            link["lossPercent"] = 0.05
                        else:
                            link["latencyMs"] = 5
                            link["lossPercent"] = 0.1
            
            # Update floor plans - improve stability score for selected AP
            if "network_floor_plans" in data and NETWORK_ID in data["network_floor_plans"]:
                for floor_plan in data["network_floor_plans"][NETWORK_ID]:
                    for coord in floor_plan.get("apCoordinates", []):
                        if coord.get("deviceSerial") == self.ap_serial:
                            coord["rfCoverageMeters"] = 25
                            coord["historicalStabilityScore"] = 94
            
            # Set uplinks to active
            if "organization_uplinks_statuses" in data and ORGANIZATION_ID in data["organization_uplinks_statuses"]:
                for device in data["organization_uplinks_statuses"][ORGANIZATION_ID]:
                    if device.get("networkId") == NETWORK_ID:
                        for uplink in device.get("uplinks", []):
                            uplink["status"] = "active"
                        device["lastReportedAt"] = datetime.now().isoformat()
            
            # UPDATE WIRELESS CHANNEL UTILIZATION - THIS IS WHAT AGENT 1 READS FOR RISK SCORES
            if "wireless_channel_utilization" not in data:
                data["wireless_channel_utilization"] = []
            
            # Find and update only the selected AP's channel utilization
            ap_found = False
            for ap_data in data["wireless_channel_utilization"]:
                if ap_data.get("serial") == self.ap_serial:
                    ap_found = True
                    # Update to healthy metrics
                    ap_data["wifi0"] = {
                        "utilization": {"total": 18, "wifi": 12, "nonWifi": 6},
                        "channelWidth": 20,
                        "channel": 6
                    }
                    ap_data["wifi1"] = {
                        "utilization": {"total": 15, "wifi": 10, "nonWifi": 5},
                        "channelWidth": 40,
                        "channel": 36
                    }
                    ap_data["signalToNoiseRatio"] = {
                        "wifi0": {"avg": 38, "min": 32, "max": 42},
                        "wifi1": {"avg": 40, "min": 35, "max": 45}
                    }
                    ap_data["retransmissions"] = {"rate": 1.2, "perMinute": 1}
                    ap_data["airtime"] = {"utilization": 20}
                    ap_data["clientCount"] = 6
                    ap_data["status"] = "healthy"
                    ap_data["note"] = f"USER_SELECTED_HEALTHY_{self.ap_name}"
                    break
            
            # If AP not found in channel utilization, add it
            if not ap_found:
                data["wireless_channel_utilization"].append({
                    "serial": self.ap_serial,
                    "name": self.ap_name,
                    "mac": self.ap_mac,
                    "network": {"id": NETWORK_ID, "name": "MCW San Jose New"},
                    "wifi0": {
                        "utilization": {"total": 18, "wifi": 12, "nonWifi": 6},
                        "channelWidth": 20,
                        "channel": 6
                    },
                    "wifi1": {
                        "utilization": {"total": 15, "wifi": 10, "nonWifi": 5},
                        "channelWidth": 40,
                        "channel": 36
                    },
                    "signalToNoiseRatio": {
                        "wifi0": {"avg": 38, "min": 32, "max": 42},
                        "wifi1": {"avg": 40, "min": 35, "max": 45}
                    },
                    "retransmissions": {"rate": 1.2, "perMinute": 1},
                    "airtime": {"utilization": 20},
                    "clientCount": 6,
                    "status": "healthy",
                    "note": f"USER_SELECTED_HEALTHY_{self.ap_name}"
                })
            
            # Write back
            with open(mock_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ WIRELESS TELEMETRY: {self.ap_name} RESTORED TO HEALTHY")
            print(f"   └─ {self.ap_name}: Channel Util: 18% ✅ EXCELLENT")
            print(f"   └─ {self.ap_name}: SNR: 38dB ✅ EXCELLENT")
            print(f"   └─ {self.ap_name}: Retransmissions: 1/min ✅ MINIMAL")
            print(f"   └─ {self.ap_name}: Latency: 7ms ✅ EXCELLENT")
            print(f"   └─ {self.ap_name}: Packet Loss: 0.03% ✅ MINIMAL")
            
            other_aps_count = len([ap for ap in ALL_APS if ap["serial"] != self.ap_serial])
            print(f"   └─ Other {other_aps_count} APs: Unchanged (existing state preserved) ✓")
            
        except Exception as e:
            print(f"❌ Error updating mock data: {e}")
            import traceback
            traceback.print_exc()
    
    async def run_scenario(self):
        """Apply the healthy scenario to selected AP"""
        print(f"\n✅ USER-SELECTED AP RECOVERY: {self.ap_name}")
        print("="*60)
        print(f"Restoring {self.ap_name} to healthy state - other APs remain in their current state...")
        print("-"*60)
        
        await self.update_appliance_settings()
        await self.update_mock_data()
        
        print("\n" + "="*60)
        print(f"✅ SCENARIO APPLIED: {self.ap_name} HEALTHY")
        print("="*60)
        print("\n📋 NETWORK STATE SUMMARY:")
        print("-"*60)
        print(f"  Restored AP:     {self.ap_name} ({self.ap_serial}) ✅")
        
        other_aps_count = len([ap for ap in ALL_APS if ap["serial"] != self.ap_serial])
        print(f"  Other APs:       {other_aps_count} APs (existing state preserved)")
        print(f"  Latency:         {HEALTHY_METRICS['latencyMs']}ms     ✅ EXCELLENT")
        print(f"  Packet Loss:     {HEALTHY_METRICS['packetLossPct']}%      ✅ MINIMAL")
        print(f"  Jitter:          {HEALTHY_METRICS['jitterMs']}ms      ✅ STABLE")
        print(f"  Channel Util:    18%          ✅ COMFORTABLE")
        print(f"  SNR:             38dB         ✅ EXCELLENT")
        print("-"*60)
        print("\n💡 Expected Agent Response: HEALTHY")
        print(f"   → Should identify {self.ap_name} as healthy/recovered")
        print(f"   → Risk score should be low (~12-15)")
        print("="*60)


def display_available_aps():
    """Display available APs and get user selection"""
    print("\n" + "="*60)
    print("           AVAILABLE ACCESS POINTS")
    print("="*60)
    print("\n  #  | AP Name | Serial Number      | MAC Address")
    print("-" * 60)
    
    for i, ap in enumerate(ALL_APS, 1):
        print(f"  {i}  | {ap['name']:7} | {ap['serial']:18} | {ap['mac']}")
    
    print("="*60)
    
    while True:
        try:
            choice = input("\nSelect AP to restore to healthy (1-5) or 'q' to quit: ").strip().lower()
            
            if choice == 'q':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(ALL_APS):
                selected_ap = ALL_APS[choice_num - 1]
                print(f"\n✓ Selected: {selected_ap['name']} ({selected_ap['serial']})")
                
                confirm = input(f"  Confirm restoring {selected_ap['name']} to healthy? (y/n): ").strip().lower()
                if confirm == 'y':
                    return selected_ap
                else:
                    print("  Selection cancelled. Choose again.\n")
            else:
                print(f"  ⚠️  Please enter a number between 1 and {len(ALL_APS)}")
        except ValueError:
            print("  ⚠️  Invalid input. Please enter a number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled by user")
            return None


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║      USER-SELECTED AP RECOVERY - Interactive Scenario        ║
║                                                              ║
║  This script allows you to select which specific AP should  ║
║  be restored to healthy state while keeping all other APs   ║
║  in their current state.                                    ║
║                                                              ║
║  Perfect for testing recovery scenarios and validating      ║
║  agent responses to AP restoration.                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    selected_ap = display_available_aps()
    
    if selected_ap is None:
        print("\n👋 Exiting without making changes.")
        return
    
    scenario = UserSelectedAPHealthy(selected_ap)
    
    try:
        await scenario.initialize()
        await scenario.run_scenario()
    except Exception as e:
        print(f"\n❌ Scenario failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scenario.close()


if __name__ == "__main__":
    asyncio.run(main())
