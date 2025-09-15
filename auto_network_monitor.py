#!/usr/bin/env python3
"""
AUTO NETWORK MONITOR - One-Click Solution
Automatically handles everything without dependencies
"""
import subprocess
import sys
import os
import time
import json

def check_ollama_server():
    """Check if Ollama server is running"""
    try:
        import requests
        response = requests.get("http://192.168.13.162:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_json_data():
    """Check if JSON data exists"""
    return os.path.exists("mock_data/comprehensive_api_data.json")

def create_mock_data_if_needed():
    """Create mock data if it doesn't exist"""
    if not check_json_data():
        print("📁 Creating mock data...")
        os.makedirs("mock_data", exist_ok=True)
        
        # Create basic mock data
        mock_data = {
            "networks": {
                "L_3947405073390239794": {
                    "name": "Test Network",
                    "appliance_settings": [{
                        "latencyMs": 110,
                        "packetLossPct": 3.2,
                        "jitterMs": 12,
                        "degradedLinks": [
                            {"uplink": "wan1", "status": "ok"},
                            {"uplink": "wan2", "status": "ok"},
                            {"uplink": "wan3", "status": "ok"}
                        ]
                    }]
                }
            },
            "organization_uplinks_statuses": {
                "999781": []
            }
        }
        
        # Add 29 devices (mostly on wan2 to create imbalance)
        devices = []
        for i in range(29):
            device_id = f"Q2MN-Q3J9-YJ{i:02d}"
            wan = "wan2" if i < 24 else "wan1"  # 24 on wan2, 5 on wan1
            devices.append({
                "networkId": "L_3947405073390239794",
                "serial": device_id,
                "model": "MX64W",
                "uplinks": [{
                    "interface": wan,
                    "status": "active",
                    "ip": f"192.168.1.{i+10}",
                    "gateway": "192.168.1.1"
                }]
            })
        
        mock_data["organization_uplinks_statuses"]["999781"] = devices
        
        with open("mock_data/comprehensive_api_data.json", "w") as f:
            json.dump(mock_data, f, indent=2)
        
        print("✅ Mock data created")

def main():
    """Main launcher function"""
    print("🚀 AUTO NETWORK MONITOR")
    print("=" * 30)
    
    # Check requirements
    print("🔍 Checking requirements...")
    
    # Check if query_model.py exists
    if not os.path.exists("query_model.py"):
        print("❌ query_model.py not found!")
        print("💡 Make sure you're in the right directory")
        return
    
    # Check Ollama server
    if not check_ollama_server():
        print("⚠️  Ollama server not responding at 192.168.13.162:11434")
        print("💡 Make sure your friend's Ollama server is running")
        print("🔄 Continuing anyway...")
    else:
        print("✅ Ollama server is running")
    
    # Check/create mock data
    if not check_json_data():
        print("📁 Creating mock data...")
        create_mock_data_if_needed()
    else:
        print("✅ Mock data found")
    
    # Run the simple monitor
    print("\n🚀 Starting network monitoring...")
    print("=" * 30)
    
    try:
        # Import and run the simple monitor
        import simple_network_monitor
        simple_network_monitor.main()
    except Exception as e:
        print(f"❌ Error running monitor: {e}")
        print("💡 Make sure all files are in the current directory")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
