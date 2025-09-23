#!/usr/bin/env python3
"""
MCP Client using Multiple LLMs (Gemini, DeepSeek, Anthropic) for Meraki Network Tools
Uses mcp_use library to connect LLMs to Meraki MCP tools
"""
import json
import re
import sys
import os
from typing import Optional
import asyncio
import logging
import os
import sys
import time
# LangChain/LangGraph imports for the new agent system
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

# Add Anthropic support
try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Anthropic not available. Install with: pip install langchain-anthropic")

# LangChain imports - using the same approach as MCPAgent
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# MCP imports - keep MCPClient, but use proper adapter instead of MCPAgent
from mcp_use import MCPClient
from mcp_use.adapters.langchain_adapter import LangChainAdapter

import sys
import os


# Configure basic logging with Unicode error handling
class UnicodeSafeFormatter(logging.Formatter):
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Replace Unicode characters with ASCII equivalents
            safe_msg = str(record.getMessage()).encode('ascii', 'replace').decode('ascii')
            record.msg = safe_msg
            return super().format(record)

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Apply Unicode-safe formatter to all handlers
for handler in logging.root.handlers:
    handler.setFormatter(UnicodeSafeFormatter())

# Disable verbose MCP logging
logging.getLogger("mcp_use").setLevel(logging.ERROR)
logging.getLogger("mcp_use.agent").setLevel(logging.ERROR)
logging.getLogger("mcp_use.client").setLevel(logging.ERROR)

# Set environment variable to disable telemetry
os.environ["MCP_USE_ANONYMIZED_TELEMETRY"] = "false"

# Set up logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def convert_mcp_tools_to_langchain(client):
    """
    Convert MCP tools to LangChain tools using the proper MCP adapter.
    This uses the same approach as MCPAgent but returns tools for LangGraph.
    
    Args:
        client: MCPClient instance with active sessions
        
    Returns:
        list: LangChain-compatible tools for use with LangGraph
    """
    # Create the LangChain adapter (same as MCPAgent uses)
    adapter = LangChainAdapter()
    
    try:
        # Use the same method MCPAgent uses to convert tools
        tools = await adapter.create_tools(client)
        print(f"SUCCESS: Converted {len(tools)} MCP tools to LangChain format using official adapter")
        return tools
    except Exception as e:
        print(f"ERROR: Failed to convert MCP tools: {e}")
        return []


def get_common_system_prompt():
    """Get the common system prompt used across all MCP client functions."""
    return """You are a NETWORK ORCHESTRATION AGENT.

        You are an expert network orchestration agent with 10 years of experience. You must use available tools to collect real data and make actual changes when required.

        CRITICAL: You MUST use the available tools to collect real-time data and execute changes (for example: get_device_loss_and_latency_history, get_organization_uplinks_statuses, update_appliance_settings, update_uplink). Do not simulate data.

        OUTPUT FORMAT REQUIREMENTS — USE THIS EXACT FORMAT FOR ALL RESPONSES:
        **Analysis:**
        [Concise analysis of the network data: what was checked, metrics observed, issues identified, and impact.]

        **Decision:**
        [Clear statement of what you will do or 'No issues detected'. If actions are taken, list them.]

        **Reasoning:**
        [Brief reasoning explaining why this decision was made and the expected impact.]

        RULES:
        - Do NOT output the phrase "NO CHANGES NEEDED."
        - If no problems are detected, respond with exactly: "No issues detected" and do nothing.
        - NEVER make suggestions or recommendations — only fix actual problems.
        - Keep responses concise and focused on analysis, decisions, and reasoning.
        - Always include timestamps for the data used and for any actions taken.

        DECISION-MAKING FRAMEWORK:
        - ANALYZE: Collect and examine relevant network metrics and state.
        - EVALUATE: Determine whether there are real, actionable problems.
        - DECIDE: Only make changes if problems exist.
        - EXECUTE: If changes are needed, call the appropriate tools immediately (e.g., use update_uplink for device moves). Include the specific tool actions performed in the Decision section.
        - REPORT: Document what was checked, what was changed, and why.

        OPERATIONAL REQUIREMENT:
        - You MUST execute actual tool calls for any device movement (e.g., call update_uplink when moving a device). Do not only analyze.

        MONITORING CAPABILITIES (for context):
        - Latency, loss, jitter, throughput monitoring
        - Traffic and bandwidth utilization analysis
        - Security event detection and device identification
        - Client behavior and usage patterns
        - Network health assessment and predictive indicators

        END OF PROMPT"""

def generate_dynamic_latency_prompt():
    return """NETWORK LATENCY FIX TASK:
            Do not assume. Always use real tool responses.

            Steps:
            1. Call get_organization_uplinks_statuses FIRST → capture BEFORE wan_distribution
            2. Call get_device_loss_and_latency_history → capture device latency & trends

            Rules:
            - If single device >100ms → move it to other WANs availabel  (whichever has fewer devices connected )
            - If multiple devices >100ms → sort by latency (highest first), move each to WAN with lowest latency (tie → fewer devices)
            - If one WAN > 50% devices and has many >100ms → move high-latency devices to other WANs until balanced
            - If ALL WANs >100ms → create new WAN (wan), move worst-affected devices (>110ms)
            - If PRIORITY devices (VoIP/video) >80ms → move them first to lowest-latency WAN
            - If latency trend rising fast → reroute proactively before threshold breach
            - If WAN down (0 devices) → move its devices to healthy WANs immediately
            - If latency <100ms and stable → no action

            3. After updates, call get_organization_uplinks_statuses AGAIN → capture AFTER wan_distribution
            4. Report BEFORE vs AFTER counts using actual wan_distribution values only
            'SHOW THEW MWOVED DEVICES AND TELL WHY THE DECISON IS MADED 

            """

def create_llm_instance(provider="gemini", temperature=0.1, max_tokens=512):
    """Create an LLM instance based on the provider."""
    
    if provider == "gemini":
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            print("GEMINI_API_KEY not found in .env file")
            return None
        
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=30,
            retry_on_failure=True
        )
    
    elif provider == "deepseek":
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            print("DEEPSEEK_API_KEY not found in .env file")
            return None
        
        return ChatOpenAI(
            model="deepseek/deepseek-chat-v3.1:free",
            api_key=deepseek_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=30,
            max_retries=3
        )
    
    elif provider == "anthropic":
        if not ANTHROPIC_AVAILABLE:
            print("Anthropic not available. Install with: pip install langchain-anthropic")
            return None
            
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            print("ANTHROPIC_API_KEY not found in .env file")
            return None
        
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",  # Latest Claude model
            anthropic_api_key=anthropic_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30,
            max_retries=3
        )
    
    elif provider == "glm":
        if not ANTHROPIC_AVAILABLE:
            print("GLM requires Anthropic client. Install with: pip install langchain-anthropic")
            return None
            
        # GLM through z.ai using Anthropic-compatible API
        glm_api_key = os.getenv("ANTHROPIC_API_KEY", "44910560602c44a0abb2607d908e7798.sSjyekht0ZkjJWwz")
        glm_base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
        
        if not glm_api_key or glm_api_key == "YOUR_ZAI_API_KEY":
            print("ANTHROPIC_API_KEY not found for GLM model")
            return None
        
        return ChatAnthropic(
            model="glm-4.5",  # GLM model
            anthropic_api_key=glm_api_key,
            base_url=glm_base_url,  # z.ai endpoint
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30,
            max_retries=3
        )
    
    elif provider == "openrouter-gemini":
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            print("DEEPSEEK_API_KEY not found in .env file")
            return None
        
        return ChatOpenAI(
            model="google/gemini-2.5-flash",
            api_key=deepseek_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=30,
            max_retries=3
        )
    
    else:
        print(f"Unknown provider: {provider}")
        return None

async def run_meraki_chat(llm_provider="gemini"):
    """Run a chat using LangGraph create_react_agent with specified LLM for Meraki tools."""
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print(f"Initializing Meraki MCP Chat with {llm_provider.upper()}...")
    print("="*30)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Set up the model as the best automated network orchestration and monitoring agent
        system_prompt = get_common_system_prompt()

        # Create LLM with specialized network orchestration role
        print(f"Initializing {llm_provider.upper()} LLM as Network Orchestration Agent...")
        llm = create_llm_instance(llm_provider, temperature=0.1, max_tokens=512)
        if not llm:
            return
        
        # LANGGRAPH CONVERSION: Replace MCPAgent with create_react_agent
        print("Creating Network Orchestration Agent (LangGraph)...")
        
        # Step 1: Convert MCP tools to LangChain tools using proper adapter
        tools = await convert_mcp_tools_to_langchain(client)
        if not tools:
            print("ERROR: No tools available - cannot create agent")
            return
        
        # Step 2: Create tool-calling agent (same approach as MCPAgent)
        # This uses the exact same method as MCPAgent internally
        system_prompt = get_common_system_prompt()
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_tool_calling_agent(
            llm=llm,  # Selected LLM
            tools=tools,  # Converted MCP tools
            prompt=prompt  # Same prompt structure as MCPAgent
        )
        
        # Step 3: Wrap in AgentExecutor for execution control
        # This replaces the old MCPAgent execution model
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            max_iterations=5,  # Equivalent to old max_steps
            verbose=False,  # Same as before
            handle_parsing_errors=True,  # Better error handling than MCPAgent
            return_intermediate_steps=False  # Clean output
        )
        
        # LangGraph agent is now ready with converted MCP tools
        # System prompt is embedded in the agent via state_modifier
        
        print("Setup complete!")
        print("\n" + "="*30)
        print(f"AUTOMATED NETWORK ORCHESTRATION AGENT ({llm_provider.upper()})")
        print("="*30)

        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = input(f"\nYou [{llm_provider}]: ").strip()
                
                # Check for exit command
                if user_input.lower() in ["exit", "quit"]:
                    print("Ending conversation...")
                    break
                
                # Check for provider switch
                if user_input.lower().startswith("/switch"):
                    parts = user_input.split()
                    if len(parts) > 1 and parts[1] in ["gemini", "deepseek", "anthropic", "glm", "openrouter-gemini"]:
                        new_provider = parts[1]
                        print(f"Switching to {new_provider}...")
                        await client.close_all_sessions()
                        await run_meraki_chat(new_provider)
                        return
                    else:
                        print("Usage: /switch [gemini|deepseek|anthropic|glm|openrouter-gemini]")
                        continue
                
                # Check for clear history command
                if user_input.lower() == "clear":
                    print("Conversation history cleared.")
                    continue
                
                # Check for orchestration commands (preserve all existing commands)
                if user_input.lower() == "monitor":
                    print("\nStarting comprehensive network monitoring and AUTOMATIC FIXING...")
                    enhanced_input = f"""{system_prompt}

                     COMPREHENSIVE NETWORK MONITORING TASK - CHECK ALL ENDPOINTS:
                     
                     REQUIRED TOOLS TO USE:
                     - Get all available tools and use them systematically
                     - Check all connected devices, traffic patterns, performance metrics, security events, and network health
                     - For each issue identified, IMMEDIATELY use the appropriate tools to fix the problems automatically
                     - DO NOT ask for permission - just execute fixes immediately
                     - Report what was fixed and the results
                     - BE EFFICIENT and complete the task in minimal steps
                     
                     CRITICAL: Fix ALL detected problems - do not stop until every issue is addressed!
                     
                     CRITICAL: Use ACTUAL FIXING TOOLS:
                     - For performance/VPN issues: use update_network_settings
                     - For connectivity issues: use create_network_appliance_settings  
                     - For unauthorized devices: use update_network_access_control_lists
                     - For security issues: use update_organization_login_security
                     
                     DO NOT just add monitoring - ACTUALLY FIX the problems!
                     
                     IMPORTANT: EMPTY RESPONSES ARE VALID - If a tool returns empty data, report as "no data found" not "tool failed". Empty responses indicate healthy networks with no issues to report."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "analyze":
                    print("\nPerforming AI-powered network analysis and AUTOMATIC FIXING...")
                    enhanced_input = f"""{get_common_system_prompt()}

                     TASK: Conduct AI-powered analysis of the network. Get all available tools and use them systematically to evaluate performance metrics, security posture, traffic patterns, and identify optimization opportunities. For each issue found, IMMEDIATELY use the appropriate tools to fix the problems automatically. DO NOT ask for permission - just execute fixes immediately. Report what was fixed and the results.
                     
                     CRITICAL: Fix ALL detected problems - do not stop until every issue is addressed!
                     
                     CRITICAL: Use ACTUAL FIXING TOOLS:
                     - For performance/VPN issues: use update_network_settings
                     - For connectivity issues: use create_network_appliance_settings  
                     - For unauthorized devices: use update_network_access_control_lists
                     - For security issues: use update_organization_login_security
                     
                     DO NOT just add monitoring - ACTUALLY FIX the problems!
                     
                     IMPORTANT: EMPTY RESPONSES ARE VALID - If a tool returns empty data, report as "no data found" not "tool failed". Empty responses indicate healthy networks with no issues to report."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "optimize":
                    print("\n Getting automated optimization and EXECUTING fixes...")
                    enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Analyze the current network state and provide automated optimization recommendations. Focus on performance improvements, bandwidth optimization, security enhancements, and policy refinements. For each optimization opportunity, IMMEDIATELY use the appropriate tools to implement the improvements automatically. DO NOT ask for permission - just execute optimizations immediately. Report what was optimized and the results."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "security":
                    print("\n Reviewing and ENHANCING security posture automatically...")
                    enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Perform a comprehensive security analysis of the network. Check for security vulnerabilities, unauthorized devices, suspicious activities, and security policy effectiveness. For each security issue identified, IMMEDIATELY use the appropriate tools to fix the problems automatically. DO NOT ask for permission - just execute security improvements immediately. Report what security measures were implemented and the results."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "performance":
                    print("\nAnalyzing and IMPROVING network performance automatically...")
                    enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Analyze network performance metrics including latency, packet loss, jitter, bandwidth utilization, and throughput. Identify performance bottlenecks and IMMEDIATELY use the appropriate tools to fix performance issues automatically. DO NOT ask for permission - just execute performance improvements immediately. Report what performance optimizations were applied and the results."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "automate":
                    print("\nGetting automation suggestions and EXECUTING fixes...")
                    enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Identify current network issues and provide specific automation suggestions. For each issue found, IMMEDIATELY use the appropriate tools to resolve problems, optimize performance, and improve network management efficiency automatically. DO NOT ask for permission - just execute automation actions immediately. Report what was automated and the results."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "fix":
                     print("\nAutomatically fixing identified issues...")
                     enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Identify all current network issues and IMMEDIATELY use the available tools to fix them automatically. DO NOT ask for permission - just execute fixes immediately. Resolve problems, optimize performance, and improve security automatically. Report what was fixed and the results of each fix."""
                     user_input = enhanced_input
                
                elif user_input.lower() == "tools":
                    print(f"\nAvailable Network Orchestration Tools ({llm_provider.upper()}):")
                    try:
                        print("/switch [provider] - Switch LLM provider")
                        print("Available providers: gemini, deepseek, anthropic, glm, openrouter-gemini")
                        print()
                        # Get tools from the agent's tool list
                        if tools:
                            print(f"Found {len(tools)} orchestration tools:")
                            for tool in tools:
                                print(f"- {tool.name}: {tool.description}")
                        # Fallback to client sessions
                        elif client and client.sessions:
                            print(f"Found {len(client.sessions)} sessions:")
                            for session_name, session in client.sessions.items():
                                print(f"  Session: {session_name}")
                                if hasattr(session, 'tools') and session.tools:
                                    print(f"    Found {len(session.tools)} tools:")
                                    for tool in session.tools:
                                        print(f"    - {tool.name}: {tool.description}")
                                else:
                                    print(f"    No tools found in session {session_name}")
                    except Exception as e:
                        print(f"Error getting tools: {e}")
                        print("Available tools: get_network_clients, get_network_traffic, get_device_loss_and_latency_history, get_network_vpn_stats, get_network_events")
                        print("Commands: monitor, analyze, optimize, security, performance, automate, fix, tools, clear, exit")
                    continue
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Get response from agent
                print(f"\n{llm_provider.upper()}: ", end="", flush=True)
                
                try:
                    # Run the agent
                    response = await agent_executor.ainvoke({
                        "input": user_input,
                        "chat_history": []
                    })
                    
                    # Handle response format
                    if isinstance(response, dict) and 'output' in response:
                        print(response['output'])
                    else:
                        print(response)
                    
                except Exception as e:
                    print(f"\nError: {e}")
                    print("Try asking about network clients, traffic, performance, VPN stats, or events.")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Ending conversation...")
                break
            except Exception as e:
                print(f"\nUnexpected error: {e}")
    
    except Exception as e:
        print(f"Failed to initialize: {e}")
        print("Make sure your MCP server is running and config file is correct.")
    
    finally:
        # Clean up
        if 'client' in locals() and client and hasattr(client, 'close_all_sessions'):
            print("Cleaning up connections...")
            await client.close_all_sessions()

async def run_automated_analysis(phase=None, llm_provider="anthropic"):
    """Run automated network analysis and issue resolution with specified LLM."""
    
    # Define phase-specific prompts (preserve all existing phases)
    phase_prompts = {
        1: """PHASE 1: ORGANIZATION OVERVIEW
        
        REQUIRED TOOLS:
        - get_organization_networks - List all networks in organization
        
        ANALYSIS TARGETS:
         - Organization structure and network count
         - Network types and configurations
         - Any obvious organizational issues
         
        EXECUTION RULE: FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!""",
        
        2: """PHASE 2: NETWORK INFRASTRUCTURE
        
        REQUIRED TOOLS:
         - get_organization_uplinks_statuses - Check uplink connectivity
         - get_network_settings - Review configuration
         - get_network_traffic - Check bandwidth usage
         - get_network_vpn_stats - Check VPN performance
         - get_device_loss_and_latency_history - Check device performance
         - get_connectivity_monitoring_destinations - Check connectivity monitoring
        - update_network_settings - Fix performance/VPN issues if needed
         - create_network_appliance_settings - Fix connectivity issues
         
        ANALYSIS TARGETS:
         - Uplink connectivity issues
         - Network configuration problems
         - Traffic bottlenecks
         - VPN performance issues
         - Device performance problems (latency, packet loss)
         - Connectivity monitoring failures
         
        EXECUTION RULES:
        - Use ALL tools and fix EVERY problem detected!
        - FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!""",
        
        3: """PHASE 3: SECURITY & MONITORING
        
        REQUIRED TOOLS:
         - get_network_events - Check for security issues
          - get_network_security_intrusion - Check intrusion detection
          - get_network_access_control_lists - Check access controls
         - get_network_clients - Check for unauthorized devices
         - update_network_security_intrusion - Fix intrusion detection
         
        ANALYSIS TARGETS:
         - Security vulnerabilities
         - Unauthorized access attempts
         - Intrusion detection status
         - Access control issues
         - Unauthorized devices connected
         
        EXECUTION RULES:
        - Use ALL tools and fix EVERY problem detected!
        - FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!""",
        
        4: """PHASE 4: DEVICES & PERFORMANCE
        
        REQUIRED TOOLS:
         - get_network_clients - Check connected devices
         - get_device_loss_and_latency_history - Check device performance
         - get_connectivity_monitoring_destinations - Monitor connectivity
         - get_network_group_policies - Review group policies
         - update_network_settings - Fix performance issues
         - update_network_group_policy - Fix policy issues
         - update_connectivity_monitoring_destinations - Fix connectivity issues
         
        ANALYSIS TARGETS:
         - Connected device issues
         - Performance problems (latency, loss)
         - Connectivity monitoring issues
         - Policy configuration problems
         
        EXECUTION RULES:
        - Use ALL tools and fix EVERY problem detected!
        - For performance issues, use update_network_settings to actually fix them!
        - For connectivity issues, use update_connectivity_monitoring_destinations to fix them!
        - FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!""",
         
        5: """PHASE 5: VPN & ADVANCED PERFORMANCE
        
        REQUIRED TOOLS:
         - get_organization_vpn_stats - Check VPN performance metrics
         - get_network_vpn_stats - Check network-specific VPN issues
         - get_device_loss_and_latency_history - Check detailed performance
         - update_network_settings - Fix VPN/performance configuration
         - create_network_appliance_settings - Fix advanced connectivity
         
        ANALYSIS TARGETS:
         - VPN latency issues (high ping times)
         - VPN packet loss problems
         - Tunnel connectivity issues
         - QoS and bandwidth optimization
         - Advanced performance tuning
         
        EXECUTION RULES:
        - Use ALL tools and fix EVERY problem detected!
        - FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!"""
    }
    
    async def run_single_phase(phase_num, client, llm):
        """Run a single phase and return the result."""
        
        # Create agent for this phase with LangGraph
        tools = await convert_mcp_tools_to_langchain(client)
        if not tools:
            return f"ERROR: No tools available for Phase {phase_num}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", get_common_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            max_iterations=75,
            verbose=False,
            handle_parsing_errors=True
        )
        
        # Create phase-specific prompt
        automated_prompt = f"""{get_common_system_prompt()}

        AUTOMATED NETWORK ANALYSIS - PHASE {phase_num}:
        
        {phase_prompts[phase_num]}
        
        EXECUTION RULES:
        
        CRITICAL REQUIREMENTS:
        - FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!
        - When you detect a problem, immediately use fixing tools to resolve it!
        - DO NOT just monitor - ACTUALLY FIX the problems you find!
        - Use update_network_settings, create_network_appliance_settings, and other fixing tools!
        
        PHASE EXECUTION:
          - Use ONLY the tools specified for this phase
          - ANALYZE network data thoroughly before making any decisions
          - ONLY make changes when you identify ACTUAL network problems or issues
          - ALWAYS explain your reasoning for any decisions made
          - Report what was checked, what decisions were made, and the reasoning
          - If you made changes, summarize what was changed
        
        EFFICIENCY RULES:
          - Be concise and efficient - Complete in 3-5 tool calls maximum
          - DO NOT over-analyze - Make quick decisions based on clear data
          - COMPLETE THE PHASE QUICKLY - Do not get stuck in analysis loops
          - STOP after making your decision - Do not continue analyzing
        - Do NOT say "NO CHANGES NEEDED." at any time
        
        DATA HANDLING:
          - ALWAYS use the exact output format specified in the system prompt
          - EMPTY RESPONSES ARE VALID: If a tool returns empty data, report as "no data found" not "tool failed"
          - HANDLE EMPTY DATA: Empty responses mean "no issues detected" not "tool failure"
          - RETRY EMPTY TOOLS: If a tool returns empty data, try it again or use alternative tools
        
        PROBLEM RESOLUTION:
        - COMPREHENSIVE PROBLEM SOLVING: For EVERY problem detected, use appropriate tools to fix it
          - FIX ALL ISSUES: Do not stop until ALL detected problems are addressed with fixes
          - USE ALL AVAILABLE TOOLS: In each phase, use ALL tools that could help identify/fix problems
          - ACTUALLY FIX PROBLEMS: Use configuration tools to fix issues, not just monitoring tools
          - PRIORITIZE FIXES OVER MONITORING: When you detect a problem, fix it first, then add monitoring
        
        TOOL USAGE:
          - USE NETWORK SETTINGS TOOLS: For performance/VPN issues, use update_network_settings
          - USE APPLIANCE SETTINGS: For connectivity issues, use create_network_appliance_settings
        
          START NOW: Execute this phase only."""
        
        try:
            response = await agent_executor.ainvoke({
                "input": automated_prompt,
                "chat_history": []
            })
            
            if isinstance(response, dict) and 'output' in response:
                return response['output']
            return str(response)
        except Exception as e:
            return f"Error in Phase {phase_num}: {e}"
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print(f"AUTOMATED NETWORK ANALYSIS MODE ({llm_provider.upper()})")
    print("="*50)
    print("Gathering comprehensive network information...")
    print("="*50)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Create LLM instance
        print(f"Initializing {llm_provider.upper()} LLM as Network Orchestration Agent...")
        llm = create_llm_instance(llm_provider, temperature=0.1, max_tokens=1024)
        if not llm:
            return

        # Create MCP agent with specialized network orchestration role
        print("Creating Network Orchestration Agent...")
        
        print("Setup complete!")
        print("\n" + "="*50)
        
        # Run analysis based on phase parameter
        if phase and phase in phase_prompts:
            # Run specific phase only
            print(f"\nRUNNING PHASE {phase} ONLY ({llm_provider.upper()})")
            print("="*50)
            
            try:
                response = await run_single_phase(phase, client, llm)
                print("\n" + "="*50)
                print(f"PHASE {phase} COMPLETE")
                print("="*50)
                print(response)
                print("\n" + "="*50)
                print(f"Phase {phase} analysis completed!")
                
            except Exception as e:
                print(f"\nError in Phase {phase}: {e}")
                
        else:
            # Run all phases sequentially
            print(f"STARTING SEQUENTIAL PHASE ANALYSIS ({llm_provider.upper()})")
            print("Will run all 5 phases with 15-second delays")
            print("="*50)
            
            all_results = []
            
            for phase_num in [1, 2, 3, 4, 5]:
                try:
                    # Run the phase
                    result = await run_single_phase(phase_num, client, llm)
                    all_results.append(f"PHASE {phase_num} RESULT:\n{result}")
                    
                    print("\n" + "="*50)
                    print(f"PHASE {phase_num} COMPLETE")
                    print("="*50)
                    print(result)
                    
                    # Wait 15 seconds before next phase to avoid model overload
                    if phase_num < 5:
                        print(f"\nWaiting 15 seconds before Phase {phase_num + 1}...")
                        await asyncio.sleep(15)
                        
                except Exception as e:
                    error_msg = f"Error in Phase {phase_num}: {e}"
                    all_results.append(error_msg)
                    print(f"\n{error_msg}")
                    
                    # Wait 15 seconds before next phase to avoid model overload
                    if phase_num < 5:
                        print(f"\nWaiting 15 seconds before Phase {phase_num + 1}...")
                        await asyncio.sleep(15)
            
            # Final summary
            print("\n" + "="*50)
            print("COMPLETE SEQUENTIAL ANALYSIS FINISHED")
            print("="*50)
            print("All 5 phases have been completed!")
            print("Network analysis and optimization completed.")
        
    except Exception as e:
        print(f"Failed to initialize automated analysis: {e}")
        print("Make sure your MCP server is running and config file is correct.")
    
    finally:
        # Clean up
        if 'client' in locals() and client and hasattr(client, 'close_all_sessions'):
            print("Cleaning up connections...")
            await client.close_all_sessions()

async def get_uplink_latency_monitoring(llm_provider="anthropic"):
    """Monitor uplinks based on latency thresholds with specified LLM."""
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print(f"UPLINK LATENCY MONITORING ({llm_provider.upper()})")
    print("="*60)
    print("Monitoring uplink performance based on latency...")
    print("="*60)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Create LLM instance
        print(f"Initializing {llm_provider.upper()} LLM as Latency Monitoring Agent...")
        llm = create_llm_instance(llm_provider, temperature=0.1, max_tokens=1500)
        if not llm:
            return

        # LANGGRAPH CONVERSION: Replace MCPAgent with create_react_agent
        print("Creating Latency Monitoring Agent (LangGraph)...")
        
        # Step 1: Convert MCP tools to LangChain tools using proper adapter
        tools = await convert_mcp_tools_to_langchain(client)
        if not tools:
            print("ERROR: No tools available - cannot create agent")
            return
        
        # Step 2: Create tool-calling agent
        system_prompt = get_common_system_prompt()
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_tool_calling_agent(
            llm=llm,  # Selected LLM
            tools=tools,  # Converted MCP tools
            prompt=prompt  # Same prompt structure
        )
        
        # Step 3: Wrap in AgentExecutor for execution control
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            max_iterations=30,
            verbose=False,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        print("Setup complete!")
        print("\n" + "="*60)

        # Simple latency monitoring
        print("Running latency monitoring...")
        
        try:
            task_prompt = generate_dynamic_latency_prompt()
            print(f"Sending prompt to LangGraph agent ({llm_provider.upper()})...")
            
            # AgentExecutor execution
            response = await agent_executor.ainvoke({
                "input": task_prompt,
                "chat_history": []
            })

            print("\n" + "="*60)
            print("UPLINK ANALYSIS COMPLETE")
            print("="*60)
            
            # Handle response format
            try:
                if isinstance(response, dict) and 'output' in response:
                    print(response['output'])
                else:
                    print(response)
            except UnicodeEncodeError:
                safe_response = str(response).encode('ascii', 'replace').decode('ascii')
                print(safe_response)
            print("\n" + "="*60)
            print("Uplink analysis completed!")
            
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"Error in latency monitoring: {error_msg}")
            return
        
    except Exception as e:
        print(f"ERROR in latency monitoring: {e}")
        import traceback
        traceback.print_exc()
        return

async def test_connection():
    """Test the MCP connection and available tools."""
    print("Testing MCP Connection...")
    
    try:
        # Load environment
        load_dotenv()
        
        # Test MCP client
        config_file = "mcp-inspector-config.json"
        client = MCPClient.from_config_file(config_file)
        print("MCP Client created successfully")
        
        # Test available LLMs
        providers_tested = []
        
        # Test Gemini
        gemini_llm = create_llm_instance("gemini")
        if gemini_llm:
            providers_tested.append("gemini")
            print("✅ Gemini LLM available")
        else:
            print("❌ Gemini LLM not available")
        
        # Test DeepSeek
        deepseek_llm = create_llm_instance("deepseek")
        if deepseek_llm:
            providers_tested.append("deepseek")
            print("✅ DeepSeek LLM available")
        else:
            print("❌ DeepSeek LLM not available")
        
        # Test Anthropic
        anthropic_llm = create_llm_instance("anthropic")
        if anthropic_llm:
            providers_tested.append("anthropic")
            print("✅ Anthropic LLM available")
        else:
            print("❌ Anthropic LLM not available")
        
        # Test GLM
        glm_llm = create_llm_instance("glm")
        if glm_llm:
            providers_tested.append("glm")
            print("✅ GLM LLM available")
        else:
            print("❌ GLM LLM not available")
        
        if not providers_tested:
            print("❌ No LLMs available - check your API keys")
            return False
        
        # Test agent creation with first available LLM
        test_llm = create_llm_instance(providers_tested[0])
        tools = await convert_mcp_tools_to_langchain(client)
        if tools:
            system_prompt = get_common_system_prompt()
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            agent = create_tool_calling_agent(
                llm=test_llm,
                tools=tools,
                prompt=prompt
            )
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                max_iterations=5,
                verbose=False,
                handle_parsing_errors=True
            )
        
        print(f"✅ MCP Agent created successfully with {providers_tested[0]}")
        print(f"✅ Available providers: {', '.join(providers_tested)}")
        
        # Clean up
        await client.close_all_sessions()
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Main function."""
    print("Enhanced Meraki MCP Client with Multiple LLMs")
    print("="*60)
    
    # Show help if requested
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print("\nUsage Options:")
        print("  python mcp_client_with_anthropic.py                    - Run interactive chat mode (default: gemini)")
        print("  python mcp_client_with_anthropic.py --llm=anthropic    - Run with Anthropic LLM")
        print("  python mcp_client_with_anthropic.py --llm=deepseek     - Run with DeepSeek LLM") 
        print("  python mcp_client_with_anthropic.py --llm=gemini       - Run with Gemini LLM")
        print("  python mcp_client_with_anthropic.py --llm=glm          - Run with GLM-4.5 LLM")
        print("  python mcp_client_with_anthropic.py test               - Test MCP connection")
        print("  python mcp_client_with_anthropic.py --automate --llm=anthropic         - Run full automated analysis with Anthropic")
        print("  python mcp_client_with_anthropic.py --uplink-through-latency --llm=anthropic - Monitor uplinks with Anthropic")
        print("  python mcp_client_with_anthropic.py --automate --phase=1 --llm=anthropic - Run Phase 1 with Anthropic")
        print("  python mcp_client_with_anthropic.py --automate --phase=2 --llm=deepseek  - Run Phase 2 with DeepSeek")
        print("\nAvailable LLM Providers:")
        print("  - anthropic: Claude 3.5 Sonnet (requires ANTHROPIC_API_KEY)")
        print("  - gemini: Gemini 2.5 Flash (requires GEMINI_API_KEY)")
        print("  - deepseek: DeepSeek v3.1 via OpenRouter (requires DEEPSEEK_API_KEY)")
        print("  - glm: GLM-4.5 via z.ai (requires ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL)")
        print("  - openrouter-gemini: Gemini via OpenRouter (requires DEEPSEEK_API_KEY)")
        print("\nEnvironment Variables:")
        print("  ANTHROPIC_API_KEY - For Anthropic Claude models and GLM models")
        print("  ANTHROPIC_BASE_URL - For GLM models (default: https://api.z.ai/api/anthropic)")
        print("  GEMINI_API_KEY - For Google Gemini models")
        print("  DEEPSEEK_API_KEY - For OpenRouter API (DeepSeek & other models)")
        print("\nInteractive Commands (during chat):")
        print("  /switch [provider] - Switch LLM provider")
        print("  monitor - Comprehensive monitoring")
        print("  analyze - AI-powered analysis")
        print("  optimize - Automated optimization")
        print("  security - Security review")
        print("  performance - Performance analysis")
        print("  tools - Show available tools")
        print("  clear - Clear history")
        print("  exit/quit - Exit chat")
        return
    
    # Parse LLM provider
    llm_provider = "gemini"  # Default
    for arg in sys.argv:
        if arg.startswith("--llm="):
            provider = arg.split("=")[1]
            if provider in ["gemini", "deepseek", "anthropic", "glm", "openrouter-gemini"]:
                llm_provider = provider
            else:
                print(f"Unknown LLM provider: {provider}")
                print("Available: gemini, deepseek, anthropic, glm, openrouter-gemini")
                return
    
    # Check if we want to test first
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = await test_connection()
        if success:
            print("\n🚀 Ready to run chat!")
        else:
            print("\n❌ Please fix issues before running chat.")
        return
    
    # Check if we want to run in automated mode
    if len(sys.argv) > 1 and sys.argv[1] == "--automate":
        # Check if a specific phase is requested
        phase = None
        for arg in sys.argv:
            if arg.startswith("--phase="):
                try:
                    phase = int(arg.split("=")[1])
                    if phase not in [1, 2, 3, 4, 5]:
                        print("Invalid phase. Use --phase=1, --phase=2, --phase=3, --phase=4, or --phase=5")
                        return
                except (IndexError, ValueError):
                    print("Invalid phase format. Use --phase=1, --phase=2, --phase=3, --phase=4, or --phase=5")
                    return
        
        await run_automated_analysis(phase, llm_provider)
        return
    
    # Check for --uplink-through-latency flag
    if "--uplink-through-latency" in sys.argv:
        await get_uplink_latency_monitoring(llm_provider)
        return
    
    # Run the chat with specified LLM
    await run_meraki_chat(llm_provider)

if __name__ == "__main__":
    asyncio.run(main())
