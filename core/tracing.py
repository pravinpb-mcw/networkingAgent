"""
Langfuse Tracing Module for Predictive Telemetry Agent
Provides centralized tracing with LangChain callback integration
Uses Langfuse SDK v3 API
"""

import os
import uuid
import logging
from typing import Optional, Dict, Any, List
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
import httpx
import base64

from langfuse import get_client, observe, propagate_attributes
from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler

# Load environment variables
load_dotenv()

# Suppress OpenTelemetry errors BEFORE initializing Langfuse client
logging.getLogger("opentelemetry.sdk._shared_internal").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.sdk.trace.export").setLevel(logging.CRITICAL)

# Langfuse configuration from environment
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-3b7e7816-d943-4f19-94d7-036de2857a8a")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-0e3ab579-b733-4eb2-806c-ec8992b533a0")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "http://localhost:3000")

# Set environment variables for SDK v3 (required for get_client())
os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_HOST"] = LANGFUSE_BASE_URL

# Get client using SDK v3 singleton pattern
langfuse_client = get_client()


def verify_langfuse_connection() -> bool:
    """Verify Langfuse connection and authentication"""
    try:
        return langfuse_client.auth_check()
    except Exception as e:
        print(f"Langfuse connection failed: {e}")
        return False


def create_session_id() -> str:
    """Generate a new session ID for grouping traces"""
    return str(uuid.uuid4())


def get_langfuse_handler(parent_trace_id: Optional[str] = None) -> LangfuseCallbackHandler:
    """
    Create a Langfuse callback handler for LangChain.
    
    SDK v3 uses the `update_trace` callback to link LLM generations to existing traces.
    When parent_trace_id is provided, all LLM generations will be nested under that trace.
    
    Args:
        parent_trace_id: Parent trace ID to nest all LLM calls under.
                        If provided, generations will appear as children of this trace.
    
    Returns:
        LangfuseCallbackHandler configured for tracing
    """
    if parent_trace_id:
        # update_trace callback is called when a new trace/generation is created
        # Returning a dict with trace_id links the generation to the parent trace
        def link_to_parent(trace):
            return {"trace_id": parent_trace_id}
        
        return LangfuseCallbackHandler(update_trace=link_to_parent)
    
    # No parent - create independent traces
    return LangfuseCallbackHandler()


class TracingContext:
    """
    Context manager for tracing agent operations using SDK v3.
    Uses start_as_current_observation + propagate_attributes pattern.
    
    The trace_id property can be used to nest LLM callbacks under this trace,
    preventing separate traces for each tool call.
    """
    
    def __init__(
        self,
        name: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.session_id = session_id or create_session_id()
        self.user_id = user_id or "system"
        self.tags = tags or ["predictive-telemetry"]
        self.metadata = metadata or {}
        self.span = None
        self.langfuse_handler = None
        self.start_time = None
        self._span_context = None
        self._propagate_context = None
        self._trace_id = None
    
    @property
    def trace_id(self) -> Optional[str]:
        """Get the trace ID for nesting LLM callbacks under this trace."""
        if self._trace_id:
            return self._trace_id
        if self.span:
            # Get trace_id from the span/observation
            return getattr(self.span, 'trace_id', None)
        return None
    
    def __enter__(self):
        self.start_time = datetime.now()
        
        # Create the LangChain callback handler
        self.langfuse_handler = get_langfuse_handler()
        
        # Start span using SDK v3 context manager
        self._span_context = langfuse_client.start_as_current_observation(
            as_type="span",
            name=self.name,
            metadata=self.metadata
        )
        self.span = self._span_context.__enter__()
        
        # Propagate session_id, user_id, and tags to all child observations
        self._propagate_context = propagate_attributes(
            session_id=self.session_id,
            user_id=self.user_id,
            tags=self.tags
        )
        self._propagate_context.__enter__()
        
        # Alias for backward compatibility
        self.trace = self.span
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if self.span:
            if exc_type:
                self.span.update(
                    output={"error": str(exc_val)},
                    metadata={**self.metadata, "duration_seconds": duration, "success": False}
                )
            else:
                self.span.update(
                    metadata={**self.metadata, "duration_seconds": duration, "success": True}
                )
        
        # Exit propagate context first
        if self._propagate_context:
            self._propagate_context.__exit__(exc_type, exc_val, exc_tb)
        
        # Exit span context manager
        if self._span_context:
            self._span_context.__exit__(exc_type, exc_val, exc_tb)
        
        # Flush to ensure all events are sent
        langfuse_client.flush()
        
        return False  # Don't suppress exceptions
    
    def log_mcp_tool_call(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Optional[Any] = None,
        error: Optional[str] = None
    ):
        """Log an MCP tool call as a span"""
        with langfuse_client.start_as_current_observation(
            as_type="span",
            name=f"mcp_tool:{tool_name}",
            input=args,
            metadata={"tool_name": tool_name, "success": error is None}
        ) as span:
            span.update(output=result if result else {"error": error})
    
    def log_agent_step(
        self,
        step_name: str,
        input_data: Any,
        output_data: Any,
        step_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an agent reasoning step"""
        with langfuse_client.start_as_current_observation(
            as_type="span",
            name=f"agent_step:{step_name}",
            input=input_data,
            metadata=step_metadata or {}
        ) as span:
            span.update(output=output_data)
    
    def log_generation(
        self,
        name: str,
        model: str,
        prompt: str,
        completion: str,
        tokens: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None
    ):
        """Log an LLM generation"""
        with langfuse_client.start_as_current_observation(
            as_type="generation",
            name=name,
            model=model,
            input=prompt,
            metadata={"cost": cost} if cost else {}
        ) as gen:
            gen.update(output=completion, usage_details=tokens)


def trace_agent_run(
    name: str = "agent-run",
    tags: Optional[List[str]] = None
):
    """
    Decorator for tracing agent runs.
    
    Usage:
        @trace_agent_run(name="predictive-analysis", tags=["monitoring"])
        async def run_analysis(self):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with TracingContext(name=name, tags=tags) as ctx:
                kwargs['_tracing_context'] = ctx
                try:
                    result = await func(*args, **kwargs)
                    if ctx.span:
                        ctx.span.update(output={"result": "success"})
                    return result
                except Exception as e:
                    if ctx.span:
                        ctx.span.update(output={"error": str(e)})
                    raise
        return wrapper
    return decorator


# ============ REST API functions for fetching traces ============
# SDK v3 doesn't expose get_traces(), so we use the REST API

def get_recent_traces(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch recent traces from Langfuse for dashboard display.
    Uses REST API since SDK v3 doesn't have get_traces method.
    """
    try:
        auth_string = f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/json"
        }
        
        url = f"{LANGFUSE_BASE_URL}/api/public/traces?limit={limit}"
        
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        
        data = response.json()
        traces = data.get("data", [])
        
        return [
            {
                "id": t.get("id") or "",
                "name": t.get("name") or "Unnamed",
                "session_id": t.get("sessionId") or "",
                "user_id": t.get("userId") or "",
                "timestamp": t.get("timestamp") or "",
                "tags": t.get("tags") or [],
                "metadata": t.get("metadata") or {},
                "observations": len(t.get("observations") or [])
            }
            for t in traces
        ]
    except Exception as e:
        print(f"Error fetching traces: {e}")
        return []


def get_trace_details(trace_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed information about a specific trace.
    Uses REST API since SDK v3 doesn't have get_trace method.
    """
    try:
        auth_string = f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/json"
        }
        
        url = f"{LANGFUSE_BASE_URL}/api/public/traces/{trace_id}"
        
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        
        trace = response.json()
        
        return {
            "id": trace.get("id") or "",
            "name": trace.get("name") or "Unnamed",
            "session_id": trace.get("sessionId") or "",
            "user_id": trace.get("userId") or "",
            "timestamp": trace.get("timestamp") or "",
            "input": trace.get("input"),
            "output": trace.get("output"),
            "metadata": trace.get("metadata") or {},
            "tags": trace.get("tags") or [],
            "observations": [
                {
                    "id": obs.get("id") or "",
                    "name": obs.get("name") or "",
                    "type": obs.get("type") or "",
                    "start_time": obs.get("startTime") or "",
                    "end_time": obs.get("endTime") or "",
                    "input": obs.get("input"),
                    "output": obs.get("output"),
                    "metadata": obs.get("metadata") or {}
                }
                for obs in trace.get("observations") or []
            ]
        }
    except Exception as e:
        print(f"Error fetching trace {trace_id}: {e}")
        return None


# Module test
if __name__ == "__main__":
    if verify_langfuse_connection():
        print("✅ Langfuse connection verified!")
    else:
        print("❌ Langfuse connection failed. Check your credentials and host.")
