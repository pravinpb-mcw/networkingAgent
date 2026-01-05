from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import subprocess
import logging
import psutil
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request Models
class APRequest(BaseModel):
    ap_serial: str
    latency_ms: float = 350.0  # Default failure latency
    jitter_ms: float = 55.0    # Default failure jitter

def cleanup_old_processes():
    """Kill any old Phoenix and agent processes from previous runs"""
    logger.info("Cleaning up old processes on startup...")
    killed = []
    
    # Targets to kill - Phoenix and agent scripts
    targets = [
        "phoenix/server.py",
        "phoenix\\server.py",
        "agent_1_risk_calculation.py",
        "agent_2_nearest_ap.py", 
        "agent_3_failover_suggestion.py",
        "auto_risk_score_updater.py",
        "arize-phoenix",
        "phoenix.server.main",
    ]
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            cmd_str = ' '.join(cmdline).lower() if cmdline else ''
            proc_name = proc.info.get('name', '').lower()
            
            # Skip this backend process
            if 'uvicorn' in cmd_str and 'main:app' in cmd_str:
                continue
                
            # Check if this is a target process
            for target in targets:
                if target.lower() in cmd_str or target.lower() in proc_name:
                    logger.info(f"Killing old process: {proc.info['pid']} - {cmd_str[:80]}")
                    proc.kill()
                    killed.append(proc.info['pid'])
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if killed:
        logger.info(f"Cleaned up {len(killed)} old processes: {killed}")
    else:
        logger.info("No old processes found to clean up")
    
    return killed

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Clean up old processes
    cleanup_old_processes()
    yield
    # Shutdown: Nothing needed for now

app = FastAPI(title="Network Observability Dashboard API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get paths dynamically - no hardcoded paths!
# Priority: 1) .env BASE_PATH, 2) Auto-detect from current file location
BASE_PATH = os.getenv('BASE_PATH')

if BASE_PATH:
    # If BASE_PATH is set in .env, use it
    PROJECT_ROOT = os.path.join(BASE_PATH, 'networkingAgent')
else:
    # Auto-detect: go up 3 levels from backend/main.py -> networkingAgent/
    PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
    BASE_PATH = str(Path(PROJECT_ROOT).parent)

# Check for Python virtual environment (supports both .wenv and .venv)
venv_names = ['.wenv', '.venv', 'venv', 'env']
PYTHON_EXE = None

for venv_name in venv_names:
    venv_path = os.path.join(BASE_PATH, venv_name)
    python_path = os.path.join(venv_path, 'Scripts', 'python.exe')  # Windows
    if os.path.exists(python_path):
        PYTHON_EXE = python_path
        break
    # Try Unix-style path
    python_path = os.path.join(venv_path, 'bin', 'python')  # Unix/Mac
    if os.path.exists(python_path):
        PYTHON_EXE = python_path
        break

# Fallback to system Python if no venv found
if not PYTHON_EXE:
    PYTHON_EXE = sys.executable

# Convert to Path objects
BASE_DIR = Path(PROJECT_ROOT)
AGENT_DATA_DIR = BASE_DIR / "agent_data"
LOG_DIR = AGENT_DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# React Dashboard (built files from react_dashboard/dist)
REACT_DIST_DIR = BASE_DIR / "react_dashboard" / "dist"

# Mount React build files if they exist
if REACT_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(REACT_DIST_DIR / "assets")), name="assets")
    logger.info(f"✅ Serving React dashboard from: {REACT_DIST_DIR}")
else:
    logger.warning(f"⚠️ React dashboard not built yet. Run: cd react_dashboard && npm run build")

@app.get("/")
async def serve_dashboard():
    """Serve the React dashboard index.html"""
    index_file = REACT_DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return {
            "error": "Dashboard not built",
            "message": "Run: cd react_dashboard && npm install && npm run build",
            "api_docs": "http://localhost:8000/docs"
        }

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
        from datetime import datetime, timedelta, timezone
        
        file_path = AGENT_DATA_DIR / "risk_scores.json"
        if not file_path.exists():
            return {}
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        # Calculate time threshold (use UTC for consistency)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        result = {}
        
        for ap_serial, ap_data in data.items():
            history = ap_data.get("history", [])
            filtered_data = []
            
            for entry in history:
                try:
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    # Make entry_time offset-aware if it's not
                    if entry_time.tzinfo is None:
                        entry_time = entry_time.replace(tzinfo=timezone.utc)
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

# Global storage for agent logs
MAX_LOG_LINES = 200  # Keep last 200 lines per agent

# Agent process handles
agent_processes = {}

def read_log_file(agent_name: str) -> list:
    """Read log entries from agent log file"""
    log_file = LOG_DIR / f"{agent_name}.log"
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-MAX_LOG_LINES:]  # Last N lines
                for line in lines:
                    line = line.strip()
                    if line:
                        logs.append({
                            "timestamp": datetime.now().isoformat(),
                            "message": line,
                            "level": "error" if "error" in line.lower() or "❌" in line else 
                                    "warn" if "warning" in line.lower() or "⚠️" in line else
                                    "success" if "✅" in line or "success" in line.lower() else "info"
                        })
        except Exception as e:
            logs.append({"timestamp": datetime.now().isoformat(), "message": f"Error reading log: {e}", "level": "error"})
    return logs

@app.get("/system/logs/{agent_name}")
async def get_agent_logs(agent_name: str):
    """Get logs for a specific agent"""
    valid_agents = ["agent1", "agent2", "agent3", "phoenix", "risk_updater"]
    if agent_name not in valid_agents:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")
    
    # Read from log file
    logs = read_log_file(agent_name)
    return {"agent": agent_name, "logs": logs}

@app.delete("/system/logs/{agent_name}")
async def clear_agent_logs(agent_name: str):
    """Clear logs for a specific agent"""
    valid_agents = ["agent1", "agent2", "agent3", "phoenix", "risk_updater"]
    if agent_name not in valid_agents:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")
    
    # Clear log file
    log_file = LOG_DIR / f"{agent_name}.log"
    if log_file.exists():
        log_file.unlink()
    return {"status": "cleared"}

@app.get("/system/logs")
async def get_all_agent_logs():
    """Get logs for all agents"""
    return {
        "agent1": read_log_file("agent1"),
        "agent2": read_log_file("agent2"),
        "agent3": read_log_file("agent3"),
        "phoenix": read_log_file("phoenix"),
        "risk_updater": read_log_file("risk_updater")
    }

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

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

@app.post("/system/start")
async def start_agents():
    """Start all agents directly with Python (no popup terminals)"""
    global agent_processes
    
    try:
        # Check if Phoenix is already running (ports 6006 and 4317)
        phoenix_running = is_port_in_use(6006)
        
        if not phoenix_running:
            # Only stop and restart if Phoenix is not running
            await stop_system()
        else:
            # Phoenix is running, just stop the agents (not Phoenix)
            logger.info("Phoenix already running, only restarting agents...")
            for name in ["agent1", "agent2", "agent3", "risk_updater"]:
                if name in agent_processes and agent_processes[name]:
                    try:
                        agent_processes[name].terminate()
                        agent_processes[name].wait(timeout=2)
                    except:
                        pass
        
        # Clear old log files (except phoenix if it's running)
        logs_to_clear = ["agent1", "agent2", "agent3", "risk_updater"]
        if not phoenix_running:
            logs_to_clear.append("phoenix")
            
        for agent_name in logs_to_clear:
            log_file = LOG_DIR / f"{agent_name}.log"
            try:
                if log_file.exists():
                    log_file.unlink()
            except Exception as e:
                logger.warning(f"Could not delete log file {agent_name}: {e}")
        
        logger.info("Starting agents in background...")
        
        # Determine Python executable
        python_exe = PYTHON_EXE
        if not python_exe or not os.path.exists(python_exe):
            python_exe = "python"
        
        logger.info(f"Using Python: {python_exe}")
        logger.info(f"BASE_DIR: {BASE_DIR}")
        
        # Create startup info to hide windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Set environment to use UTF-8 encoding for subprocess output
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        
        # Start Phoenix Server only if not already running
        if not phoenix_running:
            phoenix_log = open(LOG_DIR / "phoenix.log", "w", encoding="utf-8")
            agent_processes["phoenix"] = subprocess.Popen(
                [python_exe, str(BASE_DIR / "phoenix" / "server.py"), "--auto-eval", "--eval-interval", "10"],
                cwd=str(BASE_DIR),
                stdout=phoenix_log,
                stderr=subprocess.STDOUT,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env
            )
            logger.info("Phoenix server started")
            
            # Wait for Phoenix to be ready
            import time
            time.sleep(3)
        else:
            logger.info("Phoenix already running, skipping...")
        
        # Start Risk Score Updater (updates risk_scores.json from mock data)
        risk_updater_log = open(LOG_DIR / "risk_updater.log", "w", encoding="utf-8")
        agent_processes["risk_updater"] = subprocess.Popen(
            [python_exe, str(BASE_DIR / "scripts" / "auto_risk_score_updater.py"), "--continuous", "10"],
            cwd=str(BASE_DIR),
            stdout=risk_updater_log,
            stderr=subprocess.STDOUT,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=env
        )
        logger.info("Risk Score Updater started")
        
        # Start Agent 1 - Risk Calculation (LLM-based)
        agent1_log = open(LOG_DIR / "agent1.log", "w", encoding="utf-8")
        agent_processes["agent1"] = subprocess.Popen(
            [python_exe, str(BASE_DIR / "agents" / "agent_1_risk_calculation.py"), "--continuous", "15"],
            cwd=str(BASE_DIR),
            stdout=agent1_log,
            stderr=subprocess.STDOUT,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=env
        )
        logger.info("Agent 1 - Risk Calculation started")
        
        # Start Agent 2 - Nearest AP
        agent2_log = open(LOG_DIR / "agent2.log", "w", encoding="utf-8")
        agent_processes["agent2"] = subprocess.Popen(
            [python_exe, str(BASE_DIR / "agents" / "agent_2_nearest_ap.py"), "--continuous", "15"],
            cwd=str(BASE_DIR),
            stdout=agent2_log,
            stderr=subprocess.STDOUT,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=env
        )
        logger.info("Agent 2 - Nearest AP started")
        
        # Start Agent 3 - Failover Suggestion
        agent3_log = open(LOG_DIR / "agent3.log", "w", encoding="utf-8")
        agent_processes["agent3"] = subprocess.Popen(
            [python_exe, str(BASE_DIR / "agents" / "agent_3_failover_suggestion.py"), "--continuous", "60"],
            cwd=str(BASE_DIR),
            stdout=agent3_log,
            stderr=subprocess.STDOUT,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=env
        )
        logger.info("Agent 3 - Failover Suggestion started")
        
        return {"status": "initiated", "message": "All agents started in background"}
    except Exception as e:
        logger.error(f"Failed to start agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/start-agent/{agent_num}")
async def start_single_agent(agent_num: int):
    """Start a specific agent (1, 2, or 3)"""
    try:
        print(f"\n🚀 Starting Agent {agent_num}...")
        
        if agent_num not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="Invalid agent number. Use 1, 2, or 3")
        
        # Kill existing process for this agent
        print(f"   Killing existing Agent {agent_num} process...")
        subprocess.run(
            ["taskkill", "/F", "/FI", f"WINDOWTITLE eq Agent {agent_num}*"],
            capture_output=True
        )
        
        # Use batch files just like "Run All" button
        batch_file = BASE_DIR / "batch" / f"start_agent_{agent_num}.bat"
        if not batch_file.exists():
            # Try old location
            batch_file = BASE_DIR / f"start_agent_{agent_num}.bat"
        
        print(f"   Batch file: {batch_file}")
        print(f"   Exists: {batch_file.exists()}")
        
        if not batch_file.exists():
            raise HTTPException(status_code=404, detail=f"Batch file not found: start_agent_{agent_num}.bat")
        
        # Start the batch file in background without popup window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        subprocess.Popen(
            [str(batch_file)], 
            shell=True, 
            cwd=str(BASE_DIR),
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        print(f"   ✅ Agent {agent_num} started in background")
        
        return {
            "status": "started", 
            "agent": agent_num, 
            "message": f"Agent {agent_num} started in background",
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
        import importlib
        scenarios_dir = BASE_DIR / "scenarios"
        if str(scenarios_dir) not in sys.path:
            sys.path.insert(0, str(scenarios_dir))
        
        # Import and reload to get latest changes
        import user_selected_ap_failure
        importlib.reload(user_selected_ap_failure)
        UserSelectedAPFailure = user_selected_ap_failure.UserSelectedAPFailure
        
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
        
        # Log the user-provided values
        logger.info(f"📡 Simulating AP failure for {selected_ap['name']}")
        logger.info(f"📊 User input - Latency: {request.latency_ms}ms, Jitter: {request.jitter_ms}ms")
        
        # Run the scenario with user-provided latency and jitter
        scenario = UserSelectedAPFailure(selected_ap, latency_ms=request.latency_ms, jitter_ms=request.jitter_ms)
        await scenario.initialize()
        await scenario.update_appliance_settings()
        await scenario.update_mock_data()
        await scenario.close()
        
        logger.info(f"✅ AP failure simulation complete for {selected_ap['name']}")
        
        return {
            "status": "success",
            "message": f"AP {selected_ap['name']} ({ap_serial}) failure simulated with Latency: {request.latency_ms}ms, Jitter: {request.jitter_ms}ms",
            "ap_name": selected_ap['name'],
            "latency_ms": request.latency_ms,
            "jitter_ms": request.jitter_ms
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