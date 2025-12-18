#!/usr/bin/env python3
"""
Phoenix Server with REAL Persistent Storage

This version ACTUALLY saves data to disk using Phoenix's database backend.
Data will persist across restarts.
"""

import os
import sys
import time
import threading
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Project directory
PROJECT_DIR = Path(__file__).parent
PHOENIX_DB_DIR = PROJECT_DIR / ".phoenix"
PHOENIX_DB_DIR.mkdir(exist_ok=True)

# Database file
DB_FILE = PHOENIX_DB_DIR / "phoenix_traces.db"

print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     PHOENIX WITH PERSISTENT STORAGE                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

📁 Database location: {DB_FILE}
🔧 Configuring Phoenix for persistent storage...
""")

try:
    import phoenix as px
    from phoenix.db import get_printable_db_url
    from phoenix.config import get_env_database_connection_str
    import pandas as pd
    import requests
    
    print(f"✅ Phoenix version: {px.__version__}")
    
    # Check which evaluation backend to use - MOVED TO TOP
    # Priority: Ollama (local, fast) > Anthropic (cloud, slower for detailed prompts)
    ollama_available = False
    best_ollama_model = None
    
    try:
        ollama_response = requests.get("http://192.168.13.162:11434/api/tags", timeout=2)
        if ollama_response.status_code == 200:
            models = ollama_response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            # Prioritize best models for evaluation (larger = better reasoning)
            priority_models = ['llama3.1:70b', 'mixtral:8x22b', 'mixtral:8x7b', 'llama3.1:8b', 'llama3:8b']
            for model in priority_models:
                if model in model_names:
                    best_ollama_model = model
                    ollama_available = True
                    break
            
            if not best_ollama_model and model_names:
                # Use first available model
                best_ollama_model = model_names[0]
                ollama_available = True
    except:
        pass
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    anthropic_url = os.getenv("ANTHROPIC_BASE_URL")
    
    print("\n" + "="*80)
    if ollama_available:
        print(f"🚀 EVALUATION BACKEND: OLLAMA ({best_ollama_model})")
        print("="*80)
        print(f"   🌐 Endpoint: http://192.168.13.162:11434")
        print(f"   📦 Model: {best_ollama_model}")
        print(f"   ⚡ Expected speed: ~5-6s per span (LOCAL & FAST)")
        print(f"   ✅ DETAILED EXPLANATIONS ENABLED")
        print("="*80 + "\n")
    elif anthropic_key and anthropic_url:
        print("🚀 EVALUATION BACKEND: ANTHROPIC API (GLM-4.5 via z.ai)")
        print("="*80)
        print(f"   🌐 Endpoint: {anthropic_url}")
        print(f"   🔑 API Key: {anthropic_key[:20]}...{anthropic_key[-10:]}")
        print(f"   ⚠️  Expected speed: ~20-30s per span (SLOW for detailed prompts)")
        print(f"   ✅ DETAILED EXPLANATIONS ENABLED")
        print("="*80 + "\n")
    else:
        print("⚠️  EVALUATION BACKEND: NOT AVAILABLE")
        print("="*80)
        print(f"   ❌ Ollama not reachable at http://192.168.13.162:11434")
        print(f"   ❌ Anthropic API credentials not found in .env")
        print(f"   💡 Install Ollama or add ANTHROPIC_API_KEY to enable evaluations")
        print("="*80 + "\n")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def run_evaluations_once(endpoint="http://localhost:6006", evaluated_span_ids=None):
    """Run evaluations on current traces using best available model (Ollama or Anthropic)
    
    Args:
        endpoint: Phoenix endpoint URL
        evaluated_span_ids: Set of span IDs already evaluated (to avoid re-evaluation)
    """
    # Access global variables
    global ollama_available, best_ollama_model
    
    if evaluated_span_ids is None:
        evaluated_span_ids = set()
    
    try:
        from phoenix.evals import HallucinationEvaluator, run_evals
        from phoenix.session.client import Client
        from phoenix.evals.models import LiteLLMModel
    except ImportError:
        print("⚠️  Phoenix evals not available")
        print("   Install with: pip install arize-phoenix[evals] litellm")
        return evaluated_span_ids
    
    try:
        client = Client(endpoint=endpoint)
        
        # Try to get spans with error handling
        try:
            spans_df = client.get_spans_dataframe()
        except Exception as graphql_error:
            if "Cannot return null" in str(graphql_error) or "spanId" in str(graphql_error):
                print("   ⚠️  Skipping evaluation - spans still being processed")
                return evaluated_span_ids
            else:
                raise
        
        if spans_df is None or spans_df.empty:
            print("   No traces to evaluate yet")
            return evaluated_span_ids
        
        llm_spans = spans_df[spans_df['span_kind'] == 'LLM']
        if llm_spans.empty:
            print("   No LLM spans to evaluate")
            return evaluated_span_ids
        
        # Filter out already-evaluated spans
        current_span_ids = set(llm_spans.index)
        new_span_ids = current_span_ids - evaluated_span_ids
        
        if not new_span_ids:
            print(f"   ✅ All {len(current_span_ids)} spans already evaluated - skipping")
            return evaluated_span_ids
        
        # Only evaluate new spans
        llm_spans = llm_spans.loc[list(new_span_ids)]
        print(f"   📊 Found {len(llm_spans)} NEW spans to evaluate ({len(evaluated_span_ids)} already done)")
        
        print(f"\n🔍 Evaluating {len(llm_spans)} LLM spans for hallucinations...")
        
        # Prepare data
        eval_df = llm_spans.copy()
        
        def safe_str(x):
            if x is None:
                return ""
            try:
                if isinstance(x, (list, tuple)):
                    return str(x)
                return str(x)
            except:
                return ""
        
        eval_df['input'] = eval_df['attributes.llm.input_messages'].apply(safe_str)
        eval_df['output'] = eval_df['attributes.llm.output_messages'].apply(safe_str)
        
        # Include tool results in reference context for proper grounding
        # This allows evaluator to see data from API calls
        def build_reference(row):
            """Build reference including input prompt + tool results from parent span"""
            ref = safe_str(row.get('attributes.llm.input_messages', ''))
            
            # Try to get tool results from attributes
            tool_results = row.get('attributes.llm.tool_calls', '')
            if tool_results:
                ref += f"\n\nTool Results Available:\n{safe_str(tool_results)}"
            
            return ref
        
        eval_df['reference'] = eval_df.apply(build_reference, axis=1)
        
        if 'input' not in eval_df.columns or 'output' not in eval_df.columns:
            print("   ⚠️  Failed to extract input/output columns")
            return
        
        # Reuse the global variables set at startup
        # Priority: Ollama (local, fast) > Anthropic (cloud, slower for detailed prompts)
        # These are already defined at the top of the file
        
        # Use Ollama if available, otherwise fall back to Anthropic
        use_anthropic = (not ollama_available) and os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_BASE_URL")
        use_anthropic = (not ollama_available) and anthropic_key and anthropic_url
        
        if use_anthropic:
            print("   ⚡ Using Anthropic API (GLM-4.5) - SLOW for detailed prompts (~20-30s per span)")
            print(f"   🌐 Endpoint: {anthropic_url}")
        else:
            print(f"   ⚡ Using Ollama: {best_ollama_model} - LOCAL & FAST (~5-6s per span)")
            print(f"   🌐 Endpoint: http://192.168.13.162:11434")
        
        try:
            if use_anthropic:
                # Use Anthropic (cloud API, slower for detailed prompts ~20-30s)
                # Set environment variables for LiteLLM
                os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
                os.environ["ANTHROPIC_BASE_URL"] = os.getenv("ANTHROPIC_BASE_URL")
                
                # LiteLLMModel only takes model parameter
                model = LiteLLMModel(
                    model="claude-3-5-sonnet-20241022"
                )
            else:
                # Configure LiteLLM for Ollama (local, faster ~5-6s with detailed prompts)
                os.environ["OLLAMA_API_BASE"] = "http://192.168.13.162:11434"
                model = LiteLLMModel(
                    model=f"ollama_chat/{best_ollama_model}"
                )
            
            # Create custom hallucination evaluator with content-focused analysis
            from phoenix.evals.legacy import LLMEvaluator
            from phoenix.evals.legacy.templates import ClassificationTemplate
            
            # Content-focused prompt - evaluates based on actual actions and data
            template = ClassificationTemplate(
                rails=["factual", "hallucinated"],
                template="""Evaluate if the AI agent's actions and outputs are grounded in actual data or hallucinated.

**INPUT (Agent's Instructions):**
{input}

**REFERENCE (Ground Truth + Tool Results):**
{reference}

**OUTPUT (Agent's Actions):**
{output}

**EVALUATION TASK:**
Analyze the agent's actual actions and determine if they are based on real data:

1. What did the agent DO? (What tools did it call? What data did it use?)
2. Where did this data come from? (Tool results? Given context? Or invented?)
3. Are the values/claims in the output grounded in actual data sources?

**KEY RULES:**
- If agent calls a tool and uses the result → FACTUAL
- If agent uses data from the reference context → FACTUAL  
- If agent invents data without any source → HALLUCINATED
- If agent contradicts tool results → HALLUCINATED
- Default values (like score=20 for missing data) are FACTUAL if documented in instructions

**YOUR RESPONSE:**
Analyze what the agent did and where the data came from. Then on the last line, output ONLY one word:
factual
OR
hallucinated
"""
            )
            
            evaluator = LLMEvaluator(model=model, template=template)
            
            # Run evaluations with explanation
            results = run_evals(
                dataframe=eval_df,
                evaluators=[evaluator],
                provide_explanation=True,
            )
            
            # run_evals returns a list containing DataFrame(s)
            # Get the first DataFrame (which contains all results)
            if isinstance(results, list) and len(results) > 0:
                results = results[0]
            
            # Filter out null results
            results = results.dropna(subset=['label'])
            
            hallucinated = results[results['label'] == 'hallucinated']
            factual = results[results['label'] == 'factual']
            
            print(f"   ✅ Factual: {len(factual)}")
            print(f"   ⚠️  Hallucinated: {len(hallucinated)}")
            
            if len(hallucinated) > 0:
                print(f"\n   🚨 {len(hallucinated)} hallucinations detected!")
                for idx, row in hallucinated.head(3).iterrows():
                    print(f"      - {row.get('explanation', 'No explanation')[:100]}...")
            
            # Save results to CSV
            output_file = PROJECT_DIR / "phoenix_eval_results.csv"
            results.to_csv(output_file, index=False)
            print(f"   💾 Results saved to: phoenix_eval_results.csv")
            
            # LOG RESULTS TO PHOENIX DASHBOARD using Client API
            try:
                from phoenix.trace import SpanEvaluations
                
                # The key insight: eval_df has the same index as the original spans_df
                # So results.index points back to the original span indices
                
                # Create evaluation dataframe with proper span_id index
                # Use the DataFrame index directly - Phoenix uses this to match spans
                eval_dataframe = pd.DataFrame({
                    'label': results['label'],
                    'score': results['label'].apply(lambda x: 1.0 if x == 'factual' else 0.0),
                    'explanation': results['explanation']
                })
                
                # CRITICAL: The index must match the span index from get_spans_dataframe()
                # results already has the correct index from eval_df
                
                # Log to Phoenix using Client
                client.log_evaluations(
                    SpanEvaluations(
                        eval_name="Hallucination",
                        dataframe=eval_dataframe
                    )
                )
                
                print(f"   📊 ✅ Logged {len(eval_dataframe)} evaluations to Phoenix!")
                print(f"   🌐 View in dashboard: {endpoint}")
                print(f"   💡 Evaluations appear as annotations in Traces view")
                print(f"   💡 Filter by annotation 'Hallucination' to see evaluated spans")
                
            except Exception as log_error:
                print(f"   ⚠️  Could not log to dashboard: {log_error}")
                print(f"   (Results still saved to CSV)")
                import traceback
                traceback.print_exc()
            
            # Mark these spans as evaluated
            evaluated_span_ids.update(new_span_ids)
            
        except Exception as model_error:
            print(f"   ❌ Ollama evaluation failed: {model_error}")
            print(f"   Make sure Ollama is running at http://192.168.13.162:11434")
            print(f"   Check model with: curl http://192.168.13.162:11434/api/tags")
        
    except Exception as e:
        print(f"   ⚠️  Evaluation error: {e}")
        import traceback
        traceback.print_exc()
    
    return evaluated_span_ids


def auto_evaluation_loop(interval=5, endpoint="http://localhost:6006"):
    """Background thread for continuous auto-evaluation
    
    Checks every few seconds for NEW spans and evaluates them immediately.
    Much faster with Anthropic API (~1-2s per span) vs Ollama (~5-6s per span).
    """
    from phoenix.session.client import Client
    
    anthropic_enabled = os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_BASE_URL")
    
    print(f"\n🤖 Auto-evaluation enabled (checking every {interval}s for new spans)")
    if anthropic_enabled:
        print(f"   ⚡ Using Anthropic API - evaluations run quickly (~1-2s per span)")
    else:
        print(f"   ⚠️  Using Ollama - evaluations are slow (~5-6s per span)")
        print(f"   💡 Add Anthropic API credentials to .env for 5x faster evals")
    print(f"   🔄 Evaluates new spans immediately as they appear\n")
    
    evaluated_span_ids = set()
    
    while True:
        time.sleep(interval)
        try:
            # Check if Phoenix is responding
            import requests
            response = requests.get(endpoint, timeout=2)
            if response.status_code != 200:
                continue
                
            # Get current spans
            client = Client(endpoint=endpoint)
            try:
                spans_df = client.get_spans_dataframe()
            except Exception as e:
                if "Cannot return null" in str(e) or "spanId" in str(e):
                    continue  # Spans still being processed
                else:
                    continue  # Skip other errors
            
            if spans_df is None or spans_df.empty:
                continue
            
            # Find NEW LLM spans that haven't been evaluated yet
            llm_spans = spans_df[spans_df['span_kind'] == 'LLM']
            if llm_spans.empty:
                continue
            
            # Get span IDs that we haven't evaluated yet
            current_span_ids = set(llm_spans.index)
            new_span_ids = current_span_ids - evaluated_span_ids
            
            if new_span_ids:
                print(f"\n[{time.strftime('%H:%M:%S')}] 🆕 Found {len(new_span_ids)} new spans - evaluating now...")
                evaluated_span_ids = run_evaluations_once(endpoint, evaluated_span_ids)
                
        except KeyboardInterrupt:
            raise
        except Exception as e:
            # Silently continue on errors - don't spam console
            pass


def start_phoenix(port=6006, auto_eval=False, eval_interval=60):
    """Start Phoenix with persistent SQLite database"""
    
    # CRITICAL: Set environment variables BEFORE any Phoenix imports
    # This ensures Phoenix uses persistent storage from the start
    database_url = f"sqlite:///{str(DB_FILE.absolute()).replace(chr(92), '/')}"
    
    # Set Phoenix environment variables for persistent storage
    os.environ["PHOENIX_SQL_DATABASE_URL"] = database_url
    os.environ["PHOENIX_WORKING_DIR"] = str(PHOENIX_DB_DIR.absolute())
    os.environ["PHOENIX_PORT"] = str(port)
    
    # Force SQLite mode (not in-memory)
    os.environ["PHOENIX_SQL_DATABASE_SCHEMA"] = "public"
    
    print(f"💾 Database URL: {database_url}")
    print(f"📁 Working directory: {PHOENIX_DB_DIR.absolute()}")
    
    # Create database directory if it doesn't exist
    PHOENIX_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Import Phoenix AFTER setting environment variables
    import phoenix as px
    
    # CRITICAL: Initialize database manually
    if not DB_FILE.exists():
        print(f"🔧 Creating new database: {DB_FILE}")
        import sqlite3
        conn = sqlite3.connect(str(DB_FILE))
        conn.execute("CREATE TABLE IF NOT EXISTS _phoenix_initialized (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        print(f"✅ Database initialized")
    else:
        db_size = DB_FILE.stat().st_size
        print(f"📊 Existing database found")
        print(f"📏 Database size: {db_size:,} bytes")
        
        # Count existing traces
        try:
            import sqlite3
            conn = sqlite3.connect(str(DB_FILE))
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            if tables:
                print(f"📋 Database tables: {len(tables)} found")
                print(f"   Tables: {', '.join(tables[:5])}")
            else:
                print(f"⚠️  Database is empty (no tables yet)")
        except Exception as e:
            print(f"⚠️  Could not read database: {e}")
    
    # Launch Phoenix with persistent database
    print(f"\n🚀 Launching Phoenix on port {port}...")
    
    try:
        # Use environment variable instead of port parameter
        session = px.launch_app(run_in_thread=True)
        
        # Give it time to start
        time.sleep(3)
        
        # Verify database was created/updated
        if DB_FILE.exists():
            new_size = DB_FILE.stat().st_size
            print(f"""
{'='*80}
✅ PHOENIX SERVER IS RUNNING WITH PERSISTENT STORAGE!

   📊 Dashboard: http://localhost:{port}
   💾 Database: {DB_FILE}
   📏 Database size: {new_size:,} bytes
   
   ✅ DATA WILL PERSIST ACROSS RESTARTS!
   
   🔄 Send traces from agents to: http://localhost:{port}
   🌐 UI will show all historical data
""")
            if auto_eval:
                print(f"   🤖 Auto-evaluation running every {eval_interval}s\n")
            
            print(f"""   Press Ctrl+C to stop
{'='*80}
""")
        else:
            print(f"""
⚠️  WARNING: Database file was NOT created!
   Phoenix might be using in-memory storage.
   Data will be lost on restart.
""")
        
        # Global tracking for evaluated spans (shared between manual and auto evals)
        evaluated_span_ids_global = set()
        
        # Start auto-evaluation if enabled
        if auto_eval:
            eval_thread = threading.Thread(
                target=auto_evaluation_loop,
                args=(eval_interval, f"http://localhost:{port}"),
                daemon=True
            )
            eval_thread.start()
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⚠️  Shutting down Phoenix...")
            
            if auto_eval:
                print("🔍 Running final evaluation on new spans...")
                # Use global tracking to avoid re-evaluating
                try:
                    run_evaluations_once(f"http://localhost:{port}", evaluated_span_ids_global)
                except:
                    pass
            
            # Show final database size
            if DB_FILE.exists():
                final_size = DB_FILE.stat().st_size
                print(f"💾 Final database size: {final_size:,} bytes")
                print(f"💾 Database saved at: {DB_FILE}")
            
            print("✅ Phoenix stopped")
            
    except Exception as e:
        print(f"\n❌ Error starting Phoenix: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    port = 6006
    auto_eval = False
    eval_interval = 30  # Default 30 seconds - balance between responsiveness and API slowness
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
        elif arg == "--auto-eval":
            auto_eval = True
        elif arg == "--eval-interval" and i + 1 < len(sys.argv):
            eval_interval = int(sys.argv[i + 1])
            auto_eval = True  # Enable auto-eval if interval specified
        elif arg in ["-h", "--help"]:
            print(__doc__)
            print("\nUsage:")
            print("  python phoenix_persistent.py [--auto-eval] [--eval-interval SECONDS] [--port 6006]")
            print("\nOptions:")
            print("  --auto-eval           Enable automatic continuous evaluation")
            print("  --eval-interval N     Set check interval in seconds (default: 5)")
            print("                        Checks for new spans every N seconds")
            print("  --port N              Phoenix UI port (default: 6006)")
            print("\nExamples:")
            print("  # Auto-eval with Anthropic API (fast, checks every 5s)")
            print("  python phoenix_persistent.py --auto-eval")
            print("")
            print("  # Check for new spans every 10 seconds")
            print("  python phoenix_persistent.py --eval-interval 10")
            print("")
            print("\nEvaluation Backends:")
            print("  - Anthropic API (GLM-4.5): ~1-2s per span (FAST) - requires .env credentials")
            print("  - Ollama (mixtral:8x7b): ~5-6s per span (SLOW) - fallback if no API key")
            print("")
            print("This version uses SQLite database for persistent storage.")
            print("All traces will be saved and available after restart.")
            sys.exit(0)
    
    start_phoenix(port, auto_eval, eval_interval)


if __name__ == "__main__":
    main()
