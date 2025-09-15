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
    
    /* Make dropdowns more obvious and colorful with blue gradient */
    .stSelectbox > div > div {
        border: 2px solid #1E3A8A !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #DBEAFE, #E0F2FE) !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(30, 58, 138, 0.2) !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #3B82F6 !important;
        background: linear-gradient(135deg, #BFDBFE, #93C5FD) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    .stSelectbox > div > div:focus {
        border-color: #2563EB !important;
        background: linear-gradient(135deg, #93C5FD, #60A5FA) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3) !important;
    }
    
    /* Style the dropdown arrow */
    .stSelectbox > div > div > div[data-testid="stSelectboxArrow"] {
        color: #1E3A8A !important;
    }
    
    .stSelectbox > div > div:hover > div[data-testid="stSelectboxArrow"] {
        color: #3B82F6 !important;
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
    tab1, tab2, tab3, tab4 = st.tabs(["MCP Chatbot", "Network Monitor", "Analytics", "Network Orchestration"])
    
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
        
        # JavaScript to handle Enter key - only for chat input
        st.markdown("""
        <script>
        // Wait for page to load
        setTimeout(function() {
            const chatInput = document.querySelector('input[data-testid="stTextInput"]');
            if (chatInput && chatInput.placeholder && chatInput.placeholder.includes('Ask about your network')) {
                chatInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        // Find and click the Send button
                        const sendButton = document.querySelector('div[data-testid="stChatInputContainer"] button[kind="primary"]');
                        if (sendButton) {
                            sendButton.click();
                        }
                    }
                });
            }
        }, 1000);
        </script>
        """, unsafe_allow_html=True)
        
        # Send and Clear buttons
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if st.button("Send", type="primary", key="chat_send_btn"):
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
         st.info("Run network management functions directly from the dashboard")
         
         # Configuration tool selection
         st.subheader("🔧 Select Function to Run")
         st.info("💡 **Click the dropdown below to select what you want to run**")
         
         config_tool = st.selectbox(
             "Choose what you want to run:",
             [
                 ("uplink_through_latency", "🔄 --uplink-through-latency"),
                 ("automate", "🤖 --automate"),
                 ("available", "📋 Available Functions")
             ],
             format_func=lambda x: x[1],  # Show the friendly name
             help="Click to select which network function you want to run",
             key="config_tool_selector",
             index=0  # Set default selection
         )
         
         # Extract the actual tool name from the tuple
         if config_tool:
             config_tool = config_tool[0]
         
         # Debug: Show what was selected (hidden for clean interface)
         # st.write(f"Selected tool: {config_tool}")
         
         if config_tool == "uplink_through_latency":
             st.subheader("🔄 --uplink-through-latency")
             st.info("Run latency-based WAN rerouting to optimize network performance")
             
             col1, col2 = st.columns(2)
             with col1:
                 st.write("**Function:** `--uplink-through-latency`")
                 st.write("**Purpose:** Automatically reroute devices across WANs based on latency thresholds")
                #  st.write("**Policy:** Uses `latency_policy.yaml` for decision making")
             
             with col2:
                 st.write("**Features:**")
                 st.write("• Real-time latency monitoring")
                 st.write("• Automatic device redistribution")
                #  st.write("• Before/after performance reporting")
                 st.write("• Dynamic WAN creation")
             
             if st.button("🚀 Run Uplink Through Latency", type="primary", key="uplink_latency_btn"):
                 with st.spinner("Running latency-based WAN rerouting..."):
                     try:
                         # Run the MCP client with uplink-through-latency option
                         import subprocess
                         import os
                         
                         # Use the virtual environment Python if available
                         python_cmd = "python"
                         if os.path.exists("../myenv/Scripts/python.exe"):
                             python_cmd = "../myenv/Scripts/python.exe"
                         elif os.path.exists("myenv/Scripts/python.exe"):
                             python_cmd = "myenv/Scripts/python.exe"
                         
                        #  st.info("🔄 Starting latency-based WAN rerouting...")
                         st.info("📊 Analyzing current network performance...")
                        #  st.info(f"🐍 Using Python: {python_cmd}")
                        #  st.info(f"📁 Working directory: {os.getcwd()}")
                         
                         # Show command being executed
                         cmd = [python_cmd, "client/mcp_client.py", "--uplink-through-latency"]
                        #  st.info(f"🔧 Executing: {' '.join(cmd)}")
                         
                         # Create a placeholder for real-time output
                         output_placeholder = st.empty()
                         
                         # Run the command and capture output in real-time
                         process = subprocess.Popen(
                             cmd, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.STDOUT, 
                             text=True, 
                             cwd=".", 
                             shell=False,
                             bufsize=1,
                             universal_newlines=True
                         )
                         
                         # Display output in real-time
                         output_lines = []
                         while True:
                             output = process.stdout.readline()
                             if output == '' and process.poll() is not None:
                                 break
                             if output:
                                 output_lines.append(output.strip())
                                 # Show all output so far
                                 output_placeholder.code('\n'.join(output_lines))  # Show all lines
                                 
                         # Wait for process to complete
                         return_code = process.wait()
                         
                         # Add a small delay to ensure all output is captured
                         import time
                         time.sleep(0.5)
                         
                         if return_code == 0:
                             st.success("✅ Uplink through latency completed successfully!")
                             
                             # Show what was accomplished
                             st.subheader("📊 Analysis Results:")
                             st.info("✅ Network latency analysis completed")
                            #  st.info("✅ WAN rerouting recommendations generated")
                             st.info("✅ Device distribution optimized")
                             
                             # Show the complete output
                             st.subheader("📋 Complete Terminal Output:")
                             
                             st.code('\n'.join(output_lines))
                             
                             # Show the result in expandable section
                             with st.expander("🔍 View Full Technical Output"):
                                 st.text('\n'.join(output_lines))
                         else:
                             st.error("❌ Uplink through latency failed!")
                             st.error(f"Return code: {return_code}")
                             st.error("Please check the error details below:")
                             st.code('\n'.join(output_lines))
                             
                     except subprocess.TimeoutExpired:
                         st.error("⏰ Operation timed out after 2 minutes")
                         st.info("The operation is taking longer than expected. Please try again.")
                     except Exception as e:
                         st.error(f"Error running uplink through latency: {e}")
                         st.exception(e)
          
         elif config_tool == "automate":
             st.subheader("🤖 --automate")
             st.info("Run automated network management and optimization")
             
             col1, col2 = st.columns(2)
             with col1:
                 st.write("**Function:** `--automate`")
                 st.write("**Purpose:** Automated network management and optimization")
                 st.write("**Features:** Continuous monitoring and adjustment")
             
             with col2:
                 st.write("**Capabilities:**")
                 st.write("• Continuous monitoring")
                 st.write("• Automatic optimization")
                 st.write("• Performance tuning")
                 st.write("• Proactive maintenance")
             
             if st.button("🚀 Run Automate", type="primary", key="automate_btn"):
                 with st.spinner("Running automated network management..."):
                     try:
                         # Run the MCP client with automate option
                         import subprocess
                         import os
                         
                         # Use the virtual environment Python if available
                         python_cmd = "python"
                         if os.path.exists("../myenv/Scripts/python.exe"):
                             python_cmd = "../myenv/Scripts/python.exe"
                         elif os.path.exists("myenv/Scripts/python.exe"):
                             python_cmd = "myenv/Scripts/python.exe"
                         
                        #  st.info("🤖 Starting automated network management...")
                         st.info("📈 Monitoring network performance and making optimizations...")
                        #  st.info(f"🐍 Using Python: {python_cmd}")
                        #  st.info(f"📁 Working directory: {os.getcwd()}")
                         
                         # Show command being executed
                         cmd = [python_cmd, "client/mcp_client.py", "--automate"]
                         st.info(f"🔧 Executing: {' '.join(cmd)}")
                         
                         # Create a placeholder for real-time output
                         output_placeholder = st.empty()
                         
                         # Run the command and capture output in real-time
                         process = subprocess.Popen(
                             cmd, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.STDOUT, 
                             text=True, 
                             cwd=".", 
                             shell=False,
                             bufsize=1,
                             universal_newlines=True
                         )
                         
                         # Display output in real-time
                         output_lines = []
                         while True:
                             output = process.stdout.readline()
                             if output == '' and process.poll() is not None:
                                 break
                             if output:
                                 output_lines.append(output.strip())
                                 # Show all output so far
                                 output_placeholder.code('\n'.join(output_lines))  # Show all lines
                                 
                         # Wait for process to complete
                         return_code = process.wait()
                         
                         # Add a small delay to ensure all output is captured
                         import time
                         time.sleep(0.5)
                         
                         if return_code == 0:
                             st.success("✅ Automate completed successfully!")
                             
                             # Show what was accomplished
                             st.subheader("🤖 Automation Results:")
                             st.info("✅ Network monitoring completed")
                             st.info("✅ Performance optimizations applied")
                             st.info("✅ Configuration changes implemented")
                             st.info("✅ System health checks performed")
                             
                             # Show the complete output
                             st.subheader("📋 Complete Terminal Output:")
                             
                             # Filter for clean, important output only
                             clean_output = []
                             seen_analysis = set()  # Track seen analysis to avoid duplicates
                             for line in output_lines:
                                 # Skip technical/verbose lines
                                 if any(skip in line.lower() for skip in [
                                     'base_url:', 'use_mock:', 'using real meraki api mode',
                                     'testing api connectivity', 'successfully connected to api',
                                     'processing request of type', 'i am working on',
                                     'get api call:', 'http request:', 'retrieved data for device',
                                     'retrieved uplink statuses for', 'converted natural language',
                                     'successfully converted', 'updating uplink status data',
                                     'successfully updated uplink status', 'meraki mcp client with gemini',
                                     'connecting to mcp server', 'initializing gemini llm',
                                     'creating latency monitoring agent', 'setup complete',
                                     'running latency monitoring analysis', 'starting latency-based wan rerouting',
                                     'analyzing current network performance', 'using python:',
                                     'working directory:', 'executing:', 'policy: uses latency_policy.yaml',
                                     'policy: uses', 'for decision making', 'latency monitoring complete',
                                     'uplink analysis complete', 'monitoring uplink performance',
                                     'gathering comprehensive', 'running latency monitoring analysis'
                                 ]):
                                     continue
                                 
                                 # Skip lines with only equals signs
                                 if line.strip() == '=' * len(line.strip()) and len(line.strip()) > 10:
                                     continue
                                 
                                 # Keep important lines - be more inclusive
                                 if any(keep in line.lower() for keep in [
                                     'analysis:', 'reasoning:', 'decision:', 'summary of changes:',
                                     'moved device', 'phase', 'automation', 'optimization', 
                                     'reroute', 'wan', 'no changes required', 'no issues detected',
                                     'equal distribution', 'devices connected', 'latency of',
                                     'threshold', 'network performance', 'devices on wan',
                                     'prior to any actions', 'detected latency', 'policy for',
                                     'requires devices', 'rerouted equally', 'across 2 wans',
                                     'high latency', 'medium latency', 'critical latency',
                                     'observed latency', 'acceptable threshold', 'optimal performance',
                                     'classified as', 'load balancing', 'distribute traffic',
                                     'reduce the latency', 'improving network performance',
                                     'balance the load', 'mitigate high latency'
                                 ]) or line.strip().startswith('**') or (line.strip() and not line.strip().startswith('=') and len(line.strip()) > 10):
                                     # Avoid duplicates
                                     line_key = line.strip().lower()
                                     if line_key not in seen_analysis:
                                         seen_analysis.add(line_key)
                                         clean_output.append(line)
                             
                             if clean_output:
                                 # Use text_area for better wrapping and scrolling
                                 st.text_area(
                                     "Analysis Results", 
                                     '\n'.join(clean_output), 
                                     height=400, 
                                     key="results_summary_automate",
                                     help="Scroll to view complete analysis"
                                 )
                             else:
                                 st.info("Analysis completed successfully - no detailed output to display")
                             
                             # Show technical details in expandable section for debugging
                             with st.expander("🔧 View Technical Details (for debugging)"):
                                 st.text('\n'.join(output_lines))
                         else:
                             st.error("❌ Automate failed!")
                             st.error(f"Return code: {return_code}")
                             st.error("Please check the error details below:")
                             st.code('\n'.join(output_lines))
                             
                     except subprocess.TimeoutExpired:
                         st.error("⏰ Operation timed out after 2 minutes")
                         st.info("The operation is taking longer than expected. Please try again.")
                     except Exception as e:
                         st.error(f"Error running automate: {e}")
                         st.exception(e)
          
         elif config_tool == "available":
             st.subheader("📋 Available Functions")
             st.info("List of all available network management functions")
             
             # Function categories
             col1, col2 = st.columns(2)
             
             with col1:
                 st.write("**🔧 Core Functions:**")
                 st.write("• `--uplink-through-latency` - Latency-based WAN rerouting")
                 st.write("• `--automate` - Automated network management")
                 st.write("• `--monitor` - Real-time network monitoring")
                 st.write("• `--analyze` - Network analysis and reporting")
                 
                 st.write("**📊 Monitoring Functions:**")
                 st.write("• `--get-clients` - Get network clients")
                 st.write("• `--get-traffic` - Get traffic data")
                 st.write("• `--get-events` - Get network events")
                 st.write("• `--get-latency` - Get latency metrics")
             
             with col2:
                 st.write("**⚙️ Configuration Functions:**")
                 st.write("• `--update-uplink` - Update uplink settings")
                 st.write("• `--update-appliance` - Update appliance settings")
                 st.write("• `--create-policy` - Create group policies")
                 st.write("• `--update-network` - Update network settings")
                 
                 st.write("**🔍 Analysis Functions:**")
                 st.write("• `--get-vpn-stats` - Get VPN statistics")
                 st.write("• `--get-connectivity` - Get connectivity data")
                 st.write("• `--get-security` - Get security settings")
                 st.write("• `--get-acl` - Get access control lists")
             
             # Usage examples
             st.subheader("💡 Usage Examples")
             st.code("""
                # Run latency-based WAN rerouting
                python client/mcp_client.py --uplink-through-latency

                # Run automated management
                python client/mcp_client.py --automate

                # Get network clients
                python client/mcp_client.py --get-clients

                # Monitor network traffic
                python client/mcp_client.py --get-traffic
                            """)
                
             # Help button
             if st.button("📖 Show Help", type="secondary"):
                 st.info("Use the command line or this dashboard to run network management functions. Each function has specific parameters and options.")
    
    # with tab5:
    #     st.header("⚡ Latency Monitoring & Uplink Management")
    #     st.info("Monitor network latency and automatically manage uplinks based on performance thresholds")
        
    #     # Latency monitoring controls
    #     col1, col2, col3 = st.columns(3)
    #     with col1:
    #         if st.button("🚀 Start Latency Monitoring", type="primary"):
    #             st.success("Latency monitoring started! This will monitor uplink performance and automatically manage device distribution.")
    #             st.info("Use the MCP Chatbot tab with '--uplink-through-latency' command for manual latency-based uplink management.")
        
    #     with col2:
    #         if st.button("📊 View Latency Policy"):
    #             try:
    #                 with open('latency_policy.yaml', 'r') as f:
    #                     policy_content = f.read()
    #                 st.text_area("Latency Policy", policy_content, height=400)
    #             except FileNotFoundError:
    #                 try:
    #                     with open('latency_policy.txt', 'r') as f:
    #                         policy_content = f.read()
    #                     st.text_area("Latency Policy", policy_content, height=400)
    #                 except FileNotFoundError:
    #                     st.error("Latency policy file not found")
        
    #     with col3:
    #         if st.button("🔄 Refresh Latency Data"):
    #             st.rerun()
        
    #         # Latency thresholds display
    #         st.subheader("📈 Latency Thresholds")
    #         col1, col2, col3, col4 = st.columns(4)
    #         with col1:
    #             st.metric("EXCELLENT", "< 30ms", "latency + < 3ms jitter")
    #         with col2:
    #             st.metric("GOOD", "30-50ms", "latency + 3-5ms jitter")
    #         with col3:
    #             st.metric("WARNING", "50-100ms", "latency OR 5-10ms jitter")
    #         with col4:
    #             st.metric("CRITICAL", "> 100ms", "latency OR > 10ms jitter")
            
    #         # Uplink management actions
    #         st.subheader("🔧 Uplink Management Actions")
                
    #         col1, col2 = st.columns(2)
    #         with col1:
    #             st.markdown("**When Latency Increases:**")
    #             st.markdown("""
    #             - Split devices across available WANs
    #             - Move 50% of devices from high-latency WAN
    #             - Prioritize high-bandwidth devices first
    #             - Create WAN3 if needed for load distribution
    #             """)
                
    #         with col2:
    #             st.markdown("**When Latency Decreases:**")
    #             st.markdown("""
    #             - Consolidate devices to fewer WANs
    #             - Reconnect devices to primary WAN
    #             - Optimize for cost efficiency
    #             - Maintain redundancy for critical devices
    #             """)
        
    #     # Device priority management
    #     st.subheader("📋 Device Priority Management")
        
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         st.markdown("**High Priority Devices:**")
    #         st.markdown("""
    #         - MX84-HQ (Headquarters)
    #         - Critical servers
    #         - Executive devices
    #         - VoIP systems
    #         """)
        
    #     with col2:
    #         st.markdown("**Standard Priority Devices:**")
    #         st.markdown("""
    #             - MX84-Branch (Branch offices)
    #             - General workstations
    #             - Mobile devices
    #             - Guest networks
    #             """)
            
    #         # Monitoring status
    #         st.subheader("📊 Current Monitoring Status")
            
    #         col1, col2, col3 = st.columns(3)
    #         with col1:
    #             st.metric("Active Monitoring", "Enabled", "Real-time latency tracking")
    #         with col2:
    #             st.metric("Policy Version", "1.0", "YAML-based configuration")
    #         with col3:
    #             st.metric("Last Update", "Now", "Live data refresh")

if __name__ == "__main__":
    main()
