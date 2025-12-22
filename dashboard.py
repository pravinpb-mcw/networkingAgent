"""
Network Observability Dashboard
=================================
Unified dashboard showing:
- Agent 3 Analysis Chat (Real-time)
- Phoenix Trace Logs
- A2A Communication
"""

import streamlit as st
import json
import requests
from datetime import datetime
from pathlib import Path
import time

# Page config
st.set_page_config(
    page_title="Network Observability - Analysis Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Project paths
project_root = Path(__file__).parent
agent_data_dir = project_root / "agent_data"

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #0e1117;
    }
    
    /* Analysis chat messages */
    .analysis-message {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8c 100%);
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 20px;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .analysis-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .analysis-title {
        font-size: 1em;
        font-weight: 600;
        color: #4CAF50;
    }
    
    .analysis-time {
        font-size: 0.85em;
        color: #888;
    }
    
    .analysis-content {
        color: #e0e0e0;
        line-height: 1.4;
    }
    
    /* Status badges */
    .status-running {
        background-color: #4CAF50;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
    }
    
    .status-stopped {
        background-color: #f44336;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
    }
    
    /* Header styling */
    .dashboard-header {
        background: linear-gradient(90deg, #1e3a5f 0%, #4CAF50 100%);
        padding: 30px;
        border-radius: 10px;
        margin-bottom: 30px;
        text-align: center;
    }
    
    .dashboard-title {
        font-size: 2.5em;
        font-weight: 700;
        color: white;
        margin: 0;
    }
    
    .dashboard-subtitle {
        font-size: 1.1em;
        color: rgba(255,255,255,0.8);
        margin-top: 10px;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e1e1e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4CAF50;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #45a049;
    }
</style>
""", unsafe_allow_html=True)


def check_agent_status(port: int) -> dict:
    """Check if an agent is running"""
    try:
        response = requests.get(f"http://localhost:{port}/a2a", timeout=1)
        return {"status": "running", "port": port}
    except:
        return {"status": "stopped", "port": port}


def check_phoenix_status() -> dict:
    """Check if Phoenix server is running"""
    try:
        response = requests.get("http://localhost:6006", timeout=1)
        return {"status": "running"}
    except:
        return {"status": "stopped"}


def load_analysis_history():
    """Load analysis history"""
    history_file = agent_data_dir / "analysis_history.json"
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


# Header
st.markdown("""
<div class="dashboard-header">
    <h1 class="dashboard-title">🌐 Network Observability Dashboard</h1>
    <p class="dashboard-subtitle">Real-time Agent-to-Agent Communication & Analysis</p>
</div>
""", unsafe_allow_html=True)

# System Status Bar
col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

agent1_status = check_agent_status(5001)
agent2_status = check_agent_status(5002)
phoenix_status = check_phoenix_status()

with col1:
    if agent1_status["status"] == "running":
        st.markdown('<span class="status-running">🤖 Agent 1: Running</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-stopped">🤖 Agent 1: Stopped</span>', unsafe_allow_html=True)

with col2:
    if agent2_status["status"] == "running":
        st.markdown('<span class="status-running">🤖 Agent 2: Running</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-stopped">🤖 Agent 2: Stopped</span>', unsafe_allow_html=True)

with col3:
    st.markdown('<span class="status-running">🤖 Agent 3: Analyzing</span>', unsafe_allow_html=True)

with col4:
    if phoenix_status["status"] == "running":
        st.markdown('<span class="status-running">📊 Phoenix: Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-stopped">📊 Phoenix: Offline</span>', unsafe_allow_html=True)

with col5:
    auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)

st.divider()

# Main Content - TABS
tab1, tab2 = st.tabs(["💬 Failover Analysis Chat", "📊 Phoenix Trace Logs"])

# TAB 1 - Analysis Chat (Latest Only)
with tab1:
    st.markdown("### 💬 Failover Analysis Chat")
    st.caption("Real-time analysis from Agent 3 using A2A protocol")
    
    # Load history
    analysis_history = load_analysis_history()
    
    if analysis_history:
        # Show ONLY the latest analysis
        entry = analysis_history[-1]
        timestamp = entry.get('timestamp', 'Unknown')
        iteration = entry.get('iteration', '?')
        analysis = entry.get('analysis', 'No analysis available')
        
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime('%H:%M:%S')
            date_str = dt.strftime('%b %d, %Y')
        except:
            time_str = timestamp
            date_str = ""
        
        # Display latest message - render markdown tables properly
        import re
        
        # Convert markdown to HTML for proper table display
        def convert_markdown_tables(md_text):
            """Convert markdown tables to HTML tables"""
            lines = md_text.split('\n')
            result = []
            in_table = False
            table_headers = []
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Check if this is a table header row
                if '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
                    # Start table
                    in_table = True
                    table_headers = [cell.strip() for cell in line.split('|')[1:-1]]
                    result.append('<table style="width:100%; border-collapse: collapse; margin: 15px 0;">')
                    result.append('<thead><tr>')
                    for header in table_headers:
                        result.append(f'<th style="border: 1px solid #444; padding: 10px; background: #2a2a2a; text-align: left;">{header}</th>')
                    result.append('</tr></thead><tbody>')
                    i += 2  # Skip separator line
                    continue
                
                # Check if this is a table row
                elif in_table and '|' in line and line.strip():
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    result.append('<tr>')
                    for cell in cells:
                        result.append(f'<td style="border: 1px solid #444; padding: 10px;">{cell}</td>')
                    result.append('</tr>')
                    i += 1
                    continue
                
                # End table if we hit a non-table line
                elif in_table and '|' not in line:
                    result.append('</tbody></table>')
                    in_table = False
                
                # Regular line
                result.append(line)
                i += 1
            
            # Close table if still open
            if in_table:
                result.append('</tbody></table>')
            
            return '\n'.join(result)
        
        formatted_analysis = convert_markdown_tables(analysis)
        
        st.markdown(f"""
<div class="analysis-message">
    <div class="analysis-header">
        <span class="analysis-title">Analysis #{iteration}</span>
        <span class="analysis-time">{date_str} {time_str}</span>
    </div>
    <div class="analysis-content">
        {formatted_analysis.replace('#', '##')}
    </div>
</div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Download button for HTML report with proper markdown rendering
        # Simple conversion without external library
        def markdown_to_html(md_text):
            """Convert markdown to HTML (tables and basic formatting)"""
            import re
            
            html = md_text
            
            # Convert markdown tables to HTML tables
            lines = html.split('\n')
            result = []
            in_table = False
            
            for i, line in enumerate(lines):
                # Detect table start (line with |---|---|)
                if '|' in line and '---' in line:
                    if not in_table:
                        # Start table
                        result.append('<table>')
                        # Previous line is header
                        if i > 0 and '|' in lines[i-1]:
                            header_cells = [cell.strip() for cell in lines[i-1].split('|')[1:-1]]
                            result[-1] = '<table>\n<thead>\n<tr>'
                            for cell in header_cells:
                                result.append(f'<th>{cell}</th>')
                            result.append('</tr>\n</thead>\n<tbody>')
                        in_table = True
                    continue
                elif in_table and '|' in line and line.strip():
                    # Table row
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    result.append('<tr>')
                    for cell in cells:
                        result.append(f'<td>{cell}</td>')
                    result.append('</tr>')
                elif in_table and '|' not in line:
                    # End table
                    result.append('</tbody>\n</table>')
                    in_table = False
                    result.append(line)
                else:
                    result.append(line)
            
            if in_table:
                result.append('</tbody>\n</table>')
            
            html = '\n'.join(result)
            
            # Convert headers
            html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
            
            # Convert bold
            html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
            
            # Convert horizontal rules
            html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
            
            # Convert line breaks
            html = html.replace('\n\n', '<br><br>')
            
            return html
        
        # Convert markdown to HTML
        html_content = markdown_to_html(analysis)
        
        html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Failover Analysis Report #{iteration}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            padding: 40px;
            margin: 0;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: #0f3460;
            padding: 50px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 217, 255, 0.2);
        }}
        h1 {{
            color: #00D9FF;
            border-bottom: 3px solid #00D9FF;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2em;
        }}
        h2 {{
            color: #00D9FF;
            margin-top: 35px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(0, 217, 255, 0.3);
            font-size: 1.6em;
        }}
        h3 {{
            color: #00BFFF;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        h4 {{
            color: #87CEEB;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .meta-info {{
            background: rgba(0, 217, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 35px;
            border-left: 4px solid #00D9FF;
            font-size: 1.05em;
        }}
        .meta-info strong {{
            color: #00D9FF;
        }}
        .content {{
            line-height: 1.8;
            font-size: 16px;
        }}
        
        /* Table Styling */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }}
        
        thead {{
            background: linear-gradient(135deg, #00D9FF 0%, #0099CC 100%);
        }}
        
        th {{
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            color: #0a0a0a;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            color: #e0e0e0;
        }}
        
        tbody tr:hover {{
            background: rgba(0, 217, 255, 0.15);
        }}
        
        tbody tr:last-child td {{
            border-bottom: none;
        }}
        
        /* Alternating row colors */
        tbody tr:nth-child(even) {{
            background: rgba(255, 255, 255, 0.03);
        }}
        
        /* Code blocks */
        code {{
            background: rgba(255, 255, 255, 0.1);
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            color: #FFD700;
            font-size: 0.9em;
        }}
        
        pre {{
            background: rgba(0, 0, 0, 0.4);
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            border-left: 3px solid #00D9FF;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: #e0e0e0;
        }}
        
        /* Lists */
        ul, ol {{
            margin: 15px 0;
            padding-left: 25px;
        }}
        
        li {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        
        /* Horizontal rules */
        hr {{
            border: none;
            border-top: 2px solid rgba(0, 217, 255, 0.3);
            margin: 30px 0;
        }}
        
        /* Strong/Bold text */
        strong {{
            color: #00D9FF;
            font-weight: 600;
        }}
        
        /* Emphasis */
        em {{
            color: #87CEEB;
        }}
        
        .footer {{
            margin-top: 50px;
            padding-top: 25px;
            border-top: 2px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            color: #888;
            font-size: 14px;
        }}
        
        /* Status badges */
        .status-ok {{ color: #4CAF50; font-weight: bold; }}
        .status-warning {{ color: #FFC107; font-weight: bold; }}
        .status-critical {{ color: #F44336; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Network Failover Analysis Report</h1>
        <div class="meta-info">
            <strong>Report ID:</strong> Analysis #{iteration}<br>
            <strong>Generated:</strong> {date_str} at {time_str}<br>
            <strong>Agent:</strong> Agent 3 - Failover Coordinator<br>
            <strong>Protocol:</strong> A2A (Agent-to-Agent) Communication
        </div>
        <div class="content">
            {html_content}
        </div>
        <div class="footer">
            Network Observability Dashboard | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        col1, col2 = st.columns([3, 1])
        with col2:
            st.download_button(
                label="📥 Download HTML Report",
                data=html_report,
                file_name=f"failover_analysis_{iteration}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True,
                key="download_html_report"
            )
        
        st.info(f"📋 Total Analyses: {len(analysis_history)} | Showing latest only")
        
        # View full history expander
        with st.expander("📜 View Full History"):
            for entry in reversed(analysis_history[:-1]):  # All except latest
                timestamp = entry.get('timestamp', 'Unknown')
                iteration = entry.get('iteration', '?')
                analysis = entry.get('analysis', 'No analysis available')
                
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime('%H:%M:%S')
                    date_str = dt.strftime('%b %d, %Y')
                except:
                    time_str = timestamp
                    date_str = ""
                
                st.markdown(f"**🤖 Analysis #{iteration}** | {date_str} {time_str}")
                st.markdown(analysis)
                st.divider()
    else:
        st.info("⏳ Waiting for Agent 3 analysis... Start agents to see results here.")
        st.code("start_agents_with_a2a.bat", language="bash")

# TAB 2 - Phoenix Full Tab
with tab2:
    st.markdown("### 📊 Phoenix Trace Logs")
    st.caption("Real-time observability and A2A communication tracing")
    
    if phoenix_status["status"] == "running":
        st.success("✅ Phoenix server is running - http://localhost:6006")
        
        # Full-width Phoenix iframe
        st.markdown("""
        <iframe src="http://localhost:6006" width="100%" height="900" style="border:2px solid #00D9FF; border-radius:8px;"></iframe>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # A2A Communication Flow
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔗 A2A Communication Flow")
            st.markdown("""
**Active Communication:**

```
Agent 3 (Failover Coordinator)
    ↓
    ├─→ Agent 1 (Risk Scores) :5001
    │   └─→ Returns: At-risk APs
    │
    └─→ Agent 2 (Nearest APs) :5002
        └─→ Returns: Failover candidates
```
            """)
        
        with col2:
            st.markdown("#### 🔍 Trace Spans in Phoenix")
            st.markdown("""
- `Agent3_queries_Agent1_RiskScores`
- `Agent3_queries_Agent2_NearestAP_*`
- `Agent1_receives_A2A_request`
- `Agent2_receives_A2A_request`
- `llm_failover_analysis` (GLM-4.5)
            """)
    else:
        st.error("❌ Phoenix server is offline")
        st.code("start_phoenix.bat", language="bash")
# Footer
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption(f"🕐 Last updated: {datetime.now().strftime('%H:%M:%S')}")

with col2:
    if st.button("🔄 Refresh Now", use_container_width=True, key="btn_refresh"):
        st.rerun()

with col3:
    if st.button("🗑️ Clear History", use_container_width=True, key="btn_clear"):
        history_file = agent_data_dir / "analysis_history.json"
        if history_file.exists():
            history_file.unlink()
        st.success("History cleared!")
        st.rerun()

# Auto-refresh logic
if auto_refresh:
    time.sleep(5)
    st.rerun()

