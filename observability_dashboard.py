#!/usr/bin/env python3
"""
Observability Dashboard for Predictive Telemetry Agent
Visualizes Langfuse traces and DeepEval evaluation results
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

# Import tracing and evaluation modules
try:
    from tracing import (
        verify_langfuse_connection,
        get_recent_traces,
        get_trace_details,
        langfuse_client
    )
    TRACING_AVAILABLE = True
except ImportError as e:
    TRACING_AVAILABLE = False
    TRACING_ERROR = str(e)

try:
    from eval import (
        run_evaluation,
        evaluate_trace,
        DecisionQualityMetric,
        ToolUsageMetric,
        AlertAccuracyMetric
    )
    from eval.runner import result_store
    from eval.metrics import create_test_case_from_trace
    EVAL_AVAILABLE = True
except ImportError as e:
    EVAL_AVAILABLE = False
    EVAL_ERROR = str(e)

# Page configuration
st.set_page_config(
    page_title="Observability Dashboard - Predictive Telemetry Agent",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.2rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #333;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .trace-card {
        background: white;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .span-item {
        background: #f8f9fa;
        border-radius: 6px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        font-family: monospace;
        font-size: 0.85rem;
    }
    .span-llm { border-left: 3px solid #10b981; }
    .span-tool { border-left: 3px solid #f59e0b; }
    .span-agent { border-left: 3px solid #3b82f6; }
    .status-connected { color: #10b981; }
    .status-disconnected { color: #ef4444; }
    .score-high { color: #10b981; font-weight: bold; }
    .score-medium { color: #f59e0b; font-weight: bold; }
    .score-low { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🔮 Observability Dashboard</h1>
    <p>Predictive Telemetry Agent - Langfuse Tracing & DeepEval Metrics</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for connection status and filters
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Connection Status
    st.subheader("Connection Status")
    
    if TRACING_AVAILABLE:
        if verify_langfuse_connection():
            st.markdown('<p class="status-connected">✅ Langfuse Connected</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-disconnected">❌ Langfuse Disconnected</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="status-disconnected">❌ Tracing unavailable: {TRACING_ERROR}</p>', unsafe_allow_html=True)
    
    if EVAL_AVAILABLE:
        st.markdown('<p class="status-connected">✅ DeepEval Ready</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="status-disconnected">❌ DeepEval unavailable: {EVAL_ERROR}</p>', unsafe_allow_html=True)
    
    st.divider()
    
    # Filters
    st.subheader("🔍 Filters")
    
    trace_limit = st.slider("Traces to fetch", 10, 100, 50)
    
    filter_tags = st.multiselect(
        "Filter by tags",
        options=["predictive-telemetry", "monitoring", "alert", "analysis"],
        default=[]
    )
    
    st.divider()
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    if st.button("🔄 Refresh Traces", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🧪 Run Quick Evaluation", use_container_width=True):
        st.session_state["run_eval"] = True

# Main content - Tabs
tab1, tab2, tab3 = st.tabs(["📊 Trace Explorer", "🧪 Decision Evaluation", "📈 Analytics"])

# ============== TAB 1: Trace Explorer ==============
with tab1:
    st.header("Trace Explorer")
    
    if not TRACING_AVAILABLE:
        st.error(f"Tracing module not available: {TRACING_ERROR}")
        st.info("Make sure you have installed langfuse: `pip install langfuse>=3.0.0`")
    else:
        # Fetch traces
        @st.cache_data(ttl=60)  # Cache for 60 seconds
        def fetch_traces(limit: int):
            return get_recent_traces(limit=limit)
        
        traces = fetch_traces(trace_limit)
        
        if not traces:
            st.warning("No traces found. Run the agent to generate traces.")
            st.code("""
# Run the predictive telemetry agent to generate traces:
python predictive_telemetry_agent.py
            """)
        else:
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(traces)}</div>
                    <div class="metric-label">Total Traces</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Count traces by tag
                tagged_count = sum(1 for t in traces if t.get("tags"))
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{tagged_count}</div>
                    <div class="metric-label">Tagged Traces</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Sessions
                unique_sessions = len(set(t.get("session_id", "") for t in traces if t.get("session_id")))
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{unique_sessions}</div>
                    <div class="metric-label">Sessions</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                # Observation count
                total_obs = sum(t.get("observations", 0) for t in traces)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_obs}</div>
                    <div class="metric-label">Total Spans</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Trace list
            st.subheader("Recent Traces")
            
            # Filter traces if tags selected
            filtered_traces = traces
            if filter_tags:
                filtered_traces = [
                    t for t in traces 
                    if any(tag in (t.get("tags") or []) for tag in filter_tags)
                ]
            
            for trace in filtered_traces[:20]:  # Show top 20
                with st.expander(
                    f"🔹 {trace.get('name', 'Unnamed')} - {trace.get('id', 'N/A')[:8]}...",
                    expanded=False
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Trace ID:** `{trace.get('id', 'N/A')}`")
                        st.markdown(f"**Session:** `{trace.get('session_id', 'N/A')[:12]}...`")
                        st.markdown(f"**User:** {trace.get('user_id', 'N/A')}")
                        
                        if trace.get("tags"):
                            tag_html = " ".join([f"`{tag}`" for tag in trace["tags"]])
                            st.markdown(f"**Tags:** {tag_html}")
                    
                    with col2:
                        st.markdown(f"**Observations:** {trace.get('observations', 0)}")
                        if trace.get("timestamp"):
                            st.markdown(f"**Time:** {trace['timestamp']}")
                    
                    # Load detailed trace data
                    if st.button(f"View Details", key=f"view_{trace['id']}"):
                        detail = get_trace_details(trace["id"])
                        if detail:
                            st.session_state[f"trace_detail_{trace['id']}"] = detail
                    
                    # Show details if loaded
                    if f"trace_detail_{trace['id']}" in st.session_state:
                        detail = st.session_state[f"trace_detail_{trace['id']}"]
                        
                        st.divider()
                        st.markdown("**Input:**")
                        if detail.get("input"):
                            st.json(detail["input"] if isinstance(detail["input"], dict) else {"content": detail["input"]})
                        
                        st.markdown("**Output:**")
                        if detail.get("output"):
                            if isinstance(detail["output"], str) and len(detail["output"]) > 500:
                                st.text_area("Output", detail["output"], height=200)
                            else:
                                st.json(detail["output"] if isinstance(detail["output"], dict) else {"content": detail["output"]})
                        
                        # Observations/Spans
                        if detail.get("observations"):
                            st.markdown("**Spans:**")
                            for obs in detail["observations"]:
                                span_class = "span-llm" if obs["type"] == "generation" else \
                                            "span-tool" if "tool" in obs["name"].lower() else \
                                            "span-agent"
                                st.markdown(f"""
                                <div class="span-item {span_class}">
                                    <strong>{obs['name']}</strong> ({obs['type']})
                                </div>
                                """, unsafe_allow_html=True)

# ============== TAB 2: Decision Evaluation ==============
with tab2:
    st.header("Decision Evaluation")
    
    if not EVAL_AVAILABLE:
        st.error(f"Evaluation module not available: {EVAL_ERROR}")
        st.info("Make sure you have installed deepeval: `pip install deepeval>=1.0.0`")
    elif not TRACING_AVAILABLE:
        st.error("Tracing module required for evaluation")
    else:
        st.markdown("""
        Evaluate agent decisions using DeepEval metrics:
        - **Decision Quality**: Risk classification accuracy
        - **Tool Usage**: MCP tool selection effectiveness
        - **Alert Accuracy**: Alert severity and content correctness
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Select Trace to Evaluate")
            
            # Fetch traces for selection
            eval_traces = fetch_traces(20)
            
            if eval_traces:
                trace_options = {
                    f"{t['name']} ({t['id'][:8]}...)": t['id'] 
                    for t in eval_traces
                }
                selected_trace = st.selectbox(
                    "Choose a trace:",
                    options=list(trace_options.keys())
                )
                
                if selected_trace and st.button("🧪 Evaluate Selected Trace"):
                    trace_id = trace_options[selected_trace]
                    with st.spinner("Running evaluation..."):
                        trace_detail = get_trace_details(trace_id)
                        if trace_detail:
                            result = evaluate_trace(trace_detail, threshold=0.7)
                            result_store.add_result(result)
                            st.session_state["last_eval_result"] = result
                            st.success("Evaluation complete!")
                        else:
                            st.error("Could not fetch trace details")
        
        with col2:
            st.subheader("Evaluation History")
            summary = result_store.get_summary()
            
            st.metric("Total Evaluations", summary.get("total", 0))
            st.metric("Successful", summary.get("successful", 0))
            if summary.get("avg_score"):
                st.metric("Avg Score", f"{summary['avg_score']:.2f}")
        
        # Show last evaluation result
        if "last_eval_result" in st.session_state:
            st.divider()
            st.subheader("Latest Evaluation Result")
            
            result = st.session_state["last_eval_result"]
            
            if result.get("success"):
                col1, col2, col3 = st.columns(3)
                
                summary = result.get("summary", {})
                
                with col1:
                    passed = summary.get("passed", 0)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value score-high">{passed}</div>
                        <div class="metric-label">Passed</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    failed = summary.get("failed", 0)
                    score_class = "score-low" if failed > 0 else "score-high"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value {score_class}">{failed}</div>
                        <div class="metric-label">Failed</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    avg = summary.get("avg_score", 0)
                    score_class = "score-high" if avg >= 0.7 else "score-medium" if avg >= 0.5 else "score-low"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value {score_class}">{avg:.2f}</div>
                        <div class="metric-label">Avg Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show detailed results
                if result.get("results"):
                    st.markdown("**Detailed Results:**")
                    for r in result["results"]:
                        score_class = "score-high" if r.score >= 0.7 else "score-medium" if r.score >= 0.5 else "score-low"
                        st.markdown(f"""
                        <div class="span-item">
                            <strong>{r.name}</strong>: 
                            <span class="{score_class}">{r.score:.2f}</span>
                            {" ✅" if r.score >= 0.7 else " ⚠️" if r.score >= 0.5 else " ❌"}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error(f"Evaluation failed: {result.get('error', 'Unknown error')}")

# ============== TAB 3: Analytics ==============
with tab3:
    st.header("Analytics")
    
    if not TRACING_AVAILABLE:
        st.error("Tracing module required for analytics")
    else:
        traces = fetch_traces(trace_limit)
        
        if not traces:
            st.warning("No data available for analytics")
        else:
            # Create mock analytics data (in production, this would come from actual trace metrics)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Trace Distribution by Tag")
                
                # Count tags
                tag_counts = {}
                for t in traces:
                    for tag in (t.get("tags") or []):
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                if tag_counts:
                    df_tags = pd.DataFrame([
                        {"Tag": k, "Count": v} for k, v in tag_counts.items()
                    ])
                    fig = px.bar(df_tags, x="Tag", y="Count", color="Tag")
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No tagged traces found")
            
            with col2:
                st.subheader("Traces Over Time")
                
                # Mock time series (in production, parse actual timestamps)
                dates = pd.date_range(end=datetime.now(), periods=7, freq='D')
                trace_counts = [len(traces) // 7 + i % 3 for i in range(7)]
                
                df_time = pd.DataFrame({
                    "Date": dates,
                    "Traces": trace_counts
                })
                
                fig = px.line(df_time, x="Date", y="Traces", markers=True)
                fig.update_traces(line_color="#667eea")
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Sessions breakdown
            st.subheader("Session Distribution")
            
            session_counts = {}
            for t in traces:
                session = t.get("session_id", "unknown")[:8]
                session_counts[session] = session_counts.get(session, 0) + 1
            
            if session_counts:
                df_sessions = pd.DataFrame([
                    {"Session": k, "Traces": v} for k, v in list(session_counts.items())[:10]
                ])
                
                fig = px.pie(df_sessions, names="Session", values="Traces", hole=0.4)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Evaluation scores over time (if available)
            st.subheader("Evaluation Scores Trend")
            
            results = result_store.get_results(limit=20)
            if results:
                eval_data = []
                for r in results:
                    if r.get("success") and r.get("summary"):
                        eval_data.append({
                            "Timestamp": r.get("timestamp", ""),
                            "Score": r["summary"].get("avg_score", 0)
                        })
                
                if eval_data:
                    df_eval = pd.DataFrame(eval_data)
                    fig = px.line(df_eval, x="Timestamp", y="Score", markers=True)
                    fig.update_traces(line_color="#10b981")
                    fig.add_hline(y=0.7, line_dash="dash", line_color="orange", annotation_text="Threshold")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Run some evaluations to see score trends")
            else:
                st.info("No evaluation results yet. Use the Decision Evaluation tab to run evaluations.")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.8rem;">
    Predictive Telemetry Agent Dashboard | Langfuse + DeepEval Integration
</div>
""", unsafe_allow_html=True)
