#!/usr/bin/env python3
"""
Risk Score Agent WITH EXPLAINABILITY

This version logs explanations for EVERY action:
- Why each tool was called
- How metrics were calculated
- Why risk classifications were chosen
- Hallucination detection for all outputs
- Decision reasoning logged to Phoenix

All explanations visible in Phoenix dashboard!
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core"))

# Import explainability module FIRST
from explainability import create_explainability_tracker, ExplainabilityTracker

# Phoenix Tracing
from phoenix_tracing import initialize_phoenix, is_phoenix_enabled

# LangChain imports
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("langchain_mcp_adapters").setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("openinference.instrumentation.langchain._tracer").setLevel(logging.CRITICAL)
logger = logging.getLogger("risk-score-agent-explainable")


@dataclass
class RiskAgentContext:
    """Context schema for the risk score calculation agent"""
    session_id: str
    user_id: str
    network_id: str
    calculation_interval: int


class ExplainableRiskScoreAgent:
    """
    Risk Score Agent with FULL EXPLAINABILITY
    
    Every action is explained:
    - Tool calls: WHY each tool was chosen
    - Metric calculations: HOW scores were computed
    - Decisions: WHY a classification was assigned
    - Hallucination checks: WHAT is factual vs fabricated
    """
    
    def __init__(
        self,
        calculation_interval: int = 10,
        enable_explainability: bool = True,
        phoenix_port: int = 6006
    ):
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.agent = None
        self.tools = None
        
        # Configuration
        self.calculation_interval = calculation_interval
        self.session_id = f"risk-agent-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.user_id = "risk-score-agent"
        self.network_id = "L_3947405073390239794"
        
        # Explainability tracker
        self.explainer: Optional[ExplainabilityTracker] = None
        if enable_explainability:
            self.explainer = create_explainability_tracker(
                agent_name="RiskScoreAgent",
                phoenix_endpoint=f"http://localhost:{phoenix_port}",
                judge_model="gpt-4o",
                enable=True
            )
            if self.explainer:
                logger.info("✅ Explainability tracker initialized")
        
        # Risk score weights
        self.weights = {
            "latency": 0.25,
            "jitter": 0.20,
            "retransmission": 0.20,
            "snr_degradation": 0.15,
            "client_load": 0.10,
            "auth_failure_rate": 0.10
        }
        
        # Thresholds
        self.thresholds = {
            "latency_ms": {"good": 30, "warning": 60, "critical": 100},
            "jitter_ms": {"good": 10, "warning": 20, "critical": 30},
            "packet_loss_pct": {"good": 1.0, "warning": 3.0, "critical": 6.0},
            "retransmissions_per_min": {"good": 20, "warning": 35, "critical": 50},
            "snr_db": {"good": 25, "warning": 20, "critical": 15},
            "client_count": {"good": 20, "warning": 40, "critical": 60},
            "auth_failures_per_hour": {"good": 3, "warning": 8, "critical": 15}
        }
        
        # Explain configuration
        if self.explainer:
            self.explainer.explain_action(
                action_type="initialization",
                input_context=f"Network ID: {self.network_id}, Interval: {calculation_interval}s",
                output_result=f"Weights: {json.dumps(self.weights)}\nThresholds configured",
                reference_context="Agent configuration with risk formula and thresholds",
                metadata={
                    "weights": self.weights,
                    "thresholds": self.thresholds
                }
            )
    
    async def initialize(self) -> bool:
        """Initialize the MCP client and agent"""
        try:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            server_path = os.path.join(script_dir, "server", "meraki_server.py")
            
            # Explain MCP setup
            if self.explainer:
                self.explainer.explain_decision(
                    decision_point="Choose MCP server configuration",
                    chosen_option=f"stdio transport to {server_path}",
                    alternatives=["HTTP transport", "WebSocket transport", "No MCP"],
                    reasoning="stdio provides reliable local communication with Meraki API mock server",
                    supporting_data={"server_path": server_path}
                )
            
            # Try to initialize MCP client
            mcp_success = False
            try:
                self.mcp_client = MultiServerMCPClient(
                    {
                        "cisco-meraki-observability": {
                            "transport": "stdio",
                            "command": "python",
                            "args": [server_path],
                            "env": {
                                "TIMESPAN": "7200",
                                "BASE_URL": "https://api.meraki.com/api/v1",
                                "MOCK_BASE_URL": "http://127.0.0.1:5000",
                                "PRODUCT_TYPE": "appliance"
                            }
                        }
                    }
                )
                
                self.tools = await self.mcp_client.get_tools()
                logger.info(f"✅ Loaded {len(self.tools)} MCP tools successfully")
                mcp_success = True
                
                # Explain tool discovery
                if self.explainer:
                    tool_names = [t.name for t in self.tools] if self.tools else []
                    self.explainer.explain_action(
                        action_type="tool_discovery",
                        input_context="MCP server connected",
                        output_result=f"Discovered {len(self.tools)} tools: {', '.join(tool_names[:5])}...",
                        reference_context="Available Meraki API tools for network monitoring",
                        metadata={"tool_count": len(self.tools), "tool_names": tool_names}
                    )
                
            except Exception as mcp_error:
                logger.error(f"❌ MCP initialization failed: {mcp_error}")
                self.tools = []
                self.mcp_client = None
                
                if self.explainer:
                    self.explainer.explain_action(
                        action_type="error",
                        input_context="MCP server connection attempted",
                        output_result=f"Failed: {str(mcp_error)}",
                        reference_context="MCP tools unavailable - agent will run with limited functionality"
                    )
            
            # Initialize model
            model = init_chat_model(
                model="claude-sonnet-4-20250514",
                model_provider="anthropic",
                temperature=0,
                max_tokens=512,
                timeout=60,
                max_retries=1,
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
                base_url=os.environ.get("ANTHROPIC_BASE_URL"),
            )
            
            # Create agent
            self.agent = create_agent(
                model=model,
                tools=self.tools,
                system_prompt=self.get_system_prompt(),
                context_schema=RiskAgentContext,
            )
            
            logger.info("✅ Risk Score Agent with Explainability initialized!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            if self.explainer:
                self.explainer.explain_action(
                    action_type="error",
                    input_context="Agent initialization",
                    output_result=f"Fatal error: {str(e)}",
                    reference_context="Agent could not be initialized"
                )
            return False
    
    async def close(self):
        """Close the MCP client and print explainability summary"""
        if self.mcp_client:
            self.mcp_client = None
        
        # Print explainability summary
        if self.explainer:
            self.explainer.print_summary()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for risk score calculation"""
        return f"""You are an AP RISK SCORE CALCULATION AGENT with FULL EXPLAINABILITY.

**PRIMARY MISSION:**
1. Get network topology to discover ALL available Access Points
2. Calculate risk scores for EVERY available AP
3. **EXPLAIN EVERY DECISION AND CALCULATION**
4. Update calculated scores in JSON storage

**EXPLAINABILITY REQUIREMENTS:**
- For EVERY tool call, state WHY you chose that tool
- For EVERY metric, show HOW you calculated it
- For EVERY decision, explain YOUR REASONING
- Provide step-by-step justification

**AGENT WORKFLOW:**

STEP 1: GET TOPOLOGY & DISCOVER APs
- Call get_network_topology_link_layer(network_id="{self.network_id}")
  **WHY**: Get complete network topology with all devices
  **EXPECTED**: List of all APs with serial numbers
- Count total APs discovered
- Extract serial numbers for ALL APs

STEP 2: CALCULATE RISK SCORES FOR ALL APs
For EACH AP found in Step 1:
  a) get_wireless_latency_history(network_id, device_serial)
     **WHY**: Need latency & jitter metrics for risk calculation
  b) get_wireless_usage_history(network_id, device_serial)
     **WHY**: Need retransmission & SNR data for risk calculation
  c) get_device_clients(device_serial)
     **WHY**: Need client load & auth failures for risk calculation

**RISK SCORE FORMULA (EXPLAIN EACH CALCULATION):**
RISK_SCORE = 0.25 * latency_score + 
             0.20 * jitter_score + 
             0.20 * retrans_score + 
             0.15 * snr_score + 
             0.10 * load_score + 
             0.10 * auth_score

**FOR EACH METRIC, EXPLAIN:**
1. Raw value obtained from tool
2. How it maps to 0-100 score
3. Why this threshold was used
4. How it contributes to final risk

SCORING (each metric scored 0-100, higher = worse):
- Latency: <30ms=20, 30-60ms=50, 60-100ms=80, >100ms=100
- Jitter: <10ms=20, 10-20ms=50, 20-30ms=80, >30ms=100
- Retrans: <20/min=20, 20-35/min=50, 35-50/min=80, >50/min=100
- SNR: >25dB=20, 20-25dB=50, 15-20dB=80, <15dB=100
- Load: <20 clients=20, 20-40=50, 40-60=80, >60=100
- Auth Failures: <3/hr=20, 3-8/hr=50, 8-15/hr=80, >15/hr=100

RISK CLASSIFICATION (EXPLAIN WHY EACH AP FALLS INTO ITS CATEGORY):
- 0-20: Stable Network - All metrics within normal range
- 21-40: Temporary Degradation - Some metrics elevated
- 41-70: Sustained Degradation - Multiple metrics problematic
- 71-100: Likely Failure - Critical metrics failing

STEP 3: UPDATE JSON FOR ALL APs
For EACH AP, call update_risk_score with complete data

**OUTPUT FORMAT:**
Provide detailed explanation including:
- Total APs discovered and WHY that count
- For EACH AP: metric values, calculations, and reasoning
- Risk classifications with justifications
- Summary of decisions made

**REMEMBER: EXPLAIN EVERY STEP!**"""
    
    async def calculate_risk_scores(self) -> Dict[str, Any]:
        """Run risk score calculation with explanations"""
        try:
            prompt = f"""**AGENT 1: RISK SCORE CALCULATION WITH EXPLAINABILITY**

Network ID: {self.network_id}

**EXECUTE WITH FULL EXPLANATIONS:**

STEP 1: GET TOPOLOGY
- Call get_network_topology_link_layer(network_id="{self.network_id}")
- EXPLAIN: Why this tool? What data do we expect?
- Count APs and list serials

STEP 2: CALCULATE RISK SCORES
For EACH AP:
- Get metrics (latency, jitter, usage, clients)
- EXPLAIN: Raw values obtained
- EXPLAIN: How each metric maps to 0-100 score
- EXPLAIN: Risk score calculation step-by-step
- EXPLAIN: Why the final classification was chosen

STEP 3: UPDATE JSON
- Store all scores
- EXPLAIN: What data was saved

STEP 4: PROVIDE SUMMARY
- Total APs processed
- Risk breakdown
- Key insights and reasoning

**BEGIN WITH FULL EXPLANATIONS:**"""

            agent_context = RiskAgentContext(
                session_id=self.session_id,
                user_id=self.user_id,
                network_id=self.network_id,
                calculation_interval=self.calculation_interval
            )
            
            # Explain that we're about to invoke the agent
            if self.explainer:
                self.explainer.explain_decision(
                    decision_point="Invoke LLM agent for risk calculation",
                    chosen_option="Execute full workflow with explanations",
                    alternatives=["Skip calculation", "Partial calculation", "No explanations"],
                    reasoning="Full workflow ensures all APs are processed with complete transparency",
                    supporting_data={
                        "network_id": self.network_id,
                        "prompt_length": len(prompt)
                    }
                )
            
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]},
                context=agent_context,
                config={
                    "recursion_limit": 25,
                }
            )
            
            # Extract response
            messages = result.get("messages", [])
            final_response = ""
            if messages:
                for msg in reversed(messages):
                    if hasattr(msg, 'content') and msg.content:
                        final_response = msg.content
                        break
            
            # Check for hallucinations in the response
            if self.explainer and final_response:
                hallucination_check = self.explainer.check_hallucination(
                    output=final_response,
                    context=f"Network: {self.network_id}, Risk formula with weights {self.weights}",
                    query=prompt
                )
                
                if hallucination_check.is_hallucinated:
                    logger.warning(f"⚠️ HALLUCINATION DETECTED: {hallucination_check.explanation}")
                    logger.warning(f"Unsupported claims: {hallucination_check.unsupported_claims}")
                else:
                    logger.info(f"✅ Output verified as factual (confidence: {hallucination_check.confidence:.2%})")
                
                # Log the LLM response with explanation
                self.explainer.explain_action(
                    action_type="llm_call",
                    input_context=f"Prompt: {prompt[:200]}...",
                    output_result=f"Response: {final_response[:200]}...",
                    reference_context=f"Risk calculation for network {self.network_id}",
                    metadata={
                        "is_hallucinated": hallucination_check.is_hallucinated,
                        "confidence": hallucination_check.confidence,
                        "message_count": len(messages)
                    }
                )
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "response": final_response,
                "hallucination_check": {
                    "is_hallucinated": hallucination_check.is_hallucinated if self.explainer else None,
                    "confidence": hallucination_check.confidence if self.explainer else None,
                    "explanation": hallucination_check.explanation if self.explainer else None
                } if self.explainer else None
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            if self.explainer:
                self.explainer.explain_action(
                    action_type="error",
                    input_context="Risk score calculation",
                    output_result=f"Failed with error: {str(e)}",
                    reference_context="Calculation workflow interrupted"
                )
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    async def continuous_calculation(self):
        """Run continuous risk score calculation with explanations"""
        print(f"🚀 Starting continuous risk calculation with EXPLAINABILITY")
        print(f"   Interval: {self.calculation_interval}s")
        print(f"   Explanations: {'ENABLED ✅' if self.explainer else 'DISABLED'}")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Calculation #{iteration}")
                
                result = await self.calculate_risk_scores()
                
                if result["success"]:
                    print("✅ Complete")
                    if result.get("hallucination_check"):
                        hc = result["hallucination_check"]
                        if hc["is_hallucinated"]:
                            print(f"   ⚠️ Hallucination detected: {hc['explanation']}")
                        else:
                            print(f"   ✅ Output verified (confidence: {hc['confidence']:.2%})")
                else:
                    print(f"❌ Failed: {result.get('error')}")
                
                await asyncio.sleep(self.calculation_interval)
                
        except KeyboardInterrupt:
            print("\n⚠️ Stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def single_calculation(self):
        """Perform a single risk score calculation with explanations"""
        result = await self.calculate_risk_scores()
        
        if result["success"]:
            print("\n" + "="*80)
            print("RISK SCORE CALCULATION COMPLETE")
            print("="*80)
            print(result["response"])
            
            if result.get("hallucination_check"):
                hc = result["hallucination_check"]
                print(f"\n{'='*80}")
                print("HALLUCINATION CHECK")
                print("="*80)
                if hc["is_hallucinated"]:
                    print(f"⚠️ WARNING: Hallucination detected!")
                    print(f"Confidence: {hc['confidence']:.2%}")
                    print(f"Explanation: {hc['explanation']}")
                else:
                    print(f"✅ Output is factual")
                    print(f"Confidence: {hc['confidence']:.2%}")
                print("="*80)
        else:
            print(f"❌ Failed: {result.get('error')}")
        
        return result


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║           RISK SCORE AGENT WITH FULL EXPLAINABILITY                         ║
║                                                                              ║
║  Every action is explained and justified                                    ║
║  Hallucination detection on all outputs                                     ║
║  Decision traces logged to Phoenix dashboard                                ║
║  View explanations at: http://localhost:6006                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse arguments
    mode = "single"
    interval = 10
    enable_phoenix = True
    phoenix_port = 6006
    enable_explainability = True
    
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
        elif args[i] == "--no-phoenix":
            enable_phoenix = False
        elif args[i] == "--phoenix-port":
            if i + 1 < len(args):
                try:
                    phoenix_port = int(args[i+1])
                    i += 1
                except ValueError:
                    pass
        elif args[i] == "--no-explainability":
            enable_explainability = False
        elif args[i] in ["--help", "-h"]:
            print("\nUsage:")
            print("  python risk_score_agent_with_explainability.py")
            print("  python risk_score_agent_with_explainability.py --continuous [sec]")
            print("  python risk_score_agent_with_explainability.py --no-phoenix")
            print("  python risk_score_agent_with_explainability.py --no-explainability")
            print("  python risk_score_agent_with_explainability.py --phoenix-port [port]")
            print("\nFeatures:")
            print("  ✅ Every action is explained with reasoning")
            print("  ✅ Hallucination detection on all LLM outputs")
            print("  ✅ Tool call justifications logged")
            print("  ✅ Metric calculation transparency")
            print("  ✅ Decision traces in Phoenix dashboard")
            print("\nView explanations:")
            print("  Phoenix Dashboard: http://localhost:6006")
            print("  Explanation logs: ./explanations/")
            return
        i += 1
    
    # Initialize Phoenix
    if enable_phoenix:
        print("🔍 Initializing Phoenix observability...")
        phoenix_session = initialize_phoenix(
            project_name="Network Monitoring - Risk Score Agent (Explainable)",
            launch_ui=True,
            ui_port=phoenix_port,
            enable_langchain_instrumentation=True
        )
        if phoenix_session:
            print(f"✅ Phoenix UI: http://localhost:{phoenix_port}")
        else:
            print("⚠️ Phoenix initialization failed")
    
    # Initialize agent with explainability
    print(f"Initializing agent (explainability: {'ON' if enable_explainability else 'OFF'})...")
    agent = ExplainableRiskScoreAgent(
        calculation_interval=interval,
        enable_explainability=enable_explainability,
        phoenix_port=phoenix_port
    )
    
    if not await agent.initialize():
        print("Failed to initialize agent")
        return
    
    print("✅ Agent ready with FULL EXPLAINABILITY")
    
    if enable_explainability:
        print(f"\n{'='*80}")
        print("EXPLAINABILITY ENABLED")
        print(f"{'='*80}")
        print("Every action will be:")
        print("  ✅ Explained with reasoning")
        print("  ✅ Checked for hallucinations")
        print("  ✅ Logged to Phoenix dashboard")
        print("  ✅ Saved to ./explanations/ folder")
        print(f"\nView real-time explanations at: http://localhost:{phoenix_port}")
        print(f"{'='*80}\n")
    
    try:
        if mode == "continuous":
            await agent.continuous_calculation()
        else:
            await agent.single_calculation()
    finally:
        await agent.close()
        print("\n✅ Shutdown complete")
        if enable_phoenix:
            print(f"\n{'='*80}")
            print(f"🔍 Phoenix UI is STILL RUNNING at: http://localhost:{phoenix_port}")
            print(f"   View all explanations and traces in your browser")
            print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
