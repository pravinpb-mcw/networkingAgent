#!/usr/bin/env python3
"""
MCP Tool: Calculate Nearest APs
Wrapper around the standalone nearest AP calculation script
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
from mcp.types import TextContent

# Add scripts directory to path
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from calculate_nearest_aps import calculate_nearest_aps_for_ap

logger = logging.getLogger("calculate-nearest-aps-tool")


async def calculate_nearest_aps(
    source_ap_serial: str,
    source_ap_name: str,
    source_ap_lat: float,
    source_ap_lng: float,
    source_ap_floor: int,
    source_ap_channel: int,
    all_aps: List[Dict[str, Any]],
    max_candidates: int = 5
) -> List[TextContent]:
    """
    Calculate nearest APs for a source AP using the standalone calculation script.
    
    This tool does ALL the math - the LLM just passes parameters!
    
    Args:
        source_ap_serial: Source AP serial number (REQUIRED)
        source_ap_name: Source AP name (REQUIRED)
        source_ap_lat: Source AP latitude (REQUIRED)
        source_ap_lng: Source AP longitude (REQUIRED)
        source_ap_floor: Source AP floor number (REQUIRED)
        source_ap_channel: Source AP WiFi channel (REQUIRED)
        all_aps: List of all APs with {serial, name, lat, lng, floor, channel, client_count} (REQUIRED)
        max_candidates: Maximum number of nearest APs to return (default: 5)
        
    Returns:
        List[TextContent] containing nearest AP calculation results
    """
    try:
        logger.info(f"Calculating nearest APs for {source_ap_serial} ({source_ap_name})")
        logger.info(f"  Source location: ({source_ap_lat}, {source_ap_lng}), Floor: {source_ap_floor}")
        logger.info(f"  Comparing against {len(all_aps)} APs")
        
        # Build source AP dict
        source_ap = {
            "serial": source_ap_serial,
            "name": source_ap_name,
            "lat": source_ap_lat,
            "lng": source_ap_lng,
            "floor": source_ap_floor,
            "channel": source_ap_channel
        }
        
        # Call the calculation script (does ALL the math!)
        result = calculate_nearest_aps_for_ap(
            source_ap=source_ap,
            all_aps=all_aps,
            max_candidates=max_candidates
        )
        
        logger.info(f"  Result: Found {len(result['nearest_aps'])} nearest APs")
        if result.get('recommended_failover'):
            logger.info(f"  Recommended failover: {result['recommended_failover']['ap_serial']}")
        
        # Return complete calculation result
        response = {
            "success": True,
            "tool": "calculate_nearest_aps",
            **result  # Include all calculation details
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        return [TextContent(type="text", text=json_output)]
        
    except Exception as e:
        logger.error(f"Error calculating nearest APs: {e}")
        import traceback
        traceback.print_exc()
        error_result = {
            "success": False,
            "tool": "calculate_nearest_aps",
            "error": str(e),
            "source_ap_serial": source_ap_serial,
            "source_ap_name": source_ap_name
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
