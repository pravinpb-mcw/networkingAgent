"""
MCP Tool: Generate Failover Suggestions
Wrapper for generate_failover_suggestions.py script
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from generate_failover_suggestions import generate_failover_suggestions
from read_risk_scores import read_risk_scores
from read_nearest_aps import read_nearest_aps
from read_network_policy import read_network_policy


async def generate_failover_suggestions_tool(
    risk_scores_path: str = None,
    nearest_aps_path: str = None,
    policy_path: str = None
) -> str:
    """
    Generate failover suggestions by analyzing risk scores, nearest APs, and policy
    
    This tool performs PURE LOGIC - no LLM inference:
    1. Reads risk scores from Agent 1
    2. Reads nearest AP data from Agent 2
    3. Reads network policy configuration
    4. Applies deterministic rules to generate failover suggestions
    
    Args:
        risk_scores_path: Optional custom path to risk_scores.json
        nearest_aps_path: Optional custom path to nearest_aps.json
        policy_path: Optional custom path to policy file
    
    Returns:
        JSON string with failover suggestions, reasoning, and action items
    """
    # Load all required data
    risk_result = read_risk_scores(risk_scores_path)
    if not risk_result["success"]:
        return json.dumps({
            "success": False,
            "error": f"Failed to load risk scores: {risk_result['error']}"
        }, indent=2)
    
    nearest_result = read_nearest_aps(nearest_aps_path)
    if not nearest_result["success"]:
        return json.dumps({
            "success": False,
            "error": f"Failed to load nearest APs: {nearest_result['error']}"
        }, indent=2)
    
    policy_result = read_network_policy(policy_path)
    if not policy_result["success"]:
        return json.dumps({
            "success": False,
            "error": f"Failed to load policy: {policy_result['error']}"
        }, indent=2)
    
    # Generate suggestions using pure logic
    result = generate_failover_suggestions(
        risk_scores=risk_result["risk_scores"],
        nearest_aps_data=nearest_result["nearest_aps"],
        policy=policy_result["policy"]
    )
    
    return json.dumps(result, indent=2)
