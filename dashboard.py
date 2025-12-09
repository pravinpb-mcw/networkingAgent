#!/usr/bin/env python3
"""
Network Agent Dashboard - Streamlit App
Integrates MCP Client Chatbot and Network Monitor with real-time insights
"""

import streamlit as st
import asyncio
import json
import time
import threading
import queue
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import concurrent.futures
import nest_asyncio
import warnings

# Apply nest_asyncio to handle nested event loops
nest_asyncio.apply()

# Suppress asyncio warnings that are common with Python 3.13 and async libraries
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
warnings.filterwarnings("ignore", message=".*Task.*was never awaited.*")
warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")
warnings.filterwarnings("ignore", message=".*_UnixSelectorEventLoop.*")
warnings.filterwarnings("ignore", message=".*call_exception_handler.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="asyncio")

# Fix for Windows Event Loop issues
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add server directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

# Import required modules
try:
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.chat_models import ChatZhipuAI
    from langchain_anthropic import ChatAnthropic
    # Fallback for mcp_use if not installed, assuming it might be a local wrapper or available package
    try:
        from mcp_use import MCPAgent, MCPClient
    except ImportError:
        # Mocking mcp_use if it's missing to prevent crash during import check, 
        # but it will fail later if not installed.
        # Ideally we should install it.
        pass
    
    # Import MCP tools
    from server.get_device_loss_and_latency_history import get_device_loss_and_latency_history
    from server.get_network_traffic import get_network_traffic
    from server.get_network_events import get_network_events
    from server.get_network_clients import get_network_clients
    from server.get_organizations import get_organizations
    
    IMPORTS_SUCCESS = True
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Please install required packages: pip install streamlit plotly pandas nest-asyncio langchain-google-genai mcp-use")
    IMPORTS_SUCCESS = False

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Network Agent Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .status-normal { border-left-color: #28a745; }
    .status-warning { border-left-color: #ffc107; }
    .status-critical { border-left-color: #dc3545; }
    .chat-message {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .user-message {
        background: #e3f2fd;
        border-left: 3px solid #2196f3;
    }
    .assistant-message {
        background: #f3e5f5;
        border-left: 3px solid #9c27b0;
    }
    .api-call {
        background: #fff3e0;
        border: 1px solid #ff9800;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

class NetworkDashboard:
    """Main dashboard class that manages both MCP client and network monitor"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.zhipuai_api_key = os.getenv("ZHIPUAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_base_url = os.getenv("ANTHROPIC_BASE_URL")
        self.mcp_client = None
        self.mcp_agent = None
        self.monitoring_data = []
        self.api_calls = []
        self.chat_history = []
        self.monitoring_active = False
        self.monitor_thread = None
        self.data_queue = queue.Queue()
        self._executor = None
        
        # Initialize components
        self._init_mcp_client()
        self._init_llm()
        self._init_executor()
    
    def _init_executor(self):
        """Initialize thread pool executor for async operations"""
        try:
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        except Exception as e:
            st.error(f"Failed to initialize executor: {e}")
    
    def _init_mcp_client(self):
        """Initialize MCP client connection"""
        try:
            # Use absolute path relative to this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(script_dir, "mcp-inspector-config.json")
            
            if os.path.exists(config_file):
                # Ensure mcp_use is imported
                from mcp_use import MCPClient
                self.mcp_client = MCPClient.from_config_file(config_file)
                st.success("MCP Client connected successfully")
            else:
                st.error(f"MCP config file not found at: {config_file}")
        except Exception as e:
            st.error(f"Failed to initialize MCP client: {e}")
    
    def _init_llm(self):
        """Initialize LLM (Gemini, ZhipuAI, or Anthropic)"""
        try:
            self.llm = None
            
            # Check for ZhipuAI (GLM-4)
            if self.zhipuai_api_key:
                try:
                    self.llm = ChatZhipuAI(
                        model="glm-4.5",
                        api_key=self.zhipuai_api_key,
                        temperature=0.5,
                    )
                    st.success("ZhipuAI (GLM-4.5) LLM initialized successfully")
                    return
                except Exception as e:
                    st.warning(f"Failed to initialize ZhipuAI: {e}")

            # Check for Anthropic (Prioritized over Gemini due to quota issues)
            if self.anthropic_api_key:
                try:
                    # Check if using custom base URL (e.g. for GLM-4.5 via Anthropic adapter)
                    if self.anthropic_base_url:
                        self.llm = ChatAnthropic(
                            model="glm-4.5",
                            anthropic_api_key=self.anthropic_api_key,
                            anthropic_api_url=self.anthropic_base_url,
                            temperature=0.3,
                            max_tokens=4096
                        )
                        st.success(f"GLM-4.5 (via Anthropic SDK) initialized successfully")
                    else:
                        self.llm = ChatAnthropic(
                            model="claude-3-sonnet-20240229",
                            anthropic_api_key=self.anthropic_api_key,
                            temperature=0.3
                        )
                        st.success("Anthropic Claude LLM initialized successfully")
                    return
                except Exception as e:
                    st.warning(f"Failed to initialize Anthropic: {e}")

            # Check for Gemini
            if self.gemini_api_key:
                try:
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-2.5-flash",
                        google_api_key=self.gemini_api_key,
                        temperature=0.3,
                        max_tokens=2048
                    )
                    st.success("Gemini LLM initialized successfully")
                    return
                except Exception as e:
                    st.warning(f"Failed to initialize Gemini: {e}")

            if not self.llm:
                st.error("No valid API keys found for ZhipuAI, Gemini, or Anthropic. Please check your .env file.")
                
        except Exception as e:
            st.error(f"Failed to initialize LLM: {e}")
    
    def _create_mcp_agent(self):
        """Create MCP agent for chat functionality"""
        try:
            if self.mcp_client and self.llm:
                from mcp_use import MCPAgent
                # Create agent with proper configuration
                self.mcp_agent = MCPAgent(
                    llm=self.llm,
                    client=self.mcp_client,
                    max_steps=10,
                    memory_enabled=True,
                    verbose=False  # Disable verbose to reduce noise
                )
                return True
            return False
        except Exception as e:
            st.error(f"Failed to create MCP agent: {e}")
            return False
    
    def _reset_mcp_agent(self):
        """Reset MCP agent to handle connection issues"""
        try:
            if self.mcp_agent:
                # Clean up existing agent
                try:
                    if hasattr(self.mcp_agent, 'aclose'):
                        # Run cleanup in isolated loop
                        self._run_async_operation_safe(self.mcp_agent.aclose())
                except Exception as cleanup_error:
                    print(f"Agent cleanup error: {cleanup_error}")
                
                self.mcp_agent = None
            
            # Recreate the agent
            return self._create_mcp_agent()
        except Exception as e:
            st.error(f"Failed to reset MCP agent: {e}")
            return False
    
    def _get_or_create_event_loop(self):
        """Deprecated - no longer needed with asyncio.run() approach"""
        # This method is kept for compatibility but no longer used
        pass
    
    async def _call_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call MCP tool and track the API call"""
        start_time = time.time()
        
        try:
            # Track API call
            api_call = {
                'timestamp': datetime.now().isoformat(),
                'tool': tool_name,
                'status': 'started',
                'parameters': kwargs
            }
            self.api_calls.append(api_call)
            
            # Call the appropriate tool
            if tool_name == 'get_device_loss_and_latency_history':
                response = await get_device_loss_and_latency_history()
            elif tool_name == 'get_network_traffic':
                response = await get_network_traffic()
            elif tool_name == 'get_network_events':
                response = await get_network_events()
            elif tool_name == 'get_network_clients':
                response = await get_network_clients()
            elif tool_name == 'get_organizations':
                response = await get_organizations()
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # Update API call status
            api_call['status'] = 'completed'
            api_call['duration'] = time.time() - start_time
            api_call['response'] = str(response)
            
            return response
            
        except Exception as e:
            # Update API call status
            api_call['status'] = 'failed'
            api_call['error'] = str(e)
            api_call['duration'] = time.time() - start_time
            raise e
    
    def chat_with_mcp(self, user_message: str, skip_user_history: bool = False) -> str:
        """Chat with MCP agent and track API calls"""
        try:
            # Add user message to chat history if not skipped
            if not skip_user_history:
                self.chat_history.append({
                    'role': 'user',
                    'content': user_message,
                    'timestamp': datetime.now().isoformat()
                })
            
            print(f"Sending message to agent: {user_message}")
            
            # Define the async operation to run in a fresh loop
            def run_in_thread(message):
                import asyncio
                
                async def run_agent_task():
                    # Re-initialize everything within the async context to ensure loop compatibility
                    from mcp_use import MCPAgent, MCPClient
                    
                    # Load client config
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    config_file = os.path.join(script_dir, "mcp-inspector-config.json")
                    
                    if not os.path.exists(config_file):
                        return f"Configuration file not found: {config_file}"
                    
                    client = MCPClient.from_config_file(config_file)
                    
                    # Create agent
                    agent = MCPAgent(
                        llm=self.llm,
                        client=client,
                        max_steps=10,
                        memory_enabled=True,
                        verbose=True
                    )
                    
                    # Run agent
                    return await agent.run(message)

                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(run_agent_task())
                finally:
                    loop.close()

            # Run the async task in a separate thread to avoid loop conflicts
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_thread, user_message)
                raw_response = future.result(timeout=120) # 2 minute timeout
            
            print(f"Received response from agent: {raw_response}")
            
            # Convert to string if needed
            if raw_response is not None and not isinstance(raw_response, str):
                response = str(raw_response)
            else:
                response = raw_response

            # Check if response is valid
            if response and len(response.strip()) > 0:
                # Add assistant response to chat history
                self.chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().isoformat()
                })
                return response
            else:
                error_msg = "No response received from agent"
                self.chat_history.append({
                    'role': 'assistant',
                    'content': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
                return error_msg
            
        except Exception as e:
            error_msg = f"Chat error: {str(e)}"
            print(error_msg)
            self.chat_history.append({
                'role': 'assistant',
                'content': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            return error_msg
    
    def _run_async_operation_safe(self, coro):
        """Run async operation safely using asyncio.run() in a separate thread"""
        try:
            # Use the executor to run async operations in a separate thread
            if self._executor:
                future = self._executor.submit(self._run_with_asyncio_run, coro)
                return future.result(timeout=60)  # 60 second timeout
            else:
                # Fallback to direct execution
                return self._run_with_asyncio_run(coro)
        except Exception as e:
            st.error(f"Async operation failed: {e}")
            return f"Operation failed: {str(e)}"
    
    def _run_with_asyncio_run(self, coro):
        """Run coroutine using asyncio.run() for clean, isolated execution"""
        try:
            import inspect
            if inspect.iscoroutine(coro) or inspect.isawaitable(coro):
                # Use asyncio.run() which automatically handles loop creation and cleanup
                result = asyncio.run(coro)
                return result
            else:
                # It's already a result (synchronous return)
                return coro
        except Exception as e:
            print(f"Async execution failed: {e}")
            return f"Execution failed: {str(e)}"
    
    async def _collect_monitoring_data_async(self):
        """Collect all monitoring data in parallel"""
        try:
            results = await asyncio.gather(
                self._call_mcp_tool('get_device_loss_and_latency_history'),
                self._call_mcp_tool('get_network_traffic'),
                self._call_mcp_tool('get_network_events'),
                self._call_mcp_tool('get_network_clients'),
                return_exceptions=True
            )
            return results
        except Exception as e:
            print(f"Error in parallel collection: {e}")
            return [None, None, None, None]

    def run_network_monitor_cycle(self):
        """Run one network monitoring cycle"""
        try:
            print("Starting monitoring cycle...")
            # Collect data from all tools using async wrapper
            data = {}
            
            print("Collecting all network data in parallel...")
            # Run all data collection in parallel
            results = self._run_async_operation_safe(self._collect_monitoring_data_async())
            
            if not results or not isinstance(results, list) or len(results) < 4:
                print("Failed to collect data or partial results")
                results = [None, None, None, None]

            performance_response, traffic_response, events_response, clients_response = results[0], results[1], results[2], results[3]
            
            # Process performance data
            if performance_response and not isinstance(performance_response, Exception) and hasattr(performance_response, '__iter__') and len(performance_response) > 0:
                try:
                    data['performance'] = json.loads(performance_response[0].text)
                    print(f"Performance data collected: {len(data['performance'].get('data', []))} points")
                except Exception as e:
                    print(f"Error parsing performance response: {e}")
                    data['performance'] = {'data': [], 'error': str(e)}
            else:
                data['performance'] = {'data': [], 'error': "Failed to fetch"}
            
            # Process traffic data
            if traffic_response and not isinstance(traffic_response, Exception) and hasattr(traffic_response, '__iter__') and len(traffic_response) > 0:
                try:
                    data['traffic'] = json.loads(traffic_response[0].text)
                    print(f"Traffic data collected: {len(data['traffic'].get('data', []))} points")
                except Exception as e:
                    print(f"Error parsing traffic response: {e}")
                    data['traffic'] = {'data': [], 'error': str(e)}
            else:
                data['traffic'] = {'data': [], 'error': "Failed to fetch"}
            
            # Process events data
            if events_response and not isinstance(events_response, Exception) and hasattr(events_response, '__iter__') and len(events_response) > 0:
                try:
                    data['events'] = json.loads(events_response[0].text)
                    print(f"Events data collected: {len(data['events'].get('data', []))} points")
                except Exception as e:
                    print(f"Error parsing events response: {e}")
                    data['events'] = {'data': [], 'error': str(e)}
            else:
                data['events'] = {'data': [], 'error': "Failed to fetch"}
            
            # Process clients data
            if clients_response and not isinstance(clients_response, Exception) and hasattr(clients_response, '__iter__') and len(clients_response) > 0:
                try:
                    data['clients'] = json.loads(clients_response[0].text)
                    print(f"Clients data collected: {len(data['clients'].get('data', []))} points")
                except Exception as e:
                    print(f"Error parsing clients response: {e}")
                    data['clients'] = {'data': [], 'error': str(e)}
            else:
                data['clients'] = {'data': [], 'error': "Failed to fetch"}
            
            # Analyze data and get insights
            print("Getting AI insights...")
            insights = self._run_async_operation_safe(self._get_network_insights(data))
            print(f"Insights generated: {insights[:100]}...")
            
            # Store monitoring data
            monitoring_entry = {
                'timestamp': datetime.now().isoformat(),
                'data': data,
                'insights': insights
            }
            
            self.monitoring_data.append(monitoring_entry)
            print(f"Monitoring data stored. Total entries: {len(self.monitoring_data)}")
            
            # Keep only last 100 entries
            if len(self.monitoring_data) > 100:
                self.monitoring_data = self.monitoring_data[-100:]
            
            # Put data in queue for real-time updates
            self.data_queue.put(monitoring_entry)
            print("Monitoring cycle completed successfully")
            
        except Exception as e:
            print(f"Monitoring cycle error: {e}")
            import traceback
            traceback.print_exc()
            # Add error entry to monitoring data
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'data': {},
                'insights': f"Error during monitoring: {str(e)}",
                'error': True
            }
            self.monitoring_data.append(error_entry)
    
    async def _get_network_insights(self, data: Dict[str, Any]) -> str:
        """Get AI insights on network data"""
        try:
            if not self.llm:
                return "LLM not available"
            
            # Create summary for LLM
            summary = self._create_data_summary(data)
            
            system_prompt = """You are a network performance analyst. Analyze the network data and provide concise insights.
            Focus on:
            - Performance issues
            - Traffic patterns
            - Security concerns
            - Recommendations
            
            Keep response under 200 words."""
            
            from langchain_core.messages import SystemMessage, HumanMessage
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analyze this network data:\n\n{summary}")
            ]
            
            # Try synchronous LLM call first
            try:
                # Use invoke instead of generate for newer LangChain versions and better compatibility
                response = self.llm.invoke(messages)
                if hasattr(response, 'content'):
                    return response.content
                return str(response)
            except Exception as sync_error:
                print(f"Sync LLM call failed: {sync_error}, trying async...")
                # Fallback to async wrapper
                response = self._run_async_operation_safe(self.llm.ainvoke(messages))
                if hasattr(response, 'content'):
                    return response.content
                return str(response)
            
        except Exception as e:
            return f"Unable to get insights: {str(e)}"
    
    def _create_data_summary(self, data: Dict[str, Any]) -> str:
        """Create a summary of network data for LLM analysis"""
        summary_parts = []
        
        if 'performance' in data:
            perf = data['performance']
            if 'data' in perf and isinstance(perf['data'], list):
                summary_parts.append(f"Performance data: {len(perf['data'])} measurements")
        
        if 'traffic' in data:
            traffic = data['traffic']
            if 'data' in traffic and isinstance(traffic['data'], list):
                summary_parts.append(f"Traffic data: {len(traffic['data'])} entries")
        
        if 'events' in data:
            events = data['events']
            if 'data' in events and isinstance(events['data'], list):
                summary_parts.append(f"Network events: {len(events['data'])} events")
        
        if 'clients' in data:
            clients = data['clients']
            if 'data' in clients and isinstance(clients['data'], list):
                summary_parts.append(f"Connected clients: {len(clients['data'])} devices")
        
        return "\n".join(summary_parts) if summary_parts else "No data available"
    
    def start_monitoring(self, interval_seconds: int = 3):
        """Start background monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            print(f"Starting monitoring with {interval_seconds} second interval")
            
            def monitor_loop():
                cycle_count = 0
                while self.monitoring_active:
                    try:
                        cycle_count += 1
                        print(f"Running monitoring cycle {cycle_count}")
                        # Run monitoring cycle
                        self.run_network_monitor_cycle()
                        print(f"Monitoring cycle {cycle_count} completed")
                        time.sleep(interval_seconds)
                    except Exception as e:
                        # Don't use st.error in background thread
                        print(f"Monitoring error in cycle {cycle_count}: {e}")
                        time.sleep(5)  # Wait 5 seconds on error
            
            self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("Monitoring thread started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_monitoring()
            if self._executor:
                self._executor.shutdown(wait=True)
            
            # Additional cleanup for asyncio tasks and loops
            import gc
            import warnings
            
            # Suppress asyncio warnings during cleanup
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*was never awaited")
                warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*")
                
                # Force garbage collection to clean up lingering async objects
                gc.collect()
                
        except Exception as e:
            print(f"Cleanup error: {e}")

def main():
    """Main dashboard function"""
    st.markdown('<div class="main-header"><h1> Network Agent Dashboard</h1><p>MCP Client Chatbot + Network Monitor Integration</p></div>', unsafe_allow_html=True)
    
    if not IMPORTS_SUCCESS:
        st.stop()
    
    # Initialize dashboard
    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = NetworkDashboard()
    
    dashboard = st.session_state.dashboard
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Dashboard Controls")
        
        # Monitoring controls
        st.subheader(" Network Monitor")
        if st.button("Start Monitoring", type="primary"):
            dashboard.start_monitoring()
            st.success("Monitoring started!")
        
        if st.button("Stop Monitoring"):
            dashboard.stop_monitoring()
            st.info("Monitoring stopped!")
        
        # Status indicators
        st.subheader("Status")
        st.metric("Monitoring Active", "Yes" if dashboard.monitoring_active else "No")
        st.metric("Data Points", len(dashboard.monitoring_data))
        
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["MCP Chatbot", "Network Monitor", "Analytics"])
    
    with tab1:
        st.header("🤖 MCP Client Chatbot")
        
        # Instructional Text
        st.markdown("""
        I can help you analyze your Meraki network using real-time data. 
        
        **What I can do:**
        *   **Monitor Performance:** Check for packet loss, latency, and connectivity issues.
        *   **Analyze Traffic:** Identify top applications and bandwidth usage.
        *   **Track Clients:** List connected devices and their activity.
        *   **Security Insights:** Review network events for anomalies.
        
        👇 **Click a Quick Command below or type your own question:**
        """)
        
        # Quick Commands Section
        st.subheader("⚡ Quick Commands")
        qc_col1, qc_col2, qc_col3 = st.columns(3)
        
        quick_command = None
        
        with qc_col1:
            if st.button("📉 Check Performance", help="Check for packet loss and latency issues"):
                quick_command = "Check for any device loss or latency issues in the last 2 hours"
            if st.button("👥 Top Clients", help="List top clients by usage"):
                quick_command = "List the top network clients by usage"
                
        with qc_col2:
            if st.button("🚦 Analyze Traffic", help="Analyze traffic patterns"):
                quick_command = "Analyze the network traffic patterns and identify top applications"
            if st.button("🔔 Recent Events", help="Show recent network events"):
                quick_command = "Show me the most recent network events"
                
        with qc_col3:
            if st.button("🛡️ Security Check", help="Analyze for security threats"):
                quick_command = "Analyze network events for any security threats or anomalies"
            if st.button("🏢 Org Info", help="Get organization details"):
                quick_command = "Get information about the Meraki organization"

        # Handle Quick Command Execution
        if quick_command:
            # Add user message to history immediately
            dashboard.chat_history.append({
                'role': 'user',
                'content': quick_command,
                'timestamp': datetime.now().isoformat()
            })
            
            with st.spinner(f"🤖 Processing: {quick_command}..."):
                # Call MCP directly (it will add the assistant response)
                dashboard.chat_with_mcp(quick_command, skip_user_history=True)
                st.rerun()

        st.divider()

        # Chat interface with custom styling
        st.markdown("""
        <style>
        .stChatMessage {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .stChatMessage[data-testid="stChatMessageUser"] {
            background-color: #e3f2fd;
            border-left: 5px solid #2196f3;
        }
        .stChatMessage[data-testid="stChatMessageAssistant"] {
            background-color: #f3e5f5;
            border-left: 5px solid #9c27b0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Available tools info
        with st.expander("🔧 Available MCP Tools"):
            st.markdown("""
            - **get_network_clients** - Get connected devices
            - **get_network_traffic** - Analyze traffic patterns
            - **get_device_loss_and_latency_history** - Get performance metrics
            - **get_organization_vpn_stats** - Get VPN statistics
            - **get_network_events** - Get network events
            """)

        # Clear chat button
        if dashboard.chat_history:
            if st.button("🗑️ Clear Chat History"):
                dashboard.chat_history.clear()
                st.rerun()

        # Display chat history using Streamlit's native chat components
        chat_container = st.container()
        with chat_container:
            if not dashboard.chat_history:
                st.info("👋 Chat history is empty. Start a conversation!")
            
            for message in dashboard.chat_history:
                with st.chat_message(message['role']):
                    st.markdown(message['content'])

        # Chat Input using st.chat_input (The "Real" Chatbox)
        if prompt := st.chat_input("Ask about your network..."):
            # Add user message to history
            dashboard.chat_history.append({
                'role': 'user',
                'content': prompt,
                'timestamp': datetime.now().isoformat()
            })
            
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = dashboard.chat_with_mcp(prompt, skip_user_history=True)
                    st.markdown(response)
            
            # Rerun to update history properly
            st.rerun()
    
    with tab2:
        st.header("📊 Network Monitor")
        
        # Monitoring status
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", "Active" if dashboard.monitoring_active else "Inactive")
        with col2:
            st.metric("Data Points", len(dashboard.monitoring_data))
        with col3:
            if dashboard.monitoring_data:
                last_entry = dashboard.monitoring_data[-1]
                if last_entry.get('error', False):
                    st.metric("Last Update", "Error")
                else:
                    st.metric("Last Update", last_entry['timestamp'][:19])
            else:
                st.metric("Last Update", "Never")
        
        # Latest monitoring data
        if dashboard.monitoring_data:
            latest = dashboard.monitoring_data[-1]
            
            st.subheader("Latest Insights")
            st.markdown(f"**Timestamp:** {latest['timestamp'][:19]}")
            
            # Check if this is an error entry
            if latest.get('error', False):
                st.error(f"Monitoring Error: {latest.get('insights', 'Unknown error')}")
            else:
                # Display insights
                if 'insights' in latest:
                    st.info(latest['insights'])
                
                # Display data summary
                st.subheader("Data Summary")
                
                data = latest.get('data', {})
                
                # Performance metrics
                if 'performance' in data:
                    perf = data['performance']
                    if 'data' in perf and isinstance(perf['data'], list) and perf['data']:
                        perf_data = perf['data'][0]  # Get first data point
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Latency", f"{perf_data.get('latencyMs', 'N/A')}ms")
                        with col2:
                            st.metric("Packet Loss", f"{perf_data.get('lossPercent', 'N/A')}%")
                        with col3:
                            st.metric("Jitter", f"{perf_data.get('jitter', 'N/A')}ms")
                        with col4:
                            st.metric("Goodput", f"{perf_data.get('goodput', 'N/A')}")
                
                # Traffic data
                if 'traffic' in data:
                    traffic = data['traffic']
                    if 'data' in traffic and isinstance(traffic['data'], list):
                        st.subheader("🚦 Network Traffic")
                        st.write(f"Traffic entries: {len(traffic['data'])}")
                
                # Events data
                if 'events' in data:
                    events = data['events']
                    if 'data' in events and isinstance(events['data'], list):
                        st.subheader("📢 Network Events")
                        st.write(f"Recent events: {len(events['data'])}")
                
                # Clients data
                if 'clients' in data:
                    clients = data['clients']
                    if 'data' in clients and isinstance(clients['data'], list):
                        st.subheader("💻 Connected Clients")
                        st.write(f"Active devices: {len(clients['data'])}")
        
        else:
            st.info("No monitoring data available. Start monitoring to see data.")
    
    with tab3:
        st.header("Analytics Dashboard")
        
        if len(dashboard.monitoring_data) > 1:
            # Filter out error entries
            valid_data = [entry for entry in dashboard.monitoring_data if not entry.get('error', False)]
            
            if len(valid_data) > 1:
                # Create time series data
                timestamps = [entry['timestamp'] for entry in valid_data]
                
                # Performance trends chart
                st.subheader("Performance Trends")
                
                # Extract performance data
                perf_data = []
                for entry in valid_data:
                    if 'data' in entry and 'performance' in entry['data']:
                        perf = entry['data']['performance']
                        if 'data' in perf and isinstance(perf['data'], list) and perf['data']:
                            data_point = perf['data'][0]
                            perf_data.append({
                                'timestamp': entry['timestamp'],
                                'latency': data_point.get('latencyMs', 0),
                                'loss': data_point.get('lossPercent', 0),
                                'jitter': data_point.get('jitter', 0)
                            })
                
                if perf_data:
                    perf_df = pd.DataFrame(perf_data)
                    perf_df['timestamp'] = pd.to_datetime(perf_df['timestamp'])
                    
                    # Create performance chart
                    fig = make_subplots(
                        rows=3, cols=1,
                        subplot_titles=('Latency (ms)', 'Packet Loss (%)', 'Jitter (ms)'),
                        vertical_spacing=0.1
                    )
                    
                    fig.add_trace(
                        go.Scatter(x=perf_df['timestamp'], y=perf_df['latency'], name='Latency'),
                        row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=perf_df['timestamp'], y=perf_df['loss'], name='Packet Loss'),
                        row=2, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=perf_df['timestamp'], y=perf_df['jitter'], name='Jitter'),
                        row=3, col=1
                    )
                    
                    fig.update_layout(height=600, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Data volume chart
                st.subheader("📊 Data Volume Trends")
                
                # Count data points over time
                data_counts = []
                for entry in valid_data:
                    data_counts.append({
                        'timestamp': entry['timestamp'],
                        'total_entries': sum([
                            len(entry['data'].get(key, {}).get('data', [])) 
                            for key in ['performance', 'traffic', 'events', 'clients']
                            if key in entry['data']
                        ])
                    })
                
                if data_counts:
                    counts_df = pd.DataFrame(data_counts)
                    counts_df['timestamp'] = pd.to_datetime(counts_df['timestamp'])
                    
                    fig = px.line(counts_df, x='timestamp', y='total_entries', 
                                title='Total Data Entries Over Time')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Need more valid monitoring data for analytics. Start monitoring to see trends.")
        else:
            st.info("Need more monitoring data for analytics. Start monitoring to see trends.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Network Agent Dashboard** - Powered by MCP, Gemini LLM, and Streamlit")
    
    # Auto-refresh for real-time updates
    if dashboard.monitoring_active:
        time.sleep(3)
        st.rerun()

    # Cleanup on exit
    import atexit
    atexit.register(dashboard.cleanup)

if __name__ == "__main__":
    main()
