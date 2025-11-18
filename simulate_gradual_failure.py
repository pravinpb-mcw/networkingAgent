#!/usr/bin/env python3
"""
Simulate Gradual Network Failure
This script gradually degrades network metrics in the mock Meraki server
to emulate realistic network degradation scenarios.

Simulated Metrics:
- Latency: Increases from healthy (~15ms) to critical (~500ms+)
- Packet Loss: Increases from 0.1% to 10%+
- Jitter: Increases from 1-2ms to 50ms+
- Device Status: Devices gradually go offline
- Uplink Status: Uplinks degrade from 'active' to 'failed'
- Goodput: Decreases from 95% to below 50%
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any
import aiohttp

# Configuration
MOCK_SERVER_URL = "http://127.0.0.1:5000"
NETWORK_ID = "L_3947405073390239794"
ORGANIZATION_ID = "999781"
DEVICE_SERIAL = "Q2MN-Q3J9-YJHW"

# Failure simulation parameters
TOTAL_DURATION_SECONDS = 300  # 5 minutes for gradual failure
UPDATE_INTERVAL_SECONDS = 10  # Update every 10 seconds
STEPS = TOTAL_DURATION_SECONDS // UPDATE_INTERVAL_SECONDS


class GradualFailureSimulator:
    """Simulates gradual network degradation"""
    
    def __init__(self):
        self.session = None
        self.current_step = 0
        self.start_time = None
        
        # Initial healthy values
        self.initial_values = {
            "latencyMs": 15.5,
            "packetLossPct": 0.1,
            "jitterMs": 1.2,
            "goodput": 95.0
        }
        
        # Critical failure values
        self.failure_values = {
            "latencyMs": 500.0,
            "packetLossPct": 10.0,
            "jitterMs": 50.0,
            "goodput": 45.0
        }
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
        self.start_time = time.time()
        print("🔧 Gradual Failure Simulator Initialized")
        print(f"📊 Total Duration: {TOTAL_DURATION_SECONDS}s ({TOTAL_DURATION_SECONDS/60:.1f} minutes)")
        print(f"⏱️  Update Interval: {UPDATE_INTERVAL_SECONDS}s")
        print(f"📈 Total Steps: {STEPS}")
        print("="*60)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    def calculate_degraded_value(self, initial: float, final: float, step: int) -> float:
        """Calculate the current value based on linear degradation"""
        progress = step / STEPS
        return initial + (final - initial) * progress
    
    def get_uplink_status(self, step: int) -> str:
        """Determine uplink status based on current step"""
        progress = step / STEPS
        
        if progress < 0.3:
            return "active"
        elif progress < 0.6:
            return "connecting"
        elif progress < 0.8:
            return "connecting"
        else:
            return "failed"
    
    def get_client_status(self, client_index: int, step: int) -> str:
        """Determine if a client should be online or offline"""
        progress = step / STEPS
        
        # First 30% - all online
        if progress < 0.3:
            return "Online"
        # 30-60% - some start going offline
        elif progress < 0.6:
            # Start taking clients offline based on index
            if client_index % 3 == 0:
                return "Offline"
            return "Online"
        # 60-80% - more offline
        elif progress < 0.8:
            if client_index % 2 == 0:
                return "Offline"
            return "Online"
        # 80%+ - most offline
        else:
            if client_index % 4 != 0:
                return "Offline"
            return "Online"
    
    async def update_appliance_settings(self, step: int):
        """Update appliance settings with degraded metrics"""
        latency = self.calculate_degraded_value(
            self.initial_values["latencyMs"],
            self.failure_values["latencyMs"],
            step
        )
        packet_loss = self.calculate_degraded_value(
            self.initial_values["packetLossPct"],
            self.failure_values["packetLossPct"],
            step
        )
        jitter = self.calculate_degraded_value(
            self.initial_values["jitterMs"],
            self.failure_values["jitterMs"],
            step
        )
        
        uplink_status = self.get_uplink_status(step)
        
        settings = {
            "latencyMs": round(latency, 2),
            "packetLossPct": round(packet_loss, 2),
            "jitterMs": round(jitter, 2),
            "degradedLinks": [
                {
                    "uplink": "wan1",
                    "status": uplink_status
                },
                {
                    "uplink": "wan2",
                    "status": uplink_status if step > STEPS * 0.5 else "active"
                }
            ],
            "updated_at": datetime.now().isoformat()
        }
        
        url = f"{MOCK_SERVER_URL}/networks/{NETWORK_ID}/appliance/settings"
        
        try:
            async with self.session.post(url, json=settings) as response:
                if response.status == 200:
                    print(f"✅ Step {step}/{STEPS}: Appliance Settings Updated")
                    print(f"   └─ Latency: {settings['latencyMs']}ms, Loss: {settings['packetLossPct']}%, Jitter: {settings['jitterMs']}ms")
                    print(f"   └─ WAN1: {settings['degradedLinks'][0]['status']}, WAN2: {settings['degradedLinks'][1]['status']}")
                else:
                    print(f"⚠️  Failed to update appliance settings: {response.status}")
        except Exception as e:
            print(f"❌ Error updating appliance settings: {e}")
    
    async def update_device_history(self, step: int):
        """Update device loss and latency history"""
        latency = self.calculate_degraded_value(
            self.initial_values["latencyMs"],
            self.failure_values["latencyMs"],
            step
        )
        loss = self.calculate_degraded_value(
            self.initial_values["packetLossPct"],
            self.failure_values["packetLossPct"],
            step
        )
        jitter = self.calculate_degraded_value(
            self.initial_values["jitterMs"],
            self.failure_values["jitterMs"],
            step
        )
        goodput = self.calculate_degraded_value(
            self.initial_values["goodput"],
            self.failure_values["goodput"],
            step
        )
        
        # Read comprehensive data
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            # Add new history entry
            if "device_loss_and_latency_history" not in data:
                data["device_loss_and_latency_history"] = {}
            
            if DEVICE_SERIAL not in data["device_loss_and_latency_history"]:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = []
            
            history_entry = {
                "ts": datetime.now().isoformat(),
                "latencyMs": round(latency, 2),
                "lossPercent": round(loss, 2),
                "jitter": round(jitter, 2),
                "goodput": round(goodput, 2),
                "destinationIp": "8.8.8.8"
            }
            
            data["device_loss_and_latency_history"][DEVICE_SERIAL].append(history_entry)
            
            # Keep only last 50 entries
            if len(data["device_loss_and_latency_history"][DEVICE_SERIAL]) > 50:
                data["device_loss_and_latency_history"][DEVICE_SERIAL] = \
                    data["device_loss_and_latency_history"][DEVICE_SERIAL][-50:]
            
            # Write back
            with open('mock_data/comprehensive_api_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Step {step}/{STEPS}: Device History Updated")
            print(f"   └─ Latency: {history_entry['latencyMs']}ms, Loss: {history_entry['lossPercent']}%, Goodput: {history_entry['goodput']}%")
            
        except Exception as e:
            print(f"❌ Error updating device history: {e}")
    
    async def update_client_statuses(self, step: int):
        """Update client online/offline statuses"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            if "network_clients" in data and NETWORK_ID in data["network_clients"]:
                clients = data["network_clients"][NETWORK_ID]
                online_count = 0
                offline_count = 0
                
                for i, client in enumerate(clients):
                    new_status = self.get_client_status(i, step)
                    client["status"] = new_status
                    client["lastSeen"] = datetime.now().isoformat()
                    
                    if new_status == "Online":
                        online_count += 1
                    else:
                        offline_count += 1
                
                # Write back
                with open('mock_data/comprehensive_api_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"✅ Step {step}/{STEPS}: Client Statuses Updated")
                print(f"   └─ Online: {online_count}, Offline: {offline_count}")
                
        except Exception as e:
            print(f"❌ Error updating client statuses: {e}")
    
    async def update_uplink_statuses(self, step: int):
        """Update uplink statuses in organization data"""
        try:
            with open('mock_data/comprehensive_api_data.json', 'r') as f:
                data = json.load(f)
            
            uplink_status = self.get_uplink_status(step)
            
            if "organization_uplinks_statuses" in data and ORGANIZATION_ID in data["organization_uplinks_statuses"]:
                uplinks = data["organization_uplinks_statuses"][ORGANIZATION_ID]
                
                for device in uplinks:
                    if device.get("networkId") == NETWORK_ID:
                        # Update uplink interfaces
                        for uplink in device.get("uplinks", []):
                            if uplink["interface"] == "wan1":
                                uplink["status"] = uplink_status
                            elif uplink["interface"] == "wan2" and step > STEPS * 0.5:
                                uplink["status"] = uplink_status
                        
                        device["lastReportedAt"] = datetime.now().isoformat()
                
                # Write back
                with open('mock_data/comprehensive_api_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"✅ Step {step}/{STEPS}: Uplink Statuses Updated")
                print(f"   └─ Status: {uplink_status}")
                
        except Exception as e:
            print(f"❌ Error updating uplink statuses: {e}")
    
    async def run_simulation(self):
        """Run the gradual failure simulation"""
        print("\n🚀 Starting Gradual Network Failure Simulation")
        print("="*60)
        
        for step in range(1, STEPS + 1):
            elapsed = time.time() - self.start_time
            progress = (step / STEPS) * 100
            
            print(f"\n📊 Progress: {progress:.1f}% | Elapsed: {elapsed:.1f}s")
            print("-"*60)
            
            # Update all metrics
            await self.update_appliance_settings(step)
            await self.update_device_history(step)
            await self.update_client_statuses(step)
            await self.update_uplink_statuses(step)
            
            # Wait before next update
            if step < STEPS:
                await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
        
        print("\n" + "="*60)
        print("✅ Gradual Failure Simulation Complete!")
        print(f"⏱️  Total Time: {time.time() - self.start_time:.1f}s")
        print("="*60)
        
        # Print final summary
        print("\n📋 FINAL NETWORK STATE:")
        print("-"*60)
        print(f"Latency: {self.failure_values['latencyMs']}ms (CRITICAL)")
        print(f"Packet Loss: {self.failure_values['packetLossPct']}% (CRITICAL)")
        print(f"Jitter: {self.failure_values['jitterMs']}ms (CRITICAL)")
        print(f"Goodput: {self.failure_values['goodput']}% (DEGRADED)")
        print(f"Uplink Status: FAILED")
        print(f"Client Status: MAJORITY OFFLINE")
        print("="*60)


async def main():
    """Main entry point"""
    simulator = GradualFailureSimulator()
    
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
║      GRADUAL NETWORK FAILURE SIMULATION                      ║
║                                                              ║
║  This script simulates a gradual network degradation        ║
║  over 5 minutes, progressively worsening:                   ║
║    • Latency (15ms → 500ms)                                 ║
║    • Packet Loss (0.1% → 10%)                               ║
║    • Jitter (1ms → 50ms)                                    ║
║    • Uplink Status (active → failed)                        ║
║    • Client Connectivity (online → offline)                 ║
║                                                              ║
║  Updates occur every 10 seconds with 30 total steps         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
