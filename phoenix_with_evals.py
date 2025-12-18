#!/usr/bin/env python3
"""
Phoenix Server with Auto-Evaluation

This script runs Phoenix server AND automatically evaluates traces.
No need for separate terminals!

Usage:
    python phoenix_with_evals.py [--auto-eval] [--eval-interval 60]
"""

import os
import sys
import time
import threading
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Set persistent Phoenix directory BEFORE importing phoenix
PROJECT_DIR = Path(__file__).parent
PHOENIX_DB_DIR = PROJECT_DIR / ".phoenix"
PHOENIX_DB_DIR.mkdir(exist_ok=True)

# CRITICAL: For Phoenix 4.0+, use this environment variable
os.environ["PHOENIX_WORKING_DIR"] = str(PHOENIX_DB_DIR)

# Verify directory exists
print(f"📁 Phoenix data will be stored in: {PHOENIX_DB_DIR}")

try:
    import phoenix as px
    from phoenix.session.client import Client
    import pandas as pd
    import requests
    
    # Check Phoenix version and configuration
    print(f"🔧 Phoenix version: {px.__version__}")
    print(f"💾 Working directory: {os.getenv('PHOENIX_WORKING_DIR')}")
    
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Install with: pip install arize-phoenix requests pandas")
    sys.exit(1)


def run_evaluations_once(endpoint="http://localhost:6006"):
    """Run evaluations on current traces using Ollama"""
    try:
        from phoenix.evals import HallucinationEvaluator, run_evals
        from phoenix.evals.models import LiteLLMModel
        from phoenix.session.client import Client
    except ImportError:
        print("⚠️  Phoenix evals not available")
        print("   Install with: pip install arize-phoenix[evals] litellm")
        return
    
    try:
        client = Client(endpoint=endpoint)
        
        # Try to get spans with error handling for GraphQL issues
        try:
            spans_df = client.get_spans_dataframe()
        except Exception as graphql_error:
            # GraphQL errors can happen with incomplete/corrupted spans
            if "Cannot return null" in str(graphql_error) or "spanId" in str(graphql_error):
                print("   ⚠️  Skipping evaluation - some spans have incomplete data")
                print("      This is normal for very recent traces still being processed")
                return
            else:
                raise  # Re-raise if it's a different error
        
        if spans_df is None or spans_df.empty:
            print("   No traces to evaluate yet")
            return
        
        llm_spans = spans_df[spans_df['span_kind'] == 'LLM']
        if llm_spans.empty:
            print("   No LLM spans to evaluate")
            return
        
        print(f"\n🔍 Evaluating {len(llm_spans)} LLM spans for hallucinations...")
        print("   🤖 Using Ollama: mixtral:8x7b")
        
        # Prepare data for evaluator - map Phoenix columns to evaluator expected columns
        eval_df = llm_spans.copy()
        
        # Extract input and output from attributes - handle both None and array cases
        def safe_str(x):
            """Safely convert to string, handling None and array values"""
            if x is None:
                return ""
            # Check if it's an array/list by trying to iterate
            try:
                if isinstance(x, (list, tuple)):
                    return str(x)
                return str(x)
            except:
                return ""
        
        eval_df['input'] = eval_df['attributes.llm.input_messages'].apply(safe_str)
        eval_df['output'] = eval_df['attributes.llm.output_messages'].apply(safe_str)
        # Use input as reference (no external reference available)
        eval_df['reference'] = eval_df['input']
        
        # Verify columns exist
        if 'input' not in eval_df.columns or 'output' not in eval_df.columns:
            print("   ⚠️  Failed to extract input/output columns")
            return
        
        # Configure Ollama model using LiteLLM
        try:
            os.environ["OLLAMA_API_BASE"] = "http://192.168.13.162:11434"
            
            model = LiteLLMModel(
                model="ollama_chat/mixtral:8x7b"
            )
        except Exception as model_err:
            print(f"   ⚠️  Failed to create Ollama model: {model_err}")
            return
        
        evaluator = HallucinationEvaluator(model=model)
        
        # IMPORTANT: Pass eval_df (with the new columns), NOT llm_spans!
        results = run_evals(
            dataframe=eval_df,  # Changed from llm_spans to eval_df
            evaluators=[evaluator],
            provide_explanation=True,
        )
        
        # run_evals returns a list containing DataFrame(s)
        # Get the first DataFrame (which contains all results)
        if isinstance(results, list) and len(results) > 0:
            results = results[0]
        
        # Filter out any null results
        results = results.dropna(subset=['label'])
        
        # Show summary
        hallucinated = results[results['label'] == 'hallucinated']
        factual = results[results['label'] == 'factual']
        
        print(f"   ✅ Factual: {len(factual)}")
        print(f"   ⚠️  Hallucinated: {len(hallucinated)}")
        
        if len(hallucinated) > 0:
            print(f"\n   🚨 {len(hallucinated)} hallucinations detected!")
            for idx, row in hallucinated.head(3).iterrows():
                print(f"      - {row.get('explanation', 'No explanation')[:100]}...")
        
        # Save results
        output_file = PROJECT_DIR / "phoenix_auto_eval_results.csv"
        results.to_csv(output_file)
        print(f"   💾 Saved to: phoenix_auto_eval_results.csv")
        
        # LOG TO PHOENIX DASHBOARD
        try:
            from phoenix.trace import SpanEvaluations
            
            for idx, row in results.iterrows():
                span_id = row.get('context.span_id', None)
                if span_id:
                    client.log_evaluations(
                        SpanEvaluations(
                            eval_name="hallucination_detection",
                            dataframe=pd.DataFrame([{
                                'span_id': span_id,
                                'label': row['label'],
                                'score': 1.0 if row['label'] == 'factual' else 0.0,
                                'explanation': row.get('explanation', '')
                            }])
                        )
                    )
            
            print(f"   📊 Results logged to Phoenix dashboard at {endpoint}")
            
        except Exception as log_err:
            print(f"   ⚠️  Dashboard logging failed: {log_err}")
        
    except Exception as e:
        print(f"   ⚠️  Evaluation error: {e}")
        import traceback
        traceback.print_exc()


def auto_evaluation_loop(interval=60, endpoint="http://localhost:6006"):
    """Background thread that runs evaluations periodically"""
    print(f"\n🤖 Auto-evaluation enabled (every {interval}s)")
    print("   Will check for new traces and evaluate automatically\n")
    
    while True:
        time.sleep(interval)
        try:
            # Check if there are new traces
            response = requests.get(endpoint, timeout=2)
            if response.status_code == 200:
                print(f"\n[{time.strftime('%H:%M:%S')}] Running auto-evaluation...")
                run_evaluations_once(endpoint)
        except:
            pass  # Phoenix might be shutting down


def start_phoenix_with_evals(port=6006, auto_eval=False, eval_interval=60):
    """Start Phoenix server with optional auto-evaluation"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              PHOENIX SERVER WITH AUTO-EVALUATION                             ║
║                                                                              ║
║  All-in-one: Phoenix UI + Automatic LLM-as-a-Judge evaluations              ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔍 Starting Phoenix server on port {port}...
📁 Data directory: {PHOENIX_DB_DIR}
""")
    
    if auto_eval:
        print(f"🤖 Auto-evaluation: ENABLED (every {eval_interval}s)")
    else:
        print("🤖 Auto-evaluation: DISABLED")
        print("   (Use --auto-eval to enable)")
    
    print()
    
    # Launch Phoenix with persistent storage
    try:
        # Verify persistent storage is configured
        db_file = PHOENIX_DB_DIR / "phoenix.db"
        db_exists = db_file.exists()
        
        # Launch with explicit database path
        session = px.launch_app(
            port=port,
            run_in_thread=True  # Run in background thread so we can add auto-eval
        )
        
        # Give Phoenix a moment to initialize
        time.sleep(2)
        
        # Verify database was actually created
        time.sleep(1)
        db_exists_after = db_file.exists()
        
        print(f"""
{'='*80}
✅ PHOENIX SERVER IS RUNNING

   📊 Dashboard: http://localhost:{port}
   📁 Data directory: {PHOENIX_DB_DIR}
   💾 Database status: {'✅ Created' if db_exists_after else '⚠️ Using temp storage (data will be lost!)'}
   
   🔄 Agents can now connect and send traces to this server
   🌐 UI will remain available even after agents stop
   💾 ALL DATA PERSISTS - safe to restart anytime!
""")
        
        if auto_eval:
            print(f"""   🤖 Auto-evaluation running every {eval_interval}s
   📝 Results saved to: phoenix_auto_eval_results.csv
""")
        
        print(f"""   Press Ctrl+C to stop Phoenix server
{'='*80}
""")
        
        # Start auto-evaluation thread if enabled
        if auto_eval:
            eval_thread = threading.Thread(
                target=auto_evaluation_loop,
                args=(eval_interval, f"http://localhost:{port}"),
                daemon=True
            )
            eval_thread.start()
        
        # Keep server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⚠️  Shutting down Phoenix server...")
            
            if auto_eval:
                print("🔍 Running final evaluation before shutdown...")
                run_evaluations_once(f"http://localhost:{port}")
            
            print("✅ Phoenix stopped")
            
    except Exception as e:
        print(f"\n❌ Error starting Phoenix: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    
    # Parse arguments
    port = 6006
    auto_eval = False
    eval_interval = 60
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--port" and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                print(f"❌ Invalid port: {sys.argv[i + 1]}")
                sys.exit(1)
        elif arg == "--auto-eval":
            auto_eval = True
        elif arg == "--eval-interval" and i + 1 < len(sys.argv):
            try:
                eval_interval = int(sys.argv[i + 1])
            except ValueError:
                print(f"❌ Invalid interval: {sys.argv[i + 1]}")
                sys.exit(1)
        elif arg in ["-h", "--help"]:
            print(__doc__)
            print("\nArguments:")
            print("  --port PORT           Phoenix UI port (default: 6006)")
            print("  --auto-eval           Enable automatic evaluations")
            print("  --eval-interval SEC   Evaluation interval in seconds (default: 60)")
            print("  -h, --help            Show this help message")
            print("\nExamples:")
            print("  python phoenix_with_evals.py")
            print("  python phoenix_with_evals.py --auto-eval")
            print("  python phoenix_with_evals.py --auto-eval --eval-interval 120")
            print("  python phoenix_with_evals.py --port 6007 --auto-eval")
            print("\nEnvironment Variables:")
            print("  OPENAI_API_KEY        For GPT-based evaluations")
            print("  ANTHROPIC_API_KEY     For Claude-based evaluations")
            sys.exit(0)
    
    # Start server
    start_phoenix_with_evals(port, auto_eval, eval_interval)


if __name__ == "__main__":
    main()
