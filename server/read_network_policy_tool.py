"""
MCP Tool: Read Network Policy
Wrapper for read_network_policy.py script
"""

import json
import sys
from pathlib import Path
from typing import List
from mcp.types import TextContent

# Add scripts directory to path
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from read_network_policy import (
    read_network_policy,
    get_risk_threshold,
    get_failover_criteria,
    get_action_for_risk_score
)


async def read_network_policy_tool(file_path: str = None) -> List[TextContent]:
    """
    Read network policy configuration for failover decisions
    
    Args:
        file_path: Optional custom path to policy file
    
    Returns:
        List[TextContent] with policy configuration and extracted thresholds
    """
    # Read policy
    result = read_network_policy(file_path)
    
    if not result["success"]:
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    policy = result["policy"]
    
    # Extract key values
    result["extracted_values"] = {
        "failover_threshold": get_risk_threshold(policy),
        "failover_criteria": get_failover_criteria(policy),
        "risk_thresholds": policy.get("risk_thresholds", {}),
        "alert_rules": policy.get("alert_rules", {}),
        "decision_logic": policy.get("decision_logic", {})
    }
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
