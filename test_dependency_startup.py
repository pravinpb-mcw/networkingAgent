#!/usr/bin/env python3
"""
Test Dependency Agent Startup
Tests if the dependency agents can start correctly when launched manually.
"""

import subprocess
import sys
import time
import socket
import os
from pathlib import Path

def check_port(port: int) -> bool:
    """Check if a port is in use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def test_agent_startup(agent_name: str, script_name: str, port: int):
    """Test starting a single agent"""
    print(f"\n🧪 Testing {agent_name}")
    print("=" * 50)
    
    # Check if already running
    if check_port(port):
        print(f"⚠️ Port {port} already in use - stopping existing process")
        return False
    
    # Get script path
    script_dir = Path(__file__).parent
    agent_path = script_dir / "agents" / script_name
    
    if not agent_path.exists():
        print(f"❌ Agent script not found: {agent_path}")
        return False
    
    print(f"📍 Script path: {agent_path}")
    print(f"📂 Working dir: {script_dir}")
    
    # Start the process
    try:
        print(f"🚀 Starting {agent_name}...")
        process = subprocess.Popen(
            [sys.executable, str(agent_path), "--continuous"],
            cwd=str(script_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait and check
        for attempt in range(1, 11):  # 10 attempts, 1 second each
            time.sleep(1)
            
            if process.poll() is not None:
                # Process died
                stdout, stderr = process.communicate()
                print(f"❌ Process died (exit code: {process.returncode})")
                print(f"📤 Stdout: {stdout[:300]}...")
                print(f"📤 Stderr: {stderr[:300]}...")
                return False
            
            if check_port(port):
                print(f"✅ {agent_name} started successfully (attempt {attempt})")
                print(f"🌐 Listening on port {port}")
                
                # Give it a moment to stabilize
                time.sleep(2)
                
                # Terminate for testing
                print(f"🛑 Terminating {agent_name} for test...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {agent_name} terminated cleanly")
                return True
            
            print(f"⏳ Waiting for {agent_name} (attempt {attempt}/10)...")
        
        print(f"❌ {agent_name} failed to bind to port {port} within 10 seconds")
        process.terminate()
        return False
        
    except Exception as e:
        print(f"❌ Exception during {agent_name} startup: {e}")
        return False

def main():
    """Test all dependency agents"""
    print("🔬 DEPENDENCY AGENT STARTUP TEST")
    print("=" * 60)
    
    agents = [
        ("Risk Score Agent", "risk_score_agent.py", 5001),
        ("Nearest AP Agent", "nearest_ap_agent.py", 5002)
    ]
    
    results = []
    for agent_name, script_name, port in agents:
        success = test_agent_startup(agent_name, script_name, port)
        results.append((agent_name, success))
    
    print(f"\n📊 TEST RESULTS")
    print("=" * 30)
    for agent_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {agent_name}")
    
    all_passed = all(success for _, success in results)
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

if __name__ == "__main__":
    main()