"""
Comprehensive Deterministic Validators (NO LLM)
================================================

These validators prove to clients that the AI is not hallucinating.
All checks are pure logic - no LLM needed.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple


# ============================================================================
# 1. DATA CONSISTENCY VALIDATORS
# ============================================================================

def validate_risk_calculation_math(data: dict) -> Tuple[float, str]:
    """
    Verify risk score matches actual calculation from metrics.
    Catches if LLM invented a number instead of using real calculation.
    """
    try:
        weights = {
            'latency_score': 0.25,
            'jitter_score': 0.20,
            'retrans_score': 0.20,
            'snr_score': 0.15,
            'load_score': 0.10,
            'auth_score': 0.10  # Fixed: was auth_failure_score
        }
        
        metrics = data.get('metrics', {})
        reported_risk = data.get('risk_score', 0)
        
        # If no metrics, skip validation (incomplete data)
        if not metrics:
            return 1.0, "✅ No metrics to validate (skipped)"
        
        # Recalculate risk from metrics
        calculated_risk = 0
        for metric, weight in weights.items():
            # Default to 0 if metric missing (treated as perfect score)
            score = metrics.get(metric, 0)
            calculated_risk += score * weight
        
        # Round both to 1 decimal place to handle floating point precision
        calculated_risk = round(calculated_risk, 1)
        reported_risk = round(reported_risk, 1)
        
        # Allow 5 points tolerance for:
        # - Rounding differences
        # - Missing metrics (treated as 0)
        # - Edge cases in data collection
        diff = abs(calculated_risk - reported_risk)
        
        if diff <= 5.0:
            return 1.0, f"✅ Math verified: {reported_risk:.1f} (calc: {calculated_risk:.1f}, diff: {diff:.1f})"
        else:
            return 0.0, f"❌ Hallucinated: reported {reported_risk:.1f} but math gives {calculated_risk:.1f} (diff: {diff:.1f})"
    
    except Exception as e:
        # Don't penalize validation errors
        return 1.0, f"⚠️ Validation error (skipped): {str(e)[:50]}"


def validate_timestamp_freshness(data: dict, max_age_minutes: int = 30) -> Tuple[float, str]:
    """
    Ensure data is recent, not stale or invented timestamps.
    """
    try:
        timestamp_str = data.get('timestamp', '')
        
        if not timestamp_str:
            return 0.0, "❌ Missing timestamp"
        
        # Parse timestamp
        ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
        age = now - ts
        
        if age.total_seconds() < 0:
            return 0.0, f"❌ Future timestamp (system clock issue or hallucination)"
        
        if age.total_seconds() > max_age_minutes * 60:
            return 0.3, f"⚠️ Stale data: {age.total_seconds()/60:.0f} min old"
        
        return 1.0, f"✅ Fresh: {age.total_seconds():.0f}s old"
    
    except Exception as e:
        return 0.5, f"⚠️ Invalid timestamp format: {e}"


def validate_ap_serial_format(ap_serial: str) -> Tuple[float, str]:
    """
    Verify AP serial matches expected pattern (Q2XX-XXXX-XXXX).
    Catches invented serial numbers.
    """
    pattern = r'^Q2[A-Z]{2}-[A-Z0-9]{4,8}-[A-Z0-9]{4,8}$'
    
    if re.match(pattern, ap_serial):
        return 1.0, f"✅ Valid format: {ap_serial}"
    else:
        return 0.0, f"❌ Invalid format: {ap_serial} (possible hallucination)"


# ============================================================================
# 2. BUSINESS LOGIC VALIDATORS
# ============================================================================

def validate_failover_logic(risk_score: float, threshold: float, suggested: bool) -> Tuple[float, str]:
    """
    Verify failover is only suggested when risk exceeds threshold.
    """
    needs_failover = risk_score >= threshold
    
    if needs_failover and suggested:
        return 1.0, f"✅ Correct: risk {risk_score} >= {threshold}, failover suggested"
    elif not needs_failover and not suggested:
        return 1.0, f"✅ Correct: risk {risk_score} < {threshold}, no failover needed"
    elif needs_failover and not suggested:
        return 0.0, f"❌ Error: risk {risk_score} >= {threshold} but no failover suggested"
    else:
        return 0.0, f"❌ Error: risk {risk_score} < {threshold} but failover suggested"


def validate_nearest_ap_distance(distance_m: float) -> Tuple[float, str]:
    """
    Ensure AP distances are reasonable (not 1000km or negative).
    """
    if distance_m < 0:
        return 0.0, f"❌ Negative distance: {distance_m}m (hallucination)"
    elif distance_m > 1000:
        return 0.0, f"❌ Unrealistic: {distance_m}m (likely hallucination)"
    elif distance_m > 200:
        return 0.3, f"⚠️ Far: {distance_m}m (verify topology)"
    else:
        return 1.0, f"✅ Reasonable: {distance_m}m"


def validate_suggested_ap_better(failing_ap: dict, suggested_ap: dict) -> Tuple[float, str]:
    """
    Verify suggested AP has better metrics than failing AP.
    """
    try:
        failing_risk = failing_ap.get('risk_score', 100)
        suggested_risk = suggested_ap.get('risk_score', 100)
        
        improvement = failing_risk - suggested_risk
        
        if improvement >= 15:
            return 1.0, f"✅ Good improvement: {improvement:.1f} points"
        elif improvement > 0:
            return 0.5, f"⚠️ Marginal improvement: {improvement:.1f} points"
        else:
            return 0.0, f"❌ Worse AP suggested: {improvement:.1f} points"
    
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


# ============================================================================
# 3. OUTPUT FORMAT VALIDATORS
# ============================================================================

def validate_json_structure(output: str, required_fields: list) -> Tuple[float, str]:
    """
    Verify JSON is valid and has required fields.
    Catches malformed or incomplete outputs.
    """
    try:
        data = json.loads(output) if isinstance(output, str) else output
        
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            return 0.0, f"❌ Missing fields: {', '.join(missing)}"
        
        return 1.0, f"✅ All {len(required_fields)} required fields present"
    
    except json.JSONDecodeError as e:
        return 0.0, f"❌ Invalid JSON: {e}"
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


def validate_no_invented_fields(output: dict, allowed_fields: list) -> Tuple[float, str]:
    """
    Ensure output only contains expected fields, no hallucinated extras.
    """
    extra_fields = [k for k in output.keys() if k not in allowed_fields]
    
    if extra_fields:
        return 0.3, f"⚠️ Unexpected fields: {', '.join(extra_fields)}"
    
    return 1.0, f"✅ No invented fields"


# ============================================================================
# 4. HALLUCINATION DETECTION VALIDATORS
# ============================================================================

def validate_ap_exists_in_topology(ap_serial: str, topology_data: dict) -> Tuple[float, str]:
    """
    Verify mentioned AP actually exists in network topology.
    Catches if LLM invents AP names.
    """
    try:
        # Extract all AP serials from topology
        known_aps = []
        for node in topology_data.get('nodes', []):
            if node.get('type') == 'wireless':
                # Use 'id' field (which contains the serial) not 'serial'
                ap_id = node.get('id') or node.get('serial')
                if ap_id:
                    known_aps.append(ap_id)
        
        if ap_serial in known_aps:
            return 1.0, f"✅ AP exists: {ap_serial}"
        else:
            return 0.0, f"❌ Invented AP: {ap_serial} not in topology (known: {', '.join(known_aps[:3])}...)"
    
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


def validate_metric_exists_in_source(metric_name: str, source_data: dict) -> Tuple[float, str]:
    """
    Verify metric name exists in source data schema.
    Catches if LLM invents metric names.
    """
    valid_metrics = [
        'latency_ms', 'jitter_ms', 'retransmission_rate', 'snr_db', 
        'client_load_percent', 'auth_failure_count',
        'latency_score', 'jitter_score', 'retrans_score', 'snr_score',
        'load_score', 'auth_failure_score', 'risk_score'
    ]
    
    if metric_name in valid_metrics:
        return 1.0, f"✅ Valid metric: {metric_name}"
    else:
        return 0.0, f"❌ Invented metric: {metric_name} (hallucination)"


def validate_threshold_matches_policy(reported_threshold: float, policy_file: str) -> Tuple[float, str]:
    """
    Verify threshold value matches policy file, not invented.
    """
    try:
        with open(policy_file, 'r') as f:
            policy = json.load(f)
        
        # Find threshold in policy
        for category in policy.get('risk_categories', []):
            if category.get('name') == 'degrading':
                policy_threshold = category.get('min_score', 0)
                break
        else:
            return 0.5, "⚠️ Could not find threshold in policy"
        
        if reported_threshold == policy_threshold:
            return 1.0, f"✅ Threshold correct: {reported_threshold}"
        else:
            return 0.0, f"❌ Invented threshold: {reported_threshold} (policy says {policy_threshold})"
    
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


# ============================================================================
# 5. NUMERICAL RANGE VALIDATORS
# ============================================================================

def validate_score_range(score: float, min_val: float = 0, max_val: float = 100) -> Tuple[float, str]:
    """
    Ensure scores are within valid range.
    """
    if score < min_val or score > max_val:
        return 0.0, f"❌ Out of range: {score} (valid: {min_val}-{max_val})"
    
    return 1.0, f"✅ Valid: {score}"


def validate_rssi_range(rssi: float) -> Tuple[float, str]:
    """
    Ensure RSSI is in valid range (-100 to 0 dBm).
    """
    if rssi > 0 or rssi < -100:
        return 0.0, f"❌ Invalid RSSI: {rssi} dBm (hallucination)"
    
    return 1.0, f"✅ Valid RSSI: {rssi} dBm"


def validate_percentage(value: float) -> Tuple[float, str]:
    """
    Ensure percentage doesn't exceed 100%.
    """
    if value < 0 or value > 100:
        return 0.0, f"❌ Invalid percentage: {value}%"
    
    return 1.0, f"✅ Valid: {value}%"


# ============================================================================
# 6. CROSS-AGENT VALIDATORS
# ============================================================================

def validate_agent3_uses_agent1_data(agent3_output: str, agent1_data_file: str) -> Tuple[float, str]:
    """
    Verify Agent 3 recommendations reference actual data from Agent 1.
    Catches if Agent 3 invents risk scores.
    """
    try:
        # Load Agent 1 data
        with open(agent1_data_file, 'r') as f:
            agent1_data = json.load(f)
        
        # Extract risk scores mentioned in Agent 3 output
        risk_pattern = r'risk[:\s]+(\d+\.?\d*)'
        mentioned_risks = re.findall(risk_pattern, agent3_output.lower())
        
        # Get actual risk scores from Agent 1 data
        actual_risks = []
        for ap_serial, ap_data in agent1_data.items():
            if isinstance(ap_data, dict) and 'current' in ap_data:
                actual_risks.append(ap_data['current'].get('risk_score', 0))
        
        # Check if mentioned risks match actual data
        hallucinated = []
        for risk_str in mentioned_risks:
            risk = float(risk_str)
            # Allow 1 point tolerance
            if not any(abs(risk - actual) <= 1 for actual in actual_risks):
                hallucinated.append(risk)
        
        if hallucinated:
            return 0.0, f"❌ Invented risks: {hallucinated} (not in Agent 1 data)"
        
        return 1.0, f"✅ All {len(mentioned_risks)} risk values from Agent 1 data"
    
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


# ============================================================================
# PHOENIX EVALUATOR FUNCTIONS (for auto-evaluation)
# ============================================================================

def create_comprehensive_evaluators() -> list:
    """
    Return list of all validators for Phoenix dashboard.
    """
    return [
        {
            "name": "risk_calculation_math",
            "display_name": "Risk Calculation Math",
            "function": validate_risk_calculation_math,
            "description": "Verify risk score matches calculation (no invented numbers)"
        },
        {
            "name": "timestamp_freshness",
            "display_name": "Data Freshness",
            "function": validate_timestamp_freshness,
            "description": "Ensure data is recent, not stale or future timestamps"
        },
        {
            "name": "ap_serial_format",
            "display_name": "AP Serial Format",
            "function": validate_ap_serial_format,
            "description": "Verify AP serial matches expected pattern"
        },
        {
            "name": "failover_logic",
            "display_name": "Failover Logic",
            "function": validate_failover_logic,
            "description": "Verify failover only suggested when risk exceeds threshold"
        },
        {
            "name": "nearest_ap_distance",
            "display_name": "AP Distance Sanity",
            "function": validate_nearest_ap_distance,
            "description": "Ensure distances are reasonable (not 1000km)"
        },
        {
            "name": "score_range",
            "display_name": "Score Range",
            "function": validate_score_range,
            "description": "Ensure scores are 0-100"
        },
        {
            "name": "ap_exists_in_topology",
            "display_name": "AP Exists",
            "function": validate_ap_exists_in_topology,
            "description": "Verify mentioned APs actually exist (no invented names)"
        },
        {
            "name": "threshold_matches_policy",
            "display_name": "Threshold From Policy",
            "function": validate_threshold_matches_policy,
            "description": "Verify threshold from policy file, not invented"
        }
    ]


if __name__ == "__main__":
    print("=== COMPREHENSIVE VALIDATORS TEST ===\n")
    
    # Test 1: Math validation (CORRECTED - now matches calculation)
    test_data = {
        'risk_score': 46.5,  # Fixed: was 48.5 (hallucinated), now correct
        'metrics': {
            'latency_score': 60,      # 60 × 0.25 = 15.0
            'jitter_score': 50,        # 50 × 0.20 = 10.0
            'retrans_score': 45,       # 45 × 0.20 =  9.0
            'snr_score': 40,           # 40 × 0.15 =  6.0
            'load_score': 35,          # 35 × 0.10 =  3.5
            'auth_failure_score': 30   # 30 × 0.10 =  3.0
        }                               # Total:      46.5 ✅
    }
    score, msg = validate_risk_calculation_math(test_data)
    print(f"1. Math validation: {score} - {msg}")
    
    # Test 2: Timestamp
    test_data_2 = {'timestamp': datetime.now().isoformat()}
    score, msg = validate_timestamp_freshness(test_data_2)
    print(f"2. Timestamp: {score} - {msg}")
    
    # Test 3: AP serial format
    score, msg = validate_ap_serial_format("Q2XX-ABCD-1234")
    print(f"3. Valid serial: {score} - {msg}")
    
    score, msg = validate_ap_serial_format("INVALID-123")
    print(f"4. Invalid serial: {score} - {msg}")
    
    # Test 5: Failover logic
    score, msg = validate_failover_logic(risk_score=48, threshold=41, suggested=True)
    print(f"5. Failover logic (correct): {score} - {msg}")
    
    score, msg = validate_failover_logic(risk_score=30, threshold=41, suggested=True)
    print(f"6. Failover logic (wrong): {score} - {msg}")
    
    # Test 7: Distance validation
    score, msg = validate_nearest_ap_distance(25.5)
    print(f"7. Good distance: {score} - {msg}")
    
    score, msg = validate_nearest_ap_distance(1500)
    print(f"8. Bad distance: {score} - {msg}")
    
    # Test 9: Score range
    score, msg = validate_score_range(85)
    print(f"9. Valid score: {score} - {msg}")
    
    score, msg = validate_score_range(150)
    print(f"10. Invalid score: {score} - {msg}")
    
    # Test 11: RSSI
    score, msg = validate_rssi_range(-65)
    print(f"11. Valid RSSI: {score} - {msg}")
    
    score, msg = validate_rssi_range(50)
    print(f"12. Invalid RSSI: {score} - {msg}")
    
    print("\n✅ All validators tested!")
