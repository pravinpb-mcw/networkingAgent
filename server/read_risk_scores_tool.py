"""
MCP Tool: Read Risk Scores
Wrapper for read_risk_scores.py script
"""

import json
import sys
from pathlib import Path
from typing import List
from mcp.types import TextContent

# Add scripts directory to path
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from read_risk_scores import read_risk_scores, filter_by_threshold, categorize_by_severity


async def read_risk_scores_tool(
    file_path: str = None,
    min_threshold: float = None,
    categorize: bool = False
) -> List[TextContent]:
    """
    Read risk scores from Agent 1 output (risk_scores.json)
    
    Args:
        file_path: Optional custom path to risk_scores.json
        min_threshold: Optional minimum risk score to filter (e.g., 41 for failover candidates)
        categorize: If True, return categorized by severity
    
    Returns:
        List[TextContent] with risk scores data
    """
    # Read risk scores
    result = read_risk_scores(file_path)
    
    if not result["success"]:
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # Apply threshold filter if specified
    if min_threshold is not None:
        filtered_scores = filter_by_threshold(result["risk_scores"], min_threshold)
        result["filtered_aps"] = filtered_scores
        result["filtered_count"] = len(filtered_scores)
        result["filter_threshold"] = min_threshold
    
    # Categorize if requested
    if categorize:
        categories = categorize_by_severity(result["risk_scores"])
        result["categories"] = {
            "stable": len(categories["stable"]),
            "temporary_degradation": len(categories["temporary_degradation"]),
            "sustained_degradation": len(categories["sustained_degradation"]),
            "likely_failure": len(categories["likely_failure"])
        }
        result["categories_detail"] = categories
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
