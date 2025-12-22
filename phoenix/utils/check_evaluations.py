"""
Check Phoenix evaluation results via Client API
"""
from phoenix.session.client import Client
import pandas as pd

try:
    client = Client(endpoint="http://localhost:6006")
    
    # Get spans
    spans_df = client.get_spans_dataframe()
    
    if spans_df is None or spans_df.empty:
        print("❌ No spans found in Phoenix")
        exit(1)
    
    print(f"✅ Found {len(spans_df)} spans")
    print(f"\nSpan kinds:")
    print(spans_df['span_kind'].value_counts())
    
    # Check if there are evaluations
    eval_cols = [col for col in spans_df.columns if 'eval' in col.lower()]
    print(f"\nEvaluation columns found: {len(eval_cols)}")
    for col in eval_cols:
        print(f"  - {col}")
    
    # Try to get evaluations
    print("\n" + "="*80)
    print("CHECKING EVALUATIONS")
    print("="*80)
    
    # Check for tool_parameters_complete
    if 'eval.tool_parameters_complete.label' in spans_df.columns:
        tool_eval = spans_df['eval.tool_parameters_complete.label'].value_counts()
        print("\n1. TOOL PARAMETERS COMPLETE:")
        print(tool_eval)
        
        # Show failures
        failed = spans_df[spans_df['eval.tool_parameters_complete.label'] == 'fail']
        if not failed.empty:
            print(f"\n❌ Failed tool calls ({len(failed)}):")
            for idx, row in failed.head(10).iterrows():
                tool_name = row.get('name', 'unknown')
                explanation = row.get('eval.tool_parameters_complete.explanation', '')
                print(f"\n  - {tool_name}")
                print(f"    {explanation}")
    
    # Check for risk_math_verification
    if 'eval.risk_math_verification.label' in spans_df.columns:
        math_eval = spans_df['eval.risk_math_verification.label'].value_counts()
        print("\n\n2. RISK MATH VERIFICATION:")
        print(math_eval)
        
        # Show failures
        failed_math = spans_df[spans_df['eval.risk_math_verification.label'] == 'hallucinated']
        if not failed_math.empty:
            print(f"\n❌ Math verification failures ({len(failed_math)}):")
            for idx, row in failed_math.head(10).iterrows():
                tool_name = row.get('name', 'unknown')
                explanation = row.get('eval.risk_math_verification.explanation', '')
                print(f"\n  - {tool_name}")
                print(f"    {explanation}")
    
    # Check for input_output_consistency
    if 'eval.input_output_consistency.label' in spans_df.columns:
        io_eval = spans_df['eval.input_output_consistency.label'].value_counts()
        print("\n\n3. INPUT/OUTPUT CONSISTENCY:")
        print(io_eval)
        
        # Show failures
        failed_io = spans_df[spans_df['eval.input_output_consistency.label'] == 'inconsistent']
        if not failed_io.empty:
            print(f"\n❌ Consistency failures ({len(failed_io)}):")
            for idx, row in failed_io.head(10).iterrows():
                tool_name = row.get('name', 'unknown')
                explanation = row.get('eval.input_output_consistency.explanation', '')
                print(f"\n  - {tool_name}")
                print(f"    {explanation}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    # Calculate pass rates
    if 'eval.tool_parameters_complete.score' in spans_df.columns:
        tool_scores = spans_df['eval.tool_parameters_complete.score'].dropna()
        if not tool_scores.empty:
            tool_mean = tool_scores.mean()
            tool_passed = (tool_scores == 1.0).sum()
            tool_total = len(tool_scores)
            print(f"\nTool Parameters: μ={tool_mean:.2f} ({tool_passed}/{tool_total} passed)")
    
    if 'eval.risk_math_verification.score' in spans_df.columns:
        math_scores = spans_df['eval.risk_math_verification.score'].dropna()
        if not math_scores.empty:
            math_mean = math_scores.mean()
            math_passed = (math_scores >= 0.8).sum()
            math_total = len(math_scores)
            print(f"Risk Math: μ={math_mean:.2f} ({math_passed}/{math_total} passed)")
    
    if 'eval.input_output_consistency.score' in spans_df.columns:
        io_scores = spans_df['eval.input_output_consistency.score'].dropna()
        if not io_scores.empty:
            io_mean = io_scores.mean()
            io_passed = (io_scores >= 0.9).sum()
            io_total = len(io_scores)
            print(f"Input/Output: μ={io_mean:.2f} ({io_passed}/{io_total} consistent)")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
