#!/usr/bin/env python3
"""Phoenix Observability Server with Persistent Storage and Auto-Evaluation"""

import os
import sys
import time
import threading
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuration
PROJECT_DIR = Path(__file__).parent
DB_DIR = PROJECT_DIR / ".phoenix"
DB_DIR.mkdir(exist_ok=True)
DB_FILE = DB_DIR / "phoenix_traces.db"
OLLAMA_ENDPOINT = "http://192.168.13.162:11434"


def detect_eval_backend():
    """Detect available evaluation backend (Ollama or Anthropic)"""
    import requests
    
    # Try Ollama first (local, fast)
    try:
        response = requests.get(f"{OLLAMA_ENDPOINT}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            priority = ['llama3.1:70b', 'mixtral:8x22b', 'mixtral:8x7b', 'llama3.1:8b', 'llama3:8b']
            for model in priority:
                if model in [m.get('name', '') for m in models]:
                    return ('ollama', model)
            if models:
                return ('ollama', models[0].get('name'))
    except:
        pass
    
    # Fallback to Anthropic
    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_BASE_URL"):
        return ('anthropic', 'claude-3-5-sonnet-20241022')
    
    return (None, None)


def evaluate_spans(endpoint="http://localhost:6006", evaluated_ids=None):
    """Evaluate new spans for hallucinations"""
    if evaluated_ids is None:
        evaluated_ids = set()
    
    try:
        from phoenix.session.client import Client
        from phoenix.evals.models import LiteLLMModel
        from phoenix.evals import run_evals
        from phoenix.evals.legacy import LLMEvaluator
        from phoenix.evals.legacy.templates import ClassificationTemplate
        from phoenix.trace import SpanEvaluations
        import pandas as pd
        
        client = Client(endpoint=endpoint)
        spans_df = client.get_spans_dataframe()
        
        if spans_df is None or spans_df.empty:
            return evaluated_ids
        
        # Filter for new LLM spans
        llm_spans = spans_df[spans_df['span_kind'] == 'LLM']
        current_ids = set(llm_spans.index)
        new_ids = current_ids - evaluated_ids
        
        if not new_ids:
            return evaluated_ids
        
        llm_spans = llm_spans.loc[list(new_ids)]
        print(f"\n🔍 Evaluating {len(llm_spans)} new spans ({len(evaluated_ids)} already done)")
        
        # Prepare evaluation data
        eval_df = llm_spans.copy()
        eval_df['input'] = eval_df['attributes.llm.input_messages'].apply(str)
        eval_df['output'] = eval_df['attributes.llm.output_messages'].apply(str)
        eval_df['reference'] = eval_df['input'] + "\n\nTool Results:\n" + eval_df['attributes.llm.tool_calls'].apply(str)
        
        # Configure model
        backend, model_name = detect_eval_backend()
        if backend == 'ollama':
            os.environ["OLLAMA_API_BASE"] = OLLAMA_ENDPOINT
            model = LiteLLMModel(model=f"ollama_chat/{model_name}")
            print(f"   Using Ollama: {model_name}")
        elif backend == 'anthropic':
            os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
            os.environ["ANTHROPIC_BASE_URL"] = os.getenv("ANTHROPIC_BASE_URL")
            model = LiteLLMModel(model=model_name)
            print(f"   Using Anthropic: {model_name}")
        else:
            print("   ⚠️  No evaluation backend available")
            return evaluated_ids
        
        # Evaluation template
        template = ClassificationTemplate(
            rails=["factual", "hallucinated"],
            template="""Evaluate if AI agent outputs are grounded in data or hallucinated.

INPUT: {input}
REFERENCE: {reference}
OUTPUT: {output}

Rules:
- Agent uses tool results → FACTUAL
- Agent invents data → HALLUCINATED
- Default values from instructions → FACTUAL

Output only: factual OR hallucinated"""
        )
        
        evaluator = LLMEvaluator(model=model, template=template)
        results = run_evals(dataframe=eval_df, evaluators=[evaluator], provide_explanation=True)
        
        if isinstance(results, list):
            results = results[0]
        
        results = results.dropna(subset=['label'])
        
        # Print results
        factual = len(results[results['label'] == 'factual'])
        hallucinated = len(results[results['label'] == 'hallucinated'])
        print(f"   ✅ Factual: {factual} | ⚠️  Hallucinated: {hallucinated}")
        
        # Save to CSV
        results.to_csv(PROJECT_DIR / "phoenix_eval_results.csv", index=False)
        
        # Log to Phoenix
        eval_data = pd.DataFrame({
            'label': results['label'],
            'score': results['label'].apply(lambda x: 1.0 if x == 'factual' else 0.0),
            'explanation': results['explanation']
        })
        client.log_evaluations(SpanEvaluations(eval_name="Hallucination", dataframe=eval_data))
        print(f"   📊 Logged evaluations to {endpoint}")
        
        evaluated_ids.update(new_ids)
        
    except Exception as e:
        print(f"   ⚠️  Evaluation error: {e}")
    
    return evaluated_ids


def auto_eval_loop(interval, endpoint):
    """Background thread for continuous evaluation"""
    from phoenix.session.client import Client
    import requests
    
    evaluated_ids = set()
    print(f"\n🤖 Auto-evaluation enabled (interval: {interval}s)\n")
    
    while True:
        time.sleep(interval)
        try:
            if requests.get(endpoint, timeout=2).status_code == 200:
                client = Client(endpoint=endpoint)
                spans_df = client.get_spans_dataframe()
                
                if spans_df is not None and not spans_df.empty:
                    llm_spans = spans_df[spans_df['span_kind'] == 'LLM']
                    new_ids = set(llm_spans.index) - evaluated_ids
                    
                    if new_ids:
                        print(f"[{time.strftime('%H:%M:%S')}] Found {len(new_ids)} new spans")
                        evaluated_ids = evaluate_spans(endpoint, evaluated_ids)
        except KeyboardInterrupt:
            raise
        except:
            pass


def start_server(port=6006, auto_eval=False, eval_interval=30):
    """Start Phoenix server with persistent storage"""
    import phoenix as px
    import sqlite3
    
    # Configure Phoenix for persistent storage
    db_url = f"sqlite:///{str(DB_FILE.absolute()).replace(chr(92), '/')}"
    os.environ["PHOENIX_SQL_DATABASE_URL"] = db_url
    os.environ["PHOENIX_WORKING_DIR"] = str(DB_DIR.absolute())
    os.environ["PHOENIX_PORT"] = str(port)
    
    # Initialize database
    if not DB_FILE.exists():
        print(f"🔧 Creating database: {DB_FILE}")
        conn = sqlite3.connect(str(DB_FILE))
        conn.execute("CREATE TABLE IF NOT EXISTS _init (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
    else:
        print(f"📊 Database: {DB_FILE} ({DB_FILE.stat().st_size:,} bytes)")
    
    print(f"\n🚀 Starting Phoenix on port {port}...")
    
    # Detect eval backend
    backend, model = detect_eval_backend()
    if backend:
        print(f"✅ Evaluation: {backend} ({model})")
    
    # Launch Phoenix
    px.launch_app(run_in_thread=True)
    time.sleep(2)
    
    print(f"""
{'='*80}
✅ PHOENIX SERVER RUNNING

   📊 Dashboard: http://localhost:{port}
   💾 Database: {DB_FILE}
   {'🤖 Auto-eval: ' + str(eval_interval) + 's' if auto_eval else ''}
   
   Press Ctrl+C to stop
{'='*80}
""")
    
    # Start auto-evaluation if enabled
    if auto_eval:
        eval_thread = threading.Thread(
            target=auto_eval_loop,
            args=(eval_interval, f"http://localhost:{port}"),
            daemon=True
        )
        eval_thread.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Shutting down...")
        if DB_FILE.exists():
            print(f"💾 Database saved: {DB_FILE.stat().st_size:,} bytes")
        print("✅ Phoenix stopped")


if __name__ == "__main__":
    port = 6006
    auto_eval = False
    interval = 30
    
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
        elif arg == "--auto-eval":
            auto_eval = True
        elif arg == "--eval-interval" and i + 1 < len(sys.argv):
            interval = int(sys.argv[i + 1])
            auto_eval = True
        elif arg in ["-h", "--help"]:
            print(__doc__)
            print("\nUsage: python phoenix_server.py [options]")
            print("\nOptions:")
            print("  --port N              UI port (default: 6006)")
            print("  --auto-eval           Enable auto-evaluation")
            print("  --eval-interval N     Eval check interval in seconds (default: 30)")
            print("\nExample:")
            print("  python phoenix_server.py --auto-eval --eval-interval 30")
            sys.exit(0)
    
    start_server(port, auto_eval, interval)
