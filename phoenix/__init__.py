"""
Phoenix Observability System for AI Agent Validation

Professional-grade monitoring and validation framework with:
- 5 deterministic validators (no LLM judges)
- Real-time dashboard at http://localhost:6006
- Persistent SQLite storage
- Auto-evaluation every 10 seconds

Usage:
    from phoenix import start_server
    start_server(auto_eval=True, eval_interval=10)

Or run directly:
    python phoenix/server.py --auto-eval --eval-interval 10
"""

__version__ = "1.0.0"
__all__ = ["server", "validators"]
