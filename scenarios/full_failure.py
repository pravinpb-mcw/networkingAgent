#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCENARIO 4: FULL FAILURE - Everything Degraded
Simulates complete network failure with critical metrics across all dimensions.
This scenario represents imminent or active failure requiring immediate action.
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
            
            # Update wireless usage history - ONLY AP-03 shows failure, preserve others
            if "network_wireless_usage_history" not in data:
                data["network_wireless_usage_history"] = {}
            if NETWORK_ID not in data["network_wireless_usage_history"]:
                data["network_wireless_usage_history"][NETWORK_ID] = []
            
            # Remove only AP-03's old entries
            existing_history = data["network_wireless_usage_history"][NETWORK_ID]
            other_aps_history = [entry for entry in existing_history if entry.get("deviceSerial") != AP_SERIAL]
            
            # Define healthy APs with varied metrics (scores will range 15-19)
            healthy_aps = [
                {"serial": "Q2XX-AP06-5678", "name": "AP-06", "util": 22, "snr": 37.0, "retrans": 2, "rssi": -54},  # Score ~15
                {"serial": "Q2XX-AP01-1111", "name": "AP-01", "util": 28, "snr": 35.5, "retrans": 3, "rssi": -56},  # Score ~17
                {"serial": "Q2XX-AP04-4444", "name": "AP-04", "util": 34, "snr": 34.0, "retrans": 5, "rssi": -58},  # Score ~18
                {"serial": "Q2XX-AP08-8888", "name": "AP-08", "util": 38, "snr": 32.5, "retrans": 7, "rssi": -60}   # Score ~19
            ]
            
            # Create healthy metrics for other 4 APs
            base_time = datetime.now() - timedelta(minutes=30)
            wireless_history = []
            
            for ap in healthy_aps:
                for i in range(6):
                    bucket_start = base_time + timedelta(minutes=i*5)
                    bucket_end = bucket_start + timedelta(minutes=5)
                    entry = {
                        "bucketStart": bucket_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "bucketEnd": bucket_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "deviceSerial": ap["serial"],
                        "ssid": "MCW-SanJose",
                        "channelUtilizationPercent": round(ap["util"] + random.uniform(-1, 1), 1),
                        "airtimeUtilizationPercent": round(ap["util"] + 2 + random.uniform(-1, 1), 1),
                        "retransmissionsPerMinute": ap["retrans"] + random.randint(-1, 1),
                        "avgSignalToNoise": round(ap["snr"] + random.uniform(-0.3, 0.3), 1),
                        "avgRssi": ap["rssi"] + random.randint(-1, 1),
                        "clientCount": 3 + random.randint(-1, 2),
                        "uplinkSpeedMbps": 920 + random.randint(-20, 30),
                        "downlinkSpeedMbps": 850 + random.randint(-20, 30),
                        "note": "SCENARIO_4_FULL_FAILURE_HEALTHY"
                    }
                    wireless_history.append(entry)
            
            # Create failure progression for AP-03 ONLY
            # Note: wireless_history already contains healthy APs data, we're adding AP-03 to it
            # Progressive failure pattern for AP-03
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
            
            # Combine: healthy APs + AP-03 failure
            data["network_wireless_usage_history"][NETWORK_ID] = wireless_history
            
            # Update wireless latency history - Add healthy latency for other APs, failure for AP-03
            if "network_wireless_latency_history" not in data:
                data["network_wireless_latency_history"] = {}
            if NETWORK_ID not in data["network_wireless_latency_history"]:
                data["network_wireless_latency_history"][NETWORK_ID] = []
            
            # Healthy APs MAC addresses (must match organization_devices)
            healthy_ap_macs = [
                {"mac": "00:11:22:33:44:99", "latency": 8, "jitter": 2, "loss": 0.3},   # AP-06
                {"mac": "00:11:22:33:44:11", "latency": 10, "jitter": 3, "loss": 0.5},  # AP-01
                {"mac": "00:11:22:33:44:44", "latency": 12, "jitter": 4, "loss": 0.7},  # AP-04
                {"mac": "00:11:22:33:44:88", "latency": 14, "jitter": 5, "loss": 0.9}   # AP-08
            ]
            
            latency_history = []
            
            # Add healthy latency for other 4 APs
            for ap_mac in healthy_ap_macs:
                for i in range(6):
                    slot_start = base_time + timedelta(minutes=i*5)
                    slot_end = slot_start + timedelta(minutes=5)
                    entry = {
                        "timeslotStart": slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "timeslotEnd": slot_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "latencyMs": ap_mac["latency"] + random.randint(-2, 2),
                        "jitterMs": ap_mac["jitter"] + random.randint(-1, 1),
                        "packetLossPercent": round(ap_mac["loss"] + random.uniform(-0.1, 0.1), 2),
                        "deviceMac": ap_mac["mac"],
                        "note": "SCENARIO_4_FULL_FAILURE_HEALTHY"
                    }
                    latency_history.append(entry)
            
            # Create failure latency for AP-03 only
            # Note: latency_history already contains healthy APs data, we're adding AP-03 to it
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
            
            # Combine: healthy APs + AP-03 failure
            data["network_wireless_latency_history"][NETWORK_ID] = latency_history
            
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
                    }
                }
            }
            
            # Update failed connections for AP-03 ONLY
            
            # Update failed connections for AP-03 ONLY
            if "network_wireless_failed_connections" not in data:
                data["network_wireless_failed_connections"] = {}
            if NETWORK_ID not in data["network_wireless_failed_connections"]:
                data["network_wireless_failed_connections"][NETWORK_ID] = []
            
            # Remove old AP-03 failures, keep others
            existing_failures = data["network_wireless_failed_connections"][NETWORK_ID]
            other_failures = [f for f in existing_failures if f.get("deviceSerial") != AP_SERIAL]
            
            # Add new failures for AP-03
            ap03_failures = [
                {"eventTime": (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:01", "failureReason": "auth_failure", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                {"eventTime": (datetime.now() - timedelta(minutes=12)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:02", "failureReason": "dhcp_timeout", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                {"eventTime": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:03", "failureReason": "association_rejected", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                {"eventTime": (datetime.now() - timedelta(minutes=8)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:04", "failureReason": "auth_failure", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                {"eventTime": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:05", "failureReason": "dhcp_timeout", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"},
                {"eventTime": (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviceSerial": AP_SERIAL, "clientMac": "AA:BB:CC:DD:EE:06", "failureReason": "deauthentication", "ssid": "MCW-SanJose", "apMac": "00:11:22:33:44:55"}
            ]
            
            data["network_wireless_failed_connections"][NETWORK_ID] = other_failures + ap03_failures
            
            # Update service impact predictions - CRITICAL
            data["service_impact_predictions"] = {
                NETWORK_ID: {
                    "sourceAp": "AP-03",
                    "sourceApSerial": AP_SERIAL,
                    "window": f"{(datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')}/{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                    "usersImpacted": 22,
                    "failureProbability": 0.92,
                    "recoveryLikelihood": "NONE",
                    "recoveryReason": "Critical cascade with sustained worsening across all time buckets - no recovery pattern visible",
                    "estimatedTimeToFailure": "5-10 minutes",
                    "interventionPriority": "CRITICAL",
                    "recommendedFallbackAp": "AP-06",
                    "reason": "CRITICAL: Multiple correlated failures - immediate intervention required",
                    "applications": [
                        {"name": "Teams Video", "activeUserPercent": 62, "impactLevel": "critical", "notes": "CRITICAL RISK - 65ms latency + 3.2% packet loss will cause video freezing"},
                        {"name": "VOIP", "activeUserPercent": 15, "impactLevel": "critical", "notes": "UNAVAILABLE - jitter >30ms, loss >5%"},
                        {"name": "SSH Sessions", "activeUserPercent": 8, "impactLevel": "high", "notes": "HIGH RISK - 22ms jitter causing terminal lag and connection drops"},
                        {"name": "Email", "activeUserPercent": 20, "impactLevel": "high", "notes": "SEVERELY DEGRADED - loss >8%"},
                        {"name": "File Transfers", "activeUserPercent": 12, "impactLevel": "critical", "notes": "CRITICAL RISK - 58% speed degradation will timeout transfers"}
                    ],
                    "trendAnalysis": {
                        "channelUtilization": {"start": 66, "end": 89, "change": 35, "trend": "WORSENING"},
                        "airtimeUtilization": {"start": 71, "end": 92, "change": 30, "trend": "WORSENING"},
                        "retransmissions": {"start": 16, "end": 44, "change": 175, "trend": "WORSENING"},
                        "signalSNR": {"start": 26.5, "end": 18.1, "change": -32, "trend": "WORSENING"},
                        "uplinkSpeed": {"start": 850, "end": 360, "change": -58, "trend": "WORSENING"},
                        "downlinkSpeed": {"start": 780, "end": 350, "change": -55, "trend": "WORSENING"},
                        "clientLoad": {"start": 23, "end": 31, "change": 35, "trend": "WORSENING"},
                        "pattern": "CRITICAL CASCADE - No recovery in last 2 buckets, metrics accelerating toward failure"
                    },
                    "currentThresholds": {
                        "latency": {"value": 65, "threshold": 60, "status": "CRITICAL"},
                        "jitter": {"value": 22, "threshold": 20, "status": "CRITICAL"},
                        "packetLoss": {"value": 3.2, "threshold": 3.0, "status": "CRITICAL"}
                    },
                    "failoverCandidates": [
                        {
                            "rank": 1,
                            "apName": "AP-06",
                            "apSerial": "Q2XX-AP06-5678",
                            "score": 92,
                            "reason": "LOW LOAD (1 client), GOOD SIGNAL (-58dBm)",
                            "clientExpectations": [
                                {"clientName": "Anton-Laptop", "expectedRssi": -58, "expectedChannelUtil": 24},
                                {"clientName": "Teams-Room", "expectedRssi": -58, "expectedLatency": "low"}
                            ]
                        },
                        {
                            "rank": 2,
                            "apName": "AP-04",
                            "apSerial": "Q2XX-AP04-4444",
                            "score": 89,
                            "reason": "EXCELLENT SIGNAL (-52dBm), LOW LOAD (1 client)"
                        }
                    ]
                }
            }
            
            # Update topology - Show ALL 5 APs, only AP-03 is failing
            all_aps = [
                {"serial": "Q2XX-ABCD-1234", "name": "AP-03"},
                {"serial": "Q2XX-AP06-5678", "name": "AP-06"},
                {"serial": "Q2XX-AP01-1111", "name": "AP-01"},
                {"serial": "Q2XX-AP04-4444", "name": "AP-04"},
                {"serial": "Q2XX-AP08-8888", "name": "AP-08"}
            ]
            
            nodes = [{"type": "appliance", "id": DEVICE_SERIAL, "name": "San Jose MX64", "uplink": "wan1", "status": "degraded"}]
            links = []
            
            for ap in all_aps:
                status = "failing" if ap["serial"] == AP_SERIAL else "healthy"
                nodes.append({"type": "wireless", "id": ap["serial"], "name": ap["name"], "floorPlanId": "FP-FLR1", "status": status})
                
                # Links from appliance
                link_status = "critical" if ap["serial"] == AP_SERIAL else "ok"
                latency = 45 if ap["serial"] == AP_SERIAL else 3
                loss = 4.5 if ap["serial"] == AP_SERIAL else 0.05
                links.append({"source": DEVICE_SERIAL, "target": ap["serial"], "linkType": "wired", "status": link_status, "latencyMs": latency, "lossPercent": loss})
            
            # Mesh links between APs
            for i in range(len(all_aps) - 1):
                link_status = "critical" if all_aps[i]["serial"] == AP_SERIAL or all_aps[i+1]["serial"] == AP_SERIAL else "ok"
                latency = 35 if link_status == "critical" else 5
                loss = 3.2 if link_status == "critical" else 0.1
                links.append({"source": all_aps[i]["serial"], "target": all_aps[i+1]["serial"], "linkType": "wireless-mesh", "status": link_status, "latencyMs": latency, "lossPercent": loss})
            
            data["network_topology_link_layer"] = {
                NETWORK_ID: {
                    "nodes": nodes,
                    "links": links
                }
            }
            
            # Update floor plans - AP-03 critical, others healthy
            data["network_floor_plans"] = {
                NETWORK_ID: [{
                    "floorPlanId": "FP-FLR1",
                    "name": "San Jose HQ - Floor 1",
                    "center": {"lat": 37.4232, "lng": -122.0841},
                    "apCoordinates": [
                        {"deviceSerial": "Q2XX-ABCD-1234", "x": 12.4, "y": 6.1, "rfCoverageMeters": 15, "historicalStabilityScore": 18},
                        {"deviceSerial": "Q2XX-AP06-5678", "x": 35.2, "y": 8.7, "rfCoverageMeters": 25, "historicalStabilityScore": 92},
                        {"deviceSerial": "Q2XX-AP01-1111", "x": 45.2, "y": 11.7, "rfCoverageMeters": 25, "historicalStabilityScore": 89},
                        {"deviceSerial": "Q2XX-AP04-4444", "x": 55.2, "y": 6.7, "rfCoverageMeters": 25, "historicalStabilityScore": 91},
                        {"deviceSerial": "Q2XX-AP08-8888", "x": 65.2, "y": 11.7, "rfCoverageMeters": 25, "historicalStabilityScore": 88}
                    ],
                    "note": "SCENARIO_4_FULL_FAILURE"
                }]
            }
            
            print(f"🔴 WIRELESS TELEMETRY: AP-03 CRITICAL FAILURE (Other APs Healthy)")
            print(f"   └─ AP-03: Channel Util: 48% → 96.5% ❌ SATURATED")
            print(f"   └─ AP-03: SNR: 31dB → 16dB ❌ BELOW THRESHOLD")
            print(f"   └─ AP-03: Retransmissions: 12/min → 58/min ❌ CRITICAL")
            print(f"   └─ AP-03: Latency: 28ms → 155ms ❌ CRITICAL")
            print(f"   └─ AP-03: Packet Loss: 0.8% → 12% ❌ SEVERE")
            print(f"   └─ Other 4 APs: Remain Healthy ✓")
            
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
            with open(mock_file, 'w') as f:
                json.dump(data, f, indent=2)
            
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
============================================================
           SCENARIO 4: FULL NETWORK FAILURE                   
                                                              
  This script simulates complete network failure:            
    - Latency: ~350ms (CRITICAL)                             
    - Packet Loss: ~12% (SEVERE)                             
    - Jitter: ~55ms (CRITICAL)                               
    - Goodput: ~42% (FAILED)                                 
    - Channel Utilization: 96%+ (SATURATED)                  
    - SNR: ~16dB (BELOW THRESHOLD)                           
    - Both uplinks: FAILED                                   
    - 60% clients: OFFLINE                                   
                                                              
  Expected Agent Classification: LIKELY FAILURE              
  -> Risk Score: 85-100                                       
  -> Requires IMMEDIATE intervention                          
============================================================
    """)
    
    asyncio.run(main())
