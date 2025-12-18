#!/usr/bin/env python3
"""
Phoenix LLM-as-a-Judge Evaluations

Run automated evaluations on agent traces to detect:
- Hallucinations
- Relevance issues
- Correctness problems
- Tool call validity

Usage:
    python run_phoenix_evals.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Set Phoenix directory
PROJECT_DIR = Path(__file__).parent
PHOENIX_DB_DIR = PROJECT_DIR / ".phoenix"
os.environ["PHOENIX_WORKING_DIR"] = str(PHOENIX_DB_DIR)

try:
    import phoenix as px
    from phoenix.evals import (
        HallucinationEvaluator,
        RelevanceEvaluator,
        QAEvaluator,
        run_evals,
    )
    import pandas as pd
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Install with: pip install arize-phoenix openai anthropic")
    sys.exit(1)


def evaluate_traces(eval_type="hallucination", model="gpt-4o"):
    """
    Run LLM-as-a-Judge evaluations on agent traces
    
    Args:
        eval_type: Type of evaluation (hallucination, relevance, qa)
        model: Model to use as judge (gpt-4o, claude-3-opus, etc.)
    """
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PHOENIX LLM-AS-A-JUDGE EVALUATIONS                        ║
║                                                                              ║
║  Automatically evaluate agent traces for quality and accuracy               ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 Evaluation Type: {eval_type}
🤖 Judge Model: {model}
📁 Data Directory: {PHOENIX_DB_DIR}
""")
    
    # Connect to Phoenix session
    print("\n🔗 Connecting to Phoenix...")
    
    # First, try to connect to existing Phoenix instance
    session = None
    try:
        # Check if Phoenix is already running by trying to get session
        import requests
        response = requests.get("http://localhost:6006", timeout=2)
        if response.status_code == 200:
            print("✅ Connected to existing Phoenix instance on port 6006")
            # Use the client to access Phoenix data
            from phoenix.session.client import Client
            client = Client(endpoint="http://localhost:6006")
            session = clien using Phoenix client
        import pandas as pd
        from phoenix.session.client import Client
        
        client = Client(endpoint="http://localhost:6006")
        
        # Fetch spans
        try:
            spans_df = client.get_spans_dataframe()
            if spans_df is not None and not spans_df.empty:
                # Filter for LLM spans
                llm_spans = spans_df[spans_df['span_kind'] == 'LLM']
                spans_df = llm_spans
            else:
                print("⚠️  No spans found in Phoenix")
                spans_df = pd.DataFrame()
        except Exception as e:
            print(f"⚠️  Error fetching spans: {e}")
            print("   Trying alternative method...")
            # Fallback: Use active session
            try:
                session = px.active_session()
                if session:
                    spans_df = session.get_spans_dataframe('span_kind == "LLM"')
                else:
                    spans_df = pd.DataFrame()
            except:
                spans_df = pd.DataFrame(
        print(f"⚠️  Phoenix not running on port 6006")
        print("❌ Please start Phoenix first:")
        print("   python start_phoenix_standalone.py")
        print("\nOr run your agent with Phoenix:")
        print("   python agents/risk_score_agent.py")
        return
    
    # Get traces as DataFrame
    print("\n📥 Fetching traces from Phoenix...")
    try:
        # Get all LLM spans
        spans_df = session.get_spans_dataframe('span_kind == "LLM"')
        
        if spans_df.empty:
            print("❌ No LLM spans found in traces")
            print("   Run your agent first: python agents/risk_score_agent.py")
            return
        
        print(f"✅ Found {len(spans_df)} LLM spans to evaluate")
        
    except Exception as e:
        print(f"❌ Error fetching traces: {e}")
        return
    
    # Run evaluations based on type
    print(f"\n🔍 Running {eval_type} evaluation...")
    
    try:
        if eval_type == "hallucination":
            # Hallucination detection
            evaluator = HallucinationEvaluator(model=model)
            
            # Run evaluation
            results = run_evals(
                dataframe=spans_df,
                evaluators=[evaluator],
                provide_explanation=True,  # Get explanation from judge
            )
            
            print("\n" + "="*80)
            print("📊 HALLUCINATION EVALUATION RESULTS")
            print("="*80)
            
            # Show results
            hallucinated = results[results['label'] == 'hallucinated']
            factual = results[results['label'] == 'factual']
            
            print(f"\n✅ Factual responses: {len(factual)}")
            print(f"⚠️  Hallucinated responses: {len(hallucinated)}")
            
            if len(hallucinated) > 0:
                print("\n🚨 HALLUCINATED RESPONSES DETECTED:")
                for idx, row in hallucinated.iterrows():
                    print(f"\n  Span ID: {idx}")
                    print(f"  Explanation: {row.get('explanation', 'N/A')}")
                    print(f"  Score: {row.get('score', 'N/A')}")
        
        elif eval_type == "relevance":
            # Relevance evaluation
            evaluator = RelevanceEvaluator(model=model)
            
            results = run_evals(
                dataframe=spans_df,
                evaluators=[evaluator],
                provide_explanation=True,
            )
            
            print("\n" + "="*80)
            print("📊 RELEVANCE EVALUATION RESULTS")
            print("="*80)
            
            # Show results
            relevant = results[results['label'] == 'relevant']
            irrelevant = results[results['label'] == 'irrelevant']
            
            print(f"\n✅ Relevant responses: {len(relevant)}")
            print(f"⚠️  Irrelevant responses: {len(irrelevant)}")
            
            if len(irrelevant) > 0:
                print("\n🚨 IRRELEVANT RESPONSES DETECTED:")
                for idx, row in irrelevant.iterrows():
                    print(f"\n  Span ID: {idx}")
                    print(f"  Explanation: {row.get('explanation', 'N/A')}")
        
        elif eval_type == "qa":
            # Q&A correctness evaluation
            evaluator = QAEvaluator(model=model)
            
            results = run_evals(
                dataframe=spans_df,
                evaluators=[evaluator],
                provide_explanation=True,
            )
            
            print("\n" + "="*80)
            print("📊 Q&A CORRECTNESS EVALUATION RESULTS")
            print("="*80)
            
            # Show results
            correct = results[results['label'] == 'correct']
            incorrect = results[results['label'] == 'incorrect']
            
            print(f"\n✅ Correct responses: {len(correct)}")
            print(f"❌ Incorrect responses: {len(incorrect)}")
            
            if len(incorrect) > 0:
                print("\n🚨 INCORRECT RESPONSES DETECTED:")
                for idx, row in incorrect.iterrows():
                    print(f"\n  Span ID: {idx}")
                    print(f"  Explanation: {row.get('explanation', 'N/A')}")
        
        # Save results
        output_file = PROJECT_DIR / f"phoenix_{eval_type}_results.csv"
        results.to_csv(output_file)
        print(f"\n💾 Results saved to: {output_file}")
        
        # Connect to Phoenix
        from phoenix.session.client import Client
        import requests
        
        # Check if Phoenix is running
        try:
            response = requests.get("http://localhost:6006", timeout=2)
            if response.status_code != 200:
                print("❌ Phoenix not running. Start it first:")
                print("   python start_phoenix_standalone.py")
                return
        except:
            print("❌ Phoenix not running. Start it first:")
            print("   python start_phoenix_standalone.py")
            return
        
        client = Client(endpoint="http://localhost:6006")
        
        # Get tool spans
        all_spans = client.get_spans_dataframe()
        if all_spans is None or all_spans.empty:
            print("❌ No spans found")
            return
        
        tool_spans = all_spans[all_spans['span_kind'] == 'TOOL']
            print(f"⚠️  Could not upload to Phoenix: {e}")
        
        print("\n🌐 View results in Phoenix: http://localhost:6006")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


def evaluate_tool_calls():
    """Evaluate if tool calls were appropriate and effective"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    TOOL CALL EVALUATION                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    try:
        session = px.active_session()
        if not session:
            session = px.launch_app(port=6006)
        
        # Get tool spans
        tool_spans = session.get_spans_dataframe('span_kind == "TOOL"')
        
        if tool_spans.empty:
            print("❌ No tool spans found")
            return
        
        print(f"📊 Analyzing {len(tool_spans)} tool calls...")
        
        # Analyze tool call patterns
        print("\n" + "="*80)
        print("TOOL USAGE ANALYSIS")
        print("="*80)
        
        # Count by tool
        tool_counts = tool_spans['name'].value_counts()
        print("\n📈 Tool Call Frequency:")
        for tool, count in tool_counts.items():
            print(f"  {tool}: {count} calls")
        
        # Analyze failures
        failed_tools = tool_spans[tool_spans['status_code'] == 'ERROR']
        if len(failed_tools) > 0:
            print(f"\n⚠️  Failed tool calls: {len(failed_tools)}")
            for idx, row in failed_tools.iterrows():
                print(f"  - {row['name']}: {row.get('status_message', 'Unknown error')}")
        
        # Analyze latency
        print("\n⏱️  Tool Call Performance:")
        avg_latency = tool_spans.groupby('name')['latency_ms'].mean()
        for tool, latency in avg_latency.items():
            print(f"  {tool}: {latency:.2f}ms average")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    
    # Parse arguments
    eval_type = "hallucination"  # Default
    model = "gpt-4o"
    
    if len(sys.argv) > 1:
        eval_type = sys.argv[1].lower()
    
    if len(sys.argv) > 2:
        model = sys.argv[2]
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Phoenix LLM-as-a-Judge Evaluations

Usage:
    python run_phoenix_evals.py [eval_type] [model]

Evaluation Types:
    hallucination    - Detect hallucinated/fabricated information
    relevance        - Check if responses are relevant
    qa               - Evaluate Q&A correctness
    tools            - Analyze tool call effectiveness

Models:
    gpt-4o           - OpenAI GPT-4o (default)
    gpt-4-turbo      - OpenAI GPT-4 Turbo
    claude-3-opus    - Anthropic Claude 3 Opus
    claude-3-sonnet  - Anthropic Claude 3 Sonnet

Examples:
    python run_phoenix_evals.py hallucination
    python run_phoenix_evals.py relevance gpt-4-turbo
    python run_phoenix_evals.py tools

Environment Variables:
    OPENAI_API_KEY      - Required for GPT models
    ANTHROPIC_API_KEY   - Required for Claude models
""")
        return
    
    # Check API keys
    if model.startswith("gpt") and not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("   Set it in .env file or environment")
    
    if model.startswith("claude") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY not set")
        print("   Set it in .env file or environment")
    
    # Run evaluation
    if eval_type == "tools":
        evaluate_tool_calls()
    else:
        evaluate_traces(eval_type=eval_type, model=model)


if __name__ == "__main__":
    main()
