"""
Evaluation Runner for Predictive Telemetry Agent
Fetches traces from Langfuse and runs DeepEval metrics
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from deepeval import evaluate
from deepeval.test_case import ConversationalTestCase

from .metrics import get_all_metrics, create_test_case_from_trace
from .custom_model import get_default_model


def run_evaluation(
    test_cases: List[ConversationalTestCase],
    threshold: float = 0.7,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run DeepEval evaluation on test cases.
    
    Args:
        test_cases: List of ConversationalTestCase instances
        threshold: Minimum score threshold for passing
        verbose: Whether to print detailed results
    
    Returns:
        Dictionary with evaluation results
    """
    metrics = get_all_metrics(threshold=threshold)
    
    try:
        results = evaluate(
            test_cases=test_cases,
            metrics=metrics
        )
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "num_test_cases": len(test_cases),
            "results": results,
            "summary": {
                "passed": sum(1 for r in results if r.score >= threshold),
                "failed": sum(1 for r in results if r.score < threshold),
                "avg_score": sum(r.score for r in results) / len(results) if results else 0
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def evaluate_trace(
    trace_data: Dict[str, Any],
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Evaluate a single trace from Langfuse.
    
    Args:
        trace_data: Trace data dictionary from Langfuse
        threshold: Minimum score threshold
    
    Returns:
        Evaluation results dictionary
    """
    # Create test case from trace
    test_case = create_test_case_from_trace(trace_data)
    
    # Run evaluation
    return run_evaluation([test_case], threshold=threshold)


def evaluate_traces_from_langfuse(
    limit: int = 10,
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Fetch recent traces from Langfuse and evaluate them.
    
    Args:
        limit: Maximum number of traces to evaluate
        threshold: Minimum score threshold
    
    Returns:
        Combined evaluation results
    """
    # Import here to avoid circular dependency
    from tracing import get_recent_traces, get_trace_details
    
    traces = get_recent_traces(limit=limit)
    
    if not traces:
        return {
            "success": False,
            "error": "No traces found in Langfuse",
            "timestamp": datetime.now().isoformat()
        }
    
    test_cases = []
    for trace_summary in traces:
        trace_detail = get_trace_details(trace_summary["id"])
        if trace_detail and trace_detail.get("input") and trace_detail.get("output"):
            test_case = create_test_case_from_trace(trace_detail)
            test_cases.append(test_case)
    
    if not test_cases:
        return {
            "success": False,
            "error": "No valid traces with input/output found",
            "timestamp": datetime.now().isoformat()
        }
    
    return run_evaluation(test_cases, threshold=threshold)


class EvaluationResultStore:
    """
    Simple in-memory store for evaluation results.
    Can be extended to persist to database.
    """
    
    def __init__(self):
        self._results: List[Dict[str, Any]] = []
    
    def add_result(self, result: Dict[str, Any]) -> None:
        """Add an evaluation result to the store"""
        self._results.append({
            **result,
            "stored_at": datetime.now().isoformat()
        })
    
    def get_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent evaluation results"""
        return self._results[-limit:]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all results"""
        if not self._results:
            return {"total": 0}
        
        successful = [r for r in self._results if r.get("success")]
        
        return {
            "total": len(self._results),
            "successful": len(successful),
            "failed": len(self._results) - len(successful),
            "avg_score": (
                sum(r["summary"]["avg_score"] for r in successful if "summary" in r)
                / len(successful) if successful else 0
            )
        }
    
    def clear(self) -> None:
        """Clear all stored results"""
        self._results.clear()


# Global result store instance
result_store = EvaluationResultStore()
