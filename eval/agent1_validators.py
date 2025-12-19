"""
Deterministic Validators for Agent 1 (Risk Calculation Agent)
=============================================================

These validators check Agent 1 outputs WITHOUT using LLMs.
Pure deterministic logic to ensure:
1. Risk score ↔ risk class consistency
2. Per-KPI contribution breakdown is correct
3. All required output fields present
4. Numeric values are within valid ranges
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


# Risk classification thresholds (from calculate_risk_score.py)
RISK_THRESHOLDS = {
    "Stable": (0, 20),
    "Temporary Degradation": (21, 40),
    "Sustained Degradation": (41, 70),
    "Likely Failure": (71, 100)
}


def validate_risk_score_classification(risk_score: float, risk_classification: str) -> Tuple[bool, str]:
    """
    Validate that risk_score matches the risk_classification category.
    
    Args:
        risk_score: Numeric risk score (0-100)
        risk_classification: Classification string
    
    Returns:
        (is_valid, error_message)
    """
    if risk_classification not in RISK_THRESHOLDS:
        return False, f"Invalid risk_classification: {risk_classification}"
    
    min_score, max_score = RISK_THRESHOLDS[risk_classification]
    
    if not (min_score <= risk_score <= max_score):
        return False, f"Risk score {risk_score} does not match classification '{risk_classification}' (expected {min_score}-{max_score})"
    
    return True, "Risk score matches classification"


def validate_contribution_breakdown(result: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that per-KPI contribution breakdown sums to total risk score.
    
    Args:
        result: Agent 1 output dictionary
    
    Returns:
        (is_valid, error_message)
    """
    # Check if we have metrics (simplified format from Agent 1)
    if "metrics" not in result:
        return False, "Missing metrics in output"
    
    metrics = result["metrics"]
    risk_score = result.get("risk_score", 0)
    
    # Calculate expected contribution from metric scores
    # Weights: latency(0.25), jitter(0.20), retrans(0.20), snr(0.15), load(0.10), auth(0.10)
    weights = {
        "latency_score": 0.25,
        "jitter_score": 0.20,
        "retrans_score": 0.20,
        "snr_score": 0.15,
        "load_score": 0.10,
        "auth_score": 0.10
    }
    
    calculated_risk = 0
    for metric, weight in weights.items():
        score = metrics.get(metric, 20)  # Default 20 if missing
        if score is not None:
            calculated_risk += weight * score
    
    # Allow small floating point error (1.0 points)
    if abs(calculated_risk - risk_score) > 1.0:
        return False, f"Calculated risk {calculated_risk:.1f} does not match stored risk_score {risk_score}"
    
    return True, "Risk score calculation verified"


def validate_required_fields(result: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that all required output fields are present.
    
    Args:
        result: Agent 1 output dictionary
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = [
        "ap_serial",
        "risk_score",
        "risk_classification",
        "timestamp",
        "metrics"
    ]
    
    for field in required_fields:
        if field not in result:
            return False, f"Missing required field: {field}"
    
    # Check metrics subfields (at least some should be present)
    if "metrics" in result:
        metric_score_fields = ["retrans_score", "snr_score", "load_score"]
        present_count = sum(1 for field in metric_score_fields if field in result["metrics"])
        if present_count == 0:
            return False, "Missing all metric scores in metrics"
    
    return True, "All required fields present"


def validate_numeric_ranges(result: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that numeric values are within valid ranges.
    
    Args:
        result: Agent 1 output dictionary
    
    Returns:
        (is_valid, error_message)
    """
    # Risk score must be 0-100
    risk_score = result.get("risk_score")
    if risk_score is not None:
        if not (0 <= risk_score <= 100):
            return False, f"Risk score {risk_score} out of range (0-100)"
    
    # All metric scores must be 0-100
    metrics = result.get("metrics", {})
    score_fields = ["latency_score", "jitter_score", "retrans_score", "snr_score", "load_score", "auth_score"]
    for field in score_fields:
        score = metrics.get(field)
        if score is not None:
            if not (0 <= score <= 100):
                return False, f"{field} {score} out of range (0-100)"
    
    # Client count must be non-negative
    client_count = metrics.get("client_count")
    if client_count is not None:
        if client_count < 0:
            return False, f"Client count {client_count} cannot be negative"
    
    return True, "All numeric values in valid ranges"


def validate_agent1_output(output_file: Path = None) -> Dict[str, Any]:
    """
    Run all validators on Agent 1 output file.
    
    Args:
        output_file: Path to risk_scores.json (default: agent_data/risk_scores.json)
    
    Returns:
        Dictionary with validation results
    """
    if output_file is None:
        project_root = Path(__file__).parent.parent
        output_file = project_root / "agent_data" / "risk_scores.json"
    
    # Read output file
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {
            "valid": False,
            "error": f"Output file not found: {output_file}",
            "checks": []
        }
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": f"Invalid JSON: {e}",
            "checks": []
        }
    
    # Extract AP results (handle nested format)
    ap_results = []
    if isinstance(data, dict):
        # Nested format: {ap_serial: {current: {...}, historical: [...]}}
        for ap_serial, ap_data in data.items():
            if isinstance(ap_data, dict) and "current" in ap_data:
                ap_results.append(ap_data["current"])
    elif isinstance(data, list):
        # List format
        ap_results = data
    
    if not ap_results:
        return {
            "valid": False,
            "error": "No AP results found in output",
            "checks": []
        }
    
    # Run validators on each AP
    all_checks = []
    overall_valid = True
    
    for result in ap_results:
        ap_serial = result.get("ap_serial", "unknown")
        ap_checks = []
        
        # Check 1: Risk score ↔ classification
        valid, msg = validate_risk_score_classification(
            result.get("risk_score", 0),
            result.get("risk_classification", "")
        )
        ap_checks.append({
            "check": "risk_score_classification_match",
            "valid": valid,
            "message": msg
        })
        if not valid:
            overall_valid = False
        
        # Check 2: Contribution breakdown
        valid, msg = validate_contribution_breakdown(result)
        ap_checks.append({
            "check": "contribution_breakdown_sum",
            "valid": valid,
            "message": msg
        })
        if not valid:
            overall_valid = False
        
        # Check 3: Required fields
        valid, msg = validate_required_fields(result)
        ap_checks.append({
            "check": "required_fields_present",
            "valid": valid,
            "message": msg
        })
        if not valid:
            overall_valid = False
        
        # Check 4: Numeric ranges
        valid, msg = validate_numeric_ranges(result)
        ap_checks.append({
            "check": "numeric_ranges_valid",
            "valid": valid,
            "message": msg
        })
        if not valid:
            overall_valid = False
        
        all_checks.append({
            "ap_serial": ap_serial,
            "ap_name": result.get("ap_name"),
            "risk_score": result.get("risk_score"),
            "risk_classification": result.get("risk_classification"),
            "checks": ap_checks
        })
    
    return {
        "valid": overall_valid,
        "total_aps": len(ap_results),
        "checks": all_checks
    }


def print_validation_report(validation_results: Dict[str, Any]):
    """Print a formatted validation report"""
    print("\n" + "="*80)
    print("🔍 AGENT 1 DETERMINISTIC VALIDATION REPORT")
    print("="*80)
    
    if "error" in validation_results:
        print(f"\n❌ ERROR: {validation_results['error']}")
        return
    
    print(f"\n📊 Total APs validated: {validation_results['total_aps']}")
    print(f"✅ Overall valid: {validation_results['valid']}\n")
    
    for ap_result in validation_results['checks']:
        ap_status = "✅" if all(c["valid"] for c in ap_result["checks"]) else "❌"
        print(f"{ap_status} {ap_result['ap_serial']} ({ap_result['ap_name']})")
        print(f"   Risk: {ap_result['risk_score']} - {ap_result['risk_classification']}")
        
        for check in ap_result['checks']:
            status = "✅" if check["valid"] else "❌"
            print(f"   {status} {check['check']}: {check['message']}")
        print()
    
    print("="*80)


if __name__ == "__main__":
    # Run validation on latest Agent 1 output
    results = validate_agent1_output()
    print_validation_report(results)
    
    # Save validation results
    project_root = Path(__file__).parent.parent
    validation_file = project_root / "agent_data" / "agent1_validation.json"
    with open(validation_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Validation results saved to: {validation_file}")
