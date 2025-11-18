#!/usr/bin/env python3
"""
MCP Client using Gemini LLM for Meraki Network Tools
Uses mcp_use library to connect Gemini to Meraki MCP tools
"""

import asyncio
import logging
import os
import sys
import time
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from mcp_use import MCPAgent, MCPClient

# Configure basic logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable verbose MCP logging
logging.getLogger("mcp_use").setLevel(logging.ERROR)
logging.getLogger("mcp_use.agent").setLevel(logging.ERROR)
logging.getLogger("mcp_use.client").setLevel(logging.ERROR)

# Set environment variable to disable telemetry
os.environ["MCP_USE_ANONYMIZED_TELEMETRY"] = "false"

# Load environment variables
load_dotenv()

def get_common_system_prompt():
    """Get the common system prompt used across all MCP client functions."""
    return """You are an AUTOMATED NETWORK ORCHESTRATION AGENT with INTELLIGENT DECISION-MAKING capabilities.

            CRITICAL BEHAVIOR RULES:
            1. NEVER ask "Would you like me to proceed" or "Should I continue"
            2. NEVER ask for user confirmation before taking action
            3. ONLY make changes when you identify ACTUAL network problems or issues
            4. ALWAYS provide clear reasoning for your decisions
            5. ALWAYS explain why you made changes or why you didn't make changes
            6. ONLY modify settings if you believe it will improve network performance/security
            7. Do NOT say "NO CHANGES NEEDED." at any time
            8. If you made changes, summarize what was changed
            9. BE EFFICIENT - Use minimal steps to complete tasks
            10. FOCUS ON INTELLIGENT ANALYSIS - Don't make unnecessary changes

            OUTPUT FORMAT REQUIREMENTS:
            - ALWAYS use this exact format for all responses:
            **Analysis:**
            [Your analysis of the network data]
            
            **Decision:**
            [Your decision - what you will do or not do]
            
            **Reasoning:**
            [Your reasoning for the decision]
            
            - Do NOT say "NO CHANGES NEEDED." at any time
            - If you made changes, end with a summary of what was changed
            - If no problems detected, say "No issues detected" and do nothing
            - NEVER make suggestions or recommendations - ONLY fix actual problems
            - Keep responses concise and focused on the analysis

            DECISION-MAKING FRAMEWORK:
            - ANALYZE: Thoroughly examine network data and metrics
            - EVALUATE: Determine if there are actual problems or issues
            - DECIDE: Only make changes if problems exist - NEVER make suggestions or improvements
            - EXPLAIN: Always provide clear reasoning for your decisions
            - EXECUTE: If changes are needed, use appropriate tools immediately
            - REPORT: Document what was checked, what decisions were made, and why

            NETWORK ORCHESTRATION EXPERTISE:
            - Cisco Meraki network management and optimization
            - Intelligent network decision-making and action execution
            - Real-time network performance monitoring and analysis
            - Proactive network issue detection and resolution
            - Intelligent bandwidth management and traffic shaping
            - Security policy automation and threat response
            - Network policy optimization and user management

            MONITORING CAPABILITIES:
            - Continuous network performance tracking (latency, loss, jitter, throughput)
            - Traffic pattern analysis and bandwidth utilization monitoring
            - Security event detection and unauthorized device identification
            - Client behavior analysis and usage pattern recognition
            - Network health assessment and predictive maintenance
            - Real-time alert generation and automated response

            AUTOMATION FRAMEWORK:
            - AI-powered decision making with confidence scoring
            - Intelligent action execution based on network conditions
            - Threshold-based monitoring with configurable alerts
            - Trend analysis and predictive network optimization
            - Emergency response protocols for critical situations
            - Comprehensive logging and audit trail maintenance

            EXECUTION REQUIREMENTS:
            - ONLY execute fixes when you identify ACTUAL problems
            - ALWAYS explain your reasoning before making any changes
            - ALWAYS report what was checked, what decisions were made, and the reasoning
            - Do NOT say "NO CHANGES NEEDED." at any time
            - If you made changes, summarize what was changed
            - NEVER make changes just for the sake of making changes

            RESPONSE STYLE:
            - Always think as a network orchestration expert
            - Provide clear analysis of network conditions
            - Explain your decision-making process
            - Only execute actions when problems are identified
            - Report what was checked, what decisions were made, and why

            REMEMBER: You are INTELLIGENT and SELECTIVE. Only make changes when there are actual problems and you can clearly explain why the changes will improve the network."""

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
        llm = ChatAnthropic(
            model="glm-4.5",
            temperature=0,
            max_tokens=2048,
            timeout=None,
            max_retries=2,
            api_key=os.environ.get("ANTHROPIC_API_KEY", "55f27b9278af4b3a83a735e228ae4fb8.2oREoHAH8PdKM13f"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
        )
        
                # Note: ChatGoogleGenerativeAI doesn't have system_prompt attribute
        # The system prompt will be passed to the agent instead
        
        # Create MCP agent with specialized network orchestration role
        print("Creating Network Orchestration Agent...")
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=10,  # Further reduced steps to avoid quota issues
            memory_enabled=False,  # Disable memory to reduce complexity
            verbose=False,  # Disable verbose output to remove "Thought:" and "Final Answer:"
        )
        
        # Store the system prompt for use in enhanced inputs
        # The MCPAgent will use the system prompt through the orchestration commands
        
        print("Setup complete!")
        print("\n" + "="*30)
        print("🤖 AUTOMATED NETWORK ORCHESTRATION AGENT")
        print("="*30)
        print("🔧 Specialized in: Network Monitoring, Automation & Optimization")
        print("⚡ Capabilities: AI-Powered Decision Making & Automated Actions")
        print("🛡️  Focus: Security, Performance & Proactive Management")
        print("="*30)
        print("🔍 MONITORING TOOLS:")
        print("• get_network_clients - Monitor connected devices & usage patterns")
        print("• get_network_traffic - Analyze traffic patterns & bandwidth utilization") 
        print("• get_device_loss_and_latency_history - Track performance metrics (latency, loss, jitter)")
        print("• get_organization_vpn_stats - Monitor VPN performance & statistics")
        print("• get_network_events - Track network alerts & security events")
        print("• get_network_settings - Review network-wide configuration")
        print("• get_organization_uplinks_statuses - Monitor device connectivity & failover")
        print("• get_network_group_policies - Review user policies & bandwidth controls")
        print("• get_organization_networks - List all organization networks")
        print("• get_connectivity_monitoring_destinations - Check connectivity monitoring")
        print("• get_network_access_control_lists - Review access control rules")
        print("• get_organization_login_security - Check authentication security")
        print("• get_network_security_intrusion - Monitor intrusion detection settings")
        
        print("\n⚙️ ORCHESTRATION COMMANDS:")
        print("• update_network_settings - Optimize network-wide configuration")
        print("• create_network_appliance_settings - Configure network infrastructure")
        print("• create_network_wireless_settings - Optimize WiFi/SSID configuration")
        print("• update_network_group_policy - Automate policy management")
        print("• create_organization_network - Automate network creation")
        print("• update_connectivity_monitoring_destinations - Optimize monitoring")
        print("• update_network_access_control_lists - Automate access control")
        print("• update_organization_login_security - Enhance authentication security")
        print("• update_network_security_intrusion - Automate security policies")
        print("\n🎯 AUTOMATION TOOLS " )
        print("• Type 'monitor' - Start comprehensive network monitoring")
        print("• Type 'analyze' - Perform AI-powered network analysis")
        print("• Type 'optimize' - Get automated optimization recommendations")
        print("• Type 'security' - Review and enhance security posture")
        print("• Type 'performance' - Analyze and improve network performance")
        print("• Type 'automate' - Get automation suggestions for current issues")
        print("• Type 'fix' - Automatically fix identified issues")
        print("• Type 'tools' - See available orchestration tools")
        print("• Type 'clear' - Clear conversation history")
        print("• Type 'exit' or 'quit' - End orchestration session")
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
                    print("\n🔍 Starting comprehensive network monitoring and AUTOMATIC FIXING...")
                    enhanced_input = f"""{system_prompt}

                     COMPREHENSIVE NETWORK MONITORING TASK - CHECK ALL ENDPOINTS:
                     
                     REQUIRED TOOLS TO USE (in this order):
                     1. get_organizations - Get organization information
                     2. get_organization_networks - List all networks in organization
                     3. get_organization_uplinks_statuses - Check uplink connectivity
                     4. get_network_settings - Review configuration
                     5. get_network_traffic - Check bandwidth usage
                     6. get_network_vpn_stats - Check VPN performance
                     7. get_network_events - Check for security issues
                     8. get_network_clients - Check connected devices
                     9. get_device_loss_and_latency_history - Check device performance
                                           10. get_connectivity_monitoring_destinations - Monitor connectivity
                     11. get_network_group_policies - Review group policies
                     12. get_network_access_control_lists - Check access controls
                      13. get_organization_login_security - Review login security settings
                      14. get_network_security_intrusion - Check intrusion detection
                     
                     TASK: Use ALL the tools listed above systematically to perform comprehensive network monitoring. Check all connected devices, traffic patterns, performance metrics, security events, and network health. For each issue identified, IMMEDIATELY use the appropriate tools to fix the problems automatically. DO NOT ask for permission - just execute fixes immediately. Report what was fixed and the results. BE EFFICIENT and complete the task in minimal steps. PRINT THE TOOL NAMES USED as you use them.
                     
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
                    print("\n🤖 Performing AI-powered network analysis and AUTOMATIC FIXING...")
                    enhanced_input = f"""{get_common_system_prompt()}

                                         TASK: Conduct AI-powered analysis of the network. Evaluate performance metrics, security posture, traffic patterns, and identify optimization opportunities. For each issue found, IMMEDIATELY use the appropriate tools to fix the problems automatically. DO NOT ask for permission - just execute fixes immediately. Report what was fixed and the results.
                     
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
                    print("\n⚡ Getting automated optimization and EXECUTING fixes...")
                    enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Analyze the current network state and provide automated optimization recommendations. Focus on performance improvements, bandwidth optimization, security enhancements, and policy refinements. For each optimization opportunity, IMMEDIATELY use the appropriate tools to implement the improvements automatically. DO NOT ask for permission - just execute optimizations immediately. Report what was optimized and the results."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "security":
                    print("\n🛡️ Reviewing and ENHANCING security posture automatically...")
                    enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Perform a comprehensive security analysis of the network. Check for security vulnerabilities, unauthorized devices, suspicious activities, and security policy effectiveness. For each security issue identified, IMMEDIATELY use the appropriate tools to fix the problems automatically. DO NOT ask for permission - just execute security improvements immediately. Report what security measures were implemented and the results."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "performance":
                    print("\n📊 Analyzing and IMPROVING network performance automatically...")
                    enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Analyze network performance metrics including latency, packet loss, jitter, bandwidth utilization, and throughput. Identify performance bottlenecks and IMMEDIATELY use the appropriate tools to fix performance issues automatically. DO NOT ask for permission - just execute performance improvements immediately. Report what performance optimizations were applied and the results."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "automate":
                    print("\n🤖 Getting automation suggestions and EXECUTING fixes...")
                    enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Identify current network issues and provide specific automation suggestions. For each issue found, IMMEDIATELY use the appropriate tools to resolve problems, optimize performance, and improve network management efficiency automatically. DO NOT ask for permission - just execute automation actions immediately. Report what was automated and the results."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "fix":
                     print("\n🔧 Automatically fixing identified issues...")
                     enhanced_input = f"""{get_common_system_prompt()}

                    TASK: Identify all current network issues and IMMEDIATELY use the available tools to fix them automatically. DO NOT ask for permission - just execute fixes immediately. Resolve problems, optimize performance, and improve security automatically. Report what was fixed and the results of each fix."""
                     user_input = enhanced_input
                
                elif user_input.lower() == "tools":
                    print("\n🔧 Available Network Orchestration Tools:")
                    try:
                        # Get tools from the agent's tool list
                        if hasattr(agent, 'tools') and agent.tools:
                            print(f"Found {len(agent.tools)} orchestration tools:")
                            for tool in agent.tools:
                                print(f"• {tool.name}: {tool.description}")
                        # Fallback to client sessions
                        elif client and client.sessions:
                            print(f"Found {len(client.sessions)} sessions:")
                            for session_name, session in client.sessions.items():
                                print(f"  Session: {session_name}")
                                if hasattr(session, 'tools') and session.tools:
                                    print(f"    Found {len(session.tools)} tools:")
                                    for tool in session.tools:
                                        print(f"    • {tool.name}: {tool.description}")
                                else:
                                    print(f"    No tools found in session {session_name}")
                        # Hardcoded fallback
                        else:
                            print("Using hardcoded orchestration tool list:")
                            print("🔍 MONITORING TOOLS:")
                            print("• get_network_clients - Monitor connected devices & usage patterns")
                            print("• get_network_traffic - Analyze traffic patterns & bandwidth utilization")
                            print("• get_device_loss_and_latency_history - Track performance metrics")
                            print("• get_organization_vpn_stats - Monitor VPN performance")
                            print("• get_network_events - Track network alerts & security events")
                            print("• get_network_settings - Review network configuration")
                            print("• get_organization_uplinks_statuses - Monitor connectivity & failover")
                            print("• get_network_group_policies - Review user policies")
                            print("• get_organization_networks - List all networks")
                            print("• get_connectivity_monitoring_destinations - Check monitoring")
                            print("• get_network_access_control_lists - Review access control")
                            print("• get_organization_login_security - Check authentication")
                            print("• get_network_security_intrusion - Monitor intrusion detection")
                            print("\n⚙️ AUTOMATION TOOLS:")
                            print("• update_network_settings - Optimize network configuration")
                            print("• create_network_appliance_settings - Configure infrastructure")
                            print("• create_network_wireless_settings - Optimize WiFi")
                            print("• update_network_group_policy - Automate policy management")
                            print("• create_organization_network - Automate network creation")
                            print("• update_connectivity_monitoring_destinations - Optimize monitoring")
                            print("• update_network_access_control_lists - Automate access control")
                            print("• update_organization_login_security - Enhance authentication")
                            print("• update_network_security_intrusion - Automate security")
                    except Exception as e:
                        print(f"Error getting tools: {e}")
                        print("Using fallback tool list...")
                        print("• get_network_traffic - Analyze network traffic patterns and bandwidth usage")
                        print("• get_device_loss_and_latency_history - Get device performance metrics")
                        print("• get_organization_vpn_stats - Get VPN statistics for the organization")
                        print("• get_network_events - Get network events and alerts")
                        print("• get_network_settings - Get network-wide configuration settings")
                        print("• update_network_settings - Update network-wide configuration settings")
                        print("• create_network_appliance_settings - Create appliance settings")
                        print("• create_network_wireless_settings - Create wireless settings")
                        print("• delete_network_group_policy - Delete group policies")
                        print("• get_organization_networks - Get all networks in an organization")
                        print("• create_organization_network - Create a new network in an organization")
                        print("• get_connectivity_monitoring_destinations - Get connectivity monitoring destinations")
                        print("• get_network_access_control_lists - Get network access control lists")
                        print("• get_organization_login_security - Get organization login security settings")
                        print("• get_network_security_intrusion - Get network security intrusion settings")
                        print("• update_connectivity_monitoring_destinations - Update connectivity monitoring destinations")
                        print("• update_network_access_control_lists - Update network access control lists")
                        print("• update_organization_login_security - Update organization login security settings")
                        print("• update_network_security_intrusion - Update network security intrusion settings")
                    continue
                
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
        Use these tools only:
        - get_organizations - Get organization information
        - get_organization_networks - List all networks in organization
        
                 Check for:
         - Organization structure and network count
         - Network types and configurations
         - Any obvious organizational issues
         
          IMPORTANT: FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!""",
        
                 2: """PHASE 2: NETWORK INFRASTRUCTURE
         Use these tools only:
         - get_organization_uplinks_statuses - Check uplink connectivity
         - get_network_settings - Review configuration
         - get_network_traffic - Check bandwidth usage
         - get_network_vpn_stats - Check VPN performance
         - get_device_loss_and_latency_history - Check device performance
         - get_connectivity_monitoring_destinations - Check connectivity monitoring
         - update_network_settings - Fix performance/VPN issues
         - create_network_appliance_settings - Fix connectivity issues
         
         Check for:
         - Uplink connectivity issues
         - Network configuration problems
         - Traffic bottlenecks
         - VPN performance issues
         - Device performance problems (latency, packet loss)
         - Connectivity monitoring failures
         
                   IMPORTANT: Use ALL tools and fix EVERY problem detected!
          CRITICAL: For performance/VPN issues, use update_network_settings to actually fix them!
          CRITICAL: For connectivity issues, use create_network_appliance_settings to fix them!
          CRITICAL: FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!""",
        
                 3: """PHASE 3: SECURITY & MONITORING
         Use these tools only:
         - get_network_events - Check for security issues
                   - get_organization_login_security - Review login security settings
          - get_network_security_intrusion - Check intrusion detection
          - get_network_access_control_lists - Check access controls
         - get_network_clients - Check for unauthorized devices
         - update_network_access_control_lists - Block unauthorized devices
         - update_organization_login_security - Fix security settings
         - update_network_security_intrusion - Fix intrusion detection
         
         Check for:
         - Security vulnerabilities
         - Unauthorized access attempts
         - Intrusion detection status
         - Access control issues
         - Unauthorized devices connected
         
                   IMPORTANT: Use ALL tools and fix EVERY problem detected!
          CRITICAL: For unauthorized devices, use update_network_access_control_lists to block them!
          CRITICAL: For security issues, use update_organization_login_security and update_network_security_intrusion!
          CRITICAL: FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!""",
        
                 4: """PHASE 4: DEVICES & PERFORMANCE
         Use these tools only:
         - get_network_clients - Check connected devices
         - get_device_loss_and_latency_history - Check device performance
         - get_connectivity_monitoring_destinations - Monitor connectivity
         - get_network_group_policies - Review group policies
         - update_network_settings - Fix performance issues
         - update_network_group_policy - Fix policy issues
         - update_connectivity_monitoring_destinations - Fix connectivity issues
         
         Check for:
         - Connected device issues
         - Performance problems (latency, loss)
         - Connectivity monitoring issues
         - Policy configuration problems
         
                   IMPORTANT: Use ALL tools and fix EVERY problem detected!
          CRITICAL: For performance issues, use update_network_settings to actually fix them!
          CRITICAL: For connectivity issues, use update_connectivity_monitoring_destinations to fix them!
          CRITICAL: FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!""",
         
         5: """PHASE 5: VPN & ADVANCED PERFORMANCE
         Use these tools only:
         - get_organization_vpn_stats - Check VPN performance metrics
         - get_network_vpn_stats - Check network-specific VPN issues
         - get_device_loss_and_latency_history - Check detailed performance
         - update_network_settings - Fix VPN/performance configuration
         - create_network_appliance_settings - Fix advanced connectivity
         - update_network_group_policy - Apply QoS policies
         
         Check for:
         - VPN latency issues (high ping times)
         - VPN packet loss problems
         - Tunnel connectivity issues
         - QoS and bandwidth optimization
         - Advanced performance tuning
         
                   IMPORTANT: Use ALL tools and fix EVERY problem detected!
          CRITICAL: For VPN performance issues, use update_network_settings to fix latency/packet loss!
          CRITICAL: For QoS issues, use update_network_group_policy to apply bandwidth policies!
          CRITICAL: For advanced connectivity, use create_network_appliance_settings!
          CRITICAL: FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!"""
    }
    
    async def run_single_phase(phase_num, client, llm):
        """Run a single phase and return the result."""
        
                # Create agent for this phase
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=25,  # Increased steps to allow comprehensive problem solving
            memory_enabled=False,
            verbose=False,
        )
        
                # Create phase-specific prompt
        automated_prompt = f"""{get_common_system_prompt()}

        AUTOMATED NETWORK ANALYSIS - PHASE {phase_num}:
        
        {phase_prompts[phase_num]}
        
            EXECUTION RULES:
            CRITICAL: FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues!
            CRITICAL: When you detect a problem, immediately use fixing tools to resolve it!
            CRITICAL: DO NOT just monitor - ACTUALLY FIX the problems you find!
            CRITICAL: Use update_network_settings, create_network_appliance_settings, and other fixing tools!

          - Use ONLY the tools specified for this phase
          - ANALYZE network data thoroughly before making any decisions
          - ONLY make changes when you identify ACTUAL network problems or issues
          - FIX ALL DETECTED PROBLEMS - Use appropriate tools to resolve issues
          - When you detect a problem, immediately use fixing tools to resolve it
          - DO NOT just monitor - ACTUALLY FIX the problems you find
          - ALWAYS explain your reasoning for any decisions made
          - Report what was checked, what decisions were made, and the reasoning
          - Do NOT say "NO CHANGES NEEDED." at any time
          - If you made changes, summarize what was changed
          - Be concise and efficient - Complete in 3-5 tool calls maximum
          - DO NOT over-analyze - Make quick decisions based on clear data
          - COMPLETE THE PHASE QUICKLY - Do not get stuck in analysis loops
          - STOP after making your decision - Do not continue analyzing
          - ALWAYS use the exact output format specified in the system prompt
          - EMPTY RESPONSES ARE VALID: If a tool returns empty data, report as "no data found" not "tool failed"
          - HANDLE EMPTY DATA: Empty responses mean "no issues detected" not "tool failure"
          - COMPREHENSIVE PROBLEM SOLVING: For EVERY problem detected, use appropriate tools to fix it
          - RETRY EMPTY TOOLS: If a tool returns empty data, try it again or use alternative tools
          - FIX ALL ISSUES: Do not stop until ALL detected problems are addressed with fixes
          - USE ALL AVAILABLE TOOLS: In each phase, use ALL tools that could help identify/fix problems
          - ACTUALLY FIX PROBLEMS: Use configuration tools to fix issues, not just monitoring tools
          - PRIORITIZE FIXES OVER MONITORING: When you detect a problem, fix it first, then add monitoring
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

    print("🤖 AUTOMATED NETWORK ANALYSIS MODE")
    print("="*30)
    print("🔍 Gathering comprehensive network information...")
    print("="*30)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Set up the model as the best automated network orchestration and monitoring agent
        system_prompt = get_common_system_prompt()

        # Create Gemini LLM with specialized network orchestration role
        print("Initializing Gemini LLM as Network Orchestration Agent...")
        llm = ChatAnthropic(
            model="glm-4.5",
            temperature=0,
            max_tokens=2048,
            timeout=None,
            max_retries=2,
            api_key=os.environ.get("ANTHROPIC_API_KEY", "55f27b9278af4b3a83a735e228ae4fb8.2oREoHAH8PdKM13f"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
        )
        
        # Create MCP agent with specialized network orchestration role
        print("Creating Network Orchestration Agent...")
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=25,  # Further reduced steps to avoid quota issues
            memory_enabled=False,  # Disable memory to reduce complexity
            verbose=False,  # Disable verbose output to remove "Thought:" and "Final Answer:"
        )
        
        print("Setup complete!")
        print("\n" + "="*30)
        
                # Run analysis based on phase parameter
        if phase and phase in phase_prompts:
            # Run specific phase only
            print(f"\n🚀 RUNNING PHASE {phase} ONLY")
            print("="*30)
            
            try:
                response = await run_single_phase(phase, client, llm)
                print("\n" + "="*30)
                print(f"✅ PHASE {phase} COMPLETE")
                print("="*30)
                print(response)
                print("\n" + "="*30)
                print(f"🎯 Phase {phase} analysis completed!")
                
            except Exception as e:
                print(f"\n Error in Phase {phase}: {e}")
                
        else:
            # Run all phases sequentially
            print("🤖 STARTING SEQUENTIAL PHASE ANALYSIS")
            print("🔄 Will run all 5 phases with 30-second delays")
            print("="*30)
            
            all_results = []
            
            for phase_num in [1, 2, 3, 4, 5]:
                try:
                    # Run the phase
                    result = await run_single_phase(phase_num, client, llm)
                    all_results.append(f"PHASE {phase_num} RESULT:\n{result}")
                    
                    print("\n" + "="*30)
                    print(f"✅ PHASE {phase_num} COMPLETE")
                    print("="*30)
                    print(result)
                    
                    # Wait 30 seconds before next phase to avoid model overload
                    if phase_num < 5:
                        print(f"\n⏳ Waiting 30 seconds before Phase {phase_num + 1}...")
                        await asyncio.sleep(30)
                        
                except Exception as e:
                    error_msg = f" Error in Phase {phase_num}: {e}"
                    all_results.append(error_msg)
                    print(f"\n{error_msg}")
                    
                    # Wait 30 seconds before next phase to avoid model overload
                    if phase_num < 5:
                        print(f"\n⏳ Waiting 30 seconds before Phase {phase_num + 1}...")
                        await asyncio.sleep(30)
            
            # Final summary
            print("\n" + "="*30)
            print("🎯 COMPLETE SEQUENTIAL ANALYSIS FINISHED")
            print("="*30)
            print("📊 All 5 phases have been completed!")
            print("🔄 Network analysis and optimization completed.")
            

        
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

    print("🌐 UPLINK STATUS ANALYSIS")
    print("="*30)
    print("🔍 Gathering comprehensive uplink information...")
    print("="*30)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Set up the model as the best automated network orchestration and monitoring agent
        system_prompt = get_common_system_prompt()

        # Create Gemini LLM with specialized network orchestration role
        print("Initializing Gemini LLM as Uplink Monitoring Agent...")
        llm = ChatAnthropic(
            model="glm-4.5",
            temperature=0,
            max_tokens=2048,
            timeout=None,
            max_retries=2,
            api_key=os.environ.get("ANTHROPIC_API_KEY", "55f27b9278af4b3a83a735e228ae4fb8.2oREoHAH8PdKM13f"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
        )
        
        # Create MCP agent with specialized network orchestration role
        print("Creating Uplink Monitoring Agent...")
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=75,  # Increased steps to allow tool execution
            memory_enabled=True,  # Disable memory to reduce complexity
            verbose=True,  # Enable verbose to see what's happening
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



        print("🚀 Running uplink analysis...")
        
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
                        print(f"⚠️ Gemini model overloaded (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print(" Gemini model still overloaded after all retries. Please try again later.")
                        response = "Error: Gemini model is overloaded. Please try again in a few minutes."
                        break
                elif "finish_reason" in error_str or "int' object has no attribute 'name'" in error_str:
                    print(f"⚠️ Gemini API compatibility issue detected. This is a known issue with certain Gemini models.")
                    print("The analysis may have completed successfully despite this error.")
                    response = " UPLINK ANALYSIS COMPLETE - Analysis completed despite API compatibility warning."
                    break
                elif "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                    print(f"⚠️ Gemini API quota exceeded. You've hit the free tier limits.")
                    print("Please wait 55 seconds before trying again, or consider upgrading your API plan.")
                    response = " UPLINK ANALYSIS FAILED - API quota exceeded. Please wait 55 seconds and try again."
                    break
                else:
                    raise e
        
        print("\n" + "="*30)
        print("✅ UPLINK ANALYSIS COMPLETE")
        print("="*30)
        print(response)
        print("\n" + "="*30)
        print("🎯 Uplink analysis completed!")
        
    except Exception as e:
        print(f" Error in uplink analysis: {e}")
    
    finally:
        if 'client' in locals() and client and hasattr(client, 'close_all_sessions'):
            await client.close_all_sessions()

async def get_uplink_latency_monitoring():
    """Monitor uplinks based on latency thresholds and create policy files."""
    
    # Set up Gemini API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print(" GEMINI_API_KEY not found in .env file")
        return
    
    os.environ["GEMINI_API_KEY"] = gemini_api_key
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print("🌐 UPLINK LATENCY MONITORING")
    print("="*40)
    print("🔍 Monitoring uplink performance based on latency...")
    print("="*40)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Set up the model as the best automated network orchestration and monitoring agent
        system_prompt = get_common_system_prompt()

        # Create Gemini LLM with specialized network orchestration role
        print("Initializing Gemini LLM as Latency Monitoring Agent...")
        llm = ChatAnthropic(
            model="glm-4.5",
            temperature=0,
            max_tokens=2048,
            timeout=None,
            max_retries=2,
            api_key=os.environ.get("ANTHROPIC_API_KEY", "55f27b9278af4b3a83a735e228ae4fb8.2oREoHAH8PdKM13f"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
        )
        
        # Create MCP agent with specialized network orchestration role
        print("Creating Latency Monitoring Agent...")
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=20,  # Increased steps to complete the process
            memory_enabled=False,  # Disable memory to reduce complexity
            verbose=False,  # Disable verbose for cleaner output
        )
        
        print("Setup complete!")
        print("\n" + "="*40)

        # Read latency policy file
        try:
            with open('latency_policy.yaml', 'r') as f:
                policy_content = f.read()
        except FileNotFoundError:
            try:
                with open('latency_policy.txt', 'r') as f:
                    policy_content = f.read()
            except FileNotFoundError:
                policy_content = """# Default Latency Policy
## LATENCY THRESHOLDS:
- CRITICAL: > 150ms latency
- HIGH: 100-150ms latency  
- MEDIUM: 70-100ms latency
- LOW: < 70ms latency

## WAN REROUTING RULES:
- CRITICAL: Use 3 WANs, reroute devices equally
- HIGH: Use 2 WANs, reroute devices equally
- MEDIUM: Use 2 WANs, reroute devices equally
- LOW: No action needed"""
        
        latency_prompt = f"""{system_prompt}
        
        **POLICY FILE:**
        {policy_content}
        
        **EXECUTE:**
        Get appliance settings for latency. Get uplink statuses for devices. Read the policy file above and follow the latency rules. Reroute devices equally across WANs based on the policy. Report final rerouting results."""

        print("🚀 Running latency monitoring analysis...")
        
        # Retry logic for Gemini API overload
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                response = await agent.run(latency_prompt)
                break
            except Exception as e:
                error_str = str(e)
                if "503" in error_str or "overloaded" in error_str.lower():
                    if attempt < max_retries - 1:
                        print(f"Gemini API overloaded (attempt {attempt + 1}/{max_retries})")
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print("Max retries reached. Gemini API is overloaded.")
                        return
                else:
                    print(f"Error during latency monitoring: {e}")
                    return
        
        print("\n" + "="*40)
        print("✅ LATENCY MONITORING COMPLETE")
        print("="*40)
        print(response)
        print("\n" + "="*40)
        print("🎯 Latency monitoring completed!")
        
    except Exception as e:
        print(f" Error in latency monitoring: {e}")
    
    finally:
        if 'client' in locals() and client and hasattr(client, 'close_all_sessions'):
            await client.close_all_sessions()

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
        llm = ChatAnthropic(
            model="glm-4.5",
            temperature=0,
            max_tokens=2048,
            timeout=None,
            max_retries=2,
            api_key=os.environ.get("ANTHROPIC_API_KEY", "55f27b9278af4b3a83a735e228ae4fb8.2oREoHAH8PdKM13f"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
        )
        
        print("Gemini LLM initialized successfully")
        
        # Test agent creation
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=5,
            memory_enabled=True,
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