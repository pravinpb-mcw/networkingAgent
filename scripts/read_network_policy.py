"""
Read Network Policy Script
Pure data reading - NO LLM, NO calculations

Reads network policy configuration from policies/network_policy.json
Returns structured policy data for Agent 3 to use in decision making
"""

import json
from typing import Dict, Optional
from pathlib import Path


def read_network_policy(file_path: Optional[str] = None) -> Dict:
    """
    Read network policy configuration
    
    Args:
        file_path: Path to policy JSON file (optional, defaults to policies/network_policy.json)
    
    Returns:
        Dictionary containing policy configuration
    """
    # Default path
    if file_path is None:
        script_dir = Path(__file__).parent.parent
        file_path = script_dir / "policies" / "network_policy.json"
    
    file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        return {
            "success": False,
            "error": f"Policy file not found: {file_path}",
            "policy": {}
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            policy = json.load(f)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "policy_version": policy.get("policy_version", "unknown"),
            "policy_name": policy.get("policy_name", "unknown"),
            "policy": policy
        }
    
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON parsing error: {str(e)}",
            "policy": {}
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}",
            "policy": {}
        }


def get_risk_threshold(policy: Dict) -> float:
    """
    Extract minimum risk score threshold for failover from policy
    
    Returns:
        Minimum risk score that triggers failover recommendation
    """
    if not policy:
        return 41.0  # Default to Sustained Degradation
    
    failover_criteria = policy.get("failover_criteria", {})
    return failover_criteria.get("minimum_risk_score_for_failover", 41.0)


def get_failover_criteria(policy: Dict) -> Dict:
    """
    Extract all failover criteria from policy
    
    Returns:
        Dictionary with failover decision criteria
    """
    if not policy:
        return {
            "minimum_risk_score_for_failover": 41.0,
            "minimum_risk_improvement_required": 15.0,
            "maximum_distance_meters": 50.0,
            "minimum_rssi_dbm": -75.0,
            "prefer_same_floor": True,
            "avoid_channel_overlap": True
        }
    
    return policy.get("failover_criteria", {})


def get_action_for_risk_score(policy: Dict, risk_score: float) -> str:
    """
    Determine recommended action based on risk score and policy
    
    Args:
        policy: Policy configuration
        risk_score: AP risk score
    
    Returns:
        Recommended action: monitor, alert, failover_recommendation, urgent_failover
    """
    if not policy:
        # Default logic
        if risk_score <= 20:
            return "monitor"
        elif risk_score <= 40:
            return "alert"
        elif risk_score <= 70:
            return "failover_recommendation"
        else:
            return "urgent_failover"
    
    thresholds = policy.get("risk_thresholds", {})
    
    if risk_score <= thresholds.get("stable", {}).get("max_score", 20):
        return thresholds.get("stable", {}).get("action", "monitor")
    elif risk_score <= thresholds.get("temporary_degradation", {}).get("max_score", 40):
        return thresholds.get("temporary_degradation", {}).get("action", "alert")
    elif risk_score <= thresholds.get("sustained_degradation", {}).get("max_score", 70):
        return thresholds.get("sustained_degradation", {}).get("action", "failover_recommendation")
    else:
        return thresholds.get("likely_failure", {}).get("action", "urgent_failover")


if __name__ == "__main__":
    # Test the function
    result = read_network_policy()
    
    if result["success"]:
        print(f"✅ Successfully read policy: {result['policy_name']}")
        print(f"📁 File: {result['file_path']}")
        print(f"📋 Version: {result['policy_version']}")
        
        policy = result["policy"]
        
        # Show threshold
        threshold = get_risk_threshold(policy)
        print(f"\n⚠️  Failover Threshold: Risk Score ≥ {threshold}")
        
        # Show criteria
        criteria = get_failover_criteria(policy)
        print("\n📊 Failover Criteria:")
        for key, value in criteria.items():
            print(f"  - {key}: {value}")
        
        # Test action determination
        print("\n🎯 Action Mapping:")
        test_scores = [15, 35, 55, 85]
        for score in test_scores:
            action = get_action_for_risk_score(policy, score)
            print(f"  Risk {score}: → {action}")
    else:
        print(f"❌ Error: {result['error']}")
