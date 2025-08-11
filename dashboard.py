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
    from server.get_organizations import get_organizations
    
    IMPORTS_SUCCESS = True
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Please install required packages: pip install streamlit plotly pandas nest-asyncio")
    IMPORTS_SUCCESS = False

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Network Agent Dashboard",
    page_icon="🌐",
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
                st.success("✅ MCP Client connected successfully")
            else:
                st.error("❌ MCP config file not found")
        except Exception as e:
            st.error(f"❌ Failed to initialize MCP client: {e}")
    
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
                st.success("✅ Gemini LLM initialized successfully")
            else:
                st.error("❌ GEMINI_API_KEY not found in .env file")
        except Exception as e:
            st.error(f"❌ Failed to initialize LLM: {e}")
    
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
    st.markdown('<div class="main-header"><h1>🌐 Network Agent Dashboard</h1><p>MCP Client Chatbot + Network Monitor Integration</p></div>', unsafe_allow_html=True)
    
    if not IMPORTS_SUCCESS:
        st.stop()
    
    # Initialize dashboard
    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = NetworkDashboard()
    
    dashboard = st.session_state.dashboard
    
    # Sidebar for controls
    with st.sidebar:
        st.header("🎛️ Dashboard Controls")
        
        # Monitoring controls
        st.subheader("📊 Network Monitor")
        if st.button("Start Monitoring", type="primary"):
            dashboard.start_monitoring()
            st.success("Monitoring started!")
        
        if st.button("Stop Monitoring"):
            dashboard.stop_monitoring()
            st.info("Monitoring stopped!")
        
        # Status indicators
        st.subheader("📈 Status")
        st.metric("Monitoring Active", "🟢 Yes" if dashboard.monitoring_active else "🔴 No")
        st.metric("Data Points", len(dashboard.monitoring_data))
        
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["💬 MCP Chatbot", "📊 Network Monitor", "📈 Analytics"])
    
    with tab1:
        st.header("💬 MCP Client Chatbot")
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
        
        # Chat input
        user_input = st.text_input("Ask about your network:", key="chat_input")
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("Send", type="primary"):
                if user_input.strip():
                    with st.spinner("Getting response..."):
                        response = dashboard.chat_with_mcp(user_input.strip())
                        st.rerun()
        
        with col2:
            if st.button("Clear Chat"):
                dashboard.chat_history.clear()
                st.rerun()
        
        # Available tools info
        with st.expander("🔧 Available MCP Tools"):
            st.markdown("""
            - **get_network_clients** - Get connected devices
            - **get_network_traffic** - Analyze traffic patterns
            - **get_device_loss_and_latency_history** - Get performance metrics
            - **get_organization_vpn_stats** - Get VPN statistics
            - **get_network_events** - Get network events
            """)
    
    with tab2:
        st.header("📊 Network Monitor")
        
        # Monitoring status
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", "🟢 Active" if dashboard.monitoring_active else "🔴 Inactive")
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
            
            st.subheader("📈 Latest Insights")
            st.markdown(f"**Timestamp:** {latest['timestamp'][:19]}")
            
            # Check if this is an error entry
            if latest.get('error', False):
                st.error(f"⚠️ Monitoring Error: {latest.get('insights', 'Unknown error')}")
            else:
                # Display insights
                if 'insights' in latest:
                    st.info(latest['insights'])
                
                # Display data summary
                st.subheader("📊 Data Summary")
                
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
        st.header("📈 Analytics Dashboard")
        
        if len(dashboard.monitoring_data) > 1:
            # Filter out error entries
            valid_data = [entry for entry in dashboard.monitoring_data if not entry.get('error', False)]
            
            if len(valid_data) > 1:
                # Create time series data
                timestamps = [entry['timestamp'] for entry in valid_data]
                
                # Performance trends chart
                st.subheader("📊 Performance Trends")
                
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
        time.sleep(5)
        st.rerun()

    # Cleanup on exit
    import atexit
    atexit.register(dashboard.cleanup)

if __name__ == "__main__":
    main()
