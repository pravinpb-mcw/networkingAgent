from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import os
from pathlib import Path
import subprocess
import logging
import psutil
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request Models
class APRequest(BaseModel):
    ap_serial: str

app = FastAPI(title="Network Observability Dashboard API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AGENT_DATA_DIR = BASE_DIR / "agent_data"
DASHBOARD_DIR = BASE_DIR / "dashboard"
FRONTEND_DIR = DASHBOARD_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")

# --- Helper Functions ---

def check_port(port):
    try:
        # A2A agents usually respond to /a2a or just root depends on implementation
        # We'll try hitting the root or A2A specifics.
        # Based on logs, A2A server handled A2A requests. 
        # But we just need to see if port is open.
        requests.get(f"http://localhost:{port}/", timeout=0.2)
        return "running"
    except requests.exceptions.ConnectionError:
        return "stopped"
    except:
        # If it returns 404 or anything else (even 500), the server is UP.
        return "running"

def check_process(script_name):
    """Check if a python script is running via psutil"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and script_name in ' '.join(proc.info['cmdline']):
                return "running"
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return "stopped"

# --- API Endpoints ---

@app.get("/status")
async def get_system_status():
    return {
        "agent1": check_port(5001),
        "agent2": check_port(5002),
        "agent3": check_process("agent_3_failover_suggestion.py"),
        "phoenix": check_port(6006),
        "riskUpdater": check_process("auto_risk_score_updater.py")
    }

@app.get("/metrics/risk")
async def get_risk_metrics():
    file_path = AGENT_DATA_DIR / "risk_scores.json"
    if not file_path.exists():
        return {}
    
    # Retry logic for race conditions when file is being written
    for attempt in range(3):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    return json.loads(content)
                return {}
        except (json.JSONDecodeError, IOError) as e:
            if attempt < 2:
                import asyncio
                await asyncio.sleep(0.1)  # Wait 100ms before retry
            else:
                return {}  # Return empty on final failure instead of 500
        except Exception as e:
            return {}

@app.get("/metrics/nearest")
async def get_nearest_aps():
    file_path = AGENT_DATA_DIR / "nearest_aps.json"
    if not file_path.exists():
        return {}
    
    # Retry logic for race conditions when file is being written
    for attempt in range(3):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    return json.loads(content)
                return {}
        except (json.JSONDecodeError, IOError) as e:
            if attempt < 2:
                import asyncio
                await asyncio.sleep(0.1)
            else:
                return {}
        except Exception as e:
            return {}

@app.get("/analysis/history")
async def get_analysis_history():
    try:
        file_path = AGENT_DATA_DIR / "analysis_history.json"
        if not file_path.exists():
            return []
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return []
@app.get("/metrics/timeseries/{metric_type}")
async def get_timeseries_data(metric_type: str, hours: int = 24):
    """Get time-series data for a specific metric over the last N hours"""
    try:
        from datetime import datetime, timedelta
        
        file_path = AGENT_DATA_DIR / "risk_scores.json"
        if not file_path.exists():
            return {}
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        # Calculate time threshold
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        result = {}
        
        for ap_serial, ap_data in data.items():
            history = ap_data.get("history", [])
            filtered_data = []
            
            for entry in history:
                try:
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if entry_time >= cutoff_time:
                        # Extract the requested metric
                        value = None
                        if metric_type == "risk":
                            value = entry.get("risk_score")
                        elif metric_type == "snr":
                            value = entry.get("metrics", {}).get("snr_db")
                        elif metric_type == "latency":
                            value = entry.get("metrics", {}).get("latency_ms")
                        elif metric_type == "jitter":
                            value = entry.get("metrics", {}).get("jitter_ms")
                        elif metric_type == "retransmissions":
                            value = entry.get("metrics", {}).get("retrans_per_min")
                        
                        if value is not None:
                            filtered_data.append({
                                "timestamp": entry["timestamp"],
                                "value": value
                            })
                except (ValueError, KeyError):
                    continue
            
            if filtered_data:
                result[ap_serial] = {
                    "ap_name": ap_data.get("current", {}).get("ap_name", ap_serial[:12]),
                    "data": filtered_data
                }
        
        return result
    except Exception as e:
        logger.error(f"Time-series error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings/webhook")
async def get_webhook_settings():
    """Check webhook configuration status"""
    webhook_url = os.environ.get("TEAMS_WEBHOOK_URL", "")
    return {
        "configured": bool(webhook_url),
        "webhook_type": "Microsoft Teams" if webhook_url else None
    }

@app.post("/settings/webhook/test")
async def test_webhook():
    """Send a test notification to the configured webhook"""
    try:
        webhook_url = os.environ.get("TEAMS_WEBHOOK_URL", "")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="No webhook configured. Set TEAMS_WEBHOOK_URL environment variable.")
        
        from datetime import datetime
        
        test_message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "Dashboard Test Notification",
            "themeColor": "0078D4",
            "title": "🧪 Test Notification",
            "sections": [{
                "activityTitle": "Dashboard Connection Test",
                "activitySubtitle": f"Sent from Dashboard at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "facts": [
                    {"name": "Status", "value": "✅ Webhook Connected"},
                    {"name": "Source", "value": "Network Observability Dashboard"}
                ],
                "text": "This is a test notification. Your webhook is configured correctly!"
            }]
        }
        
        response = requests.post(webhook_url, json=test_message, timeout=10)
        
        if response.status_code == 200:
            return {"status": "success", "message": "Test notification sent successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Webhook returned status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Webhook test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/stop")
async def stop_system():
    """Stop all agents, Phoenix server, and risk updater"""
    killed_processes = []
    
    # Target patterns to identify our processes
    targets = [
        "agent_1_risk_calculation.py",
        "agent_2_nearest_ap.py",
        "agent_3_failover_suggestion.py",
        "auto_risk_score_updater.py",
        "phoenix.server" 
    ]

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline:
                cmd_str = ' '.join(cmdline)
                # Check if this process matches any of our targets
                matched = False
                for t in targets:
                    if t in cmd_str:
                        matched = True
                        break
                
                if matched:
                    proc.kill()
                    killed_processes.append(cmd_str)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    return {"status": "stopped", "killed_count": len(killed_processes)}

@app.post("/system/start")
async def start_agents():
    try:
        # We use the new master script
        batch_file = BASE_DIR / "start_system.bat"
        if not batch_file.exists():
            raise HTTPException(status_code=404, detail="Start script not found")
        
        subprocess.Popen(
            [str(batch_file)], 
            shell=True, 
            cwd=str(BASE_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return {"status": "initiated", "message": "Starting Phoenix and Agents..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/start-agent/{agent_num}")
async def start_single_agent(agent_num: int):
    """Start a specific agent (1, 2, or 3)"""
    try:
        print(f"\n🚀 Starting Agent {agent_num}...")
        
        if agent_num not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="Invalid agent number. Use 1, 2, or 3")
        
        # Use batch files just like "Run All" button
        batch_file = BASE_DIR / f"start_agent_{agent_num}.bat"
        
        print(f"   Batch file: {batch_file}")
        print(f"   Exists: {batch_file.exists()}")
        
        if not batch_file.exists():
            raise HTTPException(status_code=404, detail=f"Batch file not found: start_agent_{agent_num}.bat")
        
        # Start the batch file in new console (same as Run All button)
        subprocess.Popen(
            [str(batch_file)], 
            shell=True, 
            cwd=str(BASE_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        print(f"   ✅ Agent {agent_num} batch file launched in new console")
        
        return {
            "status": "started", 
            "agent": agent_num, 
            "message": f"Agent {agent_num} started in new console window",
            "batch_file": str(batch_file)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/stop-agent/{agent_num}")
async def stop_single_agent(agent_num: int):
    """Stop a specific agent (1, 2, or 3)"""
    try:
        agent_scripts = {
            1: "agent_1_risk_calculation.py",
            2: "agent_2_nearest_ap.py",
            3: "agent_3_failover_suggestion.py"
        }
        
        if agent_num not in agent_scripts:
            raise HTTPException(status_code=400, detail="Invalid agent number. Use 1, 2, or 3")
        
        script_name = agent_scripts[agent_num]
        killed = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline')
                if cmdline:
                    cmd_str = ' '.join(cmdline)
                    if script_name in cmd_str:
                        proc.kill()
                        killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return {"status": "stopped", "agent": agent_num, "killed": killed}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scenarios/aps")
async def get_available_aps():
    """Get list of available APs for scenario simulation"""
    aps = [
        {"serial": "Q2XX-ABCD-1234", "name": "AP-03", "mac": "00:11:22:33:44:55"},
        {"serial": "Q2XX-AP06-5678", "name": "AP-06", "mac": "00:11:22:33:44:99"},
        {"serial": "Q2XX-AP01-1111", "name": "AP-01", "mac": "00:11:22:33:44:11"},
        {"serial": "Q2XX-AP04-4444", "name": "AP-04", "mac": "00:11:22:33:44:44"},
        {"serial": "Q2XX-AP08-8888", "name": "AP-08", "mac": "00:11:22:33:44:88"}
    ]
    return aps

@app.post("/scenarios/fail-ap")
async def simulate_ap_failure(request: APRequest):
    """Simulate AP failure by running the user_selected_ap_failure script"""
    try:
        ap_serial = request.ap_serial
        
        # Import the scenario module
        import sys
        scenarios_dir = BASE_DIR / "scenarios"
        if str(scenarios_dir) not in sys.path:
            sys.path.insert(0, str(scenarios_dir))
        
        # Import and run the failure scenario
        from user_selected_ap_failure import UserSelectedAPFailure
        
        # Find the AP details
        aps = [
            {"serial": "Q2XX-ABCD-1234", "name": "AP-03", "mac": "00:11:22:33:44:55"},
            {"serial": "Q2XX-AP06-5678", "name": "AP-06", "mac": "00:11:22:33:44:99"},
            {"serial": "Q2XX-AP01-1111", "name": "AP-01", "mac": "00:11:22:33:44:11"},
            {"serial": "Q2XX-AP04-4444", "name": "AP-04", "mac": "00:11:22:33:44:44"},
            {"serial": "Q2XX-AP08-8888", "name": "AP-08", "mac": "00:11:22:33:44:88"}
        ]
        
        selected_ap = next((ap for ap in aps if ap["serial"] == ap_serial), None)
        if not selected_ap:
            raise HTTPException(status_code=404, detail="AP not found")
        
        # Run the scenario
        import asyncio
        scenario = UserSelectedAPFailure(selected_ap)
        await scenario.initialize()
        await scenario.update_appliance_settings()
        await scenario.update_mock_data()
        await scenario.close()
        
        return {
            "status": "success",
            "message": f"AP {selected_ap['name']} ({ap_serial}) failure simulated",
            "ap_name": selected_ap['name']
        }
        
    except Exception as e:
        logger.error(f"Failed to simulate AP failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scenarios/recover-ap")
async def simulate_ap_recovery(request: APRequest):
    """Restore AP to healthy state by running the user_selected_ap_healthy script"""
    try:
        ap_serial = request.ap_serial
        
        # Import the scenario module
        import sys
        scenarios_dir = BASE_DIR / "scenarios"
        if str(scenarios_dir) not in sys.path:
            sys.path.insert(0, str(scenarios_dir))
        
        # Import and run the recovery scenario
        from user_selected_ap_healthy import UserSelectedAPHealthy
        
        # Find the AP details
        aps = [
            {"serial": "Q2XX-ABCD-1234", "name": "AP-03", "mac": "00:11:22:33:44:55"},
            {"serial": "Q2XX-AP06-5678", "name": "AP-06", "mac": "00:11:22:33:44:99"},
            {"serial": "Q2XX-AP01-1111", "name": "AP-01", "mac": "00:11:22:33:44:11"},
            {"serial": "Q2XX-AP04-4444", "name": "AP-04", "mac": "00:11:22:33:44:44"},
            {"serial": "Q2XX-AP08-8888", "name": "AP-08", "mac": "00:11:22:33:44:88"}
        ]
        
        selected_ap = next((ap for ap in aps if ap["serial"] == ap_serial), None)
        if not selected_ap:
            raise HTTPException(status_code=404, detail="AP not found")
        
        # Run the scenario
        import asyncio
        scenario = UserSelectedAPHealthy(selected_ap)
        await scenario.initialize()
        await scenario.update_appliance_settings()
        await scenario.update_mock_data()
        await scenario.close()
        
        return {
            "status": "success",
            "message": f"AP {selected_ap['name']} ({ap_serial}) restored to healthy",
            "ap_name": selected_ap['name']
        }
        
    except Exception as e:
        logger.error(f"Failed to restore AP: {e}")
        raise HTTPException(status_code=500, detail=str(e))