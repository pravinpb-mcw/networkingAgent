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
PROJECT_DIR = Path(__file__).parent.parent  # Go up one level from phoenix/ to networkingAgent/
DB_DIR = Path(__file__).parent / ".phoenix_data"  # Store in phoenix/.phoenix_data/
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
        return ('anthropic', 'glm-4.5')
    
    return (None, None)


def evaluate_spans(endpoint="http://localhost:6006", evaluated_ids=None):
    """Evaluate new spans for tool parameter validation and decision completeness"""
    if evaluated_ids is None:
        evaluated_ids = set()
    
    try:
        # Use arize-phoenix-client for modern API
        from phoenix.client import Client as PhoenixClient
        from phoenix.client.__generated__.v1 import SpanAnnotationData
        import pandas as pd
        import sys
        import json
        from pathlib import Path
        
        # Import deterministic validators
        sys.path.insert(0, str(Path(__file__).parent / "validators"))
        from tool_validators import evaluate_tool_parameters, evaluate_llm_decision_completeness
        from comprehensive_validators import (
            validate_risk_calculation_math,
            validate_ap_exists_in_topology,
            validate_threshold_matches_policy
        )
        
        def log_annotation(client, span_id, name, label, score, explanation):
            """Helper to log a single span annotation with correct format"""
            try:
                annotation = SpanAnnotationData(
                    span_id=str(span_id),
                    name=name,
                    annotator_kind="CODE",
                    result={"label": label, "score": score, "explanation": explanation}
                )
                client.spans.log_span_annotations(span_annotations=[annotation])
            except Exception as e:
                print(f"   ⚠️ Failed to log annotation: {e}")
        
        # Use new Phoenix client API (arize-phoenix-client)
        client = PhoenixClient(base_url=endpoint)
        spans_df = client.spans.get_spans_dataframe()
        
        if spans_df is None or spans_df.empty:
            return evaluated_ids
        
        # Filter for new spans (both LLM and TOOL spans)
        current_ids = set(spans_df.index)
        new_ids = current_ids - evaluated_ids
        
        if not new_ids:
            return evaluated_ids
        
        new_spans = spans_df.loc[list(new_ids)]
        print(f"\n🔍 Evaluating {len(new_spans)} new spans ({len(evaluated_ids)} already done)")
        
        # Evaluate tool parameter completeness (deterministic)
        tool_spans = new_spans[new_spans['span_kind'] == 'TOOL']
        if not tool_spans.empty:
            print(f"   📋 Checking {len(tool_spans)} tool calls for parameter completeness...")
            
            tool_evals = []
            
            for idx, span in tool_spans.iterrows():
                # Get tool input (parameters), NOT output (response)
                tool_name = str(span.get('name', ''))
                input_val = span.get('attributes.input.value', {})
                output_val = span.get('attributes.output.value', {})
                
                # Parse input if it's a string (Phoenix stores as string)
                if isinstance(input_val, str):
                    try:
                        import ast
                        input_val = ast.literal_eval(input_val)
                    except:
                        try:
                            input_val = json.loads(input_val)
                        except:
                            input_val = {}
                
                # Parse output
                if isinstance(output_val, str):
                    try:
                        output_val = json.loads(output_val)
                    except:
                        output_val = {}
                
                # Build tool call data for validator
                tool_data = {
                    "tool": tool_name,
                    "input": input_val if isinstance(input_val, dict) else {}
                }
                
                # 1. Parameter completeness check
                score, explanation = evaluate_tool_parameters(json.dumps(tool_data))
                
                tool_evals.append({
                    'span_id': idx,
                    'name': 'tool_parameters_complete',
                    'label': 'pass' if score == 1.0 else 'fail',
                    'score': score,
                    'explanation': explanation
                })
            
            if tool_evals:
                # Use helper function for correct API
                for eval_item in tool_evals:
                    log_annotation(
                        client,
                        eval_item['span_id'],
                        eval_item['name'],
                        eval_item['label'],
                        eval_item['score'],
                        eval_item['explanation']
                    )
                passed = sum(1 for e in tool_evals if e['score'] == 1.0)
                print(f"   ✅ Tool parameters: {passed}/{len(tool_evals)} passed")
        
        # LLM decision completeness check removed to reduce noise
        
        # Mark as evaluated
        evaluated_ids.update(new_ids)
        print(f"   💾 Evaluation results saved to Phoenix dashboard")
        
        # ============================================================================
        # ANTI-HALLUCINATION VALIDATORS (Math, Topology, Policy)
        # ============================================================================
        
        # Get TOOL spans for anti-hallucination checks
        tool_spans_all = new_spans[new_spans['span_kind'] == 'TOOL']
        
        # 1. Math Verification (for update_risk_score calls)
        # NOTE: No file waiting needed - we validate against metrics in the tool output itself
        
        risk_tool_spans = tool_spans_all[tool_spans_all['name'].isin(['update_risk_score', 'calculate_risk_score'])]
        if not risk_tool_spans.empty:
            print(f"   🧮 Running math verification on {len(risk_tool_spans)} risk calculations...")
            
            # Track validated APs to avoid duplicates (only validate latest per AP)
            validated_aps = set()
            math_evals = []
            
            # Process in reverse order (newest first) to validate latest data
            for idx, span in risk_tool_spans.iloc[::-1].iterrows():
                output_val = span.get('attributes.output.value', '')
                
                # Parse output to get risk data
                try:
                    if isinstance(output_val, str):
                        output_data = json.loads(output_val)
                    else:
                        output_data = output_val
                    
                    # Extract from nested content field
                    if 'content' in output_data:
                        content_str = output_data['content']
                        if isinstance(content_str, str):
                            content = json.loads(content_str)
                        else:
                            content = content_str
                    else:
                        content = output_data
                    
                    # Check if we have the required fields
                    if 'risk_score' in content and 'ap_serial' in content:
                        # FIXED: Validate against metrics IN THE TOOL OUTPUT, not external file
                        # This prevents timing issues where old spans are validated against new file data
                        
                        # Check if metrics are in the output
                        if 'metrics' in content and content['metrics']:
                            ap_serial = content['ap_serial']
                            
                            # Skip if already validated this AP span (only check once per span)
                            span_key = f"{idx}_{ap_serial}"
                            if span_key in validated_aps:
                                continue
                            validated_aps.add(span_key)
                            
                            # Build data for validator with metrics from THIS tool output
                            validation_data = {
                                'risk_score': content['risk_score'],  # AI's claimed score
                                'metrics': content['metrics']  # Metrics from same output
                            }
                            
                            # Validate: AI's risk_score vs recalculation from its OWN metrics
                            score, explanation = validate_risk_calculation_math(validation_data)
                            
                            math_evals.append({
                                'span_id': idx,
                                'name': 'risk_math_verification',
                                'label': 'verified' if score >= 0.8 else 'hallucinated',
                                'score': score,
                                'explanation': explanation
                            })
                        # Skip if no metrics in output (incomplete data)
                        
                except Exception as e:
                    # Only report actual calculation errors, not parse errors
                    if 'risk_score' in str(output_val):
                        math_evals.append({
                            'span_id': idx,
                            'name': 'risk_math_verification',
                            'label': 'error',
                            'score': 0.5,
                            'explanation': f"⚠️ Parse error: {str(e)[:100]}"
                        })
            
            if math_evals:
                # Use helper function for correct API
                for eval_item in math_evals:
                    log_annotation(
                        client,
                        eval_item['span_id'],
                        eval_item['name'],
                        eval_item['label'],
                        eval_item['score'],
                        eval_item['explanation']
                    )
                verified = sum(1 for e in math_evals if e['score'] >= 0.8)
                print(f"   ✅ Math verification: {verified}/{len(math_evals)} passed")
        
        # 2. AP Existence Check (for tools mentioning AP serials)
        ap_mention_tools = tool_spans_all[tool_spans_all['name'].isin(['update_risk_score', 'calculate_risk_score', 'get_wireless_health', 'get_wireless_latency_history'])]
        if not ap_mention_tools.empty:
            print(f"   🔍 Checking AP existence for {len(ap_mention_tools)} tool calls...")
            
            # Load topology data once
            try:
                topology_path = PROJECT_DIR / "mock_data" / "comprehensive_api_data.json"
                with open(topology_path, 'r') as f:
                    mock_data = json.load(f)
                    
                    # Get ALL networks' topologies and combine APs
                    all_topology = mock_data.get('network_topology_link_layer', {})
                    
                    # Collect all APs from all networks
                    known_aps = []
                    for network_id, topology_data in all_topology.items():
                        for node in topology_data.get('nodes', []):
                            if node.get('type') == 'wireless':
                                ap_id = node.get('id') or node.get('serial')
                                if ap_id and ap_id not in known_aps:
                                    known_aps.append(ap_id)
                
                ap_evals = []
                for idx, span in ap_mention_tools.iterrows():
                    input_val = span.get('attributes.input.value', {})
                    
                    # Parse input to get AP serial
                    try:
                        if isinstance(input_val, str):
                            import ast
                            input_data = ast.literal_eval(input_val)
                        else:
                            input_data = input_val
                        
                        ap_serial = input_data.get('ap_serial') or input_data.get('device_serial') or input_data.get('serial')
                        
                        if ap_serial:
                            # Check against all known APs
                            if ap_serial in known_aps:
                                score = 1.0
                                explanation = f"✅ AP exists: {ap_serial}"
                            else:
                                score = 0.0
                                explanation = f"❌ Invented AP: {ap_serial} (known: {', '.join(known_aps[:3])}...)"
                            
                            ap_evals.append({
                                'span_id': idx,
                                'name': 'ap_exists_in_topology',
                                'label': 'exists' if score == 1.0 else 'invented',
                                'score': score,
                                'explanation': explanation
                            })
                    except Exception as e:
                        pass  # Skip if can't extract AP serial
                
                if ap_evals:
                    # Use helper function for correct API
                    for eval_item in ap_evals:
                        log_annotation(
                            client,
                            eval_item['span_id'],
                            eval_item['name'],
                            eval_item['label'],
                            eval_item['score'],
                            eval_item['explanation']
                        )
                    exists = sum(1 for e in ap_evals if e['score'] == 1.0)
                    print(f"   ✅ AP existence: {exists}/{len(ap_evals)} verified")
            
            except Exception as e:
                print(f"   ⚠️ AP existence check skipped: {e}")
        
        # 3. Policy Threshold Validation (for LLM spans mentioning threshold)
        llm_spans_policy = new_spans[new_spans['span_kind'] == 'LLM']
        if not llm_spans_policy.empty:
            print(f"   📋 Checking policy compliance for {len(llm_spans_policy)} LLM calls...")
            
            policy_evals = []
            for idx, span in llm_spans_policy.iterrows():
                output_msg = str(span.get('attributes.llm.output_messages', ''))
                
                # Check if threshold is mentioned
                import re
                threshold_match = re.search(r'threshold[:\s]+(\d+)', output_msg.lower())
                
                if threshold_match:
                    try:
                        reported_threshold = float(threshold_match.group(1))
                        policy_file = str(PROJECT_DIR / "policies" / "network_policy.json")
                        
                        score, explanation = validate_threshold_matches_policy(reported_threshold, policy_file)
                        
                        policy_evals.append({
                            'span_id': idx,
                            'name': 'threshold_from_policy',
                            'label': 'correct' if score == 1.0 else 'invented',
                            'score': score,
                            'explanation': explanation
                        })
                    except Exception as e:
                        pass  # Skip if can't validate
            
            if policy_evals:
                # Use helper function for correct API
                for eval_item in policy_evals:
                    log_annotation(
                        client,
                        eval_item['span_id'],
                        eval_item['name'],
                        eval_item['label'],
                        eval_item['score'],
                        eval_item['explanation']
                    )
                correct = sum(1 for e in policy_evals if e['score'] == 1.0)
                print(f"   ✅ Policy compliance: {correct}/{len(policy_evals)} verified")
        
        return evaluated_ids
        
    except ImportError as e:
        print(f"   ⚠️  Phoenix eval dependencies not available: {e}")
        return evaluated_ids
    except Exception as e:
        print(f"   ❌ Evaluation error: {e}")
        import traceback
        traceback.print_exc()
        return evaluated_ids
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
    from phoenix.client import Client as PhoenixClient
    import requests
    
    evaluated_ids = set()
    print(f"\n🤖 Auto-evaluation enabled (interval: {interval}s)\n")
    
    while True:
        time.sleep(interval)
        try:
            if requests.get(endpoint, timeout=2).status_code == 200:
                client = PhoenixClient(base_url=endpoint)
                # Use new API
                spans_df = client.spans.get_spans_dataframe()
                
                if spans_df is not None and not spans_df.empty:
                    # Check for both LLM and TOOL spans
                    relevant_spans = spans_df[spans_df['span_kind'].isin(['LLM', 'TOOL'])]
                    new_ids = set(relevant_spans.index) - evaluated_ids
                    
                    if new_ids:
                        print(f"[{time.strftime('%H:%M:%S')}] Found {len(new_ids)} new spans to evaluate")
                        evaluated_ids = evaluate_spans(endpoint, evaluated_ids)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            # Print errors for debugging
            if "Connection" not in str(e):
                print(f"[{time.strftime('%H:%M:%S')}] Eval error: {e}")
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
    
    # Launch Phoenix with retry logic for slower systems
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"🚀 Starting Phoenix server (attempt {attempt + 1}/{max_retries})...")
            px.launch_app(run_in_thread=True)
            time.sleep(3)  # Give it time to start
            print("✅ Phoenix started successfully!")
            break
        except RuntimeError as e:
            if "took too long to start" in str(e):
                if attempt < max_retries - 1:
                    print(f"⚠️  Phoenix startup delayed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"""
⚠️  WARNING: Phoenix failed to start after {max_retries} attempts
This is usually due to:
  - Slower system performance
  - Antivirus/Firewall interference
  - Port 6006 already in use

CONTINUING WITHOUT PHOENIX - Agents will still work!
Observability features will be limited.
""")
                    # Continue anyway - agents can work without Phoenix
            else:
                raise
    
    print(f"""
{'='*80}
✅ SYSTEM RUNNING

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
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        elif arg == "--auto-eval":
            auto_eval = True
            i += 1
        elif arg == "--eval-interval" and i + 1 < len(sys.argv):
            interval = int(sys.argv[i + 1])
            auto_eval = True
            i += 2
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
        else:
            i += 1
    
    start_server(port, auto_eval, interval)
