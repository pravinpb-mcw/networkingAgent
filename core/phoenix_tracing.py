"""
Phoenix Tracing Configuration for Network Monitoring Agents

This module sets up Arize Phoenix for LLM tracing and observability.
Phoenix provides visibility into:
- LangChain agent execution
- LLM calls and token usage
- Tool calls and their performance
- Error tracking and debugging
"""

import logging
import os
from typing import Optional
from pathlib import Path

# Set persistent Phoenix directory BEFORE any imports
# This prevents temp directory cleanup errors on Windows
_project_dir = Path(__file__).parent.parent
_phoenix_db_dir = _project_dir / ".phoenix"
_phoenix_db_dir.mkdir(exist_ok=True)

# CRITICAL: Set environment variables for persistent storage
# Use the same database as phoenix_persistent.py for consistency
_db_file = _phoenix_db_dir / "phoenix_traces.db"
os.environ["PHOENIX_WORKING_DIR"] = str(_phoenix_db_dir)
os.environ["PHOENIX_SQL_DATABASE_URL"] = f"sqlite:///{str(_db_file.absolute()).replace(chr(92), '/')}"
os.environ["PHOENIX_PORT"] = "6006"  # Default port for consistency

logger = logging.getLogger("phoenix-tracing")

# Global flag to track if Phoenix is initialized
_phoenix_initialized = False
_phoenix_session = None


def initialize_phoenix(
    project_name: str = "Network Monitoring Agents",
    launch_ui: bool = True,
    ui_port: int = 6006,
    enable_langchain_instrumentation: bool = True
) -> Optional[object]:
    """
    Initialize Arize Phoenix for tracing LLM applications.
    
    Args:
        project_name: Name of the project for Phoenix tracking
        launch_ui: Whether to launch the Phoenix UI (web interface)
        ui_port: Port for Phoenix UI (default: 6006)
        enable_langchain_instrumentation: Enable automatic LangChain tracing
    
    Returns:
        Phoenix session object if successful, None otherwise
    """
    global _phoenix_initialized, _phoenix_session
    
    if _phoenix_initialized:
        logger.info("Phoenix already initialized")
        return _phoenix_session
    
    try:
        import phoenix as px
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from opentelemetry import trace as trace_api
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk import trace as trace_sdk
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        
        # Launch Phoenix UI if requested (with persistent database)
        if launch_ui:
            # Check if Phoenix is already running
            try:
                import requests
                response = requests.get(f"http://localhost:{ui_port}", timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ Phoenix already running at http://localhost:{ui_port}")
                    print(f"\n{'='*80}")
                    print(f"🔍 PHOENIX ALREADY RUNNING: http://localhost:{ui_port}")
                    print(f"   Using existing Phoenix instance for tracing")
                    print(f"{'='*80}\n")
                    # Don't launch a new instance
                    launch_ui = False
            except:
                # Phoenix not running, we'll launch it
                pass
        
        if launch_ui:
            # Force persistent database - Phoenix needs this set before px.launch_app()
            phoenix_db_path = _phoenix_db_dir / "phoenix_traces.db"
            
            # Launch with explicit working directory
            session = px.launch_app(
                run_in_thread=True
                # Port is set via environment variable
            )
            _phoenix_session = session
            logger.info(f"✅ Phoenix UI launched at: http://localhost:{ui_port}")
            logger.info(f"📁 Phoenix data directory: {_phoenix_db_dir}")
            print(f"\n{'='*80}")
            print(f"🔍 PHOENIX OBSERVABILITY UI: http://localhost:{ui_port}")
            print(f"   Agent traces will be sent here while running")
            print(f"{'='*80}\n")
        
        # Set up tracer
        endpoint = f"http://127.0.0.1:{ui_port}/v1/traces"
        tracer_provider = trace_sdk.TracerProvider()
        tracer_provider.add_span_processor(
            SimpleSpanProcessor(OTLPSpanExporter(endpoint))
        )
        trace_api.set_tracer_provider(tracer_provider)
        
        # Instrument LangChain if enabled
        if enable_langchain_instrumentation:
            LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info("✅ LangChain instrumentation enabled")
        
        _phoenix_initialized = True
        logger.info(f"✅ Phoenix initialized for project: {project_name}")
        
        return _phoenix_session
        
    except ImportError as e:
        logger.error(f"❌ Phoenix dependencies not installed: {e}")
        logger.error("Install with: pip install arize-phoenix openinference-instrumentation-langchain opentelemetry-sdk opentelemetry-exporter-otlp")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to initialize Phoenix: {e}")
        import traceback
        traceback.print_exc()
        return None


def is_phoenix_enabled() -> bool:
    """Check if Phoenix tracing is enabled"""
    return _phoenix_initialized


def get_phoenix_session():
    """Get the current Phoenix session"""
    return _phoenix_session


def get_traces_dataframe(filter_query: Optional[str] = None):
    """
    Get traces as a pandas DataFrame for analysis.
    
    Args:
        filter_query: Optional filter query (e.g., 'span_kind == "LLM"')
    
    Returns:
        pandas DataFrame with trace data
    """
    try:
        import phoenix as px
        
        if not _phoenix_initialized:
            logger.warning("Phoenix not initialized")
            return None
        
        session = px.active_session()
        if session:
            if filter_query:
                return session.get_spans_dataframe(filter_query)
            else:
                return session.get_spans_dataframe()
        else:
            logger.warning("No active Phoenix session")
            return None
            
    except Exception as e:
        logger.error(f"Error getting traces dataframe: {e}")
        return None


def shutdown_phoenix():
    """Shutdown Phoenix (if running)"""
    global _phoenix_initialized, _phoenix_session
    
    try:
        # Note: We intentionally do NOT close the Phoenix UI
        # This allows the UI to remain available for trace viewing
        # even after the agent stops
        
        logger.info("Agent stopping - Phoenix UI will remain available")
        logger.info("To stop Phoenix UI, close the browser or kill the process")
        
        # Just reset flags, don't actually close Phoenix
        _phoenix_initialized = False
        _phoenix_session = None
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Convenience function for quick setup
def quick_start(agent_name: str = "Risk Score Agent", ui_port: int = 6006):
    """
    Quick start Phoenix with sensible defaults for network monitoring agents.
    
    Args:
        agent_name: Name of the agent being traced
        ui_port: Port for Phoenix UI
    
    Returns:
        Phoenix session or None
    """
    return initialize_phoenix(
        project_name=f"Network Monitoring - {agent_name}",
        launch_ui=True,
        ui_port=ui_port,
        enable_langchain_instrumentation=True
    )


if __name__ == "__main__":
    # Demo/test mode
    print("Starting Phoenix in demo mode...")
    session = quick_start("Test Agent")
    
    if session:
        print("\n✅ Phoenix is running!")
        print("Press Ctrl+C to stop...")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            shutdown_phoenix()
