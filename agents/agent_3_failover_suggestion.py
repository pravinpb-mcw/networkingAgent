"""
Agent 3: Failover Suggestion Agent
Reads data from Agent 1 (risk scores) and Agent 2 (nearest APs)
Generates failover suggestions with professional analysis

GLM-4.5 Role: Analysis and reasoning based on data
- Read policy, risk scores, and nearest APs
- Analyze data and provide recommendations
- Show professional tables with actual metrics
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.chat_models import init_chat_model
from langchain_core.callbacks import BaseCallbackHandler
from python_a2a import A2AClient, Conversation, Message, MessageRole, TextContent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenTelemetry imports for Phoenix tracing
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Global tracer for A2A
tracer = trace.get_tracer("agent-3-failover-a2a")


def send_teams_webhook(analysis: str, at_risk_count: int):
    """Send notification to Microsoft Teams webhook"""
    try:
        import requests
        webhook_url = os.environ.get("TEAMS_WEBHOOK_URL", "")
        
        if not webhook_url:
            print("    [INFO] No Teams webhook URL configured (set TEAMS_WEBHOOK_URL env var)")
            return
        
        # Extract key findings from analysis
        lines = analysis.split('\n')
        summary = []
        for line in lines:
            if 'Risk Score:' in line or 'AP:' in line or 'PRIMARY RECOMMENDATION' in line:
                summary.append(line.strip())
                if len(summary) >= 5:
                    break
        
        summary_text = '\n'.join(summary) if summary else analysis[:300]
        
        # Create Teams card
        teams_message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"Network Failover Analysis: {at_risk_count} AP(s) at risk",
            "themeColor": "FF6B6B" if at_risk_count > 0 else "4CAF50",
            "title": "Network Failover Analysis Report",
            "sections": [{
                "activityTitle": f"Alert: {at_risk_count} Access Point(s) require attention" if at_risk_count > 0 else "Network Status: All APs Healthy",
                "activitySubtitle": f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "facts": [
                    {"name": "At-Risk APs", "value": str(at_risk_count)},
                    {"name": "Analysis Agent", "value": "Agent 3 - Failover Coordinator"},
                    {"name": "Protocol", "value": "A2A (Agent-to-Agent)"}
                ],
                "text": f"**Key Findings:**\n\n{summary_text}"
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name": "View Phoenix Dashboard",
                "targets": [{"os": "default", "uri": "http://localhost:6006"}]
            }]
        }
        
        response = requests.post(webhook_url, json=teams_message, timeout=10)
        if response.status_code == 200:
            print("    [OK] Teams notification sent successfully")
        else:
            print(f"    [WARN] Teams notification failed: {response.status_code}")
    except Exception as e:
        print(f"    [ERROR] Teams webhook error: {e}")


def save_analysis_to_history(analysis: str, risk_response: str, nearest_responses: dict):
    """Save analysis to history file for dashboard"""
    history_file = project_root / "agent_data" / "analysis_history.json"
    
    # Load existing history
    history = []
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
    
    # Add new entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis,
        "risk_data": risk_response,
        "nearest_data": nearest_responses,
        "iteration": len(history) + 1
    }
    
    history.append(entry)
    
    # Keep only last 50 analyses
    if len(history) > 50:
        history = history[-50:]
    
    # Save back
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)


def read_agent1_risk_scores(threshold: float = 25) -> tuple[str, list[str]]:
    """Read risk scores directly from Agent 1's output file"""
    with tracer.start_as_current_span("read_agent1_data") as span:
        span.set_attribute("source", "agent_data/risk_scores.json")
        span.set_attribute("threshold", threshold)
        
        try:
            risk_file = project_root / "agent_data" / "risk_scores.json"
            with open(risk_file, 'r') as f:
                risk_data = json.load(f)
            
            # Find APs above threshold
            at_risk_aps = []
            response_lines = [f"Risk Score Analysis (Threshold: {threshold}):", ""]
            
            for ap_serial, ap_data in risk_data.items():
                if ap_data.get("history"):
                    latest = ap_data["history"][-1]
                    risk_score = latest.get("risk_score", 0)
                    
                    if risk_score >= threshold:
                        at_risk_aps.append(ap_serial)
                        classification = latest.get("risk_classification", "Unknown")
                        metrics = latest.get("metrics", {})
                        
                        response_lines.append(f"AP: {ap_serial}")
                        response_lines.append(f"  Risk Score: {risk_score}")
                        response_lines.append(f"  Classification: {classification}")
                        response_lines.append(f"  SNR: {metrics.get('snr_db', 'N/A')} dB")
                        response_lines.append(f"  Latency: {metrics.get('latency_ms', 'N/A')} ms")
                        response_lines.append(f"  Retransmissions: {metrics.get('retrans_per_min', 'N/A')}/min")
                        response_lines.append("")
            
            response_text = "\n".join(response_lines)
            if not at_risk_aps:
                response_text += f"\nNo APs found above threshold {threshold}"
            
            span.set_attribute("at_risk_count", len(at_risk_aps))
            return response_text, at_risk_aps
            
        except Exception as e:
            print(f"    ❌ Error reading risk scores: {e}")
            return f"Error reading risk scores: {e}", []


def read_agent2_nearest_aps(ap_serial: str) -> str:
    """Read nearest APs directly from Agent 2's output file"""
    with tracer.start_as_current_span(f"read_agent2_data_{ap_serial}") as span:
        span.set_attribute("source", "agent_data/nearest_aps.json")
        span.set_attribute("ap_serial", ap_serial)
        
        try:
            nearest_file = project_root / "agent_data" / "nearest_aps.json"
            with open(nearest_file, 'r') as f:
                nearest_data = json.load(f)
            
            if ap_serial not in nearest_data:
                return f"No nearest AP data found for {ap_serial}"
            
            ap_data = nearest_data[ap_serial]
            response_lines = [f"Nearest APs for {ap_serial}:", ""]
            
            if "nearest_aps" in ap_data:
                for i, candidate in enumerate(ap_data["nearest_aps"][:5], 1):
                    response_lines.append(f"{i}. {candidate.get('ap_serial', 'Unknown')} - {candidate.get('ap_name', 'N/A')}")
                    response_lines.append(f"   Distance: {candidate.get('distance_meters', 'N/A')} meters")
                    response_lines.append(f"   RSSI: {candidate.get('rssi_dbm', 'N/A')} dBm")
                    response_lines.append(f"   Same Floor: {candidate.get('same_floor', 'N/A')}")
                    response_lines.append(f"   Client Load: {candidate.get('client_load', 'N/A')}")
                    response_lines.append(f"   Composite Score: {candidate.get('composite_score', 'N/A')}")
                    response_lines.append(f"   Rank: {candidate.get('rank', i)}")
                    response_lines.append("")
            
            return "\n".join(response_lines)
            
        except Exception as e:
            print(f"    ❌ Error reading nearest APs: {e}")
            return f"Error reading nearest APs: {e}"


class RealtimeToolLogger:
    """Logger that shows tool calls immediately"""
    
    def __init__(self):
        self.call_count = 0
    
    def log_call(self, tool_name: str):
        """Log tool call in real-time"""
        self.call_count += 1
        print(f"  [{self.call_count}] Calling: {tool_name}")


# Create global logger
tool_logger = RealtimeToolLogger()


class ToolCallbackHandler(BaseCallbackHandler):
    """Callback to show tool calls in real-time"""
    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "unknown")
        tool_logger.log_call(tool_name)


async def run_analysis():
    """Run a single failover analysis by reading data directly from Agent 1 and Agent 2 output files"""
    with tracer.start_as_current_span("failover_analysis_iteration") as parent_span:
        parent_span.set_attribute("agent", "agent-3")
        parent_span.set_attribute("analysis_type", "failover")
        
        print("\n" + "="*80)
        print("📊 DATA COLLECTION")
        print("="*80)
        
        # Read Agent 1 data directly from file
        print("\n[1] Reading Agent 1 Data (Risk Scores)...")
        risk_response, at_risk_aps = read_agent1_risk_scores(threshold=25)
        print(f"    ✅ Found {len(at_risk_aps)} at-risk APs from Agent 1")
        parent_span.set_attribute("at_risk_aps_count", len(at_risk_aps))
        
        # Read Agent 2 data for each at-risk AP
        nearest_responses = {}
        for i, ap_serial in enumerate(at_risk_aps, 2):
            print(f"[{i}] Reading Agent 2 Data (Nearest APs for {ap_serial})...")
            nearest_response = read_agent2_nearest_aps(ap_serial)
            nearest_responses[ap_serial] = nearest_response
            print(f"    ✅ Retrieved nearest APs from Agent 2")
        
        print("\n" + "="*80)
        print("🤖 LLM ANALYSIS (GLM-4.5)")
        print("="*80)
        
        # Use LLM to analyze and summarize
        with tracer.start_as_current_span("llm_failover_analysis") as llm_span:
            llm_span.set_attribute("model", "glm-4.5")
            
            try:
                # Initialize LLM
                from langchain.chat_models import init_chat_model
                llm = init_chat_model(
                    "glm-4.5",
                    model_provider="anthropic",
                    base_url="https://api.z.ai/api/anthropic",
                    api_key=os.environ.get("ANTHROPIC_API_KEY", "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"),
                    temperature=0,
                    max_tokens=2048,
                    timeout=90
                )
                
                # Read policy file
                policy_file = project_root / "policies" / "network_policy.json"
                policy_data = {}
                if policy_file.exists():
                    with open(policy_file, 'r') as f:
                        policy_data = json.load(f)
                
                # Create analysis prompt (rest of the code continues...)
            
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate" in error_msg.lower():
                    print(f"\n⚠️  RATE LIMIT ERROR: GLM API rate limit exceeded")
                    print(f"    Skipping this analysis cycle. Will retry next cycle.")
                    print(f"    Error: {error_msg[:100]}")
                    
                    # Save a simple notification instead of full analysis
                    save_analysis_to_history(
                        f"# Rate Limit Notice\n\nAnalysis skipped due to API rate limit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\nThis is normal when running frequently. The system will retry automatically.",
                        risk_response,
                        nearest_responses
                    )
                    return  # Exit gracefully
                else:
                    # Re-raise if it's a different error
                    raise
            policy_file = project_root / "policies" / "network_policy.json"
            policy_data = {}
            if policy_file.exists():
                with open(policy_file, 'r') as f:
                    policy_data = json.load(f)
            
            # Prepare datetime strings outside f-string to avoid backslash issues
            report_id = f"FA-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            analysis_date = datetime.now().strftime('%B %d, %Y %H:%M:%S')
            nearest_ap_text = "\n".join([f"\nFor AP {ap_serial}:\n{response}" for ap_serial, response in nearest_responses.items()])
            
            # Create analysis prompt
            prompt = f"""You are a professional network failover analyst. Analyze the data collected from Agent 1 and Agent 2 databases and create a structured report.

**DATA SOURCES:**

1. **Policy Configuration (from network_policy.json):**
{json.dumps(policy_data, indent=2)}

2. **Risk Data from Agent 1 (read from agent_data/risk_scores.json):**
{risk_response}

3. **Nearest AP Data from Agent 2 (read from agent_data/nearest_aps.json):**
{nearest_ap_text}

**REQUIRED OUTPUT FORMAT:**

# NETWORK FAILOVER ANALYSIS REPORT

## 1. ANALYSIS OVERVIEW

| Metric | Value |
|--------|-------|
| Report ID | {report_id} |
| Analysis Date | {analysis_date} |
| Analyst | Agent 3 - Failover Coordinator |
| Data Protocol | Direct Database Read (Agent 1 & Agent 2 Output Files) |
| Policy Threshold | {policy_data.get('risk_threshold', 25)} |

## 2. DATA COLLECTION SUMMARY

**How Data Was Obtained:**
- Agent 3 read data directly from shared database files written by Agent 1 and Agent 2
- Step 1: Read risk_scores.json (written by Agent 1) to identify at-risk APs
- Step 2: Read nearest_aps.json (written by Agent 2) to get failover candidates for each at-risk AP
- Step 3: Read network_policy.json to apply configured thresholds and rules

**Data Sources:**

| Source | Data Location | Data Type | Purpose |
|--------|---------------|-----------|---------|
| Agent 1 | agent_data/risk_scores.json | Risk scores with metrics | Identify failing APs |
| Agent 2 | agent_data/nearest_aps.json | Candidate APs with distances | Find failover targets |
| Policy | policies/network_policy.json | Thresholds and rules | Apply failover criteria |

## 3. NETWORK STATUS

| Metric | Count |
|--------|-------|
| Total APs Monitored | [Extract from data] |
| APs Above Threshold (>25) | [Count from risk data] |
| Connected Clients (At-Risk APs) | [Extract if available] |
| Action Required | Yes / No |

## 4. AT-RISK ACCESS POINTS ANALYSIS

**WHY Failures Are Happening:**

**CRITICAL: List ALL at-risk APs from the risk data. If there are 2 failing APs, show analysis for BOTH!**

For EACH at-risk AP identified, create this section:

---
**AP: [AP_Serial] - [AP_Name]**
- Risk Score: [Score]/100 (Classification: [Classification])
- Root Cause: [Explain WHY this AP is failing based on risk score and classification]
  * Retransmission Rate: [Estimated] (Normal: <30/min, Current: likely elevated)
  * Signal-to-Noise Ratio: [Estimated] (Optimal: >25dB, Current: likely degraded)
  * Client Impact: [Number] clients experiencing degraded service
  * Severity: Critical/Warning based on score

---

## 5. FAILOVER CANDIDATES

**HOW Nearest APs Were Determined:**
Agent 2 used composite scoring algorithm via A2A tool call, evaluating:
- Physical distance (meters) - shorter is better
- RSSI signal strength (dBm) - higher (less negative) is better  
- Same floor preference - reduces interference
- Current client load - lower is better
- Channel interference - cleaner channels preferred

**CRITICAL: Generate a separate failover table for EACH at-risk AP identified in Section 4!**

**For EACH at-risk AP, create this section:**

---
### Candidates for: [AP_Serial] - [AP_Name]

| Rank | AP Serial | AP Name | Distance | RSSI | Same Floor | Clients | Score | Selection Reason |
|------|-----------|---------|----------|------|------------|---------|-------|------------------|
| 1st | [Serial] | [Name] | [X]m | [X]dBm | Yes/No | [X from client_load field] | [X]/100 | Closest distance + strongest signal |
| 2nd | [Serial] | [Name] | [X]m | [X]dBm | Yes/No | [X from client_load field] | [X]/100 | Good backup, acceptable signal |
| 3rd | [Serial] | [Name] | [X]m | [X]dBm | Yes/No | [X from client_load field] | [X]/100 | Last resort option |

**PRIMARY RECOMMENDATION for [AP_Serial]:**
- Target AP: [1st place serial] ([Name])
- Distance: [X]m | RSSI: [X]dBm | Same Floor: Yes/No
- Expected Risk Reduction: [Current Score] to <20
- WHY CHOSEN: [Detailed explanation]

**SECONDARY BACKUP:** [2nd place serial] - [Justification]
**TERTIARY OPTION:** [3rd place serial] - [When to use]

---

**REPEAT THE ABOVE SECTION FOR EVERY AT-RISK AP! If there are 2 failing APs, show 2 failover tables.**

## 6. RECOMMENDED ACTIONS

**For EACH at-risk AP, provide specific migration actions:**

| At-Risk AP | Target AP | Step | Action | Timeline | Details |
|------------|-----------|------|--------|----------|---------|
| [Failing AP Serial] | [Target AP Serial] | 1 | Migrate Clients | Immediate (5 min) | Move clients from [failing] to [target] |
| [Failing AP Serial] | [Target AP Serial] | 2 | Monitor Target | Continuous | Watch load, latency on target AP |
| [Failing AP Serial] | [Target AP Serial] | 3 | Verify Connectivity | After migration | Ping tests + application checks |

**If there are multiple at-risk APs, list actions for ALL of them!**

**Summary of Recommendations:**

## 7. RISK ASSESSMENT

**If Action Taken:**
- Service restored for [X] clients
- Risk score reduced by [X] points
- Network stability maintained

**If No Action Taken:**
- [X] clients continue experiencing degraded service
- Potential complete AP failure
- Business impact: Lost productivity, user complaints

**IMPORTANT:**
- Use actual numbers from the data provided
- If no APs are at risk, state "No action required - all APs healthy"
- Be specific and professional
- Keep formatting clean and concise
"""

            llm_span.set_attribute("input.value", prompt)
            print("\n🔄 Calling GLM-4.5 for analysis...")
            
            # Get LLM response
            response = llm.invoke(prompt)
            analysis = response.content
            
            llm_span.set_attribute("output.value", analysis)
            llm_span.set_attribute("analysis_length", len(analysis))
            llm_span.add_event("LLM Analysis Complete")
        
        # Send Teams notification
        print("\n[NOTIFICATION]")
        send_teams_webhook(analysis, len(at_risk_aps))
        
        # Save to history for dashboard
        save_analysis_to_history(analysis, risk_response, nearest_responses)
        
        # Display results
        print("\n" + "="*80)
        print("FAILOVER ANALYSIS REPORT")
        print("="*80 + "\n")
        
        print(analysis)
        
        print("\n" + "="*80)
        print("✅ Analysis complete\n")
        
        parent_span.set_attribute("output.value", analysis)


async def main():
    """Agent 3: Failover Suggestion Agent"""
    
    # Parse command line arguments
    mode = "single"
    interval = 10  # Default 10 seconds
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--continuous":
            mode = "continuous"
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                try:
                    interval = int(args[i+1])
                    i += 1
                except ValueError:
                    pass
        elif args[i] in ["--help", "-h"]:
            print("\nUsage:")
            print("  python agent_3_failover_suggestion.py                    - Single analysis")
            print("  python agent_3_failover_suggestion.py --continuous [sec] - Continuous mode")
            print("  python agent_3_failover_suggestion.py --help             - Show this help")
            print("\nExamples:")
            print("  python agent_3_failover_suggestion.py --continuous 60    - Analyze every 60s")
            print("  python agent_3_failover_suggestion.py --continuous 120   - Analyze every 120s")
            return
        i += 1
    
    print("="*80)
    print("🚨 AGENT 3: FAILOVER SUGGESTION AGENT (A2A Mode)")
    print("="*80)
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print("🔗 Communication: A2A Protocol")
    print("📍 Agent 1 (Risk Scores): http://localhost:5001")
    print("📍 Agent 2 (Nearest APs): http://localhost:5002")
    print("="*80)
    
    # Initialize Phoenix tracing
    resource = Resource.create({"service.name": "agent-3-failover-a2a"})
    tracer_provider = trace_sdk.TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:6006/v1/traces")
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    print("✅ Phoenix tracing enabled: http://localhost:6006\n")
    
    # Run in selected mode
    if mode == "continuous":
        print(f"\n🚀 Starting continuous failover analysis (interval: {interval}s)")
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n{'='*80}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Analysis #{iteration}")
                print(f"{'='*80}")
                
                await run_analysis()
                
                print(f"\n⏳ Next analysis in {interval}s...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⚠️ Stopped by user")
    else:
        # Single analysis
        await run_analysis()


if __name__ == "__main__":
    asyncio.run(main())
