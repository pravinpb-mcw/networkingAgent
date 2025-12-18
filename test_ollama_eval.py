#!/usr/bin/env python3
"""
Test Ollama Evaluation

Quick test to verify:
1. Ollama connection works
2. Mixtral model is available
3. Phoenix can use it for evaluation
4. Results appear in dashboard
"""

import sys
import os
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

def test_ollama_connection():
    """Test basic Ollama connectivity"""
    print("="*80)
    print("TEST 1: Ollama Connection")
    print("="*80)
    
    try:
        import requests
        response = requests.get("http://192.168.13.162:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            model_names = [m['name'] for m in models]
            
            print(f"✅ Ollama is running")
            print(f"   Found {len(models)} models:")
            for name in model_names:
                print(f"   - {name}")
            
            if 'mixtral:8x7b' in model_names:
                print(f"\n✅ mixtral:8x7b is available for evaluation")
                return True
            else:
                print(f"\n⚠️  mixtral:8x7b not found!")
                print(f"   Install with: ollama pull mixtral:8x7b")
                return False
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print(f"   Make sure Ollama is running at http://192.168.13.162:11434")
        return False


def test_litellm_integration():
    """Test LiteLLM can connect to Ollama"""
    print("\n" + "="*80)
    print("TEST 2: LiteLLM Integration")
    print("="*80)
    
    try:
        from phoenix.evals.models import LiteLLMModel
        import os
        
        print("Creating LiteLLM model for Ollama...")
        
        # Set Ollama base URL as environment variable
        os.environ["OLLAMA_API_BASE"] = "http://192.168.13.162:11434"
        
        # Create model using ollama_chat/ prefix
        model = LiteLLMModel(
            model="ollama_chat/mixtral:8x7b"
        )
        
        print(f"✅ LiteLLM model created successfully")
        print(f"   Model: ollama_chat/mixtral:8x7b")
        print(f"   Host: http://192.168.13.162:11434")
        return True
        
    except ImportError as e:
        print(f"❌ LiteLLM not installed: {e}")
        print(f"   Install with: pip install litellm")
        return False
    except Exception as e:
        print(f"❌ Failed to create model: {e}")
        return False


def test_phoenix_evaluation():
    """Test actual Phoenix evaluation with Ollama"""
    print("\n" + "="*80)
    print("TEST 3: Phoenix Evaluation")
    print("="*80)
    
    try:
        from phoenix.evals import HallucinationEvaluator
        from phoenix.evals.models import LiteLLMModel
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
        
        print("Creating Ollama-based evaluator...")
        
        # Set Ollama host
        import os
        os.environ["OLLAMA_API_BASE"] = "http://192.168.13.162:11434"
        
        model = LiteLLMModel(
            model="ollama_chat/mixtral:8x7b"
        )
        
        # Create custom hallucination evaluator with detailed explanations
        from phoenix.evals.legacy import LLMEvaluator
        from phoenix.evals.legacy.templates import ClassificationTemplate
        
        # Enhanced prompt for more detailed explanations about agent actions
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
        print("(This may take 30-60 seconds with Ollama...)")
        
        from phoenix.evals import run_evals
        
        results = run_evals(
            dataframe=test_data,
            evaluators=[evaluator],
            provide_explanation=True
        )
        
        print(f"\n✅ Evaluation completed!")
        
        # run_evals returns a list containing DataFrame(s)
        # Get the first DataFrame (which contains all results)
        if isinstance(results, list) and len(results) > 0:
            results_df = results[0]
        else:
            results_df = results
        
        print(f"\nResults:")
        
        # Iterate through DataFrame rows
        factual_count = 0
        hallucinated_count = 0
        
        for idx, row in results_df.iterrows():
            label = row['label']
            explanation = row['explanation']
            
            print(f"\n   Example {idx + 1}:")
            print(f"   Label: {label}")
            print(f"   Explanation: {explanation[:150]}...")
            
            if label == 'factual':
                factual_count += 1
            elif label == 'hallucinated':
                hallucinated_count += 1
        
        print(f"\n   Summary:")
        print(f"   ✅ Factual: {factual_count}")
        print(f"   ⚠️  Hallucinated: {hallucinated_count}")
        
        if hallucinated_count > 0:
            print(f"\n   ✅ Hallucination detection is working!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print(f"   Install with: pip install arize-phoenix[evals] litellm")
        return False
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    OLLAMA EVALUATION TEST                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # Test 1: Ollama connection
    results.append(("Ollama Connection", test_ollama_connection()))
    
    # Test 2: LiteLLM integration
    results.append(("LiteLLM Integration", test_litellm_integration()))
    
    # Test 3: Phoenix evaluation
    if results[0][1] and results[1][1]:
        results.append(("Phoenix Evaluation", test_phoenix_evaluation()))
    else:
        print("\n⚠️  Skipping Phoenix evaluation test (prerequisites failed)")
        results.append(("Phoenix Evaluation", False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        print("\nYou can now use Ollama for Phoenix evaluations:")
        print("1. Start Phoenix: python phoenix_persistent.py --auto-eval")
        print("2. Run your agent: python agents/risk_score_agent.py --continuous")
        print("3. Evaluations will run automatically using Ollama mixtral:8x7b")
        print("4. View results in Phoenix dashboard: http://localhost:6006")
    else:
        print("\n" + "="*80)
        print("⚠️  SOME TESTS FAILED")
        print("="*80)
        print("\nTo fix:")
        if not results[0][1]:
            print("- Make sure Ollama is running: http://192.168.13.162:11434")
            print("- Pull mixtral: ollama pull mixtral:8x7b")
        if not results[1][1]:
            print("- Install LiteLLM: pip install litellm")
        if not results[2][1]:
            print("- Install Phoenix evals: pip install arize-phoenix[evals]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
