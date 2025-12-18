#!/usr/bin/env python3
"""
Standalone Phoenix Observability Server

This script launches Phoenix as a persistent server that continues
running independently of any agents. This allows you to:
- View traces even after agents stop
- Keep Phoenix UI available 24/7
- Analyze historical data anytime

Usage:
    python start_phoenix_standalone.py [--port 6006]
"""

import os
import sys
import signal
from pathlib import Path

# Set persistent Phoenix directory BEFORE importing phoenix
PROJECT_DIR = Path(__file__).parent
PHOENIX_DB_DIR = PROJECT_DIR / ".phoenix"
PHOENIX_DB_DIR.mkdir(exist_ok=True)

# Force Phoenix to use our persistent directory
os.environ["PHOENIX_WORKING_DIR"] = str(PHOENIX_DB_DIR)

# Now import Phoenix
try:
    import phoenix as px
except ImportError:
    print("❌ Phoenix not installed!")
    print("Install with: pip install arize-phoenix")
    sys.exit(1)


def start_phoenix_server(port: int = 6006):
    """Start Phoenix as a standalone persistent server"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PHOENIX OBSERVABILITY SERVER (STANDALONE)                 ║
║                                                                              ║
║  Persistent Phoenix server for LLM tracing and observability                ║
║  This server runs independently and stays available 24/7                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔍 Starting Phoenix server on port {port}...
📁 Data directory: {PHOENIX_DB_DIR}
""")
    
    # Launch Phoenix
    try:
        session = px.launch_app(port=port)
        
        print(f"""
{'='*80}
✅ PHOENIX SERVER IS RUNNING

   📊 Dashboard: http://localhost:{port}
   📁 Data stored in: {PHOENIX_DB_DIR}
   
   🔄 Agents can now connect and send traces to this server
   🌐 UI will remain available even after agents stop
   
   Press Ctrl+C to stop Phoenix server
{'='*80}
""")
        
        # Keep server running until interrupted
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⚠️  Shutting down Phoenix server...")
            print("✅ Phoenix stopped")
            
    except Exception as e:
        print(f"\n❌ Error starting Phoenix: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    # Parse port argument
    port = 6006
    
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--port" and i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                except ValueError:
                    print(f"❌ Invalid port: {sys.argv[i + 1]}")
                    sys.exit(1)
            elif arg in ["-h", "--help"]:
                print(__doc__)
                print("\nArguments:")
                print("  --port PORT    Phoenix UI port (default: 6006)")
                print("  -h, --help     Show this help message")
                sys.exit(0)
    
    # Start server
    start_phoenix_server(port)


if __name__ == "__main__":
    main()
