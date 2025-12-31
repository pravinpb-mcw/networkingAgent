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
    source_ap_floor: int = 1,
    source_ap_channel: int = 1,
    all_aps: List[Dict[str, Any]] = None,
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
        source_ap_floor: Source AP floor number (default: 1)
        source_ap_channel: Source AP WiFi channel (default: 1)
        all_aps: List of all APs with {serial, name, lat, lng, floor, channel, client_count}
        max_candidates: Maximum number of nearest APs to return (default: 5)
        
    Returns:
        List[TextContent] containing nearest AP calculation results
    """
    try:
        # Convert lat/lng - handle empty strings, None, or 'null'
        if source_ap_lat is None or source_ap_lat == '' or source_ap_lat == 'null':
            raise ValueError("source_ap_lat is required and cannot be empty")
        source_ap_lat = float(source_ap_lat) if not isinstance(source_ap_lat, (int, float)) else float(source_ap_lat)
        
        if source_ap_lng is None or source_ap_lng == '' or source_ap_lng == 'null':
            raise ValueError("source_ap_lng is required and cannot be empty")
        source_ap_lng = float(source_ap_lng) if not isinstance(source_ap_lng, (int, float)) else float(source_ap_lng)
        
        # Convert empty strings or None to defaults for integer fields
        if source_ap_floor is None or source_ap_floor == '' or source_ap_floor == 'null':
            source_ap_floor = 1
        else:
            source_ap_floor = int(source_ap_floor) if not isinstance(source_ap_floor, int) else source_ap_floor
            
        if source_ap_channel is None or source_ap_channel == '' or source_ap_channel == 'null':
            source_ap_channel = 1
        else:
            source_ap_channel = int(source_ap_channel) if not isinstance(source_ap_channel, int) else source_ap_channel
            
        if max_candidates is None or max_candidates == '' or max_candidates == 'null':
            max_candidates = 5
        else:
            max_candidates = int(max_candidates) if not isinstance(max_candidates, int) else max_candidates
        
        # Handle None or empty all_aps
        if all_aps is None:
            all_aps = []
        
        # Clean up all_aps - convert string numbers to proper types
        cleaned_aps = []
        for ap in all_aps:
            cleaned_ap = dict(ap)
            
            # Handle lat/lng - convert to float, skip if invalid
            for coord_field in ['lat', 'lng']:
                if coord_field in cleaned_ap:
                    val = cleaned_ap[coord_field]
                    if val is None or val == '' or val == 'null':
                        logger.warning(f"AP {cleaned_ap.get('serial', 'unknown')} has empty {coord_field}, skipping")
                        cleaned_ap = None
                        break
                    elif not isinstance(val, (int, float)):
                        try:
                            cleaned_ap[coord_field] = float(val)
                        except (ValueError, TypeError):
                            logger.warning(f"AP {cleaned_ap.get('serial', 'unknown')} has invalid {coord_field}: {val}, skipping")
                            cleaned_ap = None
                            break
                            
            if cleaned_ap is None:
                continue
                
            # Handle integer fields - convert to int with defaults
            for field in ['floor', 'channel', 'client_count']:
                if field in cleaned_ap:
                    val = cleaned_ap[field]
                    if val is None or val == '' or val == 'null':
                        cleaned_ap[field] = 1 if field in ['floor', 'channel'] else 0
                    elif not isinstance(val, int):
                        try:
                            cleaned_ap[field] = int(val)
                        except (ValueError, TypeError):
                            cleaned_ap[field] = 1 if field in ['floor', 'channel'] else 0
            cleaned_aps.append(cleaned_ap)
        
        logger.info(f"Calculating nearest APs for {source_ap_serial} ({source_ap_name})")
        logger.info(f"  Source location: ({source_ap_lat}, {source_ap_lng}), Floor: {source_ap_floor}")
        logger.info(f"  Comparing against {len(cleaned_aps)} APs")
        
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
            all_aps=cleaned_aps,
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
