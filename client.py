#!/usr/bin/env python3
import os
import sys
import json
import asyncio
import re
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

# Anthropic client
from anthropic import Anthropic, AsyncAnthropic

# Rich console for beautiful output
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markup import escape

# FastMCP client imports
try:
    from fastmcp import Client
    import httpx
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("❌ FastMCP client libraries not available. Install with: pip install fastmcp httpx")
    sys.exit(1)

# Textual UI imports
try:
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Input, TextArea, Static, Button, LoadingIndicator, RichLog
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.reactive import reactive
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    # Don't exit - allow terminal mode to work

console = Console()

# Configure logging with timestamped file
from datetime import datetime
log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f'client_debug_{log_timestamp}.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        # Remove StreamHandler to prevent console clutter in TUI mode
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to {log_filename}")

# Debug levels: 0 = no debug, 1 = stop reason only, 2 = full debug
DEBUG_LEVEL = 0

# Agentic Search Strategy
class SearchStrategy(Enum):
    """Search strategies for agentic code generation."""
    DIRECT = "direct"  # Direct execution without search
    EXPLORE = "explore"  # Explore and gather context first
    ITERATIVE = "iterative"  # Iterative refinement
    BATCH = "batch"  # Batch multiple operations

@dataclass
class ContextWindowManager:
    """Manages context window usage and automatic summarization."""
    total_tokens: int = 200000
    reserve_percent: int = 20
    summarization_threshold: float = 0.80
    current_tokens: int = 0
    prompt_tokens_history: List[int] = field(default_factory=list)
    completion_tokens_history: List[int] = field(default_factory=list)
    system_prompt_tokens: int = 0
    tool_definitions_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    tool_call_count: int = 0
    tool_result_tokens: int = 0
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: ~4 chars per token)."""
        return len(text) // 4
    
    def update_usage(self, prompt_tokens: int, completion_tokens: int):
        """Update token usage from API response."""
        self.current_tokens = prompt_tokens + completion_tokens
        self.prompt_tokens_history.append(prompt_tokens)
        self.completion_tokens_history.append(completion_tokens)
        self.total_input_tokens += prompt_tokens
        self.total_output_tokens += completion_tokens
    
    def get_available_tokens(self) -> int:
        """Get available tokens for generation."""
        reserved = int(self.total_tokens * (self.reserve_percent / 100))
        return self.total_tokens - reserved - self.current_tokens
    
    def get_usage_percent(self) -> float:
        """Get current usage as percentage of total (excluding reserve)."""
        usable = self.total_tokens - int(self.total_tokens * (self.reserve_percent / 100))
        return (self.current_tokens / usable) * 100 if usable > 0 else 0
    
    def should_summarize(self) -> bool:
        """Check if context should be summarized."""
        return self.get_usage_percent() >= (self.summarization_threshold * 100)
    
    def get_status_display(self) -> str:
        """Get formatted status display."""
        used_pct = self.get_usage_percent()
        available = self.get_available_tokens()
        reserved = int(self.total_tokens * (self.reserve_percent / 100))
        
        # Color coding
        if used_pct < 50:
            color = "green"
            status = "✓"
        elif used_pct < 80:
            color = "yellow"
            status = "⚠"
        else:
            color = "red"
            status = "⚡"
        
        return (
            f"[{color}]{status} Context: {self.current_tokens:,}/{self.total_tokens:,} tokens "
            f"({used_pct:.1f}% used) | "
            f"Available: {available:,} | Reserved: {reserved:,}[/{color}]"
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get detailed usage statistics."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "current_context_tokens": self.current_tokens,
            "usage_percent": self.get_usage_percent(),
            "available_tokens": self.get_available_tokens(),
            "requests_count": len(self.prompt_tokens_history),
            "avg_input_per_request": sum(self.prompt_tokens_history) / len(self.prompt_tokens_history) if self.prompt_tokens_history else 0,
            "avg_output_per_request": sum(self.completion_tokens_history) / len(self.completion_tokens_history) if self.completion_tokens_history else 0,
            "system_prompt_tokens": self.system_prompt_tokens,
            "tool_definitions_tokens": self.tool_definitions_tokens,
            "tool_calls_made": self.tool_call_count,
            "tool_result_tokens": self.tool_result_tokens,
        }
    
    def add_tool_result_tokens(self, result_text: str):
        """Track tokens used by tool results."""
        tokens = self.estimate_tokens(result_text)
        self.tool_result_tokens += tokens
        self.tool_call_count += 1

@dataclass
class AgenticContext:
    """Context manager for agentic search and operations."""
    search_history: List[Dict[str, Any]] = field(default_factory=list)
    discovered_files: Dict[str, str] = field(default_factory=dict)  # path -> content
    execution_plan: List[str] = field(default_factory=list)
    strategy: SearchStrategy = SearchStrategy.ITERATIVE
    iteration_count: int = 0
    max_iterations: int = 5
    
    def add_search(self, query: str, results: Any):
        """Record a search operation."""
        self.search_history.append({
            "query": query,
            "results": results,
            "iteration": self.iteration_count
        })
    
    def should_continue(self) -> bool:
        """Determine if search should continue."""
        return self.iteration_count < self.max_iterations
    
    def increment_iteration(self):
        """Increment iteration counter."""
        self.iteration_count += 1

# GLM Configuration
GLM_CONFIG = {
    "api_key": "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj",
    "base_url": os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
    "model": "glm-4.5",
    "max_tokens": 4096,
    "context_window": 200000,  # 200K tokens total
    "context_reserve_percent": 20,  # Reserve 20% for summarization
    "summarization_threshold": 0.80  # Summarize when 80% full
}

# OpenStack System Prompt
OPENSTACK_SYSTEM_PROMPT = """You are an expert OpenStack administrator and policy management assistant with AGENTIC SEARCH capabilities. You are a full coding agent capable of planning, breaking down tasks, and executing MCP tools efficiently.

You have access to powerful OpenStack policy management tools through the MCP server. You can:

🛠️ **Policy Management**:
- Generate OpenStack policies for any service (nova, neutron, cinder, etc.)
- Validate existing policies for syntax and security
- Save policies to local files with proper naming
- Deploy policies to OpenStack environments via SSH

📋 **File Operations**:
- List and read existing policy files
- Create and manage local policy files
- Test SSH connections to deployment targets

🔧 **System Operations**:
- Get current working directory
- Test server connectivity
- Manage file operations

🧠 **AGENTIC WORKFLOW - CRITICAL INSTRUCTIONS**:
You MUST follow this iterative search-analyze-refine pattern:

1. **PLAN FIRST**: Before making tool calls, analyze what information you need and batch related operations
2. **SEARCH ITERATIVELY**: 
   - First iteration: Explore and discover (list directories, check file existence)
   - Analyze results and adjust strategy
   - Second iteration: Retrieve specific content based on discoveries
3. **BATCH OPERATIONS**: Combine multiple related tool calls into a single response when possible
   - Example: Instead of separate calls to list_remote_files and run_remote_shell_command, plan to get all info in one iteration
4. **MINIMIZE TOOL CALLS**: Aim for 2-3 iterations maximum per task
   - Iteration 1: Discovery and reconnaissance
   - Iteration 2: Execute main operation with all context
   - Iteration 3 (if needed): Verification only
5. **CONTEXT REUSE**: Remember information from previous tool calls in the conversation
6. **SMART EXECUTION**: 
   - Use sudo commands that combine multiple operations (e.g., "cd /path && ls && cat file")
   - Request comprehensive output in single commands
   - Avoid sequential calls for related information

When using tools:
1. **Always** use the available MCP tools for OpenStack operations
2. **Plan** your tool calls in batches - think ahead about what you'll need
3. **Explain** your search strategy before calling tools
4. **Format** policy content clearly with proper YAML/JSON syntax
5. **Validate** policies before deployment
6. **Provide** clear summaries of actions taken
7. **Change** or **update** policies as needed based on user requests. No need to generate entire new file. Just create the file with the changes alone.
When all other policies remain the same as the original, DO NOT include them in the new file.
Be helpful, accurate, and always prioritize security best practices in OpenStack policy management.

🗂️ **PLANNING & TODO DISCIPLINE**:
- For every new user prompt, FIRST respond with a concise machine-readable plan (2–6 steps) BEFORE any tool calls.
- Output the plan in a fenced code block with language `json` and the following shape (and nothing else around it):
    ```json
    {
        "steps": ["step 1", "step 2"],
        "todos": [ {"title": "actionable item", "status": "not-started"} ],
        "rationale": "one or two sentences"
    }
    ```
- Only after providing this PLAN_JSON should you proceed in subsequent messages to call tools and execute the plan.
- Keep the TODO list minimal and action-oriented; valid statuses: not-started, in-progress, completed.
- Update TODO statuses as you proceed: set the first relevant item to in-progress when you begin; mark items completed when done.
- Show plan and TODO updates clearly to the user.

When user asks to deploy a policy:
- Copy the policy file to the target server using the tool
- Next, use sudo docker ps --format '{{.Names}}' to check necessary openstack services to which the policy.yaml needs to be copied by grepping with the service name
- Next pull the current config from server into a backup directory in /home/mcw/policy-backup/ with a timestamp to the policy file name. Use sudo
- Next copy the new policy file to the appropriate containers into the location /etc/{service}/policy.yaml and restart containers.
- Finally, confirm the deployment was successful, by running the command: docker exec -it nova_api oslopolicy-validator --config-file /etc/nova/nova.conf  --namespace nova or something similar depending on the service.
- For running docker commands, use sudo.
- ALWAYS USE MCP TOOLS FOR DEPLOYMENT. NEVER ASSUME DIRECT SERVER ACCESS.

"""


class GLMAnthropicMCPClient:
    
    def __init__(self):
        """Initialize the GLM Anthropic MCP client with agentic capabilities."""
        self.client = Anthropic(
            api_key=GLM_CONFIG["api_key"],
            base_url=GLM_CONFIG["base_url"]
        )
        self.async_client = AsyncAnthropic(
            api_key=GLM_CONFIG["api_key"],
            base_url=GLM_CONFIG["base_url"]
        )
        self.tools = {}
        self.anthropic_tools = []
        self.conversation_history = []
        # FastMCP client management
        self.mcp_url = "http://localhost:8000/sse/"
        self.mcp_client = None
        self.client_session = None
        # Agentic search context
        self.agentic_context = AgenticContext()
        self.tool_call_count = 0
        self.total_iterations = 0
        # Context window management
        self.context_manager = ContextWindowManager(
            total_tokens=GLM_CONFIG["context_window"],
            reserve_percent=GLM_CONFIG["context_reserve_percent"],
            summarization_threshold=GLM_CONFIG["summarization_threshold"]
        )
        self.session_number = 1
        self.conversation_summary = ""
        # Eventing
        self.event_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.execution_log: List[Dict[str, Any]] = []
        # Simple TODO tracking
        self.todos: List[Dict[str, Any]] = []
        self._todo_id_counter: int = 0
        # Planning state: require an LLM-produced plan before tool calls
        self._planning_phase: bool = False
        self._planning_directive: str = (
            "Before using any tools, output a PLAN_JSON in a fenced json block with keys: steps (2-6 short steps), "
            "todos (optional, list of {title, status='not-started'}), and rationale (short). "
            "Do not invoke any tools in this planning message."
        )

    def on_event(self, listener: Callable[[Dict[str, Any]], None]):
        """Register an event listener to receive structured progress updates."""
        if callable(listener):
            self.event_listeners.append(listener)

    def _emit_event(self, event_type: str, **kwargs):
        """Emit a structured event to all listeners and store in execution log."""
        event = {"type": event_type, **kwargs}
        self.execution_log.append(event)
        for listener in list(self.event_listeners):
            try:
                listener(event)
            except Exception:
                # Don't let UI listener errors break core flow
                logger.debug("Event listener error", exc_info=True)

    # --------------------------- Planning & TODOs ---------------------------
    def _auto_plan(self, user_input: str) -> List[str]:
        """Create a lightweight plan and TODOs for the given prompt when needed."""
        text = (user_input or "").lower()
        keywords = [
            "generate", "create", "update", "modify", "deploy", "validate",
            "ssh", "policy", "openstack", "list", "configure", "fix", "build",
            "analyze", "plan", "steps", "tool", "read", "write", "copy"
        ]
        multi_step = any(k in text for k in keywords) or len(user_input) > 120

        # Generic plan template; the LLM will still do the heavy lifting after
        plan = [
            "Understand the request and constraints",
            "Discover context and select tools",
            "Execute necessary tools and gather outputs",
            "Validate results and adjust if needed",
        ]
        if "deploy" in text or "policy" in text:
            plan.append("If deployment requested: backup, copy new policy, restart services, and validate")

        # Emit plan event
        self._emit_event("plan", steps=plan)

        # Create TODOs only if multi-step
        if multi_step:
            self._create_todos_from_plan(plan)
            # set first todo in-progress initially
            self._set_first_todo_in_progress()
        return plan

    def _create_todos_from_plan(self, steps: List[str]):
        self.todos = []
        self._todo_id_counter = 0
        for step in steps:
            self._todo_id_counter += 1
            self.todos.append({
                "id": self._todo_id_counter,
                "title": step[:60],
                "status": "not-started",
            })
        self._emit_event("todo_update", todos=self.todos)

    def _set_first_todo_in_progress(self):
        for item in self.todos:
            if item.get("status") == "not-started":
                item["status"] = "in-progress"
                break
        if self.todos:
            self._emit_event("todo_update", todos=self.todos)

    def _complete_all_todos(self):
        changed = False
        for item in self.todos:
            if item.get("status") != "completed":
                item["status"] = "completed"
                changed = True
        if changed:
            self._emit_event("todo_update", todos=self.todos)

    def _parse_plan_json(self, text: str) -> Tuple[List[str], Optional[List[Dict[str, Any]]]]:
        """Extract PLAN_JSON from a fenced json block in the text. Returns (steps, todos)."""
        steps: List[str] = []
        todos: Optional[List[Dict[str, Any]]] = None
        try:
            import re
            blocks = re.findall(r"```json\s*(\{[\s\S]*?\})\s*```", text)
            candidate = None
            if blocks:
                candidate = blocks[0]
            else:
                # Fallback: first JSON-looking object
                brace_start = text.find('{')
                brace_end = text.rfind('}')
                if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
                    candidate = text[brace_start:brace_end+1]
            if candidate:
                obj = json.loads(candidate)
                raw_steps = obj.get("steps", [])
                steps = [str(s) for s in raw_steps if isinstance(s, (str, int))]
                raw_todos = obj.get("todos")
                if isinstance(raw_todos, list):
                    norm_todos: List[Dict[str, Any]] = []
                    for t in raw_todos:
                        if isinstance(t, dict):
                            title = t.get("title")
                            status = t.get("status", "not-started")
                            if title:
                                norm_todos.append({"title": str(title), "status": str(status)})
                        else:
                            norm_todos.append({"title": str(t), "status": "not-started"})
                    todos = norm_todos
        except Exception:
            logger.debug("PLAN_JSON parse failed", exc_info=True)
        return steps, todos
        
    async def connect_mcp_server(self, mcp_url: str = None) -> bool:
        """Connect to the OpenStack MCP server via FastMCP client."""
        if mcp_url is None:
            mcp_url = self.mcp_url
        else:
            self.mcp_url = mcp_url
        
        try:
            console.print(f"[bold yellow]🔌 Connecting to MCP Server at {mcp_url}...[/bold yellow]")
            
            # Create FastMCP client
            self.mcp_client = Client(mcp_url)
            
            # Test connection and get tools using async with context
            async with self.mcp_client as session:
                # Store the session for later use
                self.client_session = session
                
                # Get available tools
                tools_result = await session.list_tools()
                self.tools = {tool.name: tool for tool in tools_result}
                
                # Convert MCP tools to Anthropic tools format
                self._convert_tools_to_anthropic_format()
                
                console.print(f"[bold green]✅ Connected! Discovered {len(self.tools)} MCP tools![/bold green]")
                return True
                    
        except Exception as e:
            console.print(f"[bold red]❌ MCP server connection failed: {e}[/bold red]")
            await self.disconnect_mcp_server()
            return False
    
    def _convert_tools_to_anthropic_format(self):
        """Convert MCP tools to Anthropic tools format."""
        self.anthropic_tools = []
        
        for tool_name, tool in self.tools.items():
            anthropic_tool = {
                "name": tool_name,
                "description": tool.description or f"Execute {tool_name}",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # Convert input schema if available
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                schema = tool.inputSchema
                if isinstance(schema, dict):
                    anthropic_tool["input_schema"] = schema
                elif hasattr(schema, 'properties'):
                    anthropic_tool["input_schema"] = {
                        "type": "object",
                        "properties": schema.properties or {},
                        "required": getattr(schema, 'required', [])
                    }
            
            self.anthropic_tools.append(anthropic_tool)
        
        # Calculate token cost of tool definitions
        tools_json = json.dumps(self.anthropic_tools, indent=2)
        self.context_manager.tool_definitions_tokens = self.context_manager.estimate_tokens(tools_json)
        console.print(f"[dim]🔧 Tool definitions: ~{self.context_manager.tool_definitions_tokens:,} tokens[/dim]")
    
    def _analyze_tool_pattern(self, tool_calls: List[Dict[str, Any]]) -> str:
        """Analyze tool call patterns and suggest optimizations."""
        tool_names = [tc['name'] for tc in tool_calls]
        
        # Detect patterns that could be batched
        if tool_names.count('run_remote_shell_command') > 2:
            return "⚠️ Multiple remote commands detected. Consider combining into a single shell script."
        if 'list_remote_files' in tool_names and 'run_remote_shell_command' in tool_names:
            return "💡 Consider using 'remote_ls' which combines listing with command execution."
        if tool_names.count('get_local_cwd') > 1 or tool_names.count('get_remote_cwd') > 1:
            return "⚠️ Redundant directory queries. Cache the working directory."
        
        return ""
    
    def _get_optimization_hints(self) -> str:
        """Provide optimization hints based on tool call patterns."""
        if self.tool_call_count > 10:
            return "\n🔔 OPTIMIZATION: You've made many tool calls. Consider batching operations or using compound commands."
        if self.agentic_context.iteration_count > 3:
            return "\n🔔 ITERATION: Multiple iterations detected. Try to gather more context in earlier iterations."
        return ""
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool using the FastMCP client with tracking."""
        try:
            # Track tool usage
            self.tool_call_count += 1
            
            # Validate tool exists
            if tool_name not in self.tools:
                return f"❌ Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"
            
            # Validate MCP client is available
            if not self.mcp_client:
                return "❌ FastMCP client not initialized. Please reconnect to the server."
            
            # Call the tool using FastMCP client with async context
            async with self.mcp_client as session:
                result = await session.call_tool(tool_name, arguments or {})
                
                # Extract content from result
                result_text = ""
                if hasattr(result, 'content') and result.content:
                    if isinstance(result.content, list) and len(result.content) > 0:
                        content_item = result.content[0]
                        if hasattr(content_item, 'text'):
                            result_text = content_item.text
                        else:
                            result_text = str(content_item)
                    else:
                        result_text = str(result.content)
                else:
                    result_text = str(result)
                
                # Track tool result tokens
                self.context_manager.add_tool_result_tokens(result_text)
                
                # Store in agentic context for reuse
                self.agentic_context.add_search(f"{tool_name}({arguments})", result_text)
                
                return result_text
            
        except Exception as e:
            return f"❌ Tool execution failed: {e}"
    
    async def disconnect_mcp_server(self):
        """Disconnect from the FastMCP server and clean up resources."""
        try:
            # Clean up FastMCP client
            if self.mcp_client:
                self.mcp_client = None
            
            if self.client_session:
                self.client_session = None
            
            console.print("[yellow]🔌 Disconnected from MCP server[/yellow]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Cleanup warning: {e}[/yellow]")
    
    def _estimate_conversation_tokens(self) -> int:
        """Estimate total tokens in current conversation."""
        total = self.context_manager.system_prompt_tokens
        for entry in self.conversation_history:
            content = entry.get("content", "")
            if isinstance(content, str):
                total += self.context_manager.estimate_tokens(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        total += self.context_manager.estimate_tokens(item["text"])
                    elif isinstance(item, dict):
                        total += self.context_manager.estimate_tokens(json.dumps(item))
        return total
    
    async def count_tokens(self, messages: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count tokens for messages using Anthropic's official API.
        
        Returns a dict with 'input_tokens' count.
        """
        try:
            count = self.client.messages.count_tokens(
                model=GLM_CONFIG["model"],
                system=OPENSTACK_SYSTEM_PROMPT,
                messages=messages
            )
            return {
                "input_tokens": count.input_tokens
            }
        except Exception as e:
            console.print(f"[yellow]⚠ Token counting failed, using estimation: {e}[/yellow]")
            # Fallback to estimation
            total = self.context_manager.estimate_tokens(OPENSTACK_SYSTEM_PROMPT)
            for msg in messages:
                content = msg.get("content", "")
                if isinstance(content, str):
                    total += self.context_manager.estimate_tokens(content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            total += self.context_manager.estimate_tokens(item["text"])
            return {"input_tokens": total}
    
    async def _summarize_conversation(self) -> str:
        """Summarize the conversation to compress context."""
        console.print("\n[bold yellow]⚡ Context window approaching limit (80%). Summarizing conversation...[/bold yellow]")
        
        # Build summary prompt
        summary_prompt = """Please provide a concise summary of this conversation that preserves:
1. All important decisions and actions taken
2. Key policy configurations and deployments
3. Current state of the system
4. Any pending tasks or issues
5. Important context for future interactions

Keep the summary detailed enough to continue the conversation seamlessly."""
        
        try:
            # Create a summary using the current conversation
            messages = [{"role": "user", "content": summary_prompt}]
            
            response = self.client.messages.create(
                model=GLM_CONFIG["model"],
                max_tokens=2000,
                system=OPENSTACK_SYSTEM_PROMPT + "\n\nYou are summarizing a previous conversation. Be thorough but concise.",
                messages=messages
            )
            
            summary = response.content[0].text if response.content else "No summary generated."
            
            console.print(f"[green]✓ Conversation summarized ({len(summary)} chars)[/green]")
            return summary
            
        except Exception as e:
            console.print(f"[red]⚠ Summarization failed: {e}[/red]")
            return "Summary failed. Conversation context may be lost."
    
    def _compress_conversation_history(self, summary: str):
        """Replace old conversation history with summary."""
        # Keep only recent messages (last 5 exchanges)
        recent_threshold = 10  # Keep last 10 messages
        
        if len(self.conversation_history) > recent_threshold:
            recent_messages = self.conversation_history[-recent_threshold:]
            
            # Create new history starting with summary
            self.conversation_history = [
                {
                    "role": "user",
                    "content": f"[Previous conversation summary - Session {self.session_number}]:\n{summary}"
                },
                {
                    "role": "assistant",
                    "content": "I understand. I'll continue from where we left off with full context of our previous discussion."
                }
            ] + recent_messages
            
            self.session_number += 1
            self.conversation_summary = summary
            
            # Reset token count
            new_token_count = self._estimate_conversation_tokens()
            self.context_manager.current_tokens = new_token_count
            
            console.print(f"[green]✓ Context compressed. New session #{self.session_number} started.[/green]")
            console.print(f"[green]  Tokens reduced: {new_token_count:,} (saved space for continued generation)[/green]")
    
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
        """Send a message with tool support and handle continuous tool calls using agentic search."""
        try:
            # Reset counters for this conversation turn
            self.tool_call_count = 0
            self.agentic_context.iteration_count = 0
            
            # Check context window and summarize if needed
            estimated_tokens = self._estimate_conversation_tokens()
            self.context_manager.current_tokens = estimated_tokens
            
            if self.context_manager.should_summarize():
                summary = await self._summarize_conversation()
                self._compress_conversation_history(summary)
            
            # Add user input to conversation
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            self._emit_event("user_message", text=user_input)
            # Enter planning phase: the LLM must produce the plan first
            self._planning_phase = True
            
            # Continue processing until no more tool calls are needed
            max_iterations = 50  # Reduced from 100 to encourage efficiency
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                self.agentic_context.increment_iteration()
                self.total_iterations += 1
                
                if DEBUG_LEVEL >= 2:
                    logger.debug(f"\n{'='*60}")
                    logger.debug(f"Starting iteration {iteration}/{max_iterations}")
                    logger.debug(f"Conversation history length: {len(self.conversation_history)}")
                    logger.debug(f"Tool calls so far: {self.tool_call_count}")
                
                # Prepare messages for Anthropic
                messages = self._format_conversation_for_anthropic()
                
                if DEBUG_LEVEL >= 2:
                    logger.debug(f"Formatted {len(messages)} messages for API")
                
                # Make request with tools
                if DEBUG_LEVEL >= 2:
                    logger.debug(f"Making API request with {len(self.anthropic_tools)} tools available")
                
                # Yield to UI loop
                await asyncio.sleep(0)
                # If in planning phase, append a directive to return PLAN_JSON first without using tools
                planning_messages = []
                if self._planning_phase:
                    planning_messages = messages + [{
                        "role": "user",
                        "content": self._planning_directive
                    }]
                else:
                    planning_messages = messages

                response = await self.async_client.messages.create(
                    model=GLM_CONFIG["model"],
                    max_tokens=GLM_CONFIG["max_tokens"],
                    system=OPENSTACK_SYSTEM_PROMPT,
                    messages=planning_messages,
                    tools=self.anthropic_tools if self.anthropic_tools else None
                )
                
                if DEBUG_LEVEL >= 1:
                    logger.info(f"[Iteration {iteration}] stop_reason: {response.stop_reason}")
                
                if DEBUG_LEVEL >= 2:
                    logger.debug(f"API response received")
                    logger.debug(f"Response content blocks: {len(response.content)}")
                    for idx, block in enumerate(response.content):
                        logger.debug(f"  Block {idx}: type={block.type}")
                
                # Update token usage from response using official usage property
                if hasattr(response, 'usage'):
                    usage = response.usage
                    input_tokens = getattr(usage, 'input_tokens', 0)
                    output_tokens = getattr(usage, 'output_tokens', 0)
                    self.context_manager.update_usage(input_tokens, output_tokens)
                    
                    # Display usage for this request
                    if iteration == 1:
                        console.print(f"[dim]📊 Usage: {input_tokens:,} input + {output_tokens:,} output = {input_tokens + output_tokens:,} tokens[/dim]")
                        self._emit_event("usage", input_tokens=input_tokens, output_tokens=output_tokens, total=input_tokens+output_tokens)
                
                # Handle response
                response_text = ""
                tool_calls = []
                stop_reason = response.stop_reason
                
                if DEBUG_LEVEL >= 2:
                    logger.debug(f"Processing response with stop_reason: {stop_reason}")
                
                # Process response content
                for content in response.content:
                    if content.type == "text":
                        response_text += content.text
                        if DEBUG_LEVEL >= 2:
                            logger.debug(f"Found text content: {content.text[:100]}...")
                    elif content.type == "tool_use":
                        tool_calls.append({
                            "id": content.id,
                            "name": content.name,
                            "input": content.input
                        })
                        if DEBUG_LEVEL >= 2:
                            logger.debug(f"Found tool_use: {content.name}")
                
                if DEBUG_LEVEL >= 2:
                    logger.debug(f"Extracted {len(tool_calls)} tool calls")
                    logger.debug(f"Response text length: {len(response_text)}")
                
                # If there are tool calls, execute them and continue the loop
                if tool_calls:
                    # During planning, ignore any tool calls and ask for plan only
                    if self._planning_phase:
                        self._emit_event("hint", message="Model attempted tool calls during planning; ignoring and requesting PLAN_JSON only.")
                        # Add a nudge and continue
                        self.conversation_history.append({
                            "role": "user",
                            "content": "Please provide the PLAN_JSON first as per instructions (no tool calls)."
                        })
                        await asyncio.sleep(0)
                        continue
                    # Analyze tool call patterns
                    pattern_hint = self._analyze_tool_pattern(tool_calls)
                    if pattern_hint:
                        console.print(f"[yellow]{escape(pattern_hint)}[/yellow]")
                        self._emit_event("hint", message=pattern_hint)
                    
                    console.print(f"[yellow]🛠️ Iteration {iteration}: Executing {len(tool_calls)} tool call(s)... (Total: {self.tool_call_count + len(tool_calls)})[/]")
                    self._emit_event("tool_calls_start", iteration=iteration, count=len(tool_calls), total_so_far=self.tool_call_count)
                    
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
                        console.print(f"[cyan]• Calling {escape(tool_call['name'])}...[/cyan]")
                        
                        # Display tool parameters
                        if tool_call["input"]:
                            console.print(f"[dim cyan]  Parameters: {escape(json.dumps(tool_call['input'], indent=2))}[/dim cyan]")
                        self._emit_event("tool_call", id=tool_call["id"], name=tool_call["name"], input=tool_call.get("input", {}))
                        
                        # Execute the tool
                        # Yield to UI loop between calls
                        await asyncio.sleep(0)
                        result = await self.call_mcp_tool(
                            tool_call["name"], 
                            tool_call["input"]
                        )
                        # Emit result (truncate large payloads for event stream)
                        result_str = str(result)
                        self._emit_event("tool_result", id=tool_call["id"], name=tool_call["name"], result=result_str)
                        
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
                    
                    if DEBUG_LEVEL >= 2:
                        logger.debug(f"Added {len(tool_results)} tool results to conversation")
                        logger.debug(f"Continuing to next iteration to process tool results")
                    
                    # Continue the loop to see if more tool calls are needed
                    continue
                
                else:
                    # No tool calls in this response
                    if DEBUG_LEVEL >= 2:
                        logger.debug(f"No tool calls found in response")
                        logger.debug(f"Stop reason: {stop_reason}")
                        logger.debug(f"Response text present: {bool(response_text)}")
                    
                    # Check for empty response - if we get end_turn with no content, continue
                    if stop_reason == "end_turn" and not response_text.strip():
                        if DEBUG_LEVEL >= 1:
                            logger.warning(f"Empty response with end_turn - continuing to retry")
                        console.print(f"[yellow]⚠️ Empty response received, retrying...[/yellow]")
                        # Add a gentle prompt to continue
                        self.conversation_history.append({
                            "role": "user",
                            "content": "Please continue with your response."
                        })
                        # Allow UI refresh between iterations
                        await asyncio.sleep(0)
                        continue
                    
                    # Planning phase handling: parse PLAN_JSON and emit plan/todos
                    if self._planning_phase and response_text:
                        steps, todos = self._parse_plan_json(response_text)
                        if steps:
                            self._emit_event("plan", steps=steps)
                        if todos is not None:
                            # Assign default status if missing; coerce to minimal structure
                            self.todos = []
                            self._todo_id_counter = 0
                            for t in todos:
                                title = t.get("title") if isinstance(t, dict) else str(t)
                                status = t.get("status", "not-started") if isinstance(t, dict) else "not-started"
                                if not title:
                                    continue
                                self._todo_id_counter += 1
                                self.todos.append({"id": self._todo_id_counter, "title": title[:80], "status": status})
                            # Set first todo in progress
                            for item in self.todos:
                                if item["status"] == "not-started":
                                    item["status"] = "in-progress"
                                    break
                            self._emit_event("todo_update", todos=self.todos)
                        # End planning phase regardless of parse success
                        self._planning_phase = False
                        # Record assistant planning message
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": response_text
                        })
                        self._emit_event("assistant_text", text=response_text)
                        await asyncio.sleep(0)
                        continue

                    # Add assistant response to history
                    if response_text:
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": response_text
                        })
                        self._emit_event("assistant_text", text=response_text)
                        if DEBUG_LEVEL >= 2:
                            logger.debug(f"Added assistant response to history")
                    
                    # Check stop reason to determine if we should continue
                    # If stop_reason is "end_turn", Claude explicitly ended its turn
                    # If stop_reason is "max_tokens", we hit the limit and should stop
                    # If stop_reason is "stop_sequence", a stop sequence was hit
                    if DEBUG_LEVEL >= 2:
                        logger.debug(f"Checking stop condition for: {stop_reason}")
                    
                    if stop_reason in ["end_turn", "max_tokens", "stop_sequence"]:
                        # This is the final response
                        if DEBUG_LEVEL >= 2:
                            logger.debug(f"Final response detected. Returning.")
                            logger.debug(f"Total iterations: {iteration}")
                            logger.debug(f"Total tool calls: {self.tool_call_count}")
                        
                        # Provide optimization feedback
                        if iteration > 1:
                            console.print(f"[green]✅ Completed after {iteration} iterations | {self.tool_call_count} total tool calls[/]")
                        
                        optimization_hint = self._get_optimization_hints()
                        if optimization_hint:
                            console.print(f"[yellow]{escape(optimization_hint)}[/yellow]")
                            self._emit_event("hint", message=optimization_hint)
                        
                        # Update final token estimate
                        self.context_manager.current_tokens = self._estimate_conversation_tokens()
                        self._emit_event("complete", iterations=iteration, tool_calls=self.tool_call_count)
                        # Mark todos done
                        self._complete_all_todos()
                        
                        return response_text
                    else:
                        # Unexpected stop reason or model wants to continue
                        if DEBUG_LEVEL >= 2:
                            logger.debug(f"Continuing to next iteration. Stop reason: {stop_reason}")
                        
                        # Display the message but continue the loop
                        if response_text:
                            console.print(f"[yellow]💬 Status update: {escape(response_text)}[/yellow]")
                        # Continue to next iteration to see if model wants to make more tool calls
                        if DEBUG_LEVEL >= 2:
                            logger.debug(f"Looping to iteration {iteration + 1}")
                        # Allow UI refresh between iterations
                        await asyncio.sleep(0)
                        continue
            
            # If we hit max iterations, return what we have
            console.print(f"[yellow]⚠️ Reached maximum iterations ({max_iterations}), returning current response[/]")
            return response_text
                
        except asyncio.CancelledError:
            self._emit_event("cancelled")
            console.print("[yellow]⏹️ Request cancelled by user[/yellow]")
            raise
        except Exception as e:
            error_msg = f"❌ Chat error: {e}"
            console.print(f"[bold red]{escape(error_msg)}[/bold red]")
            return error_msg
    
    def _handle_slash_command(self, command: str) -> Optional[str]:
        """Handle slash commands. Returns response if handled, None otherwise."""
        command = command.strip().lower()
        
        if command == "/context" or command == "/ctx":
            # Display detailed context usage
            used_pct = self.context_manager.get_usage_percent()
            available = self.context_manager.get_available_tokens()
            reserved = int(self.context_manager.total_tokens * (self.context_manager.reserve_percent / 100))
            usable = self.context_manager.total_tokens - reserved
            
            # Create detailed table
            table = Table(title="📊 Context Window Usage", show_header=True, header_style="bold cyan")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Details", style="dim")
            
            table.add_row(
                "Current Usage",
                f"{self.context_manager.current_tokens:,} tokens",
                f"{used_pct:.2f}% of usable space"
            )
            table.add_row(
                "Available",
                f"{available:,} tokens",
                f"For new messages"
            )
            table.add_row(
                "Total Capacity",
                f"{self.context_manager.total_tokens:,} tokens",
                f"200K tokens"
            )
            table.add_row(
                "Usable Space",
                f"{usable:,} tokens",
                f"After {self.context_manager.reserve_percent}% reserve"
            )
            table.add_row(
                "Reserved",
                f"{reserved:,} tokens",
                f"For summarization"
            )
            table.add_row(
                "Session Number",
                f"#{self.session_number}",
                f"{len(self.conversation_history)} messages in history"
            )
            table.add_row(
                "Tool Definitions",
                f"{self.context_manager.tool_definitions_tokens:,} tokens",
                f"{len(self.tools)} tools loaded"
            )
            table.add_row(
                "Tool Results",
                f"{self.context_manager.tool_result_tokens:,} tokens",
                f"{self.context_manager.tool_call_count} calls made"
            )
            table.add_row(
                "Auto-Summarize",
                f"At {int(self.context_manager.summarization_threshold * 100)}%",
                "Triggered" if self.context_manager.should_summarize() else "Not triggered"
            )
            
            console.print()
            console.print(table)
            console.print()
            
            # Status indicator
            status_msg = self.context_manager.get_status_display()
            console.print(status_msg)
            console.print()
            
            # Warnings
            if used_pct >= 80:
                console.print("[bold red]⚠️  WARNING: Context window is nearly full. Auto-summarization will trigger soon.[/bold red]")
            elif used_pct >= 60:
                console.print("[yellow]💡 INFO: Context usage is getting high. Consider summarizing if needed.[/yellow]")
            else:
                console.print("[green]✓ Context usage is healthy.[/green]")
            
            return "Context usage displayed."
        
        elif command == "/stats":
            # Display cumulative statistics
            stats = self.context_manager.get_usage_stats()
            
            stats_table = Table(title="📈 Cumulative Session Statistics", show_header=True, header_style="bold magenta")
            stats_table.add_column("Metric", style="magenta")
            stats_table.add_column("Value", style="cyan")
            
            stats_table.add_row("Total Input Tokens", f"{stats['total_input_tokens']:,}")
            stats_table.add_row("Total Output Tokens", f"{stats['total_output_tokens']:,}")
            stats_table.add_row("Total Tokens Used", f"{stats['total_tokens']:,}")
            stats_table.add_row("─" * 25, "─" * 15)
            stats_table.add_row("System Prompt", f"{stats['system_prompt_tokens']:,} tokens")
            stats_table.add_row("Tool Definitions", f"{stats['tool_definitions_tokens']:,} tokens")
            stats_table.add_row("Tool Results", f"{stats['tool_result_tokens']:,} tokens")
            stats_table.add_row("Tool Calls Made", f"{stats['tool_calls_made']}")
            stats_table.add_row("─" * 25, "─" * 15)
            stats_table.add_row("API Requests Made", f"{stats['requests_count']}")
            stats_table.add_row("Avg Input/Request", f"{stats['avg_input_per_request']:.0f}")
            stats_table.add_row("Avg Output/Request", f"{stats['avg_output_per_request']:.0f}")
            
            console.print()
            console.print(stats_table)
            console.print()
            
            return "Statistics displayed."
        
        elif command == "/help":
            help_text = """
[bold cyan]Available Slash Commands:[/bold cyan]

[green]/context[/green] or [green]/ctx[/green]  - Display current context window usage and statistics
[green]/stats[/green]               - Show cumulative session statistics (total tokens used)
[green]/help[/green]                - Show this help message
[green]/quit[/green] or [green]/exit[/green]   - Exit the chat session
"""
            console.print(Panel(help_text, title="💡 Help", style="cyan"))
            return "Help displayed."
        
        return None
    
    def get_tools_description(self) -> str:
        """Get a formatted description of available tools."""
        if not self.tools:
            return "No tools available."
        
        description = "🛠️ **Available OpenStack Tools**:\n\n"
        for tool_name, tool in self.tools.items():
            description += f"• **{tool_name}**: {tool.description or 'No description'}\n"
        
        return description
    
    async def start_chat(self):
        """Start an interactive chat session."""
        console.print(Panel.fit(
            "[bold cyan]GLM-4.6 Anthropic with OpenStack MCP Tools[/bold cyan]\n"
            "[yellow]Enhanced OpenStack Policy Management Assistant[/yellow]\n"
            f"[dim]Context: {GLM_CONFIG['context_window']:,} tokens | "
            f"Auto-summarize at {int(GLM_CONFIG['summarization_threshold']*100)}% | "
            f"Reserve: {GLM_CONFIG['context_reserve_percent']}%[/dim]",
            title="🚀 Welcome",
            style="bold blue"
        ))
        
        # Estimate system prompt tokens
        self.context_manager.system_prompt_tokens = self.context_manager.estimate_tokens(OPENSTACK_SYSTEM_PROMPT)
        
        # Connect to MCP server
        connected = await self.connect_mcp_server()
        if not connected:
            console.print("[bold red]❌ Failed to connect to MCP server. Exiting.[/bold red]")
            return
        
        # Show available tools
        console.print(Panel(
            self.get_tools_description(),
            title="🛠️ Available Tools",
            style="green"
        ))
        
        console.print("\n[bold cyan]🧠 AGENTIC MODE: Optimized for minimal tool calls with iterative search[/bold cyan]")
        console.print("[bold green]Chat started! Type 'quit', 'exit', or 'bye' to end.[/bold green]")
        console.print("[dim]Slash commands: /context (usage), /help (commands)[/dim]\n")
        
        try:
            while True:
                # Get user input
                try:
                    user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
                except (EOFError, KeyboardInterrupt):
                    break
                
                # Check for exit commands
                if user_input.lower().strip() in ['quit', 'exit', 'bye', 'q', '/quit', '/exit']:
                    break
                
                if not user_input.strip():
                    continue
                
                # Handle slash commands
                if user_input.strip().startswith('/'):
                    result = self._handle_slash_command(user_input.strip())
                    if result:
                        continue
                
                # Display context status before processing
                console.print(f"\n{self.context_manager.get_status_display()}")
                
                # Show thinking indicator
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("🤔 GLM-4.6 thinking...", total=None)
                    
                    # Get response
                    response = await self.chat_with_tools(user_input)
                
                # Display response
                console.print(f"\n[bold green]GLM-4.6[/bold green]: {response}")
        
        except KeyboardInterrupt:
            pass
        finally:
            console.print("\n[yellow]👋 Chat ended. Cleaning up...[/yellow]")
            
            # Display session statistics
            stats = self.context_manager.get_usage_stats()
            console.print(f"\n[cyan]📊 Session Statistics:[/cyan]")
            console.print(f"  • Total iterations: {self.total_iterations}")
            console.print(f"  • Total tool calls: {self.tool_call_count}")
            if self.total_iterations > 0:
                avg_tools = self.tool_call_count / max(1, self.total_iterations)
                console.print(f"  • Average tools per iteration: {avg_tools:.2f}")
            console.print(f"\n[cyan]📊 Token Usage:[/cyan]")
            console.print(f"  • Total input tokens: {stats['total_input_tokens']:,}")
            console.print(f"  • Total output tokens: {stats['total_output_tokens']:,}")
            console.print(f"  • Total tokens: {stats['total_tokens']:,}")
            console.print(f"  • System prompt: {stats['system_prompt_tokens']:,} tokens")
            console.print(f"  • Tool definitions: {stats['tool_definitions_tokens']:,} tokens")
            console.print(f"  • Tool results: {stats['tool_result_tokens']:,} tokens ({stats['tool_calls_made']} calls)")
            console.print(f"  • API requests: {stats['requests_count']}")
            if stats['requests_count'] > 0:
                console.print(f"  • Avg tokens per request: {(stats['total_tokens'] / stats['requests_count']):.0f}")
            
            await self.disconnect_mcp_server()
            console.print("[yellow]Goodbye![/]")


# ============================================================================
# Textual UI Components
# ============================================================================

if TEXTUAL_AVAILABLE:
    class ChatView(RichLog):
        """Main chat window with rich text support."""
        
        def __init__(self):
            super().__init__(
                highlight=True,
                markup=True,
                wrap=True,
                auto_scroll=True
            )
            self.message_count = 0

        def add_message(self, sender: str, text: str, color: str = None):
            """Add a formatted message to the chat."""
            if color is None:
                color = "cyan" if sender == "You" else "green"
            
            # Add separator for readability (after first message)
            if self.message_count > 0:
                self.write("")
            
            self.write(f"[bold {color}]{sender}:[/bold {color}]")
            self.write(text)
            self.message_count += 1

    class EventsView(RichLog):
        """Side panel to display tool call executions and system events."""

        def __init__(self):
            super().__init__(
                highlight=True,
                markup=True,
                wrap=True,
                auto_scroll=True
            )
            self.event_count = 0

        def add_event(self, title: str, text: str, color: str = "cyan"):
            if self.event_count > 0:
                self.write("")
            self.write(f"[bold {color}]{escape(title)}[/bold {color}]")
            self.write(escape(text))
            self.event_count += 1

    class TodoView(RichLog):
        """Panel to display a toggleable TODO list and planning notes."""

        def __init__(self):
            super().__init__(highlight=True, markup=True, wrap=True, auto_scroll=True)
            self._last = None

        def show_plan(self, steps: List[str]):
            self.write("[bold yellow]Plan:[/bold yellow]")
            for i, s in enumerate(steps, 1):
                self.write(f"  {i}. {escape(s)}")
            self.write("")

        def show_todos(self, todos: List[Dict[str, Any]]):
            self.write("[bold cyan]TODOs:[/bold cyan]")
            for t in todos:
                status = t.get("status", "not-started")
                title = t.get("title", "")
                icon = {
                    "not-started": "⏳",
                    "in-progress": "🔧",
                    "completed": "✅",
                }.get(status, "⏳")
                self.write(f" {icon} [{status}] {escape(title)}")
            self.write("")


    class AgenticTUI(App):
        """Main TUI App with multiline input and comprehensive features."""

        CSS = """
        Screen {
            background: $surface;
        }
        
        #chat_container {
            height: 1fr;
            border: solid $primary;
            margin: 1;
            width: 2fr;
        }
        
        #events_container {
            height: 1fr;
            border: solid $secondary;
            margin: 1;
            width: 1fr;
        }

        #todo_container {
            height: 1fr;
            border: solid $success;
            margin: 1;
            width: 1fr;
        }
        
        #input_container {
            height: auto;
            max-height: 10;
            border: solid $accent;
            margin: 1;
        }
        
        #input_field {
            height: 100%;
        }
        
        #button_bar {
            height: auto;
            padding: 1;
            background: $panel;
        }
        
        #status {
            width: 1fr;
            content-align: left middle;
            padding: 0 1;
        }
        
        Button {
            margin: 0 1;
        }
        
        #context_info {
            height: 3;
            background: $panel;
            border: solid $primary;
            margin: 1;
            padding: 1;
        }

        .hidden {
            display: none;
        }
        """

        BINDINGS = [
            ("ctrl+q", "quit", "Quit"),
            ("ctrl+enter", "send_message", "Send"),
            ("escape", "clear_input", "Clear"),
            ("ctrl+c", "copy_last", "Copy Last"),
            ("ctrl+x", "show_context", "Context"),
            ("ctrl+s", "show_stats", "Stats"),
            ("ctrl+.", "cancel", "Cancel"),
            ("ctrl+t", "toggle_todo", "Toggle TODO"),
        ]

        loading = reactive(False)

        def __init__(self):
            super().__init__()
            self.client = GLMAnthropicMCPClient()
            self.chat_view = ChatView()
            self.events_view = EventsView()
            self.todo_view = TodoView()
            self.input_field = TextArea(
                text="",
                language="markdown",
                theme="monokai",
                show_line_numbers=False,
            )
            self.status_bar = Static("🔌 Initializing...", id="status")
            self.context_info = Static("", id="context_info")
            self.send_button = Button("Send (Ctrl+Enter)", id="send", variant="success")
            self.clear_button = Button("Clear (Esc)", id="clear", variant="warning")
            self.cancel_button = Button("Cancel (Ctrl+.)", id="cancel", variant="error")
            self.todo_toggle_button = Button("Toggle TODO (Ctrl+T)", id="toggle_todo", variant="primary")
            self.last_response = ""
            # Wire event stream to UI
            self.client.on_event(self._handle_client_event)
            self.current_task = None
            self.todo_visible = False
            self.last_assistant_snippet: str = ""
            self.last_plan_steps: int = 0

        async def on_mount(self):
            """Initialize on app startup."""
            self.title = "GLM-4.6 Anthropic MCP Client"
            self.sub_title = "OpenStack Policy Management Assistant"
            
            # Show welcome message
            self.chat_view.add_message(
                "System",
                f"🚀 Welcome to GLM-4.6 with OpenStack MCP Tools\n"
                f"Context: {GLM_CONFIG['context_window']:,} tokens | "
                f"Auto-summarize at {int(GLM_CONFIG['summarization_threshold']*100)}%",
                "yellow"
            )
            
            # Connect to MCP server
            self.status_bar.update("🔌 Connecting to MCP Server...")
            try:
                connected = await self.client.connect_mcp_server()
                if connected:
                    self.status_bar.update("✅ Connected to MCP Server")
                    tools_desc = self.client.get_tools_description()
                    self.chat_view.add_message("System", tools_desc, "green")
                    self._update_context_info()
                else:
                    self.status_bar.update("❌ Failed to connect to MCP Server")
                    self.chat_view.add_message(
                        "Error",
                        "Failed to connect to MCP server. Check if server is running.",
                        "red"
                    )
            except Exception as e:
                self.status_bar.update(f"❌ Connection error")
                self.chat_view.add_message("Error", f"Connection failed: {e}", "red")

        def compose(self):
            """Create the UI layout."""
            yield Header()
            yield Container(
                Horizontal(
                    ScrollableContainer(self.chat_view, id="chat_container"),
                    Vertical(
                        ScrollableContainer(self.events_view, id="events_container"),
                        ScrollableContainer(self.todo_view, id="todo_container"),
                        id="side_stack"
                    )
                ),
                Container(self.input_field, id="input_container"),
                Horizontal(
                    self.send_button,
                    self.clear_button,
                    self.cancel_button,
                    self.todo_toggle_button,
                    self.status_bar,
                    id="button_bar"
                ),
                self.context_info,
            )
            yield Footer()

        def _update_context_info(self):
            """Update context information display."""
            stats = self.client.context_manager.get_usage_stats()
            used_pct = self.client.context_manager.get_usage_percent()
            snippet = self._truncate(self.last_assistant_snippet or "", limit=100).replace("\n", " ⏎ ")
            plan_info = f" | Plan: {self.last_plan_steps} steps" if self.last_plan_steps else ""
            info = (
                f"📊 Tokens: {stats['total_tokens']:,} | "
                f"Context: {used_pct:.1f}% | Requests: {stats['requests_count']} | Tools: {stats['tool_calls_made']}" 
                f"{plan_info}\n"
                f"LLM: {snippet}"
            )
            self.context_info.update(info)

        def _truncate(self, text: str, limit: int = 1200) -> str:
            if text is None:
                return ""
            if len(text) <= limit:
                return text
            remaining = len(text) - limit
            return text[:limit] + f"\n… [truncated {remaining} chars]"

        def _pretty_json(self, data: Any) -> str:
            try:
                return json.dumps(data, indent=2)
            except Exception:
                return str(data)

        def _handle_client_event(self, event: Dict[str, Any]):
            et = event.get("type")
            if et == "user_message":
                # Already shown in chat; optionally mirror in events
                self.events_view.add_event("User", event.get("text", ""), color="white")
                # Reset last assistant snippet for next turn
                self.last_assistant_snippet = ""
                self._update_context_info()
            elif et == "usage":
                msg = f"Usage: {event.get('input_tokens',0):,} in + {event.get('output_tokens',0):,} out = {event.get('total',0):,}"
                self.events_view.add_event("📊 Token Usage", msg, color="magenta")
                self._update_context_info()
            elif et == "plan":
                # Clear previous plan rendering and show the new plan
                self.todo_view.clear()
                steps = event.get("steps", [])
                self.todo_view.show_plan(steps)
                self.last_plan_steps = len(steps)
                self._update_context_info()
            elif et == "hint":
                self.events_view.add_event("💡 Hint", event.get("message", ""), color="yellow")
                self._update_context_info()
            elif et == "tool_calls_start":
                it = event.get("iteration")
                cnt = event.get("count")
                self.events_view.add_event("🛠️ Tool Calls", f"Iteration {it}: Executing {cnt} call(s)", color="yellow")
                self._update_context_info()
            elif et == "tool_call":
                name = event.get("name", "")
                params = self._pretty_json(event.get("input", {}))
                self.events_view.add_event(f"➡️ Call: {name}", f"Parameters:\n{params}", color="cyan")
                self._update_context_info()
            elif et == "tool_result":
                name = event.get("name", "")
                res = self._truncate(str(event.get("result", "")))
                self.events_view.add_event(f"⬅️ Result: {name}", res, color="green")
                self._update_context_info()
            elif et == "todo_update":
                # Re-render todo list
                todos = event.get("todos", [])
                # Keep plan above and append TODOs
                self.todo_view.show_todos(todos)
                self._update_context_info()
            elif et == "assistant_text":
                # Mirror short assistant updates into events for quick scan
                txt = self._truncate(event.get("text", ""), limit=400)
                if txt.strip():
                    self.events_view.add_event("Assistant", txt, color="green")
                # Update bottom bar with most recent assistant text
                self.last_assistant_snippet = event.get("text", "") or ""
                self._update_context_info()
            elif et == "complete":
                iters = event.get("iterations")
                calls = event.get("tool_calls")
                self.events_view.add_event("✅ Complete", f"Iterations: {iters} | Tool calls: {calls}", color="green")
                # Ensure final TODO state is visible
                # Nothing else needed; updates already emitted on completion
                self._update_context_info()

        def action_toggle_todo(self):
            """Show/hide the TODO panel."""
            try:
                todo_container = self.query_one('#todo_container')
                self.todo_visible = not self.todo_visible
                todo_container.set_class(not self.todo_visible, 'hidden')
            except Exception:
                pass

        async def action_send_message(self):
            """Handle message send."""
            user_text = self.input_field.text.strip()
            if not user_text:
                return

            # Handle slash commands
            if user_text.startswith('/'):
                result = self.client._handle_slash_command(user_text)
                if result:
                    if '/context' in user_text or '/ctx' in user_text:
                        stats = self.client.context_manager.get_usage_stats()
                        self.chat_view.add_message("System", f"Context: {stats}", "yellow")
                    elif '/stats' in user_text:
                        stats = self.client.context_manager.get_usage_stats()
                        stats_text = "\n".join([f"{k}: {v}" for k, v in stats.items()])
                        self.chat_view.add_message("System", stats_text, "yellow")
                    self.input_field.text = ""
                    return

            # Add user message to chat
            self.chat_view.add_message("You", user_text)
            self.input_field.text = ""
            self.input_field.focus()

            # Update status
            self.loading = True
            self.status_bar.update("🤖 Thinking...")
            self.send_button.disabled = True
            self.cancel_button.disabled = False

            # Run in background to keep UI responsive
            async def _run_chat_task(prompt: str):
                try:
                    response = await self.client.chat_with_tools(prompt)
                    if response and response.strip():
                        self.chat_view.add_message("GLM-4.6", response)
                        self.last_response = response
                    else:
                        self.chat_view.add_message("System", "No response received.", "yellow")
                    self._update_context_info()
                    self.status_bar.update("✅ Ready")
                except asyncio.CancelledError:
                    self.chat_view.add_message("System", "Request cancelled.", "yellow")
                    self.status_bar.update("⏹️ Cancelled")
                    raise
                except Exception as e:
                    self.chat_view.add_message("Error", f"Error: {e}", "red")
                    self.status_bar.update("❌ Error occurred")
                finally:
                    self.loading = False
                    self.send_button.disabled = False
                    self.cancel_button.disabled = True
                    self.current_task = None

            # Cancel any previous task if somehow still running
            if self.current_task and not self.current_task.done():
                self.current_task.cancel()
            self.current_task = asyncio.create_task(_run_chat_task(user_text))

        def action_cancel(self):
            """Cancel the current running prompt."""
            if self.current_task and not self.current_task.done():
                self.current_task.cancel()
                self.status_bar.update("⏹️ Cancelling…")
            else:
                self.status_bar.update("ℹ️ Nothing to cancel")

        def action_clear_input(self):
            """Clear input area."""
            self.input_field.text = ""
            self.input_field.focus()

        def action_copy_last(self):
            """Copy last response to clipboard (show in status)."""
            if self.last_response:
                self.status_bar.update("📋 Last response ready to copy")
                self.chat_view.add_message("System", "Last response:", "yellow")
                self.chat_view.add_message("System", self.last_response, "dim")
            else:
                self.status_bar.update("⚠️ No response to copy")

        def action_show_context(self):
            """Show context usage."""
            stats = self.client.context_manager.get_usage_stats()
            used_pct = self.client.context_manager.get_usage_percent()
            context_text = (
                f"Context Window:\n"
                f"  Total Tokens: {stats['total_tokens']:,}\n"
                f"  Usage: {used_pct:.2f}%\n"
                f"  Input: {stats['total_input_tokens']:,}\n"
                f"  Output: {stats['total_output_tokens']:,}\n"
                f"  Requests: {stats['requests_count']}\n"
                f"  Tool Calls: {stats['tool_calls_made']}"
            )
            self.chat_view.add_message("Context", context_text, "cyan")
            self._update_context_info()

        def action_show_stats(self):
            """Show detailed statistics."""
            stats = self.client.context_manager.get_usage_stats()
            stats_text = (
                f"Session Statistics:\n"
                f"  Total Iterations: {self.client.total_iterations}\n"
                f"  Total Tool Calls: {self.client.tool_call_count}\n"
                f"  System Prompt: {stats['system_prompt_tokens']:,} tokens\n"
                f"  Tool Definitions: {stats['tool_definitions_tokens']:,} tokens\n"
                f"  Tool Results: {stats['tool_result_tokens']:,} tokens\n"
                f"  Avg Input/Request: {stats['avg_input_per_request']:.0f}\n"
                f"  Avg Output/Request: {stats['avg_output_per_request']:.0f}"
            )
            self.chat_view.add_message("Statistics", stats_text, "magenta")

        async def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button presses."""
            if event.button.id == "send":
                await self.action_send_message()
            elif event.button.id == "clear":
                self.action_clear_input()
            elif event.button.id == "cancel":
                self.action_cancel()
            elif event.button.id == "toggle_todo":
                self.action_toggle_todo()


# Environment setup
def setup_environment():
    """Set up environment variables if not already set."""
    if GLM_CONFIG["api_key"] == "YOUR_ZAI_API_KEY":
        console.print("[bold red]❌ Please set your ANTHROPIC_API_KEY environment variable![/]")
        console.print("[yellow]export ANTHROPIC_API_KEY='your_zai_api_key'[/]")
        sys.exit(1)


async def main():
    """Main entry point."""
    setup_environment()
    
    # Check for UI mode flag
    use_tui = "--tui" in sys.argv or "--ui" in sys.argv or os.environ.get("USE_TUI", "0") == "1"
    
    if use_tui and TEXTUAL_AVAILABLE:
        # Launch Textual UI
        console.print("[bold cyan]🚀 Launching Textual UI mode...[/bold cyan]")
        app = AgenticTUI()
        await app.run_async()
    elif use_tui and not TEXTUAL_AVAILABLE:
        console.print("[bold red]❌ Textual UI not available. Install with: pip install textual[/bold red]")
        console.print("[yellow]Falling back to terminal mode...[/yellow]\n")
        client = GLMAnthropicMCPClient()
        await client.start_chat()
    else:
        # Standard terminal mode
        client = GLMAnthropicMCPClient()
        await client.start_chat()


if __name__ == "__main__":
    asyncio.run(main())
