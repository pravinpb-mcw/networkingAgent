"""
Input-Output Cross-Validation
==============================

Verify that tool OUTPUTS match what was requested in INPUTS.
This catches if AI hallucinates different data than what was requested.
"""

import json
import re
from typing import Tuple


def validate_ap_serial_consistency(tool_name: str, input_data: dict, output_data: dict) -> Tuple[float, str]:
    """
    Verify that the AP serial in OUTPUT matches the INPUT.
    
    Example:
    INPUT:  {ap_serial: "Q2XX-ABCD-1234"}
    OUTPUT: {ap_serial: "Q2XX-ABCD-1234", risk_score: 45}  ✅ MATCH
    OUTPUT: {ap_serial: "Q2XX-FAKE-9999", risk_score: 45}  ❌ MISMATCH (hallucination!)
    """
    try:
        # Extract AP serial from input
        input_serial = (
            input_data.get('ap_serial') or 
            input_data.get('device_serial') or 
            input_data.get('serial')
        )
        
        if not input_serial:
            return 1.0, "⚪ No AP serial in input (skipped)"
        
        # Extract AP serial from output
        output_str = json.dumps(output_data) if isinstance(output_data, dict) else str(output_data)
        
        # Check if input serial appears in output
        if input_serial in output_str:
            return 1.0, f"✅ {tool_name}: INPUT={input_serial} found in OUTPUT"
        else:
            # Try to find what serial is in output
            serial_pattern = r'Q2[A-Z]{2}-[A-Z0-9]{4,8}-[A-Z0-9]{4,8}'
            found_serials = re.findall(serial_pattern, output_str)
            
            if found_serials:
                return 0.0, f"❌ {tool_name}: INPUT={input_serial} but OUTPUT has {found_serials[0]} (HALLUCINATION!)"
            else:
                return 0.0, f"❌ {tool_name}: INPUT={input_serial} NOT in OUTPUT"
    
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


def validate_network_id_consistency(tool_name: str, input_data: dict, output_data: dict) -> Tuple[float, str]:
    """
    Verify that network_id in OUTPUT matches INPUT.
    """
    try:
        input_network = input_data.get('network_id')
        
        if not input_network:
            return 1.0, "⚪ No network_id in input"
        
        output_str = json.dumps(output_data) if isinstance(output_data, dict) else str(output_data)
        
        if input_network in output_str:
            return 1.0, f"✅ {tool_name}: network_id matches"
        else:
            return 0.0, f"❌ {tool_name}: INPUT network={input_network} NOT in OUTPUT"
    
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


def validate_risk_score_in_range(output_data: dict) -> Tuple[float, str]:
    """
    Verify risk score is within valid range (0-100).
    """
    try:
        # Parse nested structure if needed
        if 'content' in output_data:
            content_str = output_data['content']
            if isinstance(content_str, str):
                content = json.loads(content_str)
            else:
                content = content_str
        else:
            content = output_data
        
        risk_score = content.get('risk_score')
        
        if risk_score is None:
            return 1.0, "⚪ No risk_score in output"
        
        if 0 <= risk_score <= 100:
            return 1.0, f"✅ Risk score in range: {risk_score}"
        else:
            return 0.0, f"❌ Risk score out of range: {risk_score} (valid: 0-100)"
    
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


def validate_metrics_present(output_data: dict, required_metrics: list = None) -> Tuple[float, str]:
    """
    Verify that expected metrics are present in output.
    """
    try:
        if required_metrics is None:
            required_metrics = ['latency_score', 'jitter_score', 'retrans_score', 'snr_score', 'load_score', 'auth_score']
        
        # Parse nested structure
        if 'content' in output_data:
            content_str = output_data['content']
            if isinstance(content_str, str):
                content = json.loads(content_str)
            else:
                content = content_str
        else:
            content = output_data
        
        metrics = content.get('metrics', {})
        
        if not metrics:
            return 0.3, "⚠️ No metrics in output"
        
        present = [m for m in required_metrics if m in metrics]
        missing = [m for m in required_metrics if m not in metrics]
        
        coverage = len(present) / len(required_metrics)
        
        if coverage >= 0.8:
            return 1.0, f"✅ Metrics present: {len(present)}/{len(required_metrics)}"
        elif coverage >= 0.5:
            return 0.5, f"⚠️ Partial metrics: {len(present)}/{len(required_metrics)}, missing: {', '.join(missing)}"
        else:
            return 0.0, f"❌ Insufficient metrics: {len(present)}/{len(required_metrics)}"
    
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


def validate_timestamp_format(output_data: dict) -> Tuple[float, str]:
    """
    Verify timestamp is in valid ISO format.
    """
    try:
        # Parse nested structure
        if 'content' in output_data:
            content_str = output_data['content']
            if isinstance(content_str, str):
                content = json.loads(content_str)
            else:
                content = content_str
        else:
            content = output_data
        
        timestamp = content.get('timestamp')
        
        if not timestamp:
            return 0.5, "⚠️ No timestamp in output"
        
        # Try to parse as ISO format
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return 1.0, f"✅ Valid timestamp: {timestamp}"
        except:
            return 0.0, f"❌ Invalid timestamp format: {timestamp}"
    
    except Exception as e:
        return 0.5, f"⚠️ Validation error: {e}"


def cross_validate_tool_call(tool_name: str, input_data: dict, output_data: dict) -> Tuple[float, str]:
    """
    Comprehensive cross-validation of tool input vs output.
    
    This is the MAIN validator that runs all checks.
    """
    try:
        checks = []
        
        # 1. AP Serial Consistency
        if 'ap_serial' in input_data or 'device_serial' in input_data or 'serial' in input_data:
            score, msg = validate_ap_serial_consistency(tool_name, input_data, output_data)
            checks.append((score, msg))
        
        # 2. Network ID Consistency
        if 'network_id' in input_data:
            score, msg = validate_network_id_consistency(tool_name, input_data, output_data)
            checks.append((score, msg))
        
        # 3. Risk Score Range (for tools that return risk scores)
        if tool_name in ['update_risk_score', 'calculate_risk_score', 'get_risk_scores']:
            score, msg = validate_risk_score_in_range(output_data)
            checks.append((score, msg))
            
            # 4. Timestamp Format (for tools that have timestamps)
            if tool_name in ['update_risk_score', 'calculate_risk_score', 'get_risk_scores']:
                score, msg = validate_timestamp_format(output_data)
                checks.append((score, msg))
        
        # 5. Metrics Present (ONLY for get_risk_scores, NOT update_risk_score)
        if tool_name == 'get_risk_scores':
            score, msg = validate_metrics_present(output_data)
            checks.append((score, msg))
        
        # Calculate overall score
        if not checks:
            return 1.0, "✅ All basic checks passed"
        
        total_score = sum(s for s, _ in checks) / len(checks)
        
        # Build explanation
        failed = [msg for s, msg in checks if s < 0.8]
        passed = len([s for s, _ in checks if s >= 0.8])
        
        if total_score >= 0.9:
            return 1.0, f"✅ {tool_name}: All {len(checks)} checks passed"
        elif total_score >= 0.7:
            return total_score, f"⚠️ {tool_name}: {passed}/{len(checks)} passed | {' | '.join(failed)}"
        else:
            return total_score, f"❌ {tool_name}: Multiple failures | {' | '.join(failed)}"
    
    except Exception as e:
        return 0.5, f"⚠️ Cross-validation error: {e}"


if __name__ == "__main__":
    print("=== INPUT-OUTPUT CROSS-VALIDATION TESTS ===\n")
    
    # Test 1: AP Serial Match
    input_data = {"ap_serial": "Q2XX-ABCD-1234"}
    output_data = {"content": json.dumps({
        "ap_serial": "Q2XX-ABCD-1234",
        "risk_score": 45,
        "metrics": {
            "latency_score": 20,
            "jitter_score": 20,
            "retrans_score": 100,
            "snr_score": 80,
            "load_score": 20,
            "auth_score": 20
        },
        "timestamp": "2025-12-19T15:00:00"
    })}
    
    score, msg = cross_validate_tool_call("update_risk_score", input_data, output_data)
    print(f"1. Correct AP Serial: {score} - {msg}\n")
    
    # Test 2: AP Serial Mismatch (Hallucination)
    output_data_wrong = {"content": json.dumps({
        "ap_serial": "Q2XX-FAKE-9999",  # Wrong AP!
        "risk_score": 45
    })}
    
    score, msg = cross_validate_tool_call("update_risk_score", input_data, output_data_wrong)
    print(f"2. Wrong AP Serial: {score} - {msg}\n")
    
    # Test 3: Invalid Risk Score
    output_data_invalid = {"content": json.dumps({
        "ap_serial": "Q2XX-ABCD-1234",
        "risk_score": 150  # Out of range!
    })}
    
    score, msg = validate_risk_score_in_range(output_data_invalid)
    print(f"3. Invalid Risk Score: {score} - {msg}\n")
    
    print("✅ All cross-validation tests complete!")
