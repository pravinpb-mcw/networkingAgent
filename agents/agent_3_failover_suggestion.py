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


def query_agent_via_a2a(agent_url: str, query: str, agent_name: str = "Unknown") -> str:
    """Query an agent via A2A protocol"""
    with tracer.start_as_current_span(f"Agent3_queries_{agent_name}") as span:
        span.set_attribute("source_agent", "Agent-3-Failover")
        span.set_attribute("target_agent", agent_name)
        span.set_attribute("agent", "agent-3")
        span.set_attribute("target_url", agent_url)
        span.set_attribute("communication.direction", "outgoing")
        span.set_attribute("communication.protocol", "A2A")
        span.set_attribute("input.value", query)
        span.set_attribute("query", query)
        span.set_attribute("target_agent", agent_name)
        span.set_attribute("communication.direction", "outgoing")
        span.add_event("A2A Query Sent")
        
        try:
            client = A2AClient(agent_url)
            conv = Conversation(messages=[
                Message(role=MessageRole.USER, content=TextContent(text=query))
            ])
            response = client.send_conversation(conv)
            
            if response.messages:
                last_msg = response.messages[-1]
                if hasattr(last_msg.content, 'text'):
                    result = last_msg.content.text
                else:
                    result = str(last_msg.content)
                
                span.set_attribute("response_length", len(result))
                span.set_attribute("output.value", result)
                span.set_attribute("status", "success")
                span.set_attribute("response_length", len(result))
                span.add_event("A2A Response Received")
                return result
            
            span.set_attribute("status", "no_response")
            return "No response"
        except Exception as e:
            span.set_attribute("status", "error")
            span.set_attribute("error", str(e))
            return f"Error: {e}"




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
    """Run a single failover analysis using A2A communication"""
    with tracer.start_as_current_span("failover_analysis_iteration") as parent_span:
        parent_span.set_attribute("agent", "agent-3")
        parent_span.set_attribute("analysis_type", "failover")
        
        print("\n" + "="*80)
        print("🔧 A2A COMMUNICATION")
        print("="*80)
        
        # Query Agent 1 for at-risk APs
        print("\n[1] Querying Agent 1 (Risk Scores)...")
        risk_response = query_agent_via_a2a(
            "http://localhost:5001",
            "Get APs at risk with threshold: 41",
            "Agent1_RiskScores"
        )
        print(f"    ✅ Received from Agent 1")
        
        # Extract AP serials from response
        import re
        ap_serials = re.findall(r'Q2XX-[A-Z0-9]{4}-[A-Z0-9]{4}', risk_response)
        parent_span.set_attribute("at_risk_aps_count", len(ap_serials))
        
        # Query Agent 2 for each at-risk AP
        nearest_responses = {}
        for i, ap_serial in enumerate(ap_serials, 2):
            print(f"[{i}] Querying Agent 2 (Nearest APs for {ap_serial})...")
            nearest_response = query_agent_via_a2a(
                "http://localhost:5002",
                f"Get nearest APs for {ap_serial}",
                f"Agent2_NearestAP_{ap_serial}"
            )
            nearest_responses[ap_serial] = nearest_response
            print(f"    ✅ Received from Agent 2")
        
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
            
            # Create analysis prompt
            prompt = f"""You are a professional network failover analyst. Analyze the A2A communication data and create a structured report.

**DATA SOURCES:**

1. **Policy Configuration (from network_policy.json):**
{json.dumps(policy_data, indent=2)}

2. **Risk Data from Agent 1 (via A2A API call to http://localhost:5001):**
{risk_response}

3. **Nearest AP Data from Agent 2 (via A2A API call to http://localhost:5002):**
{json.dumps(nearest_responses, indent=2)}

**REQUIRED OUTPUT FORMAT:**

# NETWORK FAILOVER ANALYSIS REPORT

## 1. ANALYSIS OVERVIEW

| Metric | Value |
|--------|-------|
| Report ID | FA-{datetime.now().strftime('%Y%m%d-%H%M%S')} |
| Analysis Date | {datetime.now().strftime('%B %d, %Y %H:%M:%S')} |
| Analyst | Agent 3 - Failover Coordinator |
| Protocol Used | A2A (Agent-to-Agent) |
| Policy Threshold | {policy_data.get('risk_threshold', 41)} |

## 2. DATA COLLECTION SUMMARY

**How API Data Was Obtained:**
- Agent 3 initiated A2A protocol communication via HTTP requests
- Step 1: Queried Agent 1 at http://localhost:5001 to identify at-risk APs
- Step 2: For each at-risk AP, queried Agent 2 at http://localhost:5002 for failover candidates
- Step 3: Read network_policy.json to apply configured thresholds and rules

**API Calls Made:**

| Source | Endpoint | Query Sent | Data Received | Purpose |
|--------|----------|------------|---------------|---------|
| Agent 1 | http://localhost:5001 | "Get APs at risk with threshold: 41" | Risk scores with thresholds | Identify failing APs |
| Agent 2 | http://localhost:5002 | "Get nearest APs for [AP_SERIAL]" | Candidate APs with metrics | Find failover targets |

## 3. NETWORK STATUS

| Metric | Count |
|--------|-------|
| Total APs Monitored | [Extract from data] |
| APs Above Threshold (>41) | [Count from risk data] |
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
        send_teams_webhook(analysis, len(ap_serials))
        
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
