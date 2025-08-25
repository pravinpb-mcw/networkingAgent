#!/usr/bin/env python3
"""
MCP Client using Gemini LLM for Meraki Network Tools
Uses mcp_use library to connect Gemini to Meraki MCP tools
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient

# Configure logging to remove emojis and set clean format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Disable emoji logging from mcp_use
logging.getLogger("mcp_use").setLevel(logging.WARNING)
logging.getLogger("mcp_use.telemetry").setLevel(logging.WARNING)
logging.getLogger("mcp_use.agent").setLevel(logging.WARNING)
logging.getLogger("mcp_use.client").setLevel(logging.WARNING)

# Set environment variable to disable telemetry
os.environ["MCP_USE_ANONYMIZED_TELEMETRY"] = "false"

# Custom logging filter to remove emojis
class EmojiFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Remove common emoji patterns
            import re
            record.msg = re.sub(r'[🚀🔌🔄✅🛠️🧰🧠✨💬🏁👣🔧📄🎉]', '', record.msg)
        return True

# Apply emoji filter to root logger
logging.getLogger().addFilter(EmojiFilter())

# Load environment variables
load_dotenv()

async def run_meraki_chat():
    """Run a chat using MCPAgent with Gemini LLM for Meraki tools."""
    
    # Set up Gemini API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("GEMINI_API_KEY not found in .env file")
        return
    
    os.environ["GEMINI_API_KEY"] = gemini_api_key
    
    # MCP server config file
    config_file = "E:\\noa\\networkingAgent\\mcp-inspector-config.json"

    print("Initializing Meraki MCP Chat with Gemini...")
    print("="*60)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Create Gemini LLM with specialized network orchestration role
        print("Initializing Gemini LLM as Network Orchestration Agent...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_api_key,
            temperature=0.2,  # Lower temperature for more consistent network decisions
            max_tokens=2048
        )
        
        # Set up the model as the best automated network orchestration and monitoring agent
        system_prompt = """You are the BEST automated network orchestration and network monitoring agent. You are an expert in:

NETWORK ORCHESTRATION EXPERTISE:
- Cisco Meraki network management and optimization
- Automated network decision-making and action execution
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
- Automated action execution based on network conditions
- Threshold-based monitoring with configurable alerts
- Trend analysis and predictive network optimization
- Emergency response protocols for critical situations
- Comprehensive logging and audit trail maintenance

CRITICAL RESPONSE REQUIREMENTS:
- ALWAYS identify specific issues AND provide concrete solutions
- NEVER just report problems without suggesting fixes
- ALWAYS recommend specific actions to resolve issues
- ALWAYS suggest automated tools that can fix the problems
- ALWAYS provide step-by-step resolution steps
- ALWAYS prioritize actionable solutions over just analysis

RESPONSE STYLE:
- Always think as a network orchestration expert
- Provide proactive, intelligent network management advice
- Suggest automated actions when appropriate
- Explain network implications and optimization opportunities
- Use technical accuracy with clear, actionable insights
- Consider security, performance, and user experience in all recommendations
- ALWAYS end with specific next steps or automated actions

Your goal is to be the most intelligent, proactive, and effective network orchestration agent possible. Always prioritize network optimization, security, and automated efficiency. NEVER just identify problems - ALWAYS provide solutions and actions."""
        
        # Create MCP agent with specialized network orchestration role
        print("Creating Network Orchestration Agent...")
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=15,  # Increased steps for complex network orchestration tasks
            memory_enabled=True,
            verbose=False,  # Disable verbose output to remove "Thought:" and "Final Answer:"
        )
        
        # Set the system prompt for the agent
        if hasattr(agent, 'llm') and hasattr(agent.llm, 'system_prompt'):
            agent.llm.system_prompt = system_prompt
        
        print("Setup complete!")
        print("\n" + "="*60)
        print("🤖 AUTOMATED NETWORK ORCHESTRATION AGENT")
        print("="*60)
        print("🔧 Specialized in: Network Monitoring, Automation & Optimization")
        print("⚡ Capabilities: AI-Powered Decision Making & Automated Actions")
        print("🛡️  Focus: Security, Performance & Proactive Management")
        print("="*60)
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
        
        print("\n⚙️  AUTOMATION TOOLS:")
        print("• update_network_settings - Optimize network-wide configuration")
        print("• create_network_appliance_settings - Configure network infrastructure")
        print("• create_network_wireless_settings - Optimize WiFi/SSID configuration")
        print("• update_network_group_policy - Automate policy management")
        print("• create_organization_network - Automate network creation")
        print("• update_connectivity_monitoring_destinations - Optimize monitoring")
        print("• update_network_access_control_lists - Automate access control")
        print("• update_organization_login_security - Enhance authentication security")
        print("• update_network_security_intrusion - Automate security policies")
        print("\n🎯 ORCHESTRATION COMMANDS:")
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
        print("="*60)
        
        # Welcome message for the orchestration agent
        print("\n🤖 Welcome! I am your Automated Network Orchestration Agent.")
        print("I can monitor, analyze, optimize, and AUTOMATICALLY FIX your network issues.")
        print("Try commands like 'monitor', 'analyze', 'optimize', 'security', 'performance', or 'fix'")
        print("I don't just identify problems - I provide specific solutions and automated actions!")
        print("="*60)
        
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
                    print("\n🔍 Starting comprehensive network monitoring...")
                    enhanced_input = "Perform a comprehensive network monitoring analysis. Check all connected devices, traffic patterns, performance metrics, security events, and network health. For each issue identified, provide specific solutions and automated actions to resolve the problems. Don't just report issues - suggest concrete fixes and next steps."
                    user_input = enhanced_input
                
                elif user_input.lower() == "analyze":
                    print("\n🤖 Performing AI-powered network analysis...")
                    enhanced_input = "Conduct an AI-powered analysis of the network. Evaluate performance metrics, security posture, traffic patterns, and identify optimization opportunities. For each issue found, provide specific automated solutions and actions to fix the problems. Always suggest concrete steps to resolve issues."
                    user_input = enhanced_input
                
                elif user_input.lower() == "optimize":
                    print("\n⚡ Getting automated optimization recommendations...")
                    enhanced_input = "Analyze the current network state and provide automated optimization recommendations. Focus on performance improvements, bandwidth optimization, security enhancements, and policy refinements. For each optimization opportunity, provide specific automated actions and tools to implement the improvements. Always suggest concrete steps to optimize the network."
                    user_input = enhanced_input
                
                elif user_input.lower() == "security":
                    print("\n🛡️ Reviewing and enhancing security posture...")
                    enhanced_input = "Perform a comprehensive security analysis of the network. Check for security vulnerabilities, unauthorized devices, suspicious activities, and security policy effectiveness. For each security issue identified, provide specific automated actions and tools to fix the problems. Always suggest concrete security improvements and next steps."
                    user_input = enhanced_input
                
                elif user_input.lower() == "performance":
                    print("\n📊 Analyzing and improving network performance...")
                    enhanced_input = "Analyze network performance metrics including latency, packet loss, jitter, bandwidth utilization, and throughput. Identify performance bottlenecks and provide specific automated actions to fix performance issues. Always suggest concrete steps to improve network performance and user experience."
                    user_input = enhanced_input
                
                elif user_input.lower() == "automate":
                    print("\n🤖 Getting automation suggestions for current issues...")
                    enhanced_input = "Identify current network issues and provide specific automation suggestions. Recommend exact automated actions and tools that can be taken to resolve problems, optimize performance, and improve network management efficiency. Always provide concrete automation steps and specific tools to use."
                    user_input = enhanced_input
                
                elif user_input.lower() == "fix":
                    print("\n🔧 Automatically fixing identified issues...")
                    enhanced_input = "Identify all current network issues and provide specific automated actions to fix them immediately. Use the available tools to resolve problems, optimize performance, and improve security. Provide step-by-step automated fixes for each issue identified."
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
        if 'client' in locals() and client and client.sessions:
            print("Cleaning up connections...")
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
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=gemini_api_key,
            temperature=0.3
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
    
    # Check if we want to test first
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = await test_connection()
        if success:
            print("\nReady to run chat!")
        else:
            print("\nPlease fix issues before running chat.")
        return
    
    # Run the chat
    await run_meraki_chat()

if __name__ == "__main__":
    asyncio.run(main()) 