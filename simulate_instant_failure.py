#!/usr/bin/env python3
"""
Simulate Instantaneous Network Failure
This script immediately causes catastrophic network failures in the mock Meraki server
to emulate sudden network outages (e.g., fiber cut, power loss, DDoS attack).

Simulated Metrics:
- Latency: Jumps to 1000ms+ (unreachable)
- Packet Loss: Jumps to 100% (complete loss)
- Jitter: Extreme spikes to 200ms+
- Device Status: All devices instantly go offline
- Uplink Status: All uplinks immediately fail
- Goodput: Drops to 0%
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import aiohttp

# Configuration
MOCK_SERVER_URL = "http://127.0.0.1:5000"
NETWORK_ID = "L_3947405073390239794"
ORGANIZATION_ID = "999781"
DEVICE_SERIAL = "Q2MN-Q3J9-YJHW"

# Catastrophic failure values
FAILURE_METRICS = {
    "latencyMs": 1500.0,
    "packetLossPct": 100.0,
    "jitterMs": 250.0,
    "goodput": 0.0
}


class InstantaneousFailureSimulator:
    """Simulates instant catastrophic network failure"""
    
    def __init__(self):
        self.session = None
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
        print("🔧 Instantaneous Failure Simulator Initialized")
        print("="*60)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    async def trigger_appliance_failure(self):
        """Immediately set appliance to failed state"""
        settings = {
            "latencyMs": FAILURE_METRICS["latencyMs"],
            "packetLossPct": FAILURE_METRICS["packetLossPct"],
            "jitterMs": FAILURE_METRICS["jitterMs"],
            "degradedLinks": [
                {
                    "uplink": "wan1",
                    "status": "failed"
                },
                {
                    "uplink": "wan2",
                    "status": "failed"
                }
            ],
            "updated_at": datetime.now().isoformat(),
            "note": "CATASTROPHIC_FAILURE"
        }
        
        url = f"{MOCK_SERVER_URL}/networks/{NETWORK_ID}/appliance/settings"
        
        try:
            async with self.session.post(url, json=settings) as response:
                if response.status == 200:
                    print("💥 APPLIANCE FAILURE TRIGGERED!")
                    print(f"   └─ Latency: {settings['latencyMs']}ms (CRITICAL)")
                    print(f"   └─ Packet Loss: {settings['packetLossPct']}% (TOTAL LOSS)")
                    print(f"   └─ Jitter: {settings['jitterMs']}ms (EXTREME)")
                    print(f"   └─ WAN1: FAILED")
                    print(f"   └─ WAN2: FAILED")
                else:
                    print(f"⚠️  Failed to trigger appliance failure: {response.status}")
        except Exception as e:
            print(f"❌ Error triggering appliance failure: {e}")
    
    async def trigger_device_failure(self):
        """Immediately add catastrophic device history entry"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "device_loss_and_latency_history" not in data:
                data["device_loss_and_latency_history"] = {}
            
            if DEVICE_SERIAL not in data["device_loss_and_latency_history"]:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = []
            
            # Add multiple failure entries to show severity
            for i in range(5):
                failure_entry = {
                    "ts": datetime.now().isoformat(),
                    "latencyMs": FAILURE_METRICS["latencyMs"],
                    "lossPercent": FAILURE_METRICS["packetLossPct"],
                    "jitter": FAILURE_METRICS["jitterMs"],
                    "goodput": FAILURE_METRICS["goodput"],
                    "destinationIp": "8.8.8.8",
                    "note": "CATASTROPHIC_FAILURE"
                }
                
                data["device_loss_and_latency_history"][DEVICE_SERIAL].append(failure_entry)
            
            # Keep only last 50 entries
            if len(data["device_loss_and_latency_history"][DEVICE_SERIAL]) > 50:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = \
                    data["device_loss_and_latency_history"][DEVICE_SERIAL][-50:]
            
            # Write back
            with open('mock_data/comprehensive_api_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print("💥 DEVICE HISTORY FAILURE TRIGGERED!")
            print(f"   └─ Latency: {FAILURE_METRICS['latencyMs']}ms (UNREACHABLE)")
            print(f"   └─ Packet Loss: {FAILURE_METRICS['packetLossPct']}% (TOTAL)")
            print(f"   └─ Goodput: {FAILURE_METRICS['goodput']}% (NONE)")
            
        except Exception as e:
            print(f"❌ Error triggering device failure: {e}")
    
    async def trigger_client_failure(self):
        """Immediately set all clients to offline"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "network_clients" in data and NETWORK_ID in data["network_clients"]:
                clients = data["network_clients"][NETWORK_ID]
                
                for client in clients:
                    client["status"] = "Offline"
                    client["lastSeen"] = datetime.now().isoformat()
                    client["usage"] = {
                        "sent": 0,
                        "recv": 0,
                        "total": 0
                    }
                
                # Write back
                with open('mock_data/comprehensive_api_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"💥 ALL CLIENTS OFFLINE!")
                print(f"   └─ Total Clients Affected: {len(clients)}")
                print(f"   └─ Online: 0")
                print(f"   └─ Offline: {len(clients)}")
                
        except Exception as e:
            print(f"❌ Error triggering client failure: {e}")
    
    async def trigger_uplink_failure(self):
        """Immediately fail all uplinks"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "organization_uplinks_statuses" in data and ORGANIZATION_ID in data["organization_uplinks_statuses"]:
                uplinks = data["organization_uplinks_statuses"][ORGANIZATION_ID]
                failed_count = 0
                
                for device in uplinks:
                    if device.get("networkId") == NETWORK_ID:
                        # Fail all uplink interfaces
                        for uplink in device.get("uplinks", []):
                            uplink["status"] = "failed"
                            uplink["ip"] = "0.0.0.0"
                            uplink["publicIp"] = "0.0.0.0"
                            failed_count += 1
                        
                        device["lastReportedAt"] = datetime.now().isoformat()
                
                # Write back
                with open('mock_data/comprehensive_api_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"💥 ALL UPLINKS FAILED!")
                print(f"   └─ Failed Uplinks: {failed_count}")
                print(f"   └─ Status: NETWORK UNREACHABLE")
                
        except Exception as e:
            print(f"❌ Error triggering uplink failure: {e}")
    
    async def trigger_vpn_failure(self):
        """Immediately stop all VPN traffic"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "network_vpn_stats" in data and ORGANIZATION_ID in data["network_vpn_stats"]:
                vpn_stats = data["network_vpn_stats"][ORGANIZATION_ID]
                
                for network in vpn_stats:
                    if network.get("networkId") == NETWORK_ID:
                        # Zero out all VPN traffic
                        for peer in network.get("merakiVpnPeers", []):
                            peer["usageSummary"] = {
                                "receivedInKilobytes": "0",
                                "sentInKilobytes": "0"
                            }
                
                # Write back
                with open('mock_data/comprehensive_api_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"💥 ALL VPN TUNNELS DOWN!")
                print(f"   └─ VPN Traffic: 0 KB")
                print(f"   └─ Status: NO CONNECTIVITY")
                
        except Exception as e:
            print(f"❌ Error triggering VPN failure: {e}")
    
    async def trigger_network_events(self):
        """Add critical network events"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "network_events" not in data:
                data["network_events"] = {}
            
            if NETWORK_ID not in data["network_events"]:
                data["network_events"][NETWORK_ID] = []
            
            # Add critical events
            critical_events = [
                {
                    "occurredAt": datetime.now().isoformat(),
                    "type": "wan_connectivity",
                    "description": "WAN1 connection lost - CRITICAL",
                    "severity": "critical",
                    "deviceSerial": DEVICE_SERIAL
                },
                {
                    "occurredAt": datetime.now().isoformat(),
                    "type": "wan_connectivity",
                    "description": "WAN2 connection lost - CRITICAL",
                    "severity": "critical",
                    "deviceSerial": DEVICE_SERIAL
                },
                {
                    "occurredAt": datetime.now().isoformat(),
                    "type": "device_status",
                    "description": "Device offline - Network unreachable",
                    "severity": "critical",
                    "deviceSerial": DEVICE_SERIAL
                },
                {
                    "occurredAt": datetime.now().isoformat(),
                    "type": "vpn_connectivity",
                    "description": "All VPN tunnels down",
                    "severity": "critical",
                    "deviceSerial": DEVICE_SERIAL
                },
                {
                    "occurredAt": datetime.now().isoformat(),
                    "type": "network_outage",
                    "description": "CATASTROPHIC NETWORK FAILURE - Total loss of connectivity",
                    "severity": "critical",
                    "deviceSerial": DEVICE_SERIAL
                }
            ]
            
            data["network_events"][NETWORK_ID].extend(critical_events)
            
            # Keep only last 100 events
            if len(data["network_events"][NETWORK_ID]) > 100:
                data["network_events"][NETWORK_ID] = data["network_events"][NETWORK_ID][-100:]
            
            # Write back
            with open('mock_data/comprehensive_api_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"💥 CRITICAL EVENTS LOGGED!")
            print(f"   └─ Total Events: {len(critical_events)}")
            print(f"   └─ Severity: CRITICAL")
            
        except Exception as e:
            print(f"❌ Error logging network events: {e}")
    
    async def run_simulation(self):
        """Run the instantaneous failure simulation"""
        print("\n💥 TRIGGERING INSTANTANEOUS NETWORK FAILURE")
        print("="*60)
        print("⚠️  WARNING: This will cause COMPLETE NETWORK OUTAGE")
        print("="*60)
        print()
        
        # Countdown
        for i in range(3, 0, -1):
            print(f"Triggering failure in {i}...")
            await asyncio.sleep(1)
        
        print("\n🚨 FAILURE TRIGGERED!\n")
        
        # Trigger all failures simultaneously
        await asyncio.gather(
            self.trigger_appliance_failure(),
            self.trigger_device_failure(),
            self.trigger_client_failure(),
            self.trigger_uplink_failure(),
            self.trigger_vpn_failure(),
            self.trigger_network_events()
        )
        
        print("\n" + "="*60)
        print("✅ Instantaneous Failure Simulation Complete!")
        print("="*60)
        
        # Print final summary
        print("\n📋 CATASTROPHIC FAILURE STATE:")
        print("-"*60)
        print("🔴 Network Status: TOTAL OUTAGE")
        print(f"🔴 Latency: {FAILURE_METRICS['latencyMs']}ms (UNREACHABLE)")
        print(f"🔴 Packet Loss: {FAILURE_METRICS['packetLossPct']}% (TOTAL)")
        print(f"🔴 Jitter: {FAILURE_METRICS['jitterMs']}ms (EXTREME)")
        print(f"🔴 Goodput: {FAILURE_METRICS['goodput']}% (NONE)")
        print("🔴 All Uplinks: FAILED")
        print("🔴 All Clients: OFFLINE")
        print("🔴 All VPN Tunnels: DOWN")
        print("🔴 Network Events: CRITICAL ALERTS LOGGED")
        print("="*60)
        print("\n⚠️  Network is COMPLETELY UNREACHABLE")
        print("⚠️  Requires immediate intervention!")
        print("="*60)


async def main():
    """Main entry point"""
    simulator = InstantaneousFailureSimulator()
    
    try:
        await simulator.initialize()
        await simulator.run_simulation()
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Simulation failed: {e}")
    finally:
        await simulator.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║    INSTANTANEOUS NETWORK FAILURE SIMULATION                  ║
║                                                              ║
║  This script simulates a catastrophic network failure        ║
║  that occurs instantly, such as:                             ║
║    • Fiber cut                                              ║
║    • Power outage                                           ║
║    • DDoS attack                                            ║
║    • Hardware failure                                       ║
║                                                              ║
║  All network metrics will immediately show:                  ║
║    • Latency: 1500ms+ (unreachable)                         ║
║    • Packet Loss: 100% (total loss)                         ║
║    • All uplinks: FAILED                                    ║
║    • All clients: OFFLINE                                   ║
║    • VPN tunnels: DOWN                                      ║
║                                                              ║
║  ⚠️  WARNING: This causes COMPLETE network outage            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Ask for confirmation
    response = input("\n⚠️  Are you sure you want to trigger catastrophic failure? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        asyncio.run(main())
    else:
        print("\n✅ Simulation cancelled by user")
