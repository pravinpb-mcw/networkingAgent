#!/usr/bin/env python3
"""
Network Problem Injector
Randomly injects realistic network problems into the comprehensive JSON file
for testing the agent's problem detection and fixing capabilities.
"""

import json
import random
import os
from datetime import datetime, timedelta
import copy
from dotenv import load_dotenv

class NetworkProblemInjector:
    def __init__(self, json_file_path="mock_data/comprehensive_api_data.json"):
        self.json_file_path = json_file_path
        self.problems_injected = []
        
        # Load environment variables to get your network ID
        load_dotenv()
        self.network_id = os.getenv("NETWORK_ID")
        if not self.network_id:
            print("⚠️  WARNING: NETWORK_ID not found in .env file. Will use random network IDs.")
        else:
            print(f"🎯 Using your network ID: {self.network_id}")
        
    def load_data(self):
        """Load the current JSON data"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading JSON file: {e}")
            return None
    
    def save_data(self, data):
        """Save the updated JSON data"""
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"✅ Data saved to {self.json_file_path}")
        except Exception as e:
            print(f"❌ Error saving JSON file: {e}")
    
    def inject_high_traffic_problem(self, data):
        """Inject high traffic problem"""
        network_id = self.network_id or random.choice(list(data['networks'].keys()))
        
        # Create high traffic data
        high_traffic = {
            "application": "YouTube",
            "protocol": "HTTPS",
            "port": 443,
            "recv": random.randint(80000000, 150000000),  # High receive traffic
            "sent": random.randint(50000000, 100000000),  # High sent traffic
            "numFlows": random.randint(1000, 5000),
            "time": datetime.now().isoformat()
        }
        
        if 'network_traffic' not in data:
            data['network_traffic'] = {}
        if network_id not in data['network_traffic']:
            data['network_traffic'][network_id] = []
        
        data['network_traffic'][network_id].append(high_traffic)
        
        self.problems_injected.append(f"🚨 HIGH TRAFFIC: Network {network_id} - {high_traffic['application']} consuming {high_traffic['recv']:,} bytes")
        return data
    
    def inject_security_vulnerability(self, data):
        """Inject security vulnerability"""
        network_id = self.network_id or random.choice(list(data['networks'].keys()))
        
        # Create security event
        security_event = {
            "occurredAt": datetime.now().isoformat(),
            "networkId": network_id,
            "type": random.choice([
                "unauthorized_device_connected",
                "suspicious_traffic_detected", 
                "failed_login_attempt",
                "malware_detected",
                "data_exfiltration_attempt"
            ]),
            "description": "Security threat detected - immediate action required",
            "severity": "high",
            "sourceIp": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "destinationIp": f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}"
        }
        
        if 'network_events' not in data:
            data['network_events'] = {}
        if network_id not in data['network_events']:
            data['network_events'][network_id] = []
        
        data['network_events'][network_id].append(security_event)
        
        self.problems_injected.append(f"🛡️ SECURITY THREAT: Network {network_id} - {security_event['type']} from {security_event['sourceIp']}")
        return data
    
    def inject_performance_issues(self, data):
        """Inject performance issues"""
        network_id = self.network_id or random.choice(list(data['networks'].keys()))
        
        # Create performance issue data
        performance_issue = {
            "networkId": network_id,
            "serial": f"Q2MN-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "ip": "8.8.8.8",
            "timeSeries": [
                {
                    "ts": datetime.now().isoformat(),
                    "lossPercent": random.uniform(15.0, 25.0),  # High packet loss
                    "latencyMs": random.uniform(250.0, 500.0),  # High latency
                    "jitterMs": random.uniform(50.0, 150.0)  # High jitter
                }
            ]
        }
        
        if 'device_loss_and_latency_history' not in data:
            data['device_loss_and_latency_history'] = {}
        if network_id not in data['device_loss_and_latency_history']:
            data['device_loss_and_latency_history'][network_id] = []
        
        data['device_loss_and_latency_history'][network_id].append(performance_issue)
        
        self.problems_injected.append(f"📊 PERFORMANCE ISSUE: Network {network_id} - {performance_issue['timeSeries'][0]['lossPercent']:.1f}% packet loss, {performance_issue['timeSeries'][0]['latencyMs']:.0f}ms latency")
        return data
    
    def inject_connectivity_issues(self, data):
        """Inject connectivity issues"""
        network_id = self.network_id or random.choice(list(data['networks'].keys()))
        
        # Create connectivity issue
        connectivity_issue = {
            "networkId": network_id,
            "destinations": [
                "8.8.8.8",
                "1.1.1.1",
                "208.67.222.222"
            ],
            "status": "unreachable",
            "lastCheck": datetime.now().isoformat(),
            "description": "DNS servers unreachable - connectivity failure"
        }
        
        if 'connectivity_monitoring' not in data:
            data['connectivity_monitoring'] = {}
        if network_id not in data['connectivity_monitoring']:
            data['connectivity_monitoring'][network_id] = []
        
        data['connectivity_monitoring'][network_id].append(connectivity_issue)
        
        self.problems_injected.append(f"🌐 CONNECTIVITY FAILURE: Network {network_id} - DNS servers unreachable")
        return data
    
    def inject_unauthorized_devices(self, data):
        """Inject unauthorized device connection"""
        network_id = self.network_id or random.choice(list(data['networks'].keys()))
        
        # Create unauthorized device
        unauthorized_device = {
            "id": f"{random.randint(100000000000000000, 999999999999999999)}",
            "mac": f"{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}",
            "description": "Unknown device",
            "ip": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "firstSeen": datetime.now().isoformat(),
            "lastSeen": datetime.now().isoformat(),
            "manufacturer": "Unknown",
            "os": "Unknown",
            "user": "Unknown",
            "vlan": random.randint(1, 100),
            "ssid": None,
            "status": "Online",
            "notes": "Unauthorized device detected",
            "smInstalled": False,
            "recentDeviceMac": f"{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}"
        }
        
        if 'network_clients' not in data:
            data['network_clients'] = {}
        if network_id not in data['network_clients']:
            data['network_clients'][network_id] = []
        
        data['network_clients'][network_id].append(unauthorized_device)
        
        self.problems_injected.append(f"📱 UNAUTHORIZED DEVICE: Network {network_id} - Unknown device {unauthorized_device['mac']} connected")
        return data
    
    def inject_policy_violations(self, data):
        """Inject policy violations"""
        network_id = self.network_id or random.choice(list(data['networks'].keys()))
        
        # Create policy violation
        policy_violation = {
            "networkId": network_id,
            "policyId": f"policy_{random.randint(1000, 9999)}",
            "policyName": "Bandwidth Policy",
            "violationType": random.choice([
                "bandwidth_exceeded",
                "time_limit_exceeded",
                "content_filter_violation",
                "application_blocked"
            ]),
            "timestamp": datetime.now().isoformat(),
            "description": "Policy violation detected - user exceeded bandwidth limits",
            "severity": "medium"
        }
        
        if 'policy_violations' not in data:
            data['policy_violations'] = {}
        if network_id not in data['policy_violations']:
            data['policy_violations'][network_id] = []
        
        data['policy_violations'][network_id].append(policy_violation)
        
        self.problems_injected.append(f"📋 POLICY VIOLATION: Network {network_id} - {policy_violation['violationType']} detected")
        return data
    
    def inject_uplink_failures(self, data):
        """Inject uplink failures"""
        network_id = self.network_id or random.choice(list(data['networks'].keys()))
        
        # Create uplink failure
        uplink_failure = {
            "networkId": network_id,
            "serial": f"Q2MN-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "interface": "WAN 1",
            "status": "failed",
            "ip": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "gateway": f"192.168.{random.randint(1, 254)}.1",
            "publicIp": f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "model": "MX64",
            "lastReportedAt": datetime.now().isoformat(),
            "uplink": "wan1",
            "ipAssignedBy": "dhcp",
            "externalIp": f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "usingStaticIp": False,
            "connectionType": "Cable",
            "defaultGateway": f"192.168.{random.randint(1, 254)}.1",
            "dns": ["8.8.8.8", "8.8.4.4"],
            "signalStat": {
                "rsrp": random.uniform(-120.0, -80.0),
                "rsrq": random.uniform(-20.0, -3.0),
                "rssi": random.uniform(-100.0, -50.0),
                "sinr": random.uniform(-10.0, 20.0)
            }
        }
        
        if 'organization_uplinks_statuses' not in data:
            data['organization_uplinks_statuses'] = {}
        if data['organizations'][0]['id'] not in data['organization_uplinks_statuses']:
            data['organization_uplinks_statuses'][data['organizations'][0]['id']] = []
        
        data['organization_uplinks_statuses'][data['organizations'][0]['id']].append(uplink_failure)
        
        self.problems_injected.append(f"🔌 UPLINK FAILURE: Network {uplink_failure['networkId']} - WAN 1 failed, using backup")
        return data
    
    def inject_random_problems(self, num_problems=6):
        """Inject random network problems"""
        print(f"🔧 Injecting {num_problems} random network problems...")
        
        data = self.load_data()
        if not data:
            return
        
        # List of all problem injection methods (VPN issues removed)
        problem_methods = [
            self.inject_high_traffic_problem,
            self.inject_security_vulnerability,
            self.inject_performance_issues,
            self.inject_connectivity_issues,
            self.inject_unauthorized_devices,
            self.inject_policy_violations,
            self.inject_uplink_failures
        ]
        
        # Randomly select problems to inject
        selected_problems = random.sample(problem_methods, min(num_problems, len(problem_methods)))
        
        for problem_method in selected_problems:
            try:
                data = problem_method(data)
            except Exception as e:
                print(f"❌ Error injecting problem {problem_method.__name__}: {e}")
        
        # Save the updated data
        self.save_data(data)
        
        # Print summary
        print(f"\n🎯 Successfully injected {len(self.problems_injected)} problems:")
        for problem in self.problems_injected:
            print(f"  {problem}")
        
        print(f"\n✅ Your agent now has {len(self.problems_injected)} realistic network problems to detect and fix!")
        return self.problems_injected

def main():
    """Main function"""
    print("🚨 NETWORK PROBLEM INJECTOR")
    print("=" * 50)
    print("This script will inject realistic network problems into your JSON file")
    print("so your agent can detect and fix them during testing.")
    print("VPN issues have been removed from the injection list.")
    print("=" * 50)
    
    injector = NetworkProblemInjector()
    
    # Get number of problems to inject
    try:
        num_problems = int(input("How many problems to inject? (default: 6): ") or "6")
    except ValueError:
        num_problems = 6
    
    # Inject problems
    problems = injector.inject_random_problems(num_problems)
    
    print(f"\n🎉 Ready! Run your agent to detect and fix these {len(problems)} problems!")

if __name__ == "__main__":
    main()
