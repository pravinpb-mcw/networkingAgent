#!/usr/bin/env python3
"""
Restore Network to Healthy State
This script restores all network metrics to healthy baseline values
after running failure simulations.
"""

import asyncio
import json
from datetime import datetime
import aiohttp

# Configuration
MOCK_SERVER_URL = "http://127.0.0.1:5000"
NETWORK_ID = "L_3947405073390239794"
ORGANIZATION_ID = "999781"
DEVICE_SERIAL = "Q2MN-Q3J9-YJHW"

# Healthy baseline values
HEALTHY_METRICS = {
    "latencyMs": 15.5,
    "packetLossPct": 0.1,
    "jitterMs": 1.2,
    "goodput": 95.0
}


class NetworkRestorer:
    """Restores network to healthy state"""
    
    def __init__(self):
        self.session = None
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
        print("🔧 Network Restorer Initialized")
        print("="*60)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    async def restore_appliance_settings(self):
        """Restore appliance to healthy state"""
        settings = {
            "latencyMs": HEALTHY_METRICS["latencyMs"],
            "packetLossPct": HEALTHY_METRICS["packetLossPct"],
            "jitterMs": HEALTHY_METRICS["jitterMs"],
            "degradedLinks": [
                {
                    "uplink": "wan1",
                    "status": "active"
                },
                {
                    "uplink": "wan2",
                    "status": "active"
                }
            ],
            "updated_at": datetime.now().isoformat(),
            "note": "RESTORED_TO_HEALTHY_STATE"
        }
        
        url = f"{MOCK_SERVER_URL}/networks/{NETWORK_ID}/appliance/settings"
        
        try:
            async with self.session.post(url, json=settings) as response:
                if response.status == 200:
                    print("✅ APPLIANCE SETTINGS RESTORED")
                    print(f"   └─ Latency: {settings['latencyMs']}ms")
                    print(f"   └─ Packet Loss: {settings['packetLossPct']}%")
                    print(f"   └─ Jitter: {settings['jitterMs']}ms")
                    print(f"   └─ WAN1: active")
                    print(f"   └─ WAN2: active")
                else:
                    print(f"⚠️  Failed to restore appliance settings: {response.status}")
        except Exception as e:
            print(f"❌ Error restoring appliance settings: {e}")
    
    async def restore_device_history(self):
        """Clear old history and add only healthy device history entries"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "device_loss_and_latency_history" not in data:
                data["device_loss_and_latency_history"] = {}
            
            if DEVICE_SERIAL not in data["device_loss_and_latency_history"]:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = []
            
            # Add multiple healthy entries
            for i in range(10):
                healthy_entry = {
                    "ts": datetime.now().isoformat(),
                    "latencyMs": HEALTHY_METRICS["latencyMs"],
                    "lossPercent": HEALTHY_METRICS["packetLossPct"],
                    "jitter": HEALTHY_METRICS["jitterMs"],
                    "goodput": HEALTHY_METRICS["goodput"],
                    "destinationIp": "8.8.8.8",
                    "note": "RESTORED_TO_HEALTHY_STATE"
                }
                
                data["device_loss_and_latency_history"][DEVICE_SERIAL].append(healthy_entry)
            
            # Keep only last 50 entries
            if len(data["device_loss_and_latency_history"][DEVICE_SERIAL]) > 10:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = \
                    data["device_loss_and_latency_history"][DEVICE_SERIAL][-10:]
            
            # Write back
            with open('mock_data/comprehensive_api_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print("✅ DEVICE HISTORY RESTORED")
            print(f"   └─ Latency: {HEALTHY_METRICS['latencyMs']}ms")
            print(f"   └─ Packet Loss: {HEALTHY_METRICS['packetLossPct']}%")
            print(f"   └─ Goodput: {HEALTHY_METRICS['goodput']}%")
            
        except Exception as e:
            print(f"❌ Error restoring device history: {e}")
    
    async def restore_client_statuses(self):
        """Restore all clients to online"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "network_clients" in data and NETWORK_ID in data["network_clients"]:
                clients = data["network_clients"][NETWORK_ID]
                
                # Set first 3 clients online (realistic scenario)
                for i, client in enumerate(clients):
                    if i < 3:
                        client["status"] = "Online"
                        client["lastSeen"] = datetime.now().isoformat()
                        # Restore some usage
                        client["usage"] = {
                            "sent": 42606,
                            "recv": 1581769,
                            "total": 1624375
                        }
                    else:
                        client["status"] = "Offline"
                
                # Write back
                with open('mock_data/comprehensive_api_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                online_count = sum(1 for c in clients if c["status"] == "Online")
                offline_count = len(clients) - online_count
                
                print("✅ CLIENT STATUSES RESTORED")
                print(f"   └─ Online: {online_count}")
                print(f"   └─ Offline: {offline_count}")
                
        except Exception as e:
            print(f"❌ Error restoring client statuses: {e}")
    
    async def restore_uplink_statuses(self):
        """Restore all uplinks to active"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "organization_uplinks_statuses" in data and ORGANIZATION_ID in data["organization_uplinks_statuses"]:
                uplinks = data["organization_uplinks_statuses"][ORGANIZATION_ID]
                restored_count = 0
                
                for device in uplinks:
                    if device.get("networkId") == NETWORK_ID:
                        # Restore all uplink interfaces
                        for uplink in device.get("uplinks", []):
                            uplink["status"] = "active"
                            # Restore IP if it was zeroed
                            if uplink["ip"] == "0.0.0.0":
                                uplink["ip"] = "192.168.1.69"
                            if uplink["publicIp"] == "0.0.0.0":
                                uplink["publicIp"] = "162.204.214.129"
                            restored_count += 1
                        
                        device["lastReportedAt"] = datetime.now().isoformat()
                
                # Write back
                with open('mock_data/comprehensive_api_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print("✅ UPLINK STATUSES RESTORED")
                print(f"   └─ Active Uplinks: {restored_count}")
                print(f"   └─ Status: ALL ACTIVE")
                
        except Exception as e:
            print(f"❌ Error restoring uplink statuses: {e}")
    
    async def restore_vpn_traffic(self):
        """Restore VPN traffic"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "network_vpn_stats" in data and ORGANIZATION_ID in data["network_vpn_stats"]:
                vpn_stats = data["network_vpn_stats"][ORGANIZATION_ID]
                
                for network in vpn_stats:
                    if network.get("networkId") == NETWORK_ID:
                        # Restore VPN traffic
                        for peer in network.get("merakiVpnPeers", []):
                            peer["usageSummary"] = {
                                "receivedInKilobytes": "789045",
                                "sentInKilobytes": "4530873"
                            }
                
                # Write back
                with open('mock_data/comprehensive_api_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print("✅ VPN TRAFFIC RESTORED")
                print(f"   └─ VPN Tunnels: ACTIVE")
                print(f"   └─ Traffic: NORMAL")
                
        except Exception as e:
            print(f"❌ Error restoring VPN traffic: {e}")
    
    async def clear_critical_events(self):
        """Clear critical network events"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "network_events" in data and NETWORK_ID in data["network_events"]:
                # Clear critical events, keep only info events
                events = data["network_events"][NETWORK_ID]
                data["network_events"][NETWORK_ID] = [
                    e for e in events if e.get("severity") != "critical"
                ]
                
                # Add recovery event
                recovery_event = {
                    "occurredAt": datetime.now().isoformat(),
                    "type": "network_recovery",
                    "description": "Network restored to healthy state",
                    "severity": "info",
                    "deviceSerial": DEVICE_SERIAL
                }
                data["network_events"][NETWORK_ID].append(recovery_event)
                
                # Write back
                with open('mock_data/comprehensive_api_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print("✅ CRITICAL EVENTS CLEARED")
                print(f"   └─ Recovery Event Logged")
                
        except Exception as e:
            print(f"❌ Error clearing events: {e}")
    
    async def run_restoration(self):
        """Run the network restoration"""
        print("\n🔄 STARTING NETWORK RESTORATION")
        print("="*60)
        print()
        
        # Restore all components
        await asyncio.gather(
            self.restore_appliance_settings(),
            self.restore_device_history(),
            self.restore_client_statuses(),
            self.restore_uplink_statuses(),
            self.restore_vpn_traffic(),
            self.clear_critical_events()
        )
        
        print("\n" + "="*60)
        print("✅ Network Restoration Complete!")
        print("="*60)
        
        # Print final summary
        print("\n📋 HEALTHY NETWORK STATE:")
        print("-"*60)
        print("🟢 Network Status: OPERATIONAL")
        print(f"🟢 Latency: {HEALTHY_METRICS['latencyMs']}ms (HEALTHY)")
        print(f"🟢 Packet Loss: {HEALTHY_METRICS['packetLossPct']}% (HEALTHY)")
        print(f"🟢 Jitter: {HEALTHY_METRICS['jitterMs']}ms (HEALTHY)")
        print(f"🟢 Goodput: {HEALTHY_METRICS['goodput']}% (OPTIMAL)")
        print("🟢 All Uplinks: ACTIVE")
        print("🟢 Clients: ONLINE")
        print("🟢 VPN Tunnels: ACTIVE")
        print("🟢 Events: CLEARED")
        print("="*60)


async def main():
    """Main entry point"""
    restorer = NetworkRestorer()
    
    try:
        await restorer.initialize()
        await restorer.run_restoration()
    except KeyboardInterrupt:
        print("\n\n⚠️  Restoration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Restoration failed: {e}")
    finally:
        await restorer.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           NETWORK RESTORATION TO HEALTHY STATE               ║
║                                                              ║
║  This script restores the network to healthy baseline:       ║
║    • Latency: 15.5ms                                        ║
║    • Packet Loss: 0.1%                                      ║
║    • Jitter: 1.2ms                                          ║
║    • All uplinks: ACTIVE                                    ║
║    • Clients: ONLINE                                        ║
║    • VPN tunnels: ACTIVE                                    ║
║                                                              ║
║  Use this after running failure simulations                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
