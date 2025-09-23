"""
Simple Chat Mode for GLM-4.5 with FastMCP Tools
A barebones implementation showing Anthropic SDK interacting with FastMCP tools
"""
import asyncio
import json
import os
import sys
from typing import Dict, Any, List
from dotenv import load_dotenv
from anthropic import Anthropic
from fastmcp import Client

# Load environment variables
load_dotenv()

class SimpleMCPChat:
    """Simple chat interface connecting Anthropic SDK with FastMCP tools."""
    
    def __init__(self):
        # Configure Anthropic client for GLM-4.5
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "44910560602c44a0abb2607d908e7798.sSjyekht0ZkjJWwz")
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
        
        if not self.api_key:
            print("❌ ANTHROPIC_API_KEY not found")
            sys.exit(1)
        
        self.anthropic_client = Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        self.mcp_client = None
        self.tools = []
        self.conversation = []
    
    async def connect_mcp(self):
        """Connect to the FastMCP server."""
        try:
            # Path to the MCP server script
            server_script = os.path.join("server", "meraki_fastmcp_server.py")
            server_script = os.path.abspath(server_script)
            
            if not os.path.exists(server_script):
                raise FileNotFoundError(f"Server script not found: {server_script}")
            
            print(f"🔗 Connecting to MCP server: {server_script}")
            
            # Create FastMCP client
            self.mcp_client = Client(server_script)
            await self.mcp_client.__aenter__()
            
            # Get available tools
            mcp_tools = await self.mcp_client.list_tools()
            
            # Convert MCP tools to Anthropic format
            self.tools = []
            for tool in mcp_tools:
                anthropic_tool = {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name}",
                    "input_schema": tool.inputSchema or {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
                self.tools.append(anthropic_tool)
            
            print(f"✅ Connected! Found {len(self.tools)} tools")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool and return the result."""
        try:
            if not self.mcp_client:
                return "❌ MCP client not connected"
            
            print(f"🛠️ Calling tool: {tool_name}")
            result = await self.mcp_client.call_tool(tool_name, arguments or {})
            
            # Extract content from result
            if hasattr(result, 'data'):
                return str(result.data)
            return str(result)
            
        except Exception as e:
            return f"❌ Tool execution failed: {e}"
    
    async def chat(self, user_message: str) -> str:
        """Send a message and handle tool calls."""
        try:
            # Add user message to conversation
            self.conversation.append({
                "role": "user",
                "content": user_message
            })
            
            # Call Anthropic API
            response = self.anthropic_client.messages.create(
                model="glm-4.5",
                max_tokens=2048,
                system="You are a helpful network orchestration assistant. Use the available tools to help with network management tasks.",
                messages=self.conversation,
                tools=self.tools if self.tools else None
            )
            
            # Process response
            response_text = ""
            tool_calls = []
            
            for content in response.content:
                if content.type == "text":
                    response_text += content.text
                elif content.type == "tool_use":
                    tool_calls.append({
                        "id": content.id,
                        "name": content.name,
                        "input": content.input
                    })
            
            # Execute tool calls if any
            if tool_calls:
                # Add assistant message with tool calls
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
                
                self.conversation.append({
                    "role": "assistant",
                    "content": assistant_content
                })
                
                # Execute tools and collect results
                tool_results = []
                for tool_call in tool_calls:
                    result = await self.call_tool(tool_call["name"], tool_call["input"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": str(result)
                    })
                
                # Add tool results
                self.conversation.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # Get final response
                final_response = self.anthropic_client.messages.create(
                    model="glm-4.5",
                    max_tokens=2048,
                    system="You are a helpful network orchestration assistant. Summarize the tool results clearly.",
                    messages=self.conversation
                )
                
                final_text = ""
                for content in final_response.content:
                    if content.type == "text":
                        final_text += content.text
                
                self.conversation.append({
                    "role": "assistant",
                    "content": final_text
                })
                
                return final_text
            
            else:
                # No tool calls, return response text
                self.conversation.append({
                    "role": "assistant",
                    "content": response_text
                })
                return response_text
                
        except Exception as e:
            return f"❌ Chat error: {e}"
    
    async def disconnect(self):
        """Clean up MCP connection."""
        if self.mcp_client:
            try:
                await self.mcp_client.__aexit__(None, None, None)
            except:
                pass

async def main():
    """Main chat loop."""
    print("Simple GLM-4.5 + FastMCP Chat")
    print("=" * 40)
    
    chat = SimpleMCPChat()
    
    # Connect to MCP server
    if not await chat.connect_mcp():
        print("Failed to connect to MCP server. Exiting.")
        return
    
    print("\nChat started! Type 'quit' to exit, 'tools' to see available tools")
    print("-" * 40)
    
    try:
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            
            if user_input.lower() == "tools":
                print(f"\nAvailable tools ({len(chat.tools)}):")
                for tool in chat.tools:
                    print(f"- {tool['name']}: {tool['description']}")
                continue
            
            if user_input.lower() == "clear":
                chat.conversation = []
                print("Conversation cleared.")
                continue
            
            if not user_input:
                continue
            
            # Get response
            print("\nAssistant: ", end="", flush=True)
            response = await chat.chat(user_input)
            print(response)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    
    finally:
        await chat.disconnect()

if __name__ == "__main__":
    asyncio.run(main())