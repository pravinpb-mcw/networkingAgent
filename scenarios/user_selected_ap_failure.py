#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USER-SELECTED AP FAILURE - Interactive Scenario
Allows user to select which specific AP should fail while keeping others healthy.
This simulates targeted AP failure for testing specific scenarios.
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

# Critical failure values
FAILURE_VALUES = {
    "latencyMs": 350.0,
    "packetLossPct": 12.0,
    "jitterMs": 55.0,
    "goodput": 42.0
}

# Healthy baseline for other APs
HEALTHY_APS_CONFIG = [
    {"util": 22, "snr": 37.0, "retrans": 2, "rssi": -54, "latency": 8, "jitter": 2, "loss": 0.3},
    {"util": 28, "snr": 35.5, "retrans": 3, "rssi": -56, "latency": 10, "jitter": 3, "loss": 0.5},
    {"util": 34, "snr": 34.0, "retrans": 5, "rssi": -58, "latency": 12, "jitter": 4, "loss": 0.7},
    {"util": 38, "snr": 32.5, "retrans": 7, "rssi": -60, "latency": 14, "jitter": 5, "loss": 0.9}
]


class UserSelectedAPFailure:
    """Simulates failure of user-selected AP only"""
    
    def __init__(self, selected_ap: Dict[str, str]):
        self.session = None
        self.selected_ap = selected_ap
        self.ap_serial = selected_ap["serial"]
        self.ap_name = selected_ap["name"]
        self.ap_mac = selected_ap["mac"]
        
        # Get healthy APs (all except selected)
        self.healthy_aps = [ap for ap in ALL_APS if ap["serial"] != self.ap_serial]
        
        # Find best fallback AP (first healthy one that's not the failing one)
        self.fallback_ap = self.healthy_aps[0] if self.healthy_aps else None
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 User-Selected AP Failure Scenario Initialized")
        print(f"🎯 Target: {self.ap_name} ({self.ap_serial})")
        print("="*60)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    async def update_appliance_settings(self):
        """Update appliance settings with critical failure metrics"""
        settings = {
            "latencyMs": FAILURE_VALUES["latencyMs"],
            "packetLossPct": FAILURE_VALUES["packetLossPct"],
            "jitterMs": FAILURE_VALUES["jitterMs"],
            "degradedLinks": [
                {"uplink": "wan1", "status": "failed"},
                {"uplink": "wan2", "status": "failed"}
            ],
            "updated_at": datetime.now().isoformat(),
            "note": f"USER_SELECTED_FAILURE_{self.ap_name}"
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
        """Update comprehensive mock data with failure for selected AP only"""
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
                        "latencyMs": FAILURE_VALUES["latencyMs"],
                        "packetLossPct": FAILURE_VALUES["packetLossPct"],
                        "jitterMs": FAILURE_VALUES["jitterMs"],
                        "degradedLinks": [
                            {"uplink": "wan1", "status": "failed"},
                            {"uplink": "wan2", "status": "failed"}
                        ],
                        "updated_at": datetime.now().isoformat(),
                        "note": f"USER_SELECTED_FAILURE_{self.ap_name}"
                    })
            
            # Create failure history
            if "device_loss_and_latency_history" not in data:
                data["device_loss_and_latency_history"] = {}
            
            failure_history = []
            base_latency = 50.0
            base_loss = 2.0
            base_jitter = 15.0
            base_goodput = 85.0
            
            for i in range(15):
                progress = i / 14
                entry = {
                    "ts": datetime.now().isoformat(),
                    "latencyMs": round(base_latency + (FAILURE_VALUES["latencyMs"] - base_latency) * progress + random.uniform(-10, 20), 2),
                    "lossPercent": round(base_loss + (FAILURE_VALUES["packetLossPct"] - base_loss) * progress + random.uniform(-0.5, 1), 2),
                    "jitter": round(base_jitter + (FAILURE_VALUES["jitterMs"] - base_jitter) * progress + random.uniform(-2, 5), 2),
                    "goodput": round(base_goodput - (base_goodput - FAILURE_VALUES["goodput"]) * progress + random.uniform(-3, 2), 1),
                    "destinationIp": "8.8.8.8"
                }
                failure_history.append(entry)
            
            data["device_loss_and_latency_history"][DEVICE_SERIAL] = failure_history
            
            # Update wireless usage history
            if "network_wireless_usage_history" not in data:
                data["network_wireless_usage_history"] = {}
            if NETWORK_ID not in data["network_wireless_usage_history"]:
                data["network_wireless_usage_history"][NETWORK_ID] = []
            
            # Remove only selected AP's old entries, keep all others intact
            existing_history = data["network_wireless_usage_history"][NETWORK_ID]
            other_history = [entry for entry in existing_history if entry.get("deviceSerial") != self.ap_serial]
            
            base_time = datetime.now() - timedelta(minutes=30)
            
            # Create failure progression for selected AP
            channel_util_progression = [48.0, 65.0, 78.0, 88.0, 94.0, 96.5]
            snr_progression = [31.0, 27.0, 23.0, 20.0, 17.5, 16.0]
            retrans_progression = [12, 22, 34, 44, 52, 58]
            rssi_progression = [-58, -62, -65, -68, -70, -72]
            uplink_progression = [850, 680, 520, 400, 320, 260]
            downlink_progression = [780, 580, 420, 320, 240, 170]
            
            wireless_history = []
            for i in range(6):
                bucket_start = base_time + timedelta(minutes=i*5)
                bucket_end = bucket_start + timedelta(minutes=5)
                entry = {
                    "bucketStart": bucket_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "bucketEnd": bucket_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "deviceSerial": self.ap_serial,
                    "ssid": "MCW-SanJose",
                    "channelUtilizationPercent": round(channel_util_progression[i] + random.uniform(-1, 2), 1),
                    "airtimeUtilizationPercent": round(channel_util_progression[i] + 2 + random.uniform(-1, 2), 1),
                    "retransmissionsPerMinute": retrans_progression[i] + random.randint(-2, 4),
                    "avgSignalToNoise": round(snr_progression[i] + random.uniform(-0.5, 0.5), 1),
                    "avgRssi": rssi_progression[i] + random.randint(-1, 1),
                    "clientCount": 22 + i * 3 + random.randint(-1, 2),
                    "uplinkSpeedMbps": uplink_progression[i] + random.randint(-30, 20),
                    "downlinkSpeedMbps": downlink_progression[i] + random.randint(-20, 15),
                    "note": f"USER_SELECTED_FAILURE_{self.ap_name}"
                }
                wireless_history.append(entry)
            
            data["network_wireless_usage_history"][NETWORK_ID] = other_history + wireless_history
            
            # Update wireless latency history
            if "network_wireless_latency_history" not in data:
                data["network_wireless_latency_history"] = {}
            if NETWORK_ID not in data["network_wireless_latency_history"]:
                data["network_wireless_latency_history"][NETWORK_ID] = []
            
            # Remove only selected AP's old entries, keep all others intact
            existing_latency = data["network_wireless_latency_history"][NETWORK_ID]
            other_latency = [entry for entry in existing_latency if entry.get("deviceMac") != self.ap_mac]
            
            latency_history = []
            
            # Failure latency for selected AP
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
                    "deviceMac": self.ap_mac,
                    "note": f"USER_SELECTED_FAILURE_{self.ap_name}"
                }
                latency_history.append(entry)
            
            data["network_wireless_latency_history"][NETWORK_ID] = other_latency + latency_history
            
            # Update wireless health
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
                    }
                }
            }
            
            # Update failed connections for selected AP only
            if "network_wireless_failed_connections" not in data:
                data["network_wireless_failed_connections"] = {}
            if NETWORK_ID not in data["network_wireless_failed_connections"]:
                data["network_wireless_failed_connections"][NETWORK_ID] = []
            
            # Remove old failures for selected AP, keep others
            existing_failures = data["network_wireless_failed_connections"][NETWORK_ID]
            other_failures = [f for f in existing_failures if f.get("deviceSerial") != self.ap_serial]
            
            # Add failures for selected AP
            selected_ap_failures = [
                {"eventTime": (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": self.ap_serial, "clientMac": "AA:BB:CC:DD:EE:01", "failureReason": "auth_failure", "ssid": "MCW-SanJose", "apMac": self.ap_mac},
                {"eventTime": (datetime.now() - timedelta(minutes=12)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": self.ap_serial, "clientMac": "AA:BB:CC:DD:EE:02", "failureReason": "dhcp_timeout", "ssid": "MCW-SanJose", "apMac": self.ap_mac},
                {"eventTime": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": self.ap_serial, "clientMac": "AA:BB:CC:DD:EE:03", "failureReason": "association_rejected", "ssid": "MCW-SanJose", "apMac": self.ap_mac},
                {"eventTime": (datetime.now() - timedelta(minutes=8)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": self.ap_serial, "clientMac": "AA:BB:CC:DD:EE:04", "failureReason": "auth_failure", "ssid": "MCW-SanJose", "apMac": self.ap_mac},
                {"eventTime": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": self.ap_serial, "clientMac": "AA:BB:CC:DD:EE:05", "failureReason": "dhcp_timeout", "ssid": "MCW-SanJose", "apMac": self.ap_mac},
                {"eventTime": (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": self.ap_serial, "clientMac": "AA:BB:CC:DD:EE:06", "failureReason": "deauthentication", "ssid": "MCW-SanJose", "apMac": self.ap_mac}
            ]
            
            data["network_wireless_failed_connections"][NETWORK_ID] = other_failures + selected_ap_failures
            
            # Update service impact predictions
            fallback_name = self.fallback_ap["name"] if self.fallback_ap else "N/A"
            fallback_serial = self.fallback_ap["serial"] if self.fallback_ap else "N/A"
            
            data["service_impact_predictions"] = {
                NETWORK_ID: {
                    "sourceAp": self.ap_name,
                    "sourceApSerial": self.ap_serial,
                    "window": f"{(datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')}/{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                    "usersImpacted": 22,
                    "failureProbability": 0.92,
                    "recoveryLikelihood": "NONE",
                    "recoveryReason": f"Critical cascade on {self.ap_name} with sustained worsening - no recovery pattern visible",
                    "estimatedTimeToFailure": "5-10 minutes",
                    "interventionPriority": "CRITICAL",
                    "recommendedFallbackAp": fallback_name,
                    "reason": f"CRITICAL: {self.ap_name} multiple correlated failures - immediate intervention required",
                    "applications": [
                        {"name": "Teams Video", "activeUserPercent": 62, "impactLevel": "critical", "notes": "CRITICAL RISK - video freezing"},
                        {"name": "VOIP", "activeUserPercent": 15, "impactLevel": "critical", "notes": "UNAVAILABLE - jitter >30ms"},
                        {"name": "SSH Sessions", "activeUserPercent": 8, "impactLevel": "high", "notes": "HIGH RISK - terminal lag"},
                        {"name": "Email", "activeUserPercent": 20, "impactLevel": "high", "notes": "SEVERELY DEGRADED"},
                        {"name": "File Transfers", "activeUserPercent": 12, "impactLevel": "critical", "notes": "CRITICAL RISK - timeouts"}
                    ],
                    "trendAnalysis": {
                        "channelUtilization": {"start": 66, "end": 89, "change": 35, "trend": "WORSENING"},
                        "airtimeUtilization": {"start": 71, "end": 92, "change": 30, "trend": "WORSENING"},
                        "retransmissions": {"start": 16, "end": 44, "change": 175, "trend": "WORSENING"},
                        "signalSNR": {"start": 26.5, "end": 18.1, "change": -32, "trend": "WORSENING"},
                        "pattern": f"CRITICAL CASCADE on {self.ap_name} - No recovery in last 2 buckets"
                    },
                    "currentThresholds": {
                        "latency": {"value": 65, "threshold": 60, "status": "CRITICAL"},
                        "jitter": {"value": 22, "threshold": 20, "status": "CRITICAL"},
                        "packetLoss": {"value": 3.2, "threshold": 3.0, "status": "CRITICAL"}
                    },
                    "failoverCandidates": [
                        {
                            "rank": 1,
                            "apName": fallback_name,
                            "apSerial": fallback_serial,
                            "score": 92,
                            "reason": "Best available alternative - low load, good signal"
                        }
                    ]
                }
            }
            
            # Update topology - show all APs, selected one failing
            nodes = [{"type": "appliance", "id": DEVICE_SERIAL, "name": "San Jose MX64", "uplink": "wan1", "status": "degraded"}]
            links = []
            
            for ap in ALL_APS:
                status = "failing" if ap["serial"] == self.ap_serial else "healthy"
                nodes.append({"type": "wireless", "id": ap["serial"], "name": ap["name"], "floorPlanId": "FP-FLR1", "status": status})
                
                link_status = "critical" if ap["serial"] == self.ap_serial else "ok"
                latency = 45 if ap["serial"] == self.ap_serial else 3
                loss = 4.5 if ap["serial"] == self.ap_serial else 0.05
                links.append({"source": DEVICE_SERIAL, "target": ap["serial"], "linkType": "wired", "status": link_status, "latencyMs": latency, "lossPercent": loss})
            
            # Mesh links
            for i in range(len(ALL_APS) - 1):
                link_status = "critical" if ALL_APS[i]["serial"] == self.ap_serial or ALL_APS[i+1]["serial"] == self.ap_serial else "ok"
                latency = 35 if link_status == "critical" else 5
                loss = 3.2 if link_status == "critical" else 0.1
                links.append({"source": ALL_APS[i]["serial"], "target": ALL_APS[i+1]["serial"], "linkType": "wireless-mesh", "status": link_status, "latencyMs": latency, "lossPercent": loss})
            
            data["network_topology_link_layer"] = {
                NETWORK_ID: {
                    "nodes": nodes,
                    "links": links
                }
            }
            
            # Update floor plans
            data["network_floor_plans"] = {
                NETWORK_ID: [{
                    "floorPlanId": "FP-FLR1",
                    "name": "San Jose HQ - Floor 1",
                    "center": {"lat": 37.4232, "lng": -122.0841},
                    "apCoordinates": [
                        {"deviceSerial": "Q2XX-ABCD-1234", "x": 12.4, "y": 6.1, "rfCoverageMeters": 15 if "Q2XX-ABCD-1234" == self.ap_serial else 25, "historicalStabilityScore": 18 if "Q2XX-ABCD-1234" == self.ap_serial else 92},
                        {"deviceSerial": "Q2XX-AP06-5678", "x": 35.2, "y": 8.7, "rfCoverageMeters": 15 if "Q2XX-AP06-5678" == self.ap_serial else 25, "historicalStabilityScore": 18 if "Q2XX-AP06-5678" == self.ap_serial else 92},
                        {"deviceSerial": "Q2XX-AP01-1111", "x": 45.2, "y": 11.7, "rfCoverageMeters": 15 if "Q2XX-AP01-1111" == self.ap_serial else 25, "historicalStabilityScore": 18 if "Q2XX-AP01-1111" == self.ap_serial else 89},
                        {"deviceSerial": "Q2XX-AP04-4444", "x": 55.2, "y": 6.7, "rfCoverageMeters": 15 if "Q2XX-AP04-4444" == self.ap_serial else 25, "historicalStabilityScore": 18 if "Q2XX-AP04-4444" == self.ap_serial else 91},
                        {"deviceSerial": "Q2XX-AP08-8888", "x": 65.2, "y": 11.7, "rfCoverageMeters": 15 if "Q2XX-AP08-8888" == self.ap_serial else 25, "historicalStabilityScore": 18 if "Q2XX-AP08-8888" == self.ap_serial else 88}
                    ],
                    "note": f"USER_SELECTED_FAILURE_{self.ap_name}"
                }]
            }
            
            print(f"🔴 WIRELESS TELEMETRY: {self.ap_name} CRITICAL FAILURE")
            print(f"   └─ {self.ap_name}: Channel Util: 48% → 96.5% ❌ SATURATED")
            print(f"   └─ {self.ap_name}: SNR: 31dB → 16dB ❌ BELOW THRESHOLD")
            print(f"   └─ {self.ap_name}: Retransmissions: 12/min → 58/min ❌ CRITICAL")
            print(f"   └─ {self.ap_name}: Latency: 28ms → 155ms ❌ CRITICAL")
            print(f"   └─ {self.ap_name}: Packet Loss: 0.8% → 12% ❌ SEVERE")
            print(f"   └─ Other {len(self.healthy_aps)} APs: Unchanged (existing state preserved) ✓")
            
            # Set clients to offline
            online_count = 0
            offline_count = 0
            if "network_clients" in data and NETWORK_ID in data["network_clients"]:
                for i, client in enumerate(data["network_clients"][NETWORK_ID]):
                    if i % 5 < 3:
                        client["status"] = "Offline"
                        offline_count += 1
                    else:
                        client["status"] = "Online"
                        online_count += 1
                    client["lastSeen"] = datetime.now().isoformat()
            
            # Set uplinks to failed
            if "organization_uplinks_statuses" in data and ORGANIZATION_ID in data["organization_uplinks_statuses"]:
                for device in data["organization_uplinks_statuses"][ORGANIZATION_ID]:
                    if device.get("networkId") == NETWORK_ID:
                        for uplink in device.get("uplinks", []):
                            uplink["status"] = "failed"
                        device["lastReportedAt"] = datetime.now().isoformat()
            
            # UPDATE WIRELESS CHANNEL UTILIZATION - THIS IS WHAT AGENT 1 READS FOR RISK SCORES
            if "wireless_channel_utilization" not in data:
                data["wireless_channel_utilization"] = []
            
            # Find and update only the selected AP's channel utilization to CRITICAL
            ap_found = False
            for ap_data in data["wireless_channel_utilization"]:
                if ap_data.get("serial") == self.ap_serial:
                    ap_found = True
                    # Update to critical failure metrics
                    ap_data["wifi0"] = {
                        "utilization": {"total": 96, "wifi": 85, "nonWifi": 11},
                        "channelWidth": 20,
                        "channel": 6
                    }
                    ap_data["wifi1"] = {
                        "utilization": {"total": 94, "wifi": 82, "nonWifi": 12},
                        "channelWidth": 40,
                        "channel": 36
                    }
                    ap_data["signalToNoiseRatio"] = {
                        "wifi0": {"avg": 14, "min": 8, "max": 18},
                        "wifi1": {"avg": 12, "min": 6, "max": 16}
                    }
                    ap_data["retransmissions"] = {"rate": 58.5, "perMinute": 58}
                    ap_data["airtime"] = {"utilization": 92}
                    ap_data["clientCount"] = 45
                    ap_data["status"] = "critical"
                    ap_data["note"] = f"USER_SELECTED_FAILURE_{self.ap_name}"
                    break
            
            # If AP not found in channel utilization, add it with critical values
            if not ap_found:
                data["wireless_channel_utilization"].append({
                    "serial": self.ap_serial,
                    "name": self.ap_name,
                    "mac": self.ap_mac,
                    "network": {"id": NETWORK_ID, "name": "MCW San Jose New"},
                    "wifi0": {
                        "utilization": {"total": 96, "wifi": 85, "nonWifi": 11},
                        "channelWidth": 20,
                        "channel": 6
                    },
                    "wifi1": {
                        "utilization": {"total": 94, "wifi": 82, "nonWifi": 12},
                        "channelWidth": 40,
                        "channel": 36
                    },
                    "signalToNoiseRatio": {
                        "wifi0": {"avg": 14, "min": 8, "max": 18},
                        "wifi1": {"avg": 12, "min": 6, "max": 16}
                    },
                    "retransmissions": {"rate": 58.5, "perMinute": 58},
                    "airtime": {"utilization": 92},
                    "clientCount": 45,
                    "status": "critical",
                    "note": f"USER_SELECTED_FAILURE_{self.ap_name}"
                })
            
            # Write back
            with open(mock_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"🔴 CLIENT STATUS:")
            print(f"   └─ {online_count} online, {offline_count} OFFLINE ❌")
            print(f"🔴 UPLINKS: ALL FAILED ❌")
            print(f"🔴 HEALTH SCORE: 28 ❌ CRITICAL")
            
        except Exception as e:
            print(f"❌ Error updating mock data: {e}")
            import traceback
            traceback.print_exc()
    
    async def run_scenario(self):
        """Apply the failure scenario to selected AP"""
        print(f"\n🔴 USER-SELECTED AP FAILURE: {self.ap_name}")
        print("="*60)
        print(f"Failing {self.ap_name} only - other {len(self.healthy_aps)} APs remain in their current state...")
        print("-"*60)
        
        await self.update_appliance_settings()
        await self.update_mock_data()
        
        print("\n" + "="*60)
        print(f"🔴 SCENARIO APPLIED: {self.ap_name} FAILURE")
        print("="*60)
        print("\n📋 NETWORK STATE SUMMARY:")
        print("-"*60)
        print(f"  Failed AP:       {self.ap_name} ({self.ap_serial}) ❌")
        print(f"  Other APs:       {len(self.healthy_aps)} APs (existing state preserved)")
        if self.fallback_ap:
            print(f"  Fallback AP:     {self.fallback_ap['name']} ({self.fallback_ap['serial']}) (recommended)")
        print(f"  Latency:         {FAILURE_VALUES['latencyMs']}ms     ❌ CRITICAL")
        print(f"  Packet Loss:     {FAILURE_VALUES['packetLossPct']}%      ❌ SEVERE")
        print(f"  Jitter:          {FAILURE_VALUES['jitterMs']}ms       ❌ CRITICAL")
        print(f"  Channel Util:    96.5%        ❌ SATURATED")
        print(f"  SNR:             16dB         ❌ BELOW THRESHOLD")
        print("-"*60)
        print("\n💡 Expected Agent Response: CRITICAL FAILURE")
        print(f"   → Should identify {self.ap_name} as failing")
        print(f"   → Should recommend failover to {self.fallback_ap['name'] if self.fallback_ap else 'N/A'}")
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
            choice = input("\nSelect AP to fail (1-5) or 'q' to quit: ").strip().lower()
            
            if choice == 'q':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(ALL_APS):
                selected_ap = ALL_APS[choice_num - 1]
                print(f"\n✓ Selected: {selected_ap['name']} ({selected_ap['serial']})")
                
                confirm = input(f"  Confirm failing {selected_ap['name']}? (y/n): ").strip().lower()
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
║      USER-SELECTED AP FAILURE - Interactive Scenario         ║
║                                                              ║
║  This script allows you to select which specific AP should  ║
║  fail while keeping all other APs healthy.                  ║
║                                                              ║
║  Perfect for testing targeted failure scenarios and         ║
║  validating agent responses to specific AP failures.        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    selected_ap = display_available_aps()
    
    if selected_ap is None:
        print("\n👋 Exiting without making changes.")
        return
    
    scenario = UserSelectedAPFailure(selected_ap)
    
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
