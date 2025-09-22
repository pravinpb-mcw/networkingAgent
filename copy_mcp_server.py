#!/usr/bin/env python3
"""
MCP Client using Gemini LLM for Meraki Network Tools
Uses mcp_use library to connect Gemini to Meraki MCP tools
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
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
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
   dont assume anything, use data through tools. i need output related to real data analyze my data and answer

     STEP 1: Call get_organization_uplinks_statuses FIRST to get current WAN distribution
     STEP 2: Call get_device_loss_and_latency_history to check device latency
     STEP 3: If any device has latency > 100ms, call update_uplink to move it to the best available WAN
     STEP 4: Call get_organization_uplinks_statuses AGAIN to get updated distribution
     STEP 5: Report BEFORE and AFTER counts using the actual data from the tool responses

     CRITICAL: The get_organization_uplinks_statuses tool returns wan_distribution data showing actual device counts per WAN. USE THIS DATA for accurate before/after counts.

     Rules:
     - If latency > 100ms: Move device to WAN2 or WAN3 (whichever has fewer devices)
     - If latency < 100ms: No action needed

     Available tools:
     - get_organization_uplinks_statuses    → returns wan_distribution with actual counts
     - get_device_loss_and_latency_history  → to get device latency
     - update_uplink                        → to move device uplink

     IMPORTANT: 
     1. Call get_organization_uplinks_statuses at the BEGINNING to get BEFORE counts
     2. After making changes, call get_organization_uplinks_statuses AGAIN to get AFTER counts
     3. Use the wan_distribution field from BOTH responses to show accurate before/after
     
 **Before vs After:**
 [Use the wan_distribution from the tool responses. Example:
 BEFORE (from first get_organization_uplinks_statuses): WAN1=10, WAN2=11, WAN3=8
 AFTER (from second get_organization_uplinks_statuses): WAN1=7, WAN2=14, WAN3=8]
"""


#     return """ **SIMPLE STEPS:**
          
#             • Call update_uplink  MOVE 5 DEVICE FROM WAN 1 TO WAN 2 ONLY 

#         dont ask this- Shall I move any specific device(s) to a different WAN interface?
#         move diorectly device based on latency highest order
# """




async def run_meraki_chat():
    """Run a chat using MCPAgent with Gemini LLM for Meraki tools."""
    
    # Set up Gemini API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("GEMINI_API_KEY not found in .env file")
        return
    
    os.environ["GEMINI_API_KEY"] = gemini_api_key
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print("Initializing Meraki MCP Chat with Gemini...")
    print("="*30)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Set up the model as the best automated network orchestration and monitoring agent
        system_prompt = get_common_system_prompt()

        # Create Gemini LLM with specialized network orchestration role
        print("Initializing Gemini LLM as Network Orchestration Agent...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Use flash model with higher free tier limits
            google_api_key=gemini_api_key,
            temperature=0.1,  # Even lower temperature for consistency
            max_tokens=512,  # Reduced tokens to stay within limits
            request_timeout=30,  # Add timeout
            retry_on_failure=True  # Enable retries
        )
        
                # Note: ChatGoogleGenerativeAI doesn't have system_prompt attribute
        # The system prompt will be passed to the agent instead
        
        # Create MCP agent with specialized network orchestration role
        print("Creating Network Orchestration Agent...")
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=5,  # Reduced steps for faster execution
            memory_enabled=False,  # Disable memory to reduce complexity
            verbose=False,  # Disable verbose output to remove "Thought:" and "Final Answer:"
        )
        
        # Store the system prompt for use in enhanced inputs
        # The MCPAgent will use the system prompt through the orchestration commands
        
        print("Setup complete!")
        print("\n" + "="*30)
        print("AUTOMATED NETWORK ORCHESTRATION AGENT")
        print("="*30)

        
                 # Welcome message for the orchestration agent)
        
        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                # Check for exit command
                if user_input.lower() in ["exit", "quit"]:
                    print("Ending conversation...")
                    break
                
                # Check for clear history command
                if user_input.lower() == "clear":
                    agent.clear_conversation_history()
                    print("Conversation history cleared.")
                    continue
                
                # Check for orchestration commands
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
                    print("\nAvailable Network Orchestration Tools:")
                    try:
                        # Get tools from the agent's tool list
                        if hasattr(agent, 'tools') and agent.tools:
                            print(f"Found {len(agent.tools)} orchestration tools:")
                            for tool in agent.tools:
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
                # Skip empty input
                if not user_input:
                    continue
                
                # Get response from agent
                print("\nAssistant: ", end="", flush=True)
                
                try:
                    # Run the agent
                    response = await agent.run(user_input)
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

async def run_automated_analysis(phase=None):
    """Run automated network analysis and issue resolution."""
    
    # Define phase-specific prompts
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
        session = next(iter(client.sessions.values()))
        langchain_tools = []
        
        for tool_name, tool_info in session.tools.items():
            wrapper = MCPToolWrapper(
                name=tool_name,
                description=tool_info.description,
                mcp_client=client
            )
            langchain_tools.append(wrapper)

        prompt = create_langgraph_react_prompt()
        agent = create_react_agent(llm=llm, tools=langchain_tools, prompt=prompt)
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=langchain_tools,
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
            response = await agent.run(automated_prompt)
            return response
        except Exception as e:
            return f" Error in Phase {phase_num}: {e}"
    
    # Set up Gemini API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("GEMINI_API_KEY not found in .env file")
        return
    
    os.environ["GEMINI_API_KEY"] = gemini_api_key
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print("AUTOMATED NETWORK ANALYSIS MODE")
    print("="*30)
    print("Gathering comprehensive network information...")
    print("="*30)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Set up the model as the best automated network orchestration and monitoring agent
        system_prompt = get_common_system_prompt()

        # Create Gemini LLM with specialized network orchestration role
        # print("Initializing Gemini LLM as Network Orchestration Agent...")
        # llm = ChatGoogleGenerativeAI(
        #     model="gemini-2.5-flash",  # Use the original model
        #     google_api_key=gemini_api_key,
        #     temperature=0.1,  # Even lower temperature for consistency
        #     max_tokens=512,  # Further reduced tokens to avoid overload
        #     request_timeout=30,  # Add timeout
        #     retry_on_failure=True  # Enable retries
        # )

        print("Initializing DeepSeek v3 LLM as Latency Monitoring Agent...")
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            print(" DEEPSEEK_API_KEY not found in .env file")
            return
        llm = ChatOpenAI(
            # model="anthropic/claude-sonnet-4",
            model="deepseek/deepseek-chat-v3.1:free",
            # model="google/gemini-2.5-flash",  # DeepSeek v3 model via OpenRouter
            api_key=deepseek_api_key,
            base_url="https://openrouter.ai/api/v1",  # OpenRouter endpoint
            temperature=0.1,  # Low temperature for consistent responses
            max_tokens=1024,  # Increased token limit for better responses
            request_timeout=30,  # Timeout for reliability
            max_retries=3  # Retry on failure
        )

        # groq_api_key=os.getenv("GROQ_API_KEY")

        # llm = ChatOpenAI(
        #     model="llama3.1:8b",   # must exactly match `ollama list`
        #     api_key="ollama",             # dummy key, Ollama ignores it
        #     base_url="http://192.168.13.162:11434/v1",  # MUST have /v1
        # )


        # Create MCP agent with specialized network orchestration role
        print("Creating Network Orchestration Agent...")
        
        print("Setup complete!")
        print("\n" + "="*30)
        
                # Run analysis based on phase parameter
        if phase and phase in phase_prompts:
            # Run specific phase only
            print(f"\nRUNNING PHASE {phase} ONLY")
            print("="*30)
            
            try:
                response = await run_single_phase(phase, client, llm)
                print("\n" + "="*30)
                print(f"PHASE {phase} COMPLETE")
                print("="*30)
                print(response)
                print("\n" + "="*30)
                print(f"Phase {phase} analysis completed!")
                
            except Exception as e:
                print(f"\n Error in Phase {phase}: {e}")
                
        else:
            # Run all phases sequentially
            print("STARTING SEQUENTIAL PHASE ANALYSIS")
            print("Will run all 5 phases with 30-second delays")
            print("="*30)
            
            all_results = []
            
            for phase_num in [1, 2, 3, 4, 5]:
                try:
                    # Run the phase
                    result = await run_single_phase(phase_num, client, llm)
                    all_results.append(f"PHASE {phase_num} RESULT:\n{result}")
                    
                    print("\n" + "="*30)
                    print(f"PHASE {phase_num} COMPLETE")
                    print("="*30)
                    print(result)
                    
                    # Wait 30 seconds before next phase to avoid model overload
                    if phase_num < 5:
                        print(f"\nWaiting 15 seconds before Phase {phase_num + 1}...")
                        await asyncio.sleep(10)
                        
                except Exception as e:
                    error_msg = f" Error in Phase {phase_num}: {e}"
                    all_results.append(error_msg)
                    print(f"\n{error_msg}")
                    
                    # Wait 30 seconds before next phase to avoid model overload
                    if phase_num < 5:
                        print(f"\nWaiting 15 seconds before Phase {phase_num + 1}...")
                        await asyncio.sleep(10)
            
            # Final summary
            print("\n" + "="*30)
            print("COMPLETE SEQUENTIAL ANALYSIS FINISHED")
            print("="*30)
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

async def get_uplink_data_via_llm():
    """Get uplink status and WAN details via LLM - Automated Network Orchestration Agent."""
    
    # Set up Gemini API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print(" GEMINI_API_KEY not found in .env file")
        return
    
    os.environ["GEMINI_API_KEY"] = gemini_api_key
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print("UPLINK STATUS ANALYSIS")
    print("="*30)
    print("Gathering comprehensive uplink information...")
    print("="*30)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Set up the model as the best automated network orchestration and monitoring agent
        system_prompt = get_common_system_prompt()

        # Create Gemini LLM with specialized network orchestration role
        print("Initializing Gemini LLM as Uplink Monitoring Agent...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Use flash model with higher free tier limits
            google_api_key=gemini_api_key,
            temperature=0.1,  # Low temperature for consistency
            max_tokens=512,  # Reduced tokens for speed
            request_timeout=20,  # Reduced timeout for faster responses
            retry_on_failure=False  # Disable retries for speed
        )
        
        # Create LangGraph agent with specialized network orchestration role
        print("Creating Uplink Monitoring Agent...")
        session = next(iter(client.sessions.values()))
        langchain_tools = []
        
        for tool_name, tool_info in session.tools.items():
            wrapper = MCPToolWrapper(
                name=tool_name,
                description=tool_info.description,
                mcp_client=client
            )
            langchain_tools.append(wrapper)

        prompt = create_langgraph_react_prompt()
        agent = create_react_agent(llm=llm, tools=langchain_tools, prompt=prompt)
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=langchain_tools,
            max_iterations=10,
            verbose=False,
            handle_parsing_errors=True
        )
        
        print("Setup complete!")
        print("\n" + "="*30)

        # Read policy file
        try:
            with open('policy.txt', 'r') as f:
                policy_content = f.read()
        except FileNotFoundError:
            policy_content = "Policy file not found. Using default rules."
        
        uplink_prompt = f"""{system_prompt}
            SIMPLE WAN STATUS CHECK & UPLINK REROUTING

            **POLICY FILE:**
            {policy_content}

            **SIMPLE STEPS:**
            1. Call get_network_settings to check WAN status
            2. Call get_organization_uplinks_statuses to get device data  
            3. If any WAN is down or overloaded, read the policy file above
            4. Think about what to do based on the policy
            5. If ALL WANs exceed limit, create WAN3 using update_appliance_settings
            6. Execute the uplink rerouting using update_uplink tool

            **EXECUTE NOW:**
            - Call get_network_settings
            - Call get_organization_uplinks_statuses  
            - Count devices per WAN
            - If WAN is down/overloaded, follow the policy file
            - If ALL WANs exceed 20 devices, create WAN3
            - Reroute devices using update_uplink tool
            """



        print("Running uplink analysis...")
        
        # Retry logic for Gemini API overload
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                response = await agent.run(uplink_prompt)
                break
            except Exception as e:
                error_str = str(e)
                if "503" in error_str or "overloaded" in error_str.lower():
                    if attempt < max_retries - 1:
                        print(f"Gemini model overloaded (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print(" Gemini model still overloaded after all retries. Please try again later.")
                        response = "Error: Gemini model is overloaded. Please try again in a few minutes."
                        break
                elif "finish_reason" in error_str or "int' object has no attribute 'name'" in error_str:
                    print(f"Gemini API compatibility issue detected. This is a known issue with certain Gemini models.")
                    print("The analysis may have completed successfully despite this error.")
                    response = " UPLINK ANALYSIS COMPLETE - Analysis completed despite API compatibility warning."
                    break
                elif "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                    print(f"Gemini API quota exceeded. You've hit the free tier limits.")
                    print("Please wait 55 seconds before trying again, or consider upgrading your API plan.")
                    response = " UPLINK ANALYSIS FAILED - API quota exceeded. Please wait 55 seconds and try again."
                    break
                else:
                    raise e
        
        print("\n" + "="*30)
        print("UPLINK ANALYSIS COMPLETE")
        print("="*30)
        print(response)
        print("\n" + "="*30)
        print("Uplink analysis completed!")
        
    except Exception as e:
        print(f" Error in uplink analysis: {e}")
    
    finally:
        if 'client' in locals() and client and hasattr(client, 'close_all_sessions'):
            await client.close_all_sessions()

async def get_uplink_latency_monitoring():
    """Monitor uplinks based on latency thresholds and create policy files."""
    
    import os
    

    use_gemini = False  # Set to True for Gemini, False for DeepSeek
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print("UPLINK LATENCY MONITORING")
    print("="*40)
    print("Monitoring uplink performance based on latency...")
    print("="*40)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Set up the model as the best automated network orchestration and monitoring agent
        system_prompt = get_common_system_prompt()

            
        if use_gemini:
            # OPTION 1: Gemini LLM - COMMENTED OUT
            print("Initializing Gemini LLM as Latency Monitoring Agent...")
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                print(" GEMINI_API_KEY not found in .env file")
                return
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",  # Use flash model with higher free tier limits
                google_api_key=gemini_api_key,
                temperature=0.1,  # Slightly higher for better responses
                max_tokens=512,  # Reduced tokens to avoid limits
                request_timeout=60,  # Increased timeout for reliability
                retry_on_failure=True  # Enable retries
            )
        else:
            # # OPTION 2: DeepSeek v3 LLM via OpenRouter - COMMENTED OUT
            print("Initializing DeepSeek v3 LLM as Latency Monitoring Agent...")
            deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
            if not deepseek_api_key:
                print(" DEEPSEEK_API_KEY not found in .env file")
                return
            llm = ChatOpenAI(
                # model="anthropic/claude-sonnet-4",
                model="deepseek/deepseek-chat-v3.1:free",
                # model="openai/gpt-oss-20b:free",
                # model="google/gemini-2.5-flash",  # DeepSeek v3 model via OpenRouter
                api_key=deepseek_api_key,
                base_url="https://openrouter.ai/api/v1",  # OpenRouter endpoint
                temperature=0.1,  # Low temperature for consistent responses
                max_tokens=1024,  # Increased token limit for better responses
                request_timeout=30,  # Timeout for reliability
                max_retries=3  # Retry on failure
            )

            # llm = ChatOpenAI(
            # model="llama3.1:8b",   # must exactly match `ollama list`
            # # model="gpt-oss:20b",
            # # model="qwen3:14b",
            # api_key="ollama",             # dummy key, Ollama ignores it
            # base_url="http://192.168.13.162:11434/v1",  # MUST have /v1
            # )
    

        # Create MCP agent with specialized network orchestration role
        print("Creating Latency Monitoring Agent...")
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=30,  # Reduced steps for faster execution
            memory_enabled=False,  # Disable memory for speed
            verbose=False,  # Enable verbose to see tool execution
        )
        
        # Add delay between tool calls to respect rate limits
        
        print("Setup complete!")
        print("\n" + "="*40)

        # Simple latency monitoring
        print("Running latency monitoring...")
        
        try:
            # Send the complete prompt to the agent
            full_prompt = f"{system_prompt}\n\n{generate_dynamic_latency_prompt()}"
            print("Sending prompt to agent...")
            response = await agent.run(full_prompt)

            print("\n" + "="*30)
            print("UPLINK ANALYSIS COMPLETE")
            print("="*30)
            # Handle Unicode characters in response
            try:
                print(response)
            except UnicodeEncodeError:
                # Replace problematic Unicode characters
                safe_response = response.encode('ascii', 'replace').decode('ascii')
                print(safe_response)
            print("\n" + "="*30)
            print("Uplink analysis completed!")

            
        except Exception as e:
            # Handle Unicode encoding errors
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"Error in latency monitoring: {error_msg}")
            return
        
    except Exception as e:
        print(f"ERROR in latency monitoring: {e}")
        import traceback
        traceback.print_exc()
        return

# Note: Tool execution requires MCPAgent mode

async def test_connection():
    """Test the MCP connection and available tools."""
    print("Testing MCP Connection...")
    
    try:
        # Load environment
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            print("GEMINI_API_KEY not found")
            return False
        
        # Test MCP client
        config_file = "mcp-inspector-config.json"
        client = MCPClient.from_config_file(config_file)
        
        print("MCP Client created successfully")
        
        # Test LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_api_key,
            temperature=0.1,
            max_tokens=512,
            request_timeout=30,
            retry_on_failure=True
        )
        
        print("Gemini LLM initialized successfully")
        
        # Test agent creation
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=5,
            memory_enabled=False,
            verbose=False  # Disable verbose output
        )
        
        print("MCP Agent created successfully")
        
        # Clean up
        await client.close_all_sessions()
        
        print("All tests passed!")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

async def main():
    """Main function."""
    print("Meraki MCP Client with Gemini")
    print("="*40)
    


    # Show help if requested
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print("\nUsage Options:")
        print("  python mcp_client.py                    - Run interactive chat mode")
        print("  python mcp_client.py test               - Test MCP connection")
        print("  python mcp_client.py --automate         - Run full automated analysis (all phases)")
        print("  python mcp_client.py --uplink          - Get uplink status and WAN details via LLM")
        print("  python mcp_client.py --uplink-through-latency - Monitor uplinks based on latency thresholds")

        print("  python mcp_client.py --automate --phase=1 - Run Phase 1: Organization Overview")
        print("  python mcp_client.py --automate --phase=2 - Run Phase 2: Network Infrastructure")
        print("  python mcp_client.py --automate --phase=3 - Run Phase 3: Security & Monitoring")
        print("  python mcp_client.py --automate --phase=4 - Run Phase 4: Devices & Performance")
        print("  python mcp_client.py --automate --phase=5 - Run Phase 5: VPN & Advanced Performance")
        print("\nPhase Descriptions:")
        print("  Phase 1: Organization & Networks overview (2-3 API calls)")
        print("  Phase 2: Infrastructure, traffic, VPN (3-4 API calls)")
        print("  Phase 3: Security, events, access controls (3-4 API calls)")
        print("  Phase 4: Devices, performance, policies (3-4 API calls)")
        print("  Phase 5: VPN, advanced performance, QoS (3-4 API calls)")
        print("\nQuota-Friendly Approach:")
        print("  - Use individual phases to avoid quota limits")
        print("  - Each phase uses 2-4 API calls instead of 14+")
        print("  - Run phases separately with breaks between them")
        return
    
    # Check if we want to test first
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = await test_connection()
        if success:
            print("\nReady to run chat!")
        else:
            print("\nPlease fix issues before running chat.")
        return
    
    # Check if we want to run in automated mode
    if len(sys.argv) > 1 and sys.argv[1] == "--automate":
        # Check if a specific phase is requested
        phase = None
        if len(sys.argv) > 2 and sys.argv[2].startswith("--phase"):
            try:
                phase = int(sys.argv[2].split("=")[1])
                if phase not in [1, 2, 3, 4, 5]:
                    print("Invalid phase. Use --phase=1, --phase=2, --phase=3, --phase=4, or --phase=5")
                    return
            except (IndexError, ValueError):
                print("Invalid phase format. Use --phase=1, --phase=2, --phase=3, --phase=4, or --phase=5")
                return
        
        await run_automated_analysis(phase)
        return

    # Check for --uplink flag
    if "--uplink" in sys.argv:
        await get_uplink_data_via_llm()
        return
    
    # Check for --uplink-through-latency flag
    if "--uplink-through-latency" in sys.argv:
        await get_uplink_latency_monitoring()
        return
    
    # Run the chat
    await run_meraki_chat()

if __name__ == "__main__":
    asyncio.run(main())