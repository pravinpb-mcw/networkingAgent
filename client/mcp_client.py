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
        
        # Create Gemini LLM
        print("Initializing Gemini LLM...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_api_key,
            temperature=0.3,
            max_tokens=2048
        )
        
        # Create MCP agent with memory
        print("Creating MCP Agent...")
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=10,
            memory_enabled=True,
        )
        
        print("Setup complete!")
        print("\n" + "="*60)
        print("MERAKI NETWORK MCP CHAT")
        print("="*60)
        print("Available tools:")
        print("• get_network_clients - Get connected devices")
        print("• get_network_traffic - Analyze traffic patterns") 
        print("• get_device_loss_and_latency_history - Get performance metrics")
        print("• get_organization_vpn_stats - Get VPN statistics")
        print("• get_network_events - Get network events")
        print("• get_organization_uplinks_statuses - Device uplink status and failover")
        print("• create_network_appliance_settings - Create appliance settings")
        print("• create_network_wireless_settings - Create wireless settings")
        # print("• continue_wireless_update_after_policy - Continue wireless update after policy")
        # print("• create_network_group_policy - Create group policies")
        print("• update_network_group_policy - update group policies")
        print("\nCommands:")
        print("• Type 'exit' or 'quit' to end")
        print("• Type 'clear' to clear history")
        print("• Type 'tools' to see available tools")
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
                
                # Check for tools command
                if user_input.lower() == "tools":
                    print("\nAvailable MCP Tools:")
                    try:
                        # Get tools from the agent's tool list
                        if hasattr(agent, 'tools') and agent.tools:
                            print(f"Found {len(agent.tools)} tools in agent:")
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
                            print("Using hardcoded tool list:")
                            print("• get_network_clients - Get connected network clients and devices")
                            print("• get_network_traffic - Analyze network traffic patterns and bandwidth usage")
                            print("• get_device_loss_and_latency_history - Get device performance metrics")
                            print("• get_organization_vpn_stats - Get VPN statistics for the organization")
                            print("• get_network_events - Get network events and alerts")
                            print("• create_network_appliance_settings - Create appliance settings")
                            print("• create_network_wireless_settings - Create wireless settings")
                            print("• delete_network_group_policy - Delete group policies")
                    except Exception as e:
                        print(f"Error getting tools: {e}")
                        # Hardcoded fallback
                        print("• get_network_clients - Get connected network clients and devices")
                        print("• get_network_traffic - Analyze network traffic patterns and bandwidth usage")
                        print("• get_device_loss_and_latency_history - Get device performance metrics")
                        print("• get_organization_vpn_stats - Get VPN statistics for the organization")
                        print("• get_network_events - Get network events and alerts")
                        print("• create_network_appliance_settings - Create appliance settings")
                        print("• create_network_wireless_settings - Create wireless settings")
                        print("• delete_network_group_policy - Delete group policies")
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
            memory_enabled=True
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