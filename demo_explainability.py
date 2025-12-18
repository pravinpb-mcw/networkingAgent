#!/usr/bin/env python3
"""
Explainability Demo

Quick demonstration of explainability features:
- Tool call explanations
- Metric calculation transparency
- Decision justification
- Hallucination detection
- Phoenix dashboard integration
"""

import sys
from pathlib import Path
from datetime import datetime

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from explainability import create_explainability_tracker


def demo_explainability():
    """Demonstrate explainability features"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     EXPLAINABILITY DEMONSTRATION                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create explainability tracker
    print("1. Initializing Explainability Tracker...")
    explainer = create_explainability_tracker(
        agent_name="DemoAgent",
        phoenix_endpoint="http://localhost:6006",
        judge_model="gpt-4o",
        enable=True
    )
    
    if not explainer:
        print("❌ Failed to create explainability tracker")
        return
    
    print("✅ Explainability tracker ready\n")
    
    # Demo 1: Tool Call Explanation
    print("="*80)
    print("DEMO 1: Tool Call Explanation")
    print("="*80)
    
    tool_output = {
        "latency_ms": [32, 35, 38, 42, 45],
        "jitter_ms": [8, 10, 12, 14, 15],
        "timestamp": datetime.now().isoformat()
    }
    
    exp1 = explainer.explain_tool_call(
        tool_name="get_wireless_latency_history",
        tool_input={
            "network_id": "L_123456789",
            "device_serial": "Q2AB-CD3E-FGH4"
        },
        tool_output=tool_output,
        decision_reasoning="Need latency and jitter metrics to calculate risk score for AP-001"
    )
    
    print(f"✅ Tool Call Explained:")
    print(f"   Action ID: {exp1.action_id}")
    print(f"   Explanation: {exp1.explanation}")
    print(f"   Confidence: {exp1.confidence:.2%}\n")
    
    # Demo 2: Metric Calculation
    print("="*80)
    print("DEMO 2: Metric Calculation Explanation")
    print("="*80)
    
    exp2 = explainer.explain_metric_calculation(
        metric_name="latency_risk_score",
        inputs={
            "raw_latency_ms": 45,
            "threshold_good": 30,
            "threshold_warning": 60,
            "threshold_critical": 100
        },
        formula="If latency in [30-60ms] range, score = 50",
        result=50.0,
        interpretation="Latency of 45ms is in WARNING range, contributing medium risk"
    )
    
    print(f"✅ Metric Calculation Explained:")
    print(f"   Metric: {exp2.metadata['metric_name']}")
    print(f"   Result: {exp2.metadata['result']}")
    print(f"   Explanation: {exp2.explanation}")
    print(f"   Reasoning: {exp2.reasoning[:100]}...")
    print(f"   Confidence: {exp2.confidence:.2%}\n")
    
    # Demo 3: Decision Explanation
    print("="*80)
    print("DEMO 3: Decision Explanation")
    print("="*80)
    
    risk_score = 52.5
    
    exp3 = explainer.explain_decision(
        decision_point="Risk classification for AP-001",
        chosen_option="Temporary Degradation",
        alternatives=["Stable Network", "Sustained Degradation", "Likely Failure"],
        reasoning=f"Risk score {risk_score} falls in the 21-40 range, indicating temporary network issues that should be monitored",
        supporting_data={
            "risk_score": risk_score,
            "score_range": "21-40",
            "classification": "Temporary Degradation",
            "contributing_factors": ["elevated_latency", "moderate_jitter"]
        }
    )
    
    print(f"✅ Decision Explained:")
    print(f"   Decision Point: {exp3.metadata['decision_point']}")
    print(f"   Chosen: {exp3.metadata['chosen_option']}")
    print(f"   Alternatives: {', '.join(exp3.metadata['alternatives'])}")
    print(f"   Explanation: {exp3.explanation}")
    print(f"   Confidence: {exp3.confidence:.2%}\n")
    
    # Demo 4: Hallucination Detection
    print("="*80)
    print("DEMO 4: Hallucination Detection")
    print("="*80)
    
    # Factual output
    factual_output = "AP-001 has a risk score of 52.5, classified as Temporary Degradation due to latency of 45ms and jitter of 12ms."
    context = "AP-001 metrics: Latency=45ms, Jitter=12ms, Risk Score=52.5, Classification=Temporary Degradation"
    
    print("Testing FACTUAL output...")
    check1 = explainer.check_hallucination(
        output=factual_output,
        context=context,
        query="What is the risk assessment for AP-001?"
    )
    
    print(f"   Output: '{factual_output}'")
    print(f"   Is Hallucinated: {check1.is_hallucinated}")
    print(f"   Confidence: {check1.confidence:.2%}")
    print(f"   Explanation: {check1.explanation}")
    if check1.supporting_facts:
        print(f"   Supporting Facts: {len(check1.supporting_facts)} found")
    print()
    
    # Hallucinated output (making up facts)
    hallucinated_output = "AP-001 will definitely fail within the next 2 hours and cause complete network outage affecting 500 users."
    
    print("Testing HALLUCINATED output...")
    check2 = explainer.check_hallucination(
        output=hallucinated_output,
        context=context,
        query="Predict AP failure"
    )
    
    print(f"   Output: '{hallucinated_output}'")
    print(f"   Is Hallucinated: {check2.is_hallucinated}")
    print(f"   Confidence: {check2.confidence:.2%}")
    print(f"   Explanation: {check2.explanation}")
    if check2.unsupported_claims:
        print(f"   Unsupported Claims: {len(check2.unsupported_claims)}")
        for claim in check2.unsupported_claims[:3]:
            print(f"      - {claim}")
    print()
    
    # Demo 5: Session Summary
    print("="*80)
    print("DEMO 5: Session Summary")
    print("="*80)
    
    summary = explainer.get_session_summary()
    
    print(f"Agent: {summary['agent_name']}")
    print(f"Total Actions Explained: {summary['total_actions']}")
    print(f"Average Confidence: {summary['average_confidence']:.2%}")
    print(f"\nActions by Type:")
    for action_type, count in summary['actions_by_type'].items():
        print(f"   - {action_type}: {count}")
    print(f"\nSession Log: {summary['session_file']}")
    print()
    
    # Show latest explanations
    print("Latest Explanations:")
    for exp in summary['latest_explanations']:
        print(f"   [{exp['timestamp']}] {exp['action_type']}: {exp['explanation'][:60]}...")
    
    print("\n" + "="*80)
    print("DEMO COMPLETE!")
    print("="*80)
    print(f"\n📁 Explanations saved to: {explainer.current_session_file}")
    print(f"🔍 View in Phoenix dashboard: http://localhost:6006")
    print("\nNote: Some features require Phoenix server to be running.")
    print("Start Phoenix with: python phoenix_persistent.py --auto-eval\n")


if __name__ == "__main__":
    try:
        demo_explainability()
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
