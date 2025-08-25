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

# Add server directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

# Import required modules
try:
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI
    from mcp_use import MCPAgent, MCPClient
    
    # Import MCP tools
    from server.get_device_loss_and_latency_history import get_device_loss_and_latency_history
    from server.get_network_traffic import get_network_traffic
    from server.get_network_events import get_network_events
    from server.get_network_clients import get_network_clients
    from server.get_network_group_policies import get_network_group_policies
    from server.get_organizations import get_organizations
    
    # Import configuration tools
    from server.create_network_wireless_settings import create_network_wireless_settings

    
    IMPORTS_SUCCESS = True
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Please install required packages: pip install streamlit plotly pandas nest-asyncio")
    IMPORTS_SUCCESS = False

# Load environment variables
load_dotenv()

# Import and setup configuration
try:
    from config import setup_environment
    setup_environment()
except ImportError:
    # Set basic defaults if config.py is not available
    os.environ.setdefault("USE_MOCK", "true")
    os.environ.setdefault("BASE_URL", "http://127.0.0.1:5000")

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
    
    /* Make dropdowns more obvious */
    .stSelectbox > div > div {
        border: 2px solid #1f77b4 !important;
        border-radius: 8px !important;
        background: #f8f9fa !important;
        cursor: pointer !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #ff7f0e !important;
        background: #e3f2fd !important;
        box-shadow: 0 2px 8px rgba(31, 119, 180, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

class NetworkDashboard:
    """Main dashboard class that manages both MCP client and network monitor"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
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
            config_file = "mcp-inspector-config.json"
            if os.path.exists(config_file):
                self.mcp_client = MCPClient.from_config_file(config_file)
                st.success("MCP Client connected successfully")
            else:
                st.error("MCP config file not found")
        except Exception as e:
            st.error(f"Failed to initialize MCP client: {e}")
    
    def _init_llm(self):
        """Initialize Gemini LLM"""
        try:
            if self.gemini_api_key:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=self.gemini_api_key,
                    temperature=0.3,
                    max_tokens=2048
                )
                st.success("Gemini LLM initialized successfully")
            else:
                st.error("GEMINI_API_KEY not found in .env file")
        except Exception as e:
            st.error(f"Failed to initialize LLM: {e}")
    
    def _create_mcp_agent(self):
        """Create MCP agent for chat functionality"""
        try:
            if self.mcp_client and self.llm:
                # Create agent with proper configuration
                self.mcp_agent = MCPAgent(
                    llm=self.llm,
                    client=self.mcp_client,
                    max_steps=10,
                    memory_enabled=True,
                    verbose=False,  # Disable verbose to reduce noise
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
            elif tool_name == 'get_network_group_policies':
                response = await get_network_group_policies()
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
    
    def chat_with_mcp(self, user_message: str) -> str:
        """Chat with MCP agent and track API calls"""
        try:
            if not self.mcp_agent:
                if not self._create_mcp_agent():
                    return "Failed to create MCP agent"
            
            # Add user message to chat history
            self.chat_history.append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Get response from agent using improved async wrapper
            response = self._run_async_operation_safe(self.mcp_agent.run(user_message))
            
            # Check if response is valid
            if response and isinstance(response, str) and len(response.strip()) > 0:
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
            # Use asyncio.run() which automatically handles loop creation and cleanup
            result = asyncio.run(coro)
            return result
        except Exception as e:
            print(f"Async execution failed: {e}")
            return f"Execution failed: {str(e)}"
    
    def run_network_monitor_cycle(self):
        """Run one network monitoring cycle"""
        try:
            print("Starting monitoring cycle...")
            # Collect data from all tools using async wrapper
            data = {}
            
            # Get performance data
            print("Getting performance data...")
            performance_response = self._run_async_operation_safe(self._call_mcp_tool('get_device_loss_and_latency_history'))
            if performance_response and hasattr(performance_response, '__iter__') and len(performance_response) > 0:
                try:
                    data['performance'] = json.loads(performance_response[0].text)
                    print(f"Performance data collected: {len(data['performance'].get('data', []))} points")
                except Exception as e:
                    print(f"Error parsing performance response: {e}")
                    data['performance'] = {'data': [], 'error': str(e)}
            
            # Get traffic data
            print("Getting traffic data...")
            traffic_response = self._run_async_operation_safe(self._call_mcp_tool('get_network_traffic'))
            if traffic_response and hasattr(traffic_response, '__iter__') and len(traffic_response) > 0:
                try:
                    data['traffic'] = json.loads(traffic_response[0].text)
                    print(f"Traffic data collected: {len(data['traffic'].get('data', []))} points")
                except Exception as e:
                    print(f"Error parsing traffic response: {e}")
                    data['traffic'] = {'data': [], 'error': str(e)}
            
            # Get events data
            print("Getting events data...")
            events_response = self._run_async_operation_safe(self._call_mcp_tool('get_network_events'))
            if events_response and hasattr(events_response, '__iter__') and len(events_response) > 0:
                try:
                    data['events'] = json.loads(events_response[0].text)
                    print(f"Events data collected: {len(data['events'].get('data', []))} points")
                except Exception as e:
                    print(f"Error parsing events response: {e}")
                    data['events'] = {'data': [], 'error': str(e)}
            
            # Get clients data
            print("Getting clients data...")
            clients_response = self._run_async_operation_safe(self._call_mcp_tool('get_network_clients'))
            if clients_response and hasattr(clients_response, '__iter__') and len(clients_response) > 0:
                try:
                    data['clients'] = json.loads(clients_response[0].text)
                    print(f"Clients data collected: {len(data['clients'].get('data', []))} points")
                except Exception as e:
                    print(f"Error parsing clients response: {e}")
                    data['clients'] = {'data': [], 'error': str(e)}
            
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
                response = self.llm.generate([messages])
                if hasattr(response, 'generations') and response.generations:
                    return response.generations[0][0].text
            except Exception as sync_error:
                print(f"Sync LLM call failed: {sync_error}, trying async...")
                # Fallback to async wrapper
                response = self._run_async_operation_safe(self.llm.agenerate([messages]))
                if hasattr(response, 'generations') and response.generations:
                    return response.generations[0][0].text
                else:
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
    
    def start_monitoring(self, interval_minutes: int = 1):
        """Start background monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            print(f"Starting monitoring with {interval_minutes} minute interval")
            
            def monitor_loop():
                cycle_count = 0
                while self.monitoring_active:
                    try:
                        cycle_count += 1
                        print(f"Running monitoring cycle {cycle_count}")
                        # Run monitoring cycle
                        self.run_network_monitor_cycle()
                        print(f"Monitoring cycle {cycle_count} completed")
                        time.sleep(interval_minutes * 60)
                    except Exception as e:
                        # Don't use st.error in background thread
                        print(f"Monitoring error in cycle {cycle_count}: {e}")
                        time.sleep(60)  # Wait 1 minute on error
            
            self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("Monitoring thread started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def get_available_tools(self):
        """Get available tools from MCP server"""
        try:
            if self.mcp_client and hasattr(self.mcp_client, 'sessions'):
                tools = []
                for session_name, session in self.mcp_client.sessions.items():
                    if hasattr(session, 'tools') and session.tools:
                        for tool in session.tools:
                            tools.append({
                                'name': tool.name,
                                'description': tool.description,
                                'session': session_name
                            })
                return tools
            return []
        except Exception as e:
            print(f"Error getting tools: {e}")
            return []
    
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
    tab1, tab2, tab3, tab4 = st.tabs(["MCP Chatbot", "Network Monitor", "Analytics", "Network Configuration"])
    
    with tab1:
        st.header("MCP Client Chatbot")
        st.info("Chat with the MCP agent to analyze network data using available tools")
        
        # Chat interface with custom styling
        st.markdown("""
        <style>
        .user-message {
            background-color: #02101b;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
            border-left: 4px solid #2196f3;
        }
        .assistant-message {
            background-color: #0f0611;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
            border-left: 4px solid #9c27b0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        chat_container = st.container()
        
        with chat_container:
            # Display chat history
            for message in dashboard.chat_history:
                if message['role'] == 'user':
                    st.markdown(f'<div class="user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="assistant-message"><strong>Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        
        # Chat input with auto-clear functionality
        # Initialize chat input counter for unique keys
        if 'chat_input_counter' not in st.session_state:
            st.session_state.chat_input_counter = 0
        
        user_input = st.text_input(
            "Ask about your network (press Enter to send):", 
            key=f"chat_input_{st.session_state.chat_input_counter}"
        )
        
        # JavaScript to handle Enter key
        st.markdown("""
        <script>
        const input = document.querySelector('input[data-testid="stTextInput"]');
        if (input) {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    // Find and click the Send button
                    const sendButton = document.querySelector('button[kind="primary"]');
                    if (sendButton) {
                        sendButton.click();
                    }
                }
            });
        }
        </script>
        """, unsafe_allow_html=True)
        
        # Send and Clear buttons
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if st.button("Send", type="primary"):
                if user_input.strip():
                    with st.spinner("Getting response..."):
                        response = dashboard.chat_with_mcp(user_input.strip())
                        # Clear input by incrementing counter (creates new input with empty value)
                        st.session_state.chat_input_counter += 1
                        st.rerun()
        
        with col2:
            if st.button("🗑️", help="Clear chat history"):
                dashboard.chat_history.clear()
                st.rerun()
        
        # Available tools info
        with st.expander("🔧 Available MCP Tools"):
            # Try to get tools dynamically from MCP server
            try:
                if dashboard.mcp_client and hasattr(dashboard.mcp_client, 'sessions'):
                    # Get tools from MCP client sessions
                    tools_found = False
                    for session_name, session in dashboard.mcp_client.sessions.items():
                        if hasattr(session, 'tools') and session.tools:
                            tools_found = True
                            st.markdown(f"**Session: {session_name}**")
                            for tool in session.tools:
                                st.markdown(f"- **{tool.name}** - {tool.description}")
                    
                    if not tools_found:
                        # Fallback to hardcoded list
                        st.markdown("""
                        **Monitoring Tools:**
                        - **get_network_clients** - Get connected devices
                        - **get_network_traffic** - Analyze traffic patterns
                        - **get_device_loss_and_latency_history** - Get performance metrics
                        - **get_organization_vpn_stats** - Get VPN statistics
                        - **get_network_events** - Get network events
                        
                                         **Configuration Tools:**
                 - **create_network_wireless_settings** - Create WiFi/SSID settings
                 - **continue_wireless_update_after_policy** - Continue wireless update after policy
                 - **create_network_appliance_settings** - Create network infrastructure settings
                 - **create_network_group_policy** - Create bandwidth and access policies
                 - **delete_network_group_policy** - Delete bandwidth and access policies
                        """)
                else:
                    # Fallback to hardcoded list
                    st.markdown("""
                    **Monitoring Tools:**
                    - **get_network_clients** - Get connected devices
                    - **get_network_traffic** - Analyze traffic patterns
                    - **get_device_loss_and_latency_history** - Get performance metrics
                    - **get_organization_vpn_stats** - Get VPN statistics
                    - **get_network_events** - Get network events
                    
                    **Configuration Tools:**
                    - **create_network_wireless_settings** - Create WiFi/SSID settings
                    - **continue_wireless_update_after_policy** - Continue wireless update after policy
                    - **create_network_appliance_settings** - Create network infrastructure settings
                    - **create_network_group_policy** - Create bandwidth and access policies
                    - **delete_network_group_policy** - Delete bandwidth and access policies
                    """)
            except Exception as e:
                st.warning(f"Could not fetch tools from MCP server: {e}")
                # Fallback to hardcoded list
                st.markdown("""
                **Monitoring Tools:**
                - **get_network_clients** - Get connected devices
                - **get_network_traffic** - Analyze traffic patterns
                - **get_device_loss_and_latency_history** - Get performance metrics
                - **get_organization_vpn_stats** - Get VPN statistics
                - **get_network_events** - Get network events
                
                **Configuration Tools:**
                - **create_network_wireless_settings** - Create WiFi/SSID settings
                - **continue_wireless_update_after_policy** - Continue wireless update after policy
                - **create_network_appliance_settings** - Create network infrastructure settings
                - **create_network_group_policy** - Create bandwidth and access policies
                - **delete_network_group_policy** - Delete bandwidth and access policies
                """)
    
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
    
    with tab4:
         st.header("🔧 Network Configuration")
         st.info("Configure your network settings directly from the dashboard")
         
         # Configuration tool selection
         st.subheader("🔧 Select Configuration Tool")
         st.info("💡 **Click the dropdown below to select what you want to configure**")
         
         config_tool = st.selectbox(
             "Choose what you want to configure:",
             [
                 ("create_network_wireless_settings", "📶 Wireless Network Settings"),
                 ("create_network_appliance_settings", "⚙️ Network Appliance Settings"), 
                 ("create_network_group_policy", "📋 Create Group Policy")
             ],
             format_func=lambda x: x[1],  # Show the friendly name
             help="Click to select which network configuration you want to update",
             key="config_tool_selector"
         )
         
         # Extract the actual tool name from the tuple
         if config_tool:
             config_tool = config_tool[0]
         
         
         
         # Initialize session state for form data
         if 'wireless_settings' not in st.session_state:
             st.session_state.wireless_settings = {
                 "enabled": True,
                 "ssid": "My_SSID",
                 "limit_up": 1000,
                 "limit_down": 1000
             }
         
         if 'appliance_settings' not in st.session_state:
             st.session_state.appliance_settings = {
                 "dhcp_enabled": True,
                 "dhcp_lease_time": 86400,
                 "vlan_enabled": False,
                 "vlan_id": 100
             }
         
         if 'group_policy' not in st.session_state:
             st.session_state.group_policy = {
                 "policy_name": "Guest Policy",
                 "bandwidth_enabled": True,
                 "limit_up": 500,
                 "limit_down": 1000,
                 "scheduling_enabled": False,
                 "traffic_shaping": True,
                 "content_filtering": False,
                 "splash_page": False
             }
         
         if config_tool == "create_network_wireless_settings":
             st.subheader("📶 Wireless Network Settings")
             
             col1, col2 = st.columns(2)
             with col1:
                 enabled = st.checkbox("Enable Wireless Network", value=st.session_state.wireless_settings["enabled"], key="wireless_enabled")
                 ssid = st.text_input("SSID Name", value=st.session_state.wireless_settings["ssid"], key="wireless_ssid")
             
             with col2:
                limit_up = st.number_input("Upload Bandwidth Limit (Mbps)", min_value=1, max_value=10000, value=st.session_state.wireless_settings["limit_up"], key="wireless_limit_up")
                limit_down = st.number_input("Download Bandwidth Limit (Mbps)", min_value=1, max_value=10000, value=st.session_state.wireless_settings["limit_down"], key="wireless_limit_down")
             
             # Reset button
             if st.button("🔄 Reset to Defaults", help="Reset wireless settings to default values"):
                 st.session_state.wireless_settings = {
                     "enabled": True,
                     "ssid": "My_SSID",
                     "limit_up": 1000,
                     "limit_down": 1000
                 }
                 st.success("Wireless settings reset to defaults!")
                 st.rerun()
             
             if st.button("Create Wireless Settings", type="primary"):
                 # Save current form values to session state
                 st.session_state.wireless_settings = {
                     "enabled": enabled,
                     "ssid": ssid,
                     "limit_up": limit_up,
                     "limit_down": limit_down
                 }
                 
                 with st.spinner("Updating wireless settings..."):
                     try:
                                                   # Import the function
                          from server.create_network_wireless_settings import create_network_wireless_settings
                          
                          # Prepare settings data
                          settings_data = {
                              "enabled": enabled,
                              "ssid": ssid,
                              "bandwidth": {
                                  "limitUp": limit_up,
                                  "limitDown": limit_down
                              }
                          }
                          
                          # Call the function
                          result = asyncio.run(create_network_wireless_settings(settings_data, use_mock=True))
                          
                          if result and len(result) > 0:
                              st.success("✅ Wireless settings created successfully!")
                              st.json(settings_data)
                             
                                                           # Show the result
                              with st.expander("View Create Result"):
                                 st.json(result[0]['text'])
                          else:
                              st.error("Failed to create wireless settings")
                              
                     except Exception as e:
                          st.error(f"Error creating wireless settings: {e}")
                          st.exception(e)
         
         elif config_tool == "create_network_appliance_settings":
             st.subheader("⚙️ Network Appliance Settings")
             
             col1, col2 = st.columns(2)
             with col1:
                 dhcp_enabled = st.checkbox("Enable DHCP", value=st.session_state.appliance_settings["dhcp_enabled"], key="appliance_dhcp_enabled")
                 dhcp_lease_time = st.number_input("DHCP Lease Time (seconds)", min_value=300, max_value=864000, value=st.session_state.appliance_settings["dhcp_lease_time"], key="appliance_dhcp_lease")
             
             with col2:
                vlan_enabled = st.checkbox("Enable VLAN", value=st.session_state.appliance_settings["vlan_enabled"], key="appliance_vlan_enabled")
                vlan_id = st.number_input("VLAN ID", min_value=1, max_value=4094, value=st.session_state.appliance_settings["vlan_id"], disabled=not vlan_enabled, key="appliance_vlan_id")
             
             # Reset button
             if st.button("🔄 Reset to Defaults", help="Reset appliance settings to default values"):
                 st.session_state.appliance_settings = {
                     "dhcp_enabled": True,
                     "dhcp_lease_time": 86400,
                     "vlan_enabled": False,
                     "vlan_id": 100
                 }
                 st.success("Appliance settings reset to defaults!")
                 st.rerun()
             
             if st.button("Create Appliance Settings", type="primary"):
                 # Save current form values to session state
                 st.session_state.appliance_settings = {
                     "dhcp_enabled": dhcp_enabled,
                     "dhcp_lease_time": dhcp_lease_time,
                     "vlan_enabled": vlan_enabled,
                     "vlan_id": vlan_id
                 }
                 
                 with st.spinner("Updating appliance settings..."):
                     try:
                         # Import the function
                         from server.create_network_appliance_settings import create_network_appliance_settings
                         
                         # Prepare settings data
                         settings_data = {
                             "dhcp": {
                                 "enabled": dhcp_enabled,
                                 "leaseTime": dhcp_lease_time
                             },
                             "vlan": {
                                 "enabled": vlan_enabled,
                                 "id": vlan_id if vlan_enabled else None
                             }
                         }
                         
                         # Call the function
                         result = asyncio.run(create_network_appliance_settings(settings_data, use_mock=True))
                         
                         if result and len(result) > 0:
                             st.success("✅ Appliance settings created successfully!")
                             st.json(settings_data)
                             
                             # Show the result
                             with st.expander("View Create Result"):
                                 st.json(result[0]['text'])
                         else:
                             st.error("Failed to create appliance settings")
                             
                     except Exception as e:
                         st.error(f"Error creating appliance settings: {e}")
                         st.exception(e)
          
             elif config_tool == "create_network_group_policy":
              st.subheader("📋 Create Network Group Policy")
              
              col1, col2 = st.columns(2)
              with col1:
                  policy_name = st.text_input("Policy Name", value=st.session_state.group_policy["policy_name"], key="create_policy_name")
                  bandwidth_enabled = st.checkbox("Enable Bandwidth Limits", value=st.session_state.group_policy["bandwidth_enabled"], key="create_policy_bandwidth_enabled")
              
              with col2:
                  limit_up = st.number_input("Upload Limit (Kbps)", min_value=1, max_value=100000, value=st.session_state.group_policy["limit_up"], disabled=not bandwidth_enabled, key="create_policy_limit_up")
                  limit_down = st.number_input("Download Limit (Kbps)", min_value=1, max_value=100000, value=st.session_state.group_policy["limit_down"], disabled=not bandwidth_enabled, key="create_policy_limit_down")
              
              # Advanced settings
              with st.expander("Advanced Settings"):
                  col1, col2 = st.columns(2)
                  with col1:
                      scheduling_enabled = st.checkbox("Enable Scheduling Restrictions", value=st.session_state.group_policy["scheduling_enabled"], key="create_policy_scheduling")
                      traffic_shaping = st.checkbox("Enable Firewall & Traffic Shaping", value=st.session_state.group_policy["traffic_shaping"], key="create_policy_traffic_shaping")
                  
                  with col2:
                      content_filtering = st.checkbox("Enable Content Filtering", value=st.session_state.group_policy["content_filtering"], key="create_policy_content_filtering")
                      splash_page = st.checkbox("Enable Splash Page Authentication", value=st.session_state.group_policy["splash_page"], key="create_policy_splash_page")
              
              # Reset button
              if st.button("🔄 Reset to Defaults", help="Reset group policy to default values", key="create_policy_reset"):
                  st.session_state.group_policy = {
                      "policy_name": "Guest Policy",
                      "bandwidth_enabled": True,
                      "limit_up": 500,
                      "limit_down": 1000,
                      "scheduling_enabled": False,
                      "traffic_shaping": True,
                      "content_filtering": False,
                      "splash_page": False
                  }
                  st.success("Group policy reset to defaults!")
                  st.rerun()
              
              if st.button("Create Group Policy", type="primary", key="create_policy_button"):
                  # Save current form values to session state
                  st.session_state.group_policy = {
                      "policy_name": policy_name,
                      "bandwidth_enabled": bandwidth_enabled,
                      "limit_up": limit_up,
                      "limit_down": limit_down,
                      "scheduling_enabled": scheduling_enabled,
                      "traffic_shaping": traffic_shaping,
                      "content_filtering": content_filtering,
                      "splash_page": splash_page
                  }
                  
                  with st.spinner("Creating group policy..."):
                      try:
                          # Import the function
                          from server.create_network_group_policy import create_network_group_policy
                          
                          # Prepare policy data matching comprehensive Cisco Meraki API structure
                          policy_data = {
                              "name": policy_name,
                              "scheduling": {
                                  "enabled": scheduling_enabled,
                                  "monday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                  "tuesday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                  "wednesday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                  "thursday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                  "friday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                  "saturday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                  "sunday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {}
                              },
                              "bandwidth": {
                                  "settings": "custom" if bandwidth_enabled else "network default",
                                  "bandwidthLimits": {
                                      "limitUp": limit_up if bandwidth_enabled else None,
                                      "limitDown": limit_down if bandwidth_enabled else None
                                  } if bandwidth_enabled else {}
                              },
                              "firewallAndTrafficShaping": {
                                  "settings": "custom" if traffic_shaping else "network default",
                                  "trafficShapingRules": [] if traffic_shaping else [],
                                  "l3FirewallRules": [],
                                  "l7FirewallRules": []
                              },
                              "contentFiltering": {
                                  "allowedUrlPatterns": {"settings": "network default", "patterns": []},
                                  "blockedUrlPatterns": {"settings": "append" if content_filtering else "network default", "patterns": []},
                                  "blockedUrlCategories": {"settings": "network default", "categories": []}
                              },
                              "splashAuthSettings": "custom" if splash_page else "bypass",
                              "vlanTagging": {"settings": "network default"},
                              "bonjourForwarding": {"settings": "network default", "rules": []}
                          }
                          
                          # Call the function
                          result = asyncio.run(create_network_group_policy(policy_data, use_mock=True))
                          
                          if result and len(result) > 0:
                              st.success("✅ Group policy created successfully!")
                              st.json(policy_data)
                              
                              # Show the result
                              with st.expander("View Creation Result"):
                                  st.json(result[0]['text'])
                          else:
                              st.error("Failed to create group policy")
                              
                      except Exception as e:
                          st.error(f"Error creating group policy: {e}")
                          st.exception(e)
          
         elif config_tool == "delete_network_group_policy":
             st.subheader("📋 Create Network Group Policy")
             
             col1, col2 = st.columns(2)
             with col1:
                 policy_name = st.text_input("Policy Name", value=st.session_state.group_policy["policy_name"], key="policy_name")
                 bandwidth_enabled = st.checkbox("Enable Bandwidth Limits", value=st.session_state.group_policy["bandwidth_enabled"], key="policy_bandwidth_enabled")
             
             with col2:
                 limit_up = st.number_input("Upload Limit (Kbps)", min_value=1, max_value=100000, value=st.session_state.group_policy["limit_up"], disabled=not bandwidth_enabled, key="policy_limit_up")
                 limit_down = st.number_input("Download Limit (Kbps)", min_value=1, max_value=100000, value=st.session_state.group_policy["limit_down"], disabled=not bandwidth_enabled, key="policy_limit_down")
             
             # Advanced settings
             with st.expander("Advanced Settings"):
                 col1, col2 = st.columns(2)
                 with col1:
                     scheduling_enabled = st.checkbox("Enable Scheduling Restrictions", value=st.session_state.group_policy["scheduling_enabled"], key="policy_scheduling")
                     traffic_shaping = st.checkbox("Enable Firewall & Traffic Shaping", value=st.session_state.group_policy["traffic_shaping"], key="policy_traffic_shaping")
                 
                 with col2:
                     content_filtering = st.checkbox("Enable Content Filtering", value=st.session_state.group_policy["content_filtering"], key="policy_content_filtering")
                     splash_page = st.checkbox("Enable Splash Page Authentication", value=st.session_state.group_policy["splash_page"], key="policy_splash_page")
             
             # Reset button
             if st.button("🔄 Reset to Defaults", help="Reset group policy to default values"):
                 st.session_state.group_policy = {
                     "policy_name": "Guest Policy",
                     "bandwidth_enabled": True,
                     "limit_up": 500,
                     "limit_down": 1000,
                     "scheduling_enabled": False,
                     "traffic_shaping": True,
                     "content_filtering": False,
                     "splash_page": False
                 }
                 st.success("Group policy reset to defaults!")
                 st.rerun()
             
             if st.button("Update Group Policy", type="primary"):
                 # Save current form values to session state
                 st.session_state.group_policy = {
                     "policy_name": policy_name,
                     "bandwidth_enabled": bandwidth_enabled,
                     "limit_up": limit_up,
                     "limit_down": limit_down,
                     "scheduling_enabled": scheduling_enabled,
                     "traffic_shaping": traffic_shaping,
                     "content_filtering": content_filtering,
                     "splash_page": splash_page
                 }
                 
                 with st.spinner("Creating group policy..."):
                     try:
                                                   # Note: create_network_group_policy tool has been removed
                          # Use update_network_group_policy instead
                         
                         # Prepare policy data matching comprehensive Cisco Meraki API structure
                         policy_data = {
                             "name": policy_name,
                             "scheduling": {
                                 "enabled": scheduling_enabled,
                                 "monday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                 "tuesday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                 "wednesday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                 "thursday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                 "friday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                 "saturday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {},
                                 "sunday": {"active": scheduling_enabled, "from": "9:00", "to": "17:00"} if scheduling_enabled else {}
                             },
                             "bandwidth": {
                                 "settings": "custom" if bandwidth_enabled else "network default",
                                 "bandwidthLimits": {
                                     "limitUp": limit_up if bandwidth_enabled else None,
                                     "limitDown": limit_down if bandwidth_enabled else None
                                 } if bandwidth_enabled else {}
                             },
                             "firewallAndTrafficShaping": {
                                 "settings": "custom" if traffic_shaping else "network default",
                                 "trafficShapingRules": [] if traffic_shaping else [],
                                 "l3FirewallRules": [],
                                 "l7FirewallRules": []
                             },
                             "contentFiltering": {
                                 "allowedUrlPatterns": {"settings": "network default", "patterns": []},
                                 "blockedUrlPatterns": {"settings": "append" if content_filtering else "network default", "patterns": []},
                                 "blockedUrlCategories": {"settings": "network default", "categories": []}
                             },
                             "splashAuthSettings": "custom" if splash_page else "bypass",
                             "vlanTagging": {"settings": "network default"},
                             "bonjourForwarding": {"settings": "network default", "rules": []}
                         }
                         
                         # Call the function
                         result = asyncio.run(create_network_group_policy(policy_data, use_mock=True))
                         
                         if result and len(result) > 0:
                             st.success("✅ Group policy created successfully!")
                             st.json(policy_data)
                             
                             # Show the result
                             with st.expander("View Creation Result"):
                                 st.json(result[0]['text'])
                         else:
                             st.error("Failed update group policy")
                             
                     except Exception as e:
                         st.error(f"Error creating group policy: {e}")
                         st.exception(e)
         
         # Configuration History
         st.subheader("📚 Configuration History")
         st.info("Recent configuration changes will appear here")
         
         # Add a placeholder for configuration history
         if 'config_history' not in st.session_state:
             st.session_state.config_history = []
         
         if st.session_state.config_history:
             for i, config in enumerate(st.session_state.config_history):
                 with st.expander(f"Configuration {i+1} - {config.get('timestamp', 'Unknown')}"):
                     st.json(config.get('data', {}))
         else:
             st.info("No configuration history yet. Make changes to see them here.")
     
     # Footer
    st.markdown("---")
    st.markdown("**Network Agent Dashboard** - Powered by MCP, Gemini LLM, and Streamlit")
    
    # Auto-refresh for real-time updates
    if dashboard.monitoring_active:
        time.sleep(5)
        st.rerun()

    # Cleanup on exit
    import atexit
    atexit.register(dashboard.cleanup)

if __name__ == "__main__":
    main()
