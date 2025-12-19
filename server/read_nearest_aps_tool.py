"""
MCP Tool: Read Nearest APs
Wrapper for read_nearest_aps.py script
"""

import json
import sys
from pathlib import Path
from typing import List
from mcp.types import TextContent

# Add scripts directory to path
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from read_nearest_aps import read_nearest_aps, get_nearest_for_ap, filter_candidates_by_criteria


async def read_nearest_aps_tool(
    file_path: str = None,
    ap_serial: str = None,
    min_rssi: float = -75.0,
    max_distance: float = 50.0,
    prefer_same_floor: bool = True
) -> List[TextContent]:
    """
    Read nearest APs data from Agent 2 output (nearest_aps.json)
    
    Args:
        file_path: Optional custom path to nearest_aps.json
        ap_serial: Optional specific AP serial to get candidates for
        min_rssi: Minimum acceptable RSSI in dBm (default -75)
        max_distance: Maximum distance in meters (default 50)
        prefer_same_floor: Prioritize same floor candidates (default True)
    
    Returns:
        List[TextContent] with nearest APs data
    """
    # Read nearest APs data
    result = read_nearest_aps(file_path)
    
    if not result["success"]:
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # If specific AP requested, filter to that AP only
    if ap_serial:
        ap_data = get_nearest_for_ap(result["nearest_aps"], ap_serial)
        
        if ap_data:
            # Apply criteria filtering
            candidates = ap_data.get("candidates", [])
            filtered = filter_candidates_by_criteria(
                candidates,
                min_rssi=min_rssi,
                max_distance=max_distance,
                prefer_same_floor=prefer_same_floor
            )
            
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "source_ap_serial": ap_serial,
                "source_ap_name": ap_data.get("source_ap_name"),
                "total_candidates": len(candidates),
                "filtered_candidates": len(filtered),
                "candidates": filtered,
                "filter_criteria": {
                    "min_rssi_dbm": min_rssi,
                    "max_distance_meters": max_distance,
                    "prefer_same_floor": prefer_same_floor
                }
            }, indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": f"No nearest AP data found for AP: {ap_serial}"
            }, indent=2))]
    
    # Return all data
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
