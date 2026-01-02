#!/usr/bin/env python3
"""
Standalone Risk Score Calculation Script
=========================================

This script implements the AP risk scoring logic from Agent 1 as a pure calculation tool.
NO LLM, NO MCP calls - just mathematical risk assessment.

Usage:
    As a module:
        from calculate_risk_score import calculate_ap_risk_score
        result = calculate_ap_risk_score(latency_ms=45, retrans_per_min=30, ...)
    
    As a CLI tool:
        python calculate_risk_score.py --ap-serial Q2XX-1234-5678 --latency 45 --retrans 30 --snr 22 --clients 15
        
Formula:
    RISK_SCORE = 0.25×latency + 0.20×jitter + 0.20×retrans + 0.15×snr + 0.10×load + 0.10×auth
"""

import json
import sys
import argparse
from typing import Dict, Any, Optional
from datetime import datetime


# ============================================================================
# RISK SCORING WEIGHTS (from Agent 1)
# ============================================================================

WEIGHTS = {
    "latency": 0.25,
    "jitter": 0.20,
    "retransmission": 0.20,
    "snr_degradation": 0.15,
    "client_load": 0.10,
    "auth_failure_rate": 0.10
}


# ============================================================================
# SCORING THRESHOLDS (0-100 scale, higher = worse)
# ============================================================================

def score_latency(latency_ms: float) -> float:
    """Score latency metric (0-100, higher = worse) - continuous scale"""
    if latency_ms <= 0:
        return 10.0
    elif latency_ms < 30:
        # Linear scale from 10 to 25 for 0-30ms range
        return 10.0 + (latency_ms / 30.0) * 15.0
    elif latency_ms < 60:
        # Linear scale from 25 to 55 for 30-60ms range
        return 25.0 + ((latency_ms - 30) / 30.0) * 30.0
    elif latency_ms < 100:
        # Linear scale from 55 to 85 for 60-100ms range
        return 55.0 + ((latency_ms - 60) / 40.0) * 30.0
    else:
        # Linear scale from 85 to 100 for 100ms+ (caps at 100)
        return min(100.0, 85.0 + ((latency_ms - 100) / 100.0) * 15.0)


def score_jitter(jitter_ms: float) -> float:
    """Score jitter metric (0-100, higher = worse) - continuous scale"""
    if jitter_ms <= 0:
        return 10.0
    elif jitter_ms < 10:
        # Linear scale from 10 to 25 for 0-10ms range
        return 10.0 + (jitter_ms / 10.0) * 15.0
    elif jitter_ms < 20:
        # Linear scale from 25 to 55 for 10-20ms range
        return 25.0 + ((jitter_ms - 10) / 10.0) * 30.0
    elif jitter_ms < 30:
        # Linear scale from 55 to 85 for 20-30ms range
        return 55.0 + ((jitter_ms - 20) / 10.0) * 30.0
    else:
        # Linear scale from 85 to 100 for 30ms+ (caps at 100)
        return min(100.0, 85.0 + ((jitter_ms - 30) / 30.0) * 15.0)


def score_retransmissions(retrans_per_min: float) -> float:
    """Score retransmission rate (0-100, higher = worse) - continuous scale"""
    if retrans_per_min <= 0:
        return 10.0
    elif retrans_per_min < 20:
        # Linear scale from 10 to 25 for 0-20 range
        return 10.0 + (retrans_per_min / 20.0) * 15.0
    elif retrans_per_min < 35:
        # Linear scale from 25 to 55 for 20-35 range
        return 25.0 + ((retrans_per_min - 20) / 15.0) * 30.0
    elif retrans_per_min < 50:
        # Linear scale from 55 to 85 for 35-50 range
        return 55.0 + ((retrans_per_min - 35) / 15.0) * 30.0
    else:
        # Linear scale from 85 to 100 for 50+ (caps at 100)
        return min(100.0, 85.0 + ((retrans_per_min - 50) / 30.0) * 15.0)


def score_snr(snr_db: float) -> float:
    """Score SNR (0-100, higher = worse, note: lower SNR is worse) - continuous scale"""
    if snr_db >= 35:
        return 10.0
    elif snr_db > 25:
        # Linear scale from 10 to 25 for 35-25dB range
        return 10.0 + ((35 - snr_db) / 10.0) * 15.0
    elif snr_db > 20:
        # Linear scale from 25 to 55 for 25-20dB range
        return 25.0 + ((25 - snr_db) / 5.0) * 30.0
    elif snr_db > 15:
        # Linear scale from 55 to 85 for 20-15dB range
        return 55.0 + ((20 - snr_db) / 5.0) * 30.0
    else:
        # Linear scale from 85 to 100 for below 15dB (caps at 100)
        return min(100.0, 85.0 + ((15 - snr_db) / 10.0) * 15.0)


def score_client_load(client_count: int) -> float:
    """Score client load (0-100, higher = worse) - continuous scale"""
    if client_count <= 0:
        return 10.0
    elif client_count < 20:
        # Linear scale from 10 to 25 for 0-20 clients
        return 10.0 + (client_count / 20.0) * 15.0
    elif client_count < 40:
        # Linear scale from 25 to 55 for 20-40 clients
        return 25.0 + ((client_count - 20) / 20.0) * 30.0
    elif client_count < 60:
        # Linear scale from 55 to 85 for 40-60 clients
        return 55.0 + ((client_count - 40) / 20.0) * 30.0
    else:
        # Linear scale from 85 to 100 for 60+ (caps at 100)
        return min(100.0, 85.0 + ((client_count - 60) / 40.0) * 15.0)


def score_auth_failures(auth_failures_per_hour: float) -> float:
    """Score authentication failure rate (0-100, higher = worse) - continuous scale"""
    if auth_failures_per_hour <= 0:
        return 10.0
    elif auth_failures_per_hour < 3:
        # Linear scale from 10 to 25 for 0-3 failures
        return 10.0 + (auth_failures_per_hour / 3.0) * 15.0
    elif auth_failures_per_hour < 8:
        # Linear scale from 25 to 55 for 3-8 failures
        return 25.0 + ((auth_failures_per_hour - 3) / 5.0) * 30.0
    elif auth_failures_per_hour < 15:
        # Linear scale from 55 to 85 for 8-15 failures
        return 55.0 + ((auth_failures_per_hour - 8) / 7.0) * 30.0
    else:
        # Linear scale from 85 to 100 for 15+ (caps at 100)
        return min(100.0, 85.0 + ((auth_failures_per_hour - 15) / 15.0) * 15.0)


# ============================================================================
# RISK CLASSIFICATION
# ============================================================================

def classify_risk(risk_score: float) -> str:
    """Classify risk score into categories"""
    if risk_score <= 20:
        return "Stable Network"
    elif risk_score <= 40:
        return "Temporary Degradation"
    elif risk_score <= 70:
        return "Sustained Degradation"
    else:
        return "Likely Failure"


def get_risk_indicator(risk_score: float) -> str:
    """Get emoji indicator for risk level"""
    if risk_score <= 20:
        return "🟢"
    elif risk_score <= 40:
        return "🟡"
    elif risk_score <= 70:
        return "🟠"
    else:
        return "🔴"


# ============================================================================
# MAIN RISK CALCULATION FUNCTION
# ============================================================================

def calculate_ap_risk_score(
    ap_serial: str,
    ap_name: Optional[str] = None,
    latency_ms: Optional[float] = None,
    jitter_ms: Optional[float] = None,
    retrans_per_min: Optional[float] = None,
    snr_db: Optional[float] = None,
    client_count: Optional[int] = None,
    auth_failures_per_hour: Optional[float] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate risk score for an Access Point based on metrics.
    
    Args:
        ap_serial: AP serial number (required)
        ap_name: AP friendly name (optional)
        latency_ms: Average latency in milliseconds
        jitter_ms: Jitter in milliseconds
        retrans_per_min: Retransmissions per minute
        snr_db: Signal-to-Noise Ratio in dB
        client_count: Number of connected clients
        auth_failures_per_hour: Authentication failures per hour
        timestamp: ISO timestamp (auto-generated if not provided)
    
    Returns:
        Dictionary with risk score, classification, and all metrics
    """
    
    # Default values for missing metrics (assume baseline good values, not worst case)
    # Using 15.0 as default to allow for natural variation (not exactly 20)
    DEFAULT_SCORE = 15.0
    
    # Calculate individual metric scores
    latency_score = score_latency(latency_ms) if latency_ms is not None else DEFAULT_SCORE
    jitter_score = score_jitter(jitter_ms) if jitter_ms is not None else DEFAULT_SCORE
    retrans_score = score_retransmissions(retrans_per_min) if retrans_per_min is not None else DEFAULT_SCORE
    snr_score = score_snr(snr_db) if snr_db is not None else DEFAULT_SCORE
    load_score = score_client_load(client_count) if client_count is not None else DEFAULT_SCORE
    auth_score = score_auth_failures(auth_failures_per_hour) if auth_failures_per_hour is not None else DEFAULT_SCORE
    
    # Calculate composite risk score using weighted formula
    risk_score = (
        WEIGHTS["latency"] * latency_score +
        WEIGHTS["jitter"] * jitter_score +
        WEIGHTS["retransmission"] * retrans_score +
        WEIGHTS["snr_degradation"] * snr_score +
        WEIGHTS["client_load"] * load_score +
        WEIGHTS["auth_failure_rate"] * auth_score
    )
    
    # Round to 1 decimal place
    risk_score = round(risk_score, 1)
    
    # Classify risk
    risk_classification = classify_risk(risk_score)
    risk_indicator = get_risk_indicator(risk_score)
    
    # Prepare result
    result = {
        "success": True,
        "ap_serial": ap_serial,
        "ap_name": ap_name or ap_serial,
        "risk_score": risk_score,
        "risk_classification": risk_classification,
        "risk_indicator": risk_indicator,
        "timestamp": timestamp or datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "latency_ms": latency_ms,
            "latency_score": latency_score,
            "jitter_ms": jitter_ms,
            "jitter_score": jitter_score,
            "retrans_per_min": retrans_per_min,
            "retrans_score": retrans_score,
            "snr_db": snr_db,
            "snr_score": snr_score,
            "client_count": client_count,
            "load_score": load_score,
            "auth_failures_per_hour": auth_failures_per_hour,
            "auth_score": auth_score
        },
        "calculation": {
            "formula": "0.25×lat + 0.20×jit + 0.20×ret + 0.15×snr + 0.10×load + 0.10×auth",
            "breakdown": {
                "latency_contribution": round(WEIGHTS["latency"] * latency_score, 2),
                "jitter_contribution": round(WEIGHTS["jitter"] * jitter_score, 2),
                "retrans_contribution": round(WEIGHTS["retransmission"] * retrans_score, 2),
                "snr_contribution": round(WEIGHTS["snr_degradation"] * snr_score, 2),
                "load_contribution": round(WEIGHTS["client_load"] * load_score, 2),
                "auth_contribution": round(WEIGHTS["auth_failure_rate"] * auth_score, 2)
            }
        }
    }
    
    return result


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def calculate_multiple_aps(ap_metrics_list: list) -> Dict[str, Any]:
    """
    Calculate risk scores for multiple APs in batch.
    
    Args:
        ap_metrics_list: List of dictionaries with AP metrics
    
    Returns:
        Dictionary with results for all APs
    """
    results = {}
    
    for ap_metrics in ap_metrics_list:
        ap_serial = ap_metrics.get("ap_serial")
        if not ap_serial:
            continue
        
        result = calculate_ap_risk_score(**ap_metrics)
        results[ap_serial] = result
    
    return {
        "success": True,
        "total_aps": len(results),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "results": results
    }


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for risk score calculation"""
    parser = argparse.ArgumentParser(
        description="Calculate AP risk score based on network metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate risk for a single AP with full metrics
  python calculate_risk_score.py --ap-serial Q2XX-ABCD-1234 --ap-name "AP-01" \\
      --latency 45 --jitter 15 --retrans 30 --snr 22 --clients 15

  # Calculate with partial metrics (missing metrics default to score 20)
  python calculate_risk_score.py --ap-serial Q2XX-ABCD-1234 --latency 80 --retrans 55

  # Batch processing from JSON file
  python calculate_risk_score.py --batch input.json --output results.json

  # Pretty print output
  python calculate_risk_score.py --ap-serial Q2XX-1234 --latency 45 --pretty
        """
    )
    
    # Single AP mode
    parser.add_argument("--ap-serial", help="AP serial number")
    parser.add_argument("--ap-name", help="AP friendly name")
    parser.add_argument("--latency", type=float, help="Latency in ms")
    parser.add_argument("--jitter", type=float, help="Jitter in ms")
    parser.add_argument("--retrans", type=float, help="Retransmissions per minute")
    parser.add_argument("--snr", type=float, help="SNR in dB")
    parser.add_argument("--clients", type=int, help="Number of clients")
    parser.add_argument("--auth-failures", type=float, help="Auth failures per hour")
    
    # Batch mode
    parser.add_argument("--batch", help="JSON file with multiple APs' metrics")
    parser.add_argument("--output", help="Output file for results (default: stdout)")
    
    # Output options
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output")
    parser.add_argument("--summary", action="store_true", help="Show summary only (no full metrics)")
    
    args = parser.parse_args()
    
    # Batch mode
    if args.batch:
        try:
            with open(args.batch, 'r') as f:
                ap_metrics_list = json.load(f)
            
            results = calculate_multiple_aps(ap_metrics_list)
            
            # Output
            output_json = json.dumps(results, indent=2 if args.pretty else None)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output_json)
                print(f"✅ Results written to {args.output}")
            else:
                print(output_json)
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1
    
    # Single AP mode
    if not args.ap_serial:
        parser.print_help()
        print("\n❌ Error: --ap-serial is required for single AP mode", file=sys.stderr)
        return 1
    
    try:
        result = calculate_ap_risk_score(
            ap_serial=args.ap_serial,
            ap_name=args.ap_name,
            latency_ms=args.latency,
            jitter_ms=args.jitter,
            retrans_per_min=args.retrans,
            snr_db=args.snr,
            client_count=args.clients,
            auth_failures_per_hour=args.auth_failures
        )
        
        # Summary mode
        if args.summary:
            print(f"{result['risk_indicator']} {result['ap_name']}: Risk Score = {result['risk_score']} ({result['risk_classification']})")
            return 0
        
        # Full output
        output_json = json.dumps(result, indent=2 if args.pretty else None)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_json)
            print(f"✅ Results written to {args.output}")
        else:
            print(output_json)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
