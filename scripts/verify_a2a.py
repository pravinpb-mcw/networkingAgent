#!/usr/bin/env python3
"""
Verify A2A Communication Between Agents
Tests if Agent 1 and Agent 2 A2A servers are running and responsive
"""

import sys
import json
import requests
from pathlib import Path

def check_a2a_server(port: int, agent_name: str) -> bool:
    """Check if A2A server is running on specified port"""
    url = f"http://localhost:{port}"
    
    print(f"\n{'='*60}")
    print(f"Testing {agent_name} on port {port}")
    print(f"{'='*60}")
    
    try:
        # Try to connect to the A2A server
        response = requests.get(url, timeout=2)
        print(f"✅ {agent_name} server is RUNNING on port {port}")
        print(f"   Status Code: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ {agent_name} server is NOT running on port {port}")
        print(f"   → Start it with: python {agent_name.lower().replace(' ', '_')}_agent.py --continuous 10")
        return False
    except Exception as e:
        print(f"⚠️ Error checking {agent_name}: {e}")
        return False

def test_a2a_query(port: int, agent_name: str, test_query: str) -> bool:
    """Test A2A query to an agent"""
    try:
        from python_a2a import A2AClient, Message, TextContent, MessageRole, Conversation
    except ImportError:
        print("❌ python-a2a not installed. Install with: pip install python-a2a")
        return False
    
    print(f"\n📡 Testing A2A query: '{test_query}'")
    
    try:
        client = A2AClient(f"http://localhost:{port}")
        conversation = Conversation()
        message = Message(
            content=TextContent(text=test_query),
            role=MessageRole.USER
        )
        conversation.add_message(message)
        
        response = client.send(conversation)
        
        if response and response.messages:
            last_message = response.messages[-1]
            if hasattr(last_message.content, 'text'):
                print(f"✅ Received response from {agent_name}")
                
                # Try to parse as JSON
                try:
                    data = json.loads(last_message.content.text)
                    print(f"   Response Type: JSON")
                    print(f"   Success: {data.get('success', 'N/A')}")
                    if 'ap_count' in data:
                        print(f"   AP Count: {data['ap_count']}")
                    if 'count' in data:
                        print(f"   Count: {data['count']}")
                except json.JSONDecodeError:
                    print(f"   Response Type: Text")
                    print(f"   Preview: {last_message.content.text[:100]}...")
                
                return True
        
        print(f"⚠️ No response from {agent_name}")
        return False
        
    except Exception as e:
        print(f"❌ Error querying {agent_name}: {e}")
        return False

def check_json_files():
    """Check if agent data files exist and have data"""
    print(f"\n{'='*60}")
    print("Checking Agent Data Files")
    print(f"{'='*60}")
    
    agent_data_dir = Path(__file__).parent / "agent_data"
    
    files = {
        "risk_scores.json": "Agent 1 (Risk Score) data",
        "nearest_aps.json": "Agent 2 (Nearest AP) data"
    }
    
    for filename, description in files.items():
        filepath = agent_data_dir / filename
        
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                if data:
                    print(f"✅ {filename}")
                    print(f"   {description}")
                    print(f"   Entries: {len(data)}")
                else:
                    print(f"⚠️ {filename} - EMPTY")
                    print(f"   {description}")
            except Exception as e:
                print(f"❌ {filename} - ERROR: {e}")
        else:
            print(f"❌ {filename} - NOT FOUND")
            print(f"   {description}")

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           A2A COMMUNICATION VERIFICATION TOOL                ║
║                                                              ║
║  Checks if Agent 1 and Agent 2 are running with A2A         ║
║  servers and can respond to queries                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check if agents are running
    agent1_running = check_a2a_server(5001, "Agent 1 (Risk Score)")
    agent2_running = check_a2a_server(5002, "Agent 2 (Nearest AP)")
    
    # Check data files
    check_json_files()
    
    # If agents are running, test queries
    if agent1_running:
        print(f"\n{'='*60}")
        print("Testing Agent 1 Queries")
        print(f"{'='*60}")
        test_a2a_query(5001, "Agent 1", "Get all risk scores")
        test_a2a_query(5001, "Agent 1", "Get at-risk APs with risk score >= 40")
    
    if agent2_running:
        print(f"\n{'='*60}")
        print("Testing Agent 2 Queries")
        print(f"{'='*60}")
        test_a2a_query(5002, "Agent 2", "Get all nearest APs")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if agent1_running and agent2_running:
        print("✅ Both A2A servers are running")
        print("✅ Agent 3 can communicate with Agent 1 and Agent 2")
        print("\n🚀 You can now run Agent 3:")
        print("   python network_monitoring_agent.py --continuous 15")
    elif agent1_running or agent2_running:
        print("⚠️ Only some A2A servers are running")
        if not agent1_running:
            print("   ❌ Agent 1 A2A server not detected")
            print("   → Start: python risk_score_agent.py --continuous 10 --a2a-port 5001")
        if not agent2_running:
            print("   ❌ Agent 2 A2A server not detected")
            print("   → Start: python nearest_ap_agent.py --continuous 30 --a2a-port 5002")
    else:
        print("❌ No A2A servers detected")
        print("\n📋 To enable A2A communication:")
        print("   1. Terminal 1: python mock_server.py")
        print("   2. Terminal 2: python risk_score_agent.py --continuous 10 --a2a-port 5001")
        print("   3. Terminal 3: python nearest_ap_agent.py --continuous 30 --a2a-port 5002")
        print("   4. Terminal 4: python network_monitoring_agent.py --continuous 15")

if __name__ == "__main__":
    main()
