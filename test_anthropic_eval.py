#!/usr/bin/env python3
"""
Test Anthropic API for Phoenix Evaluations

This tests if your Anthropic-compatible API (z.ai with GLM-4.5) works for evaluations.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ANTHROPIC API EVALUATION TEST                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

def test_anthropic_connection():
    """Test 1: Verify Anthropic API credentials"""
    print("="*80)
    print("TEST 1: Anthropic API Connection")
    print("="*80)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False
    
    if not base_url:
        print("❌ ANTHROPIC_BASE_URL not set")
        return False
    
    print(f"✅ API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"✅ Base URL: {base_url}")
    
    # Test connection
    try:
        import anthropic
        
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url
        )
        
        # Simple test message
        print("\n🔍 Testing API with simple message...")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ]
        )
        
        reply = response.content[0].text
        print(f"✅ API Response: {reply}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_litellm_integration():
    """Test 2: LiteLLM with Anthropic"""
    print("\n" + "="*80)
    print("TEST 2: LiteLLM Integration")
    print("="*80)
    
    try:
        from phoenix.evals.models import LiteLLMModel
        
        print("Setting environment variables for LiteLLM...")
        # LiteLLM expects environment variables, not constructor parameters
        os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
        
        # For custom base URL with Anthropic models, use litellm-specific env var
        if os.getenv("ANTHROPIC_BASE_URL"):
            os.environ["ANTHROPIC_BASE_URL"] = os.getenv("ANTHROPIC_BASE_URL")
        
        print("Creating LiteLLM model for Anthropic...")
        
        # LiteLLMModel only takes model parameter, reads credentials from env
        model = LiteLLMModel(
            model="claude-3-5-sonnet-20241022"
        )
        
        print(f"✅ LiteLLM model created successfully")
        print(f"   Model: claude-3-5-sonnet-20241022 (GLM-4.5 via z.ai)")
        print(f"   Endpoint: {os.getenv('ANTHROPIC_BASE_URL')}")
        
        return True
        
    except Exception as e:
        print(f"❌ LiteLLM integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phoenix_evaluation():
    """Test 3: Phoenix Evaluation with Anthropic"""
    print("\n" + "="*80)
    print("TEST 3: Phoenix Evaluation")
    print("="*80)
    
    try:
        from phoenix.evals import HallucinationEvaluator, run_evals
        from phoenix.evals.models import LiteLLMModel
        from phoenix.evals.legacy import LLMEvaluator
        from phoenix.evals.legacy.templates import ClassificationTemplate
        import pandas as pd
        
        # Create test data
        test_data = pd.DataFrame([
            {
                'input': 'What is the capital of France?',
                'output': 'The capital of France is Paris.',
                'reference': 'Paris is the capital city of France.'
            },
            {
                'input': 'What is the capital of France?',
                'output': 'The capital of France is London.',  # Hallucinated
                'reference': 'Paris is the capital city of France.'
            }
        ])
        
        print("Creating Anthropic-based evaluator...")
        
        # Set environment variables for LiteLLM
        os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
        if os.getenv("ANTHROPIC_BASE_URL"):
            os.environ["ANTHROPIC_BASE_URL"] = os.getenv("ANTHROPIC_BASE_URL")
        
        # LiteLLMModel only takes model parameter
        model = LiteLLMModel(
            model="claude-3-5-sonnet-20241022"
        )
        
        # Enhanced prompt
        template = ClassificationTemplate(
            rails=["factual", "hallucinated"],
            template="""You are evaluating if an AI agent's response contains hallucinations or is factual.

[Input]
{input}

[Reference - Ground Truth Context]
{reference}

[Agent's Output to Evaluate]
{output}

Provide a DETAILED explanation covering:
1. **What action/decision the agent made**: Describe what the agent is doing or claiming
2. **Why this action was taken**: What reasoning or data led to this action
3. **Reference grounding**: Is this information found in the reference context?
4. **Hallucination check**: Any invented facts, numbers, or details not in reference?
5. **Final assessment**: Is the output factual or hallucinated?

After your detailed analysis, provide your label as either "factual" or "hallucinated".
"""
        )
        
        evaluator = LLMEvaluator(model=model, template=template)
        
        print("Running evaluation on test data...")
        print("(Should be much faster than Ollama - ~1-2s per example)")
        
        import time
        start_time = time.time()
        
        results = run_evals(
            dataframe=test_data,
            evaluators=[evaluator],
            provide_explanation=True,
        )
        
        elapsed = time.time() - start_time
        
        # Handle results
        if isinstance(results, list) and len(results) > 0:
            results_df = results[0]
        else:
            results_df = results
        
        print(f"\n✅ Evaluation completed in {elapsed:.1f} seconds!")
        print(f"   Speed: {elapsed/len(test_data):.2f}s per example")
        print(f"\nResults:")
        
        factual_count = 0
        hallucinated_count = 0
        
        # Process results from DataFrame
        for idx in range(len(results_df)):
            label = str(results_df['label'].iloc[idx]) if 'label' in results_df.columns else 'unknown'
            explanation = str(results_df['explanation'].iloc[idx]) if 'explanation' in results_df.columns else 'No explanation'
            
            print(f"\n   Example {idx + 1}:")
            print(f"   Label: {label}")
            print(f"   Explanation: {explanation[:200]}...")
            
            if 'factual' in label.lower():
                factual_count += 1
            elif 'hallucinated' in label.lower():
                hallucinated_count += 1
        
        print(f"\n   Summary:")
        print(f"   ✅ Factual: {factual_count}")
        print(f"   ⚠️  Hallucinated: {hallucinated_count}")
        
        if hallucinated_count > 0:
            print(f"\n   ✅ Hallucination detection is working!")
        
        # Compare speed
        if elapsed < 5:
            print(f"\n   🚀 MUCH FASTER than Ollama (which takes ~10-12s for 2 examples)!")
        elif elapsed < 12:
            print(f"\n   ⚡ Still faster than Ollama!")
        
        return True
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    results = {
        "Anthropic Connection": False,
        "LiteLLM Integration": False,
        "Phoenix Evaluation": False
    }
    
    results["Anthropic Connection"] = test_anthropic_connection()
    
    if results["Anthropic Connection"]:
        results["LiteLLM Integration"] = test_litellm_integration()
    
    if results["LiteLLM Integration"]:
        results["Phoenix Evaluation"] = test_phoenix_evaluation()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print("\n" + "="*80)
    if all(results.values()):
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        print("\nYour Anthropic API is ready for Phoenix evaluations!")
        print("It will be MUCH faster than Ollama:")
        print("  - Anthropic: ~1-2s per span")
        print("  - Ollama: ~5-6s per span")
        print("\nRestart Phoenix and it will automatically use Anthropic:")
        print("  python phoenix_persistent.py --auto-eval")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("="*80)
        print("\nTo fix:")
        print("- Make sure ANTHROPIC_API_KEY is set in .env file")
        print("- Make sure ANTHROPIC_BASE_URL is set in .env file")
