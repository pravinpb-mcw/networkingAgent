#!/usr/bin/env python3
"""
Network Failure Simulation Manager
Master script to control all network failure scenarios
"""

import asyncio
import subprocess
import sys

def print_banner():
    """Print application banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║       NETWORK FAILURE SIMULATION MANAGER                     ║
║                                                              ║
║  Test your network monitoring and orchestration agent        ║
║  with realistic failure scenarios                            ║
╚══════════════════════════════════════════════════════════════╝
    """)

def print_menu():
    """Print the main menu"""
    print("\n" + "="*60)
    print("AVAILABLE SIMULATIONS:")
    print("="*60)
    print("1. 🐌 Gradual Network Failure (5 minutes)")
    print("   └─ Simulates slow network degradation over time")
    print("   └─ Metrics gradually worsen: latency, loss, jitter")
    print("   └─ Devices progressively go offline")
    print()
    print("2. 💥 Instantaneous Network Failure (Immediate)")
    print("   └─ Simulates catastrophic sudden failure")
    print("   └─ Complete network outage (fiber cut, power loss)")
    print("   └─ All metrics immediately critical")
    print()
    print("3. 🔄 Restore Network to Healthy State")
    print("   └─ Restores all metrics to baseline healthy values")
    print("   └─ Clears failure conditions and critical events")
    print("   └─ Returns network to operational state")
    print()
    print("4. 📊 View Current Network State")
    print("   └─ Display current network metrics")
    print("   └─ Show uplink statuses and client connections")
    print()
    print("5. ❌ Exit")
    print("="*60)

def run_script(script_name):
    """Run a simulation script"""
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Script not found: {script_name}")
        return False

async def view_network_state():
    """Display current network state"""
    try:
        import json
        
        print("\n" + "="*60)
        print("CURRENT NETWORK STATE")
        print("="*60)
        
        with open('mock_data/comprehensive_api_data.json', 'r') as f:
            data = json.load(f)
        
        # Get network ID
        network_id = "L_3947405073390239794"
        device_serial = "Q2MN-Q3J9-YJHW"
        org_id = "999781"
        
        # Display appliance settings
        if "networks" in data and network_id in data["networks"]:
            network = data["networks"][network_id]
            if "appliance_settings" in network and len(network["appliance_settings"]) > 0:
                settings = network["appliance_settings"][-1]
                
                print("\n📡 APPLIANCE METRICS:")
                print("-"*60)
                print(f"Latency: {settings.get('latencyMs', 'N/A')}ms")
                print(f"Packet Loss: {settings.get('packetLossPct', 'N/A')}%")
                print(f"Jitter: {settings.get('jitterMs', 'N/A')}ms")
                
                if "degradedLinks" in settings:
                    print(f"\n🔗 UPLINK STATUS:")
                    for link in settings["degradedLinks"]:
                        status_icon = "🟢" if link["status"] == "active" else "🔴"
                        print(f"{status_icon} {link['uplink']}: {link['status'].upper()}")
        
        # Display device history
        if "device_loss_and_latency_history" in data and device_serial in data["device_loss_and_latency_history"]:
            history = data["device_loss_and_latency_history"][device_serial]
            if len(history) > 0:
                latest = history[-1]
                print(f"\n📈 LATEST DEVICE METRICS:")
                print("-"*60)
                print(f"Latency: {latest.get('latencyMs', 'N/A')}ms")
                print(f"Loss: {latest.get('lossPercent', 'N/A')}%")
                print(f"Jitter: {latest.get('jitter', 'N/A')}ms")
                print(f"Goodput: {latest.get('goodput', 'N/A')}%")
                print(f"Timestamp: {latest.get('ts', 'N/A')}")
        
        # Display client status
        if "network_clients" in data and network_id in data["network_clients"]:
            clients = data["network_clients"][network_id]
            online = sum(1 for c in clients if c.get("status") == "Online")
            offline = len(clients) - online
            
            print(f"\n👥 CLIENT STATUS:")
            print("-"*60)
            print(f"🟢 Online: {online}")
            print(f"🔴 Offline: {offline}")
            print(f"📊 Total: {len(clients)}")
        
        # Display uplink status
        if "organization_uplinks_statuses" in data and org_id in data["organization_uplinks_statuses"]:
            uplinks = data["organization_uplinks_statuses"][org_id]
            
            for device in uplinks:
                if device.get("networkId") == network_id:
                    print(f"\n🌐 ORGANIZATION UPLINKS:")
                    print("-"*60)
                    print(f"Device: {device.get('serial', 'N/A')}")
                    print(f"Model: {device.get('model', 'N/A')}")
                    print(f"Last Reported: {device.get('lastReportedAt', 'N/A')}")
                    
                    for uplink in device.get("uplinks", []):
                        status_icon = "🟢" if uplink["status"] == "active" else "🔴"
                        print(f"\n{status_icon} Interface: {uplink.get('interface', 'N/A')}")
                        print(f"   Status: {uplink.get('status', 'N/A').upper()}")
                        print(f"   IP: {uplink.get('ip', 'N/A')}")
                        print(f"   Public IP: {uplink.get('publicIp', 'N/A')}")
        
        # Display recent events
        if "network_events" in data and network_id in data["network_events"]:
            events = data["network_events"][network_id]
            if len(events) > 0:
                print(f"\n📝 RECENT EVENTS (Last 5):")
                print("-"*60)
                for event in events[-5:]:
                    severity_icon = "🔴" if event.get("severity") == "critical" else "🟡"
                    print(f"{severity_icon} {event.get('type', 'N/A')}: {event.get('description', 'N/A')}")
                    print(f"   Time: {event.get('occurredAt', 'N/A')}")
        
        print("\n" + "="*60)
        
    except FileNotFoundError:
        print("\n❌ Network data file not found!")
        print("   Make sure the mock server has generated data.")
    except json.JSONDecodeError:
        print("\n❌ Error reading network data!")
        print("   The data file may be corrupted.")
    except Exception as e:
        print(f"\n❌ Error viewing network state: {e}")

async def main():
    """Main application loop"""
    print_banner()
    
    while True:
        print_menu()
        
        try:
            choice = input("\nSelect an option (1-5): ").strip()
            
            if choice == "1":
                print("\n🚀 Starting Gradual Failure Simulation...")
                print("This will take approximately 5 minutes.")
                confirm = input("Continue? (yes/no): ").strip().lower()
                
                if confirm in ['yes', 'y']:
                    success = run_script("simulate_gradual_failure.py")
                    if success:
                        print("\n✅ Gradual failure simulation completed!")
                    else:
                        print("\n⚠️  Gradual failure simulation encountered errors")
                else:
                    print("\n✅ Cancelled")
            
            elif choice == "2":
                print("\n💥 Starting Instantaneous Failure Simulation...")
                print("⚠️  WARNING: This will cause COMPLETE network outage!")
                
                success = run_script("simulate_instant_failure.py")
                if success:
                    print("\n✅ Instantaneous failure simulation completed!")
                else:
                    print("\n⚠️  Instantaneous failure simulation encountered errors")
            
            elif choice == "3":
                print("\n🔄 Restoring Network to Healthy State...")
                confirm = input("Continue? (yes/no): ").strip().lower()
                
                if confirm in ['yes', 'y']:
                    success = run_script("restore_network.py")
                    if success:
                        print("\n✅ Network restoration completed!")
                    else:
                        print("\n⚠️  Network restoration encountered errors")
                else:
                    print("\n✅ Cancelled")
            
            elif choice == "4":
                await view_network_state()
                input("\nPress Enter to continue...")
            
            elif choice == "5":
                print("\n👋 Exiting Network Failure Simulation Manager")
                print("Thank you for using the tool!\n")
                break
            
            else:
                print("\n⚠️  Invalid choice. Please select 1-5.")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            confirm = input("\nAre you sure you want to exit? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                print("\n👋 Goodbye!\n")
                break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("\n🔧 Checking prerequisites...")
    
    # Check if required files exist
    required_files = [
        "simulate_gradual_failure.py",
        "simulate_instant_failure.py",
        "restore_network.py"
    ]
    
    missing_files = []
    for file in required_files:
        import os
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("\n❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all simulation scripts are in the current directory.")
        sys.exit(1)
    
    print("✅ All prerequisites met!\n")
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
