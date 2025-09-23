#!/usr/bin/env python3
"""
GLM-4.5 MCP Client for Meraki Network Tools
Uses direct Anthropic SDK to connect GLM-4.5 to Meraki MCP tools
Based on original mcp_client.py structure
"""
import json
import re
import sys
import os
from typing import Optional, Dict, Any, List
import asyncio
import logging
import time
from dotenv import load_dotenv

# Anthropic client
from anthropic import Anthropic, AsyncAnthropic

# MCP imports
from mcp_use import MCPClient


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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set console encoding to UTF-8 to handle Unicode characters
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

# Configure Windows console for Unicode support
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")  # Set console to UTF-8 on Windows

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

# ROLE:
You are the NETWORK ORCHESTRATOR with 10+ years of experience.  
Your job is NOT only to analyze but also to TAKE DECISIONS and MOVE DEVICES across WANs automatically.  

# GOAL:
Rebalance all WANs so that:
1. Devices are distributed equally across WANs.  
2. High-latency devices are moved to better WANs.  
3. Provide detailed before/after WAN distribution.  

# STEPS:
1. Call get_organization_uplinks_statuses → capture BEFORE WAN distribution  
2. Call get_device_loss_and_latency_history → get latency data for each device  

# DECISION MATRIX:
- Device >100ms latency: **MOVE to WAN with lowest device count**  
- Multiple high-latency devices: **SORT by latency (worst first), MOVE systematically**  
- WAN overloaded (>50% devices): **REDISTRIBUTE to balance load**  
- All WANs >100ms: **CREATE new WAN and MOVE worst devices**  
- Priority devices (VoIP/video): **MOVE immediately to best WAN**  

# EXECUTION:
- Use update_uplink tool to ACTUALLY MOVE devices  
- Provide device serial, target WAN, and reasoning  
- Call get_organization_uplinks_statuses AGAIN → capture AFTER distribution  

# OUTPUT:
Show exact BEFORE vs AFTER device counts per WAN using real tool data.  
List every device moved with serial and reasoning.  

**CRITICAL: You MUST execute actual device moves. Do not just analyze.**"""

class GLMNetworkOrchestrator:
    """GLM-4.5 Network Orchestration Agent using direct Anthropic SDK."""
    
    def __init__(self):
        # GLM-4.5 configuration
        self.glm_api_key = os.getenv("ANTHROPIC_API_KEY", "44910560602c44a0abb2607d908e7798.sSjyekht0ZkjJWwz")
        self.glm_base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
        
        if not self.glm_api_key or self.glm_api_key == "YOUR_ZAI_API_KEY":
            print("ANTHROPIC_API_KEY not found for GLM model")
            sys.exit(1)
        
        # Initialize Anthropic client for GLM-4.5
        self.anthropic_client = Anthropic(
            api_key=self.glm_api_key,
            base_url=self.glm_base_url
        )
        
        # MCP client and tools
        self.mcp_client = None
        self.mcp_tools = {}
        self.anthropic_tools = []
        self.conversation_history = []
    
    def _convert_mcp_tools_to_anthropic_format(self):
        """Convert MCP tools to Anthropic tools format."""
        self.anthropic_tools = []
        
        for tool_name, tool_info in self.mcp_tools.items():
            anthropic_tool = {
                "name": tool_name,
                "description": getattr(tool_info, 'description', f"Execute {tool_name}"),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # Convert input schema if available
            if hasattr(tool_info, 'inputSchema') and tool_info.inputSchema:
                schema = tool_info.inputSchema
                if isinstance(schema, dict):
                    anthropic_tool["input_schema"] = schema
                elif hasattr(schema, 'properties'):
                    anthropic_tool["input_schema"] = {
                        "type": "object",
                        "properties": getattr(schema, 'properties', {}),
                        "required": getattr(schema, 'required', [])
                    }
            
            self.anthropic_tools.append(anthropic_tool)
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool using the MCP client."""
        try:
            # Validate tool exists
            if tool_name not in self.mcp_tools:
                return f"❌ Tool '{tool_name}' not found. Available tools: {list(self.mcp_tools.keys())}"
            
            # Validate MCP client is available
            if not self.mcp_client:
                return "❌ MCP client not initialized. Please reconnect to the server."
            
            # Find the session that has this tool
            tool_session = None
            for session_name, session in self.mcp_client.sessions.items():
                if hasattr(session, 'tools') and tool_name in session.tools:
                    tool_session = session
                    break
            
            if not tool_session:
                return f"❌ Could not find session for tool '{tool_name}'"
            
            # Call the tool
            result = await tool_session.call_tool(tool_name, arguments or {})
            
            # Extract content from result
            if hasattr(result, 'content') and result.content:
                if isinstance(result.content, list) and len(result.content) > 0:
                    content_item = result.content[0]
                    if hasattr(content_item, 'text'):
                        return content_item.text
                    else:
                        return str(content_item)
                return str(result.content)
            
            return str(result)
            
        except Exception as e:
            return f"❌ Tool execution failed: {e}"
    
    def _format_conversation_for_anthropic(self) -> List[Dict[str, Any]]:
        """Format conversation history for Anthropic API."""
        messages = []
        
        for entry in self.conversation_history:
            if entry["role"] in ["user", "assistant"]:
                message = {
                    "role": entry["role"],
                    "content": entry["content"]
                }
                messages.append(message)
        
        return messages
    
    async def chat_with_tools(self, user_input: str) -> str:
        """Send a message with tool support and handle continuous tool calls."""
        try:
            # Add user input to conversation
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Continue processing until no more tool calls are needed
            max_iterations = 15  # Reduced for GLM stability
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Prepare messages for Anthropic
                messages = self._format_conversation_for_anthropic()
                
                # Make request with tools
                response = self.anthropic_client.messages.create(
                    model="glm-4.5",
                    max_tokens=2048,
                    system=get_common_system_prompt(),
                    messages=messages,
                    tools=self.anthropic_tools if self.anthropic_tools else None
                )
                
                # Handle response
                response_text = ""
                tool_calls = []
                
                # Process response content
                for content in response.content:
                    if content.type == "text":
                        response_text += content.text
                    elif content.type == "tool_use":
                        tool_calls.append({
                            "id": content.id,
                            "name": content.name,
                            "input": content.input
                        })
                
                # If there are tool calls, execute them and continue the loop
                if tool_calls:
                    print(f"🛠️ Iteration {iteration}: Executing {len(tool_calls)} tool call(s)...")
                    
                    # Add assistant message with tool calls to conversation
                    assistant_content = []
                    if response_text:
                        assistant_content.append({"type": "text", "text": response_text})
                    
                    for tool_call in tool_calls:
                        assistant_content.append({
                            "type": "tool_use",
                            "id": tool_call["id"],
                            "name": tool_call["name"],
                            "input": tool_call["input"]
                        })
                    
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
                    
                    # Execute tools and collect results
                    tool_results = []
                    for tool_call in tool_calls:
                        print(f"• Calling {tool_call['name']}...")
                        
                        # Execute the tool
                        result = await self.call_mcp_tool(
                            tool_call["name"], 
                            tool_call["input"]
                        )
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call["id"],
                            "content": str(result)
                        })
                    
                    # Add tool results as user message
                    self.conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })
                    
                    # Continue the loop to see if more tool calls are needed
                    continue
                
                else:
                    # No tool calls, this is the final response
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    
                    if iteration > 1:
                        print(f"✅ Completed after {iteration} iterations")
                    
                    return response_text
            
            # If we hit max iterations, return what we have
            print(f"⚠️ Reached maximum iterations ({max_iterations}), returning current response")
            return response_text
                
        except Exception as e:
            error_msg = f"❌ Chat error: {e}"
            print(error_msg)
            return error_msg

async def get_uplink_latency_monitoring():
    """Monitor uplinks based on latency thresholds using GLM-4.5."""
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print("GLM-4.5 UPLINK LATENCY MONITORING")
    print("="*40)
    print("Monitoring uplink performance based on latency...")
    print("="*40)
    
    try:
        # Create MCP client - properly initialize sessions
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Explicitly create all sessions (this is the missing piece!)
        print("Creating MCP sessions...")
        try:
            await client.create_all_sessions()
            print("✅ Sessions created successfully")
        except Exception as e:
            print(f"Error creating sessions: {e}")
        
        # Wait for sessions to initialize
        await asyncio.sleep(2)
        
        # Check if we have sessions
        if not hasattr(client, 'sessions') or not client.sessions:
            print("❌ No MCP sessions established. Attempting manual session creation...")
            
            # Try to create individual sessions
            try:
                server_names = client.get_server_names() if hasattr(client, 'get_server_names') else ["cisco-meraki-observability"]
                print(f"Available servers: {server_names}")
                
                for server_name in server_names:
                    print(f"Creating session for: {server_name}")
                    session = await client.create_session(server_name)
                    if session:
                        print(f"✅ Created session: {server_name}")
            except Exception as e:
                print(f"Session creation error: {e}")
            
            # Wait again after manual creation
            await asyncio.sleep(1)
        
        # Set up GLM orchestrator
        orchestrator = GLMNetworkOrchestrator()
        orchestrator.mcp_client = client
        
        # Get available tools from all sessions
        all_tools = {}
        session_count = 0
        
        if hasattr(client, 'sessions') and client.sessions:
            for session_name, session in client.sessions.items():
                session_count += 1
                print(f"✅ Checking session: {session_name}")
                
                # Check if session is connected and has tools
                if hasattr(session, 'tools') and session.tools:
                    print(f"  Found {len(session.tools)} tools in {session_name}")
                    for tool_name, tool_info in session.tools.items():
                        all_tools[tool_name] = tool_info
                        print(f"    - {tool_name}")
                else:
                    print(f"  No tools found in session {session_name}")
                    # Try to trigger tool discovery
                    try:
                        if hasattr(session, 'list_tools'):
                            tools_result = await session.list_tools()
                            if tools_result:
                                print(f"  ✅ Discovered tools via list_tools()")
                                for tool in tools_result:
                                    all_tools[tool.name] = tool
                    except Exception as e:
                        print(f"  Error discovering tools: {e}")
        else:
            print("❌ No sessions found in MCP client")
            print("Available client attributes:", [attr for attr in dir(client) if not attr.startswith('_')])
        
        orchestrator.mcp_tools = all_tools
        
        if not orchestrator.mcp_tools:
            print("❌ ERROR: No MCP tools discovered!")
            print("Debug info:")
            print(f"- Sessions found: {len(client.sessions) if hasattr(client, 'sessions') and client.sessions else 0}")
            print("- Make sure your MCP server is running")
            print("- Check mcp-inspector-config.json path is correct")
            print("- Try running: python server/meraki_server.py directly to test")
            return
        
        orchestrator._convert_mcp_tools_to_anthropic_format()
        
        print(f"✅ Successfully discovered {len(orchestrator.mcp_tools)} MCP tools")
        print("Initializing GLM-4.5 LLM as Latency Monitoring Agent...")
        print("Creating Latency Monitoring Agent...")
        print("Setup complete!")
        print("\n" + "="*40)

        # Simple latency monitoring
        print("Running latency monitoring...")
        
        try:
            # Send the complete prompt to GLM
            system_prompt = get_common_system_prompt()
            full_prompt = f"{system_prompt}\n\n{generate_dynamic_latency_prompt()}"
            print("Sending prompt to GLM-4.5 agent...")
            print("This may take 60-90 seconds due to network analysis complexity...")
            
            try:
                response = await orchestrator.chat_with_tools(full_prompt)
                
                print("\n" + "="*30)
                print("UPLINK ANALYSIS COMPLETE")
                print("="*30)
                # Handle Unicode characters in response
                try:
                    print(response)
                except UnicodeEncodeError:
                    # Replace problematic Unicode characters
                    safe_response = str(response).encode('ascii', 'replace').decode('ascii')
                    print(safe_response)
                print("\n" + "="*30)
                print("Uplink analysis completed!")
                
            except Exception as agent_error:
                error_str = str(agent_error)
                if "timeout" in error_str.lower() or "ReadTimeout" in error_str:
                    print("\n" + "="*30)
                    print("GLM MODEL TIMEOUT")
                    print("="*30)
                    print("The GLM-4.5 model took too long to respond.")
                    print("This can happen with complex network analysis tasks.")
                    print("\nRecommendations:")
                    print("1. Try again - the z.ai service may be busy")
                    print("2. Use a simpler prompt")
                    print("3. Check network connectivity")
                    print("="*30)
                else:
                    # Handle other agent errors
                    safe_error = str(error_str).encode('ascii', 'replace').decode('ascii')
                    print(f"GLM Agent Error: {safe_error}")
            
        except Exception as e:
            # Handle other exceptions
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"Error in latency monitoring: {error_msg}")
            return
        
    except Exception as e:
        print(f"ERROR in latency monitoring: {e}")
        import traceback
        traceback.print_exc()
        return
    
    finally:
        # Clean up
        if 'client' in locals() and client and hasattr(client, 'close_all_sessions'):
            print("Cleaning up connections...")
            await client.close_all_sessions()

async def run_meraki_chat():
    """Run a chat using GLM-4.5 for Meraki tools."""
    
    # MCP server config file
    config_file = "mcp-inspector-config.json"

    print("Initializing GLM-4.5 Meraki MCP Chat...")
    print("="*30)
    
    try:
        # Create MCP client
        print("Connecting to MCP server...")
        client = MCPClient.from_config_file(config_file)
        
        # Set up GLM orchestrator
        orchestrator = GLMNetworkOrchestrator()
        orchestrator.mcp_client = client
        
        # Get available tools from all sessions
        all_tools = {}
        if client.sessions:
            for session_name, session in client.sessions.items():
                if hasattr(session, 'tools') and session.tools:
                    all_tools.update(session.tools)
        
        orchestrator.mcp_tools = all_tools
        orchestrator._convert_mcp_tools_to_anthropic_format()
        
        # Create GLM network orchestration agent
        print(f"Initializing GLM-4.5 LLM as Network Orchestration Agent...")
        print(f"Discovered {len(orchestrator.mcp_tools)} MCP tools")
        
        print("Setup complete!")
        print("\n" + "="*30)
        print("GLM-4.5 NETWORK ORCHESTRATION AGENT")
        print("="*30)

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
                    orchestrator.conversation_history = []
                    print("Conversation history cleared.")
                    continue
                
                # Check for orchestration commands
                if user_input.lower() == "monitor":
                    print("\nStarting comprehensive network monitoring and AUTOMATIC FIXING...")
                    enhanced_input = f"""{get_common_system_prompt()}

                     COMPREHENSIVE NETWORK MONITORING TASK - CHECK ALL ENDPOINTS:
                     
                     REQUIRED TOOLS TO USE:
                     - Get all available tools and use them systematically
                     - Check all connected devices, traffic patterns, performance metrics, security events, and network health
                     - For each issue identified, IMMEDIATELY use the appropriate tools to fix the problems automatically
                     - DO NOT ask for permission - just execute fixes immediately
                     - Report what was fixed and the results
                     - BE EFFICIENT and complete the task in minimal steps
                     
                     CRITICAL: Fix ALL detected problems - do not stop until every issue is addressed!
                     
                     IMPORTANT: EMPTY RESPONSES ARE VALID - If a tool returns empty data, report as "no data found" not "tool failed"."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "analyze":
                    print("\nPerforming AI-powered network analysis and AUTOMATIC FIXING...")
                    enhanced_input = f"""{get_common_system_prompt()}

                     TASK: Conduct AI-powered analysis of the network. Get all available tools and use them systematically to evaluate performance metrics, security posture, traffic patterns, and identify optimization opportunities. For each issue found, IMMEDIATELY use the appropriate tools to fix the problems automatically. DO NOT ask for permission - just execute fixes immediately. Report what was fixed and the results."""
                    user_input = enhanced_input
                
                elif user_input.lower() == "tools":
                    print("\nAvailable Network Orchestration Tools:")
                    try:
                        if orchestrator.mcp_tools:
                            print(f"Found {len(orchestrator.mcp_tools)} orchestration tools:")
                            for tool_name, tool_info in orchestrator.mcp_tools.items():
                                desc = getattr(tool_info, 'description', 'No description')
                                print(f"- {tool_name}: {desc}")
                    except Exception as e:
                        print(f"Error getting tools: {e}")
                    continue
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Get response from GLM agent
                print("\nGLM-4.5: ", end="", flush=True)
                
                try:
                    # Run the GLM agent
                    response = await orchestrator.chat_with_tools(user_input)
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

async def test_connection():
    """Test the MCP connection and available tools."""
    print("Testing GLM-4.5 MCP Connection...")
    
    try:
        # Load environment
        load_dotenv()
        
        # Test GLM configuration
        glm_api_key = os.getenv("ANTHROPIC_API_KEY", "44910560602c44a0abb2607d908e7798.sSjyekht0ZkjJWwz")
        if not glm_api_key or glm_api_key == "YOUR_ZAI_API_KEY":
            print("❌ ANTHROPIC_API_KEY not found")
            return False
        print("✅ GLM-4.5 API key configured")
        
        # Test MCP client
        config_file = "mcp-inspector-config.json"
        client = MCPClient.from_config_file(config_file)
        print("✅ MCP Client created successfully")
        
        # Create sessions
        print("Creating MCP sessions...")
        try:
            await client.create_all_sessions()
            print("✅ Sessions created successfully")
        except Exception as e:
            print(f"⚠️ Session creation warning: {e}")
        
        await asyncio.sleep(1)
        
        # Test GLM orchestrator
        orchestrator = GLMNetworkOrchestrator()
        orchestrator.mcp_client = client
        
        # Get available tools
        all_tools = {}
        if hasattr(client, 'sessions') and client.sessions:
            for session_name, session in client.sessions.items():
                print(f"Testing session: {session_name}")
                if hasattr(session, 'tools') and session.tools:
                    all_tools.update(session.tools)
                    print(f"  Found {len(session.tools)} tools")
        
        orchestrator.mcp_tools = all_tools
        if orchestrator.mcp_tools:
            orchestrator._convert_mcp_tools_to_anthropic_format()
        
        print(f"✅ GLM Network Orchestrator created with {len(orchestrator.mcp_tools)} tools")
        
        # Clean up
        await client.close_all_sessions()
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Main function."""
    print("GLM-4.5 Meraki MCP Client")
    print("="*40)
    
    # Show help if requested
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print("\nUsage Options:")
        print("  python client/mcp_client_glm_only.py                    - Run interactive chat mode")
        print("  python client/mcp_client_glm_only.py test               - Test MCP connection")
        print("  python client/mcp_client_glm_only.py --uplink-through-latency - Monitor uplinks based on latency thresholds")
        print("\nEnvironment Variables:")
        print("  ANTHROPIC_API_KEY - Your z.ai API key for GLM-4.5")
        print("  ANTHROPIC_BASE_URL - z.ai endpoint (default: https://api.z.ai/api/anthropic)")
        print("\nInteractive Commands (during chat):")
        print("  monitor - Comprehensive monitoring")
        print("  analyze - AI-powered analysis")
        print("  tools - Show available tools")
        print("  clear - Clear history")
        print("  exit/quit - Exit chat")
        return
    
    # Check if we want to test first
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = await test_connection()
        if success:
            print("\n🚀 Ready to run chat!")
        else:
            print("\n❌ Please fix issues before running chat.")
        return
    
    # Check for --uplink-through-latency flag
    if "--uplink-through-latency" in sys.argv:
        await get_uplink_latency_monitoring()
        return
    
    # Run the chat
    await run_meraki_chat()

if __name__ == "__main__":
    asyncio.run(main())