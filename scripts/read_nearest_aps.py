"""
Read Nearest APs Script
Pure data reading - NO LLM, NO calculations

Reads nearest AP data produced by Agent 2 from agent_data/nearest_aps.json
Returns structured data for Agent 3 to process
"""

import json
from typing import Dict, List, Optional
from pathlib import Path


def read_nearest_aps(file_path: Optional[str] = None) -> Dict:
    """
    Read nearest APs data from JSON file produced by Agent 2
    
    Args:
        file_path: Path to nearest_aps.json (optional, defaults to agent_data/nearest_aps.json)
    
    Returns:
        Dictionary containing nearest AP data for all source APs
    """
    # Default path
    if file_path is None:
        script_dir = Path(__file__).parent.parent
        file_path = script_dir / "agent_data" / "nearest_aps.json"
    
    file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        return {
            "success": False,
            "error": f"Nearest APs file not found: {file_path}",
            "nearest_aps": []
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        if not isinstance(data, dict):
            return {
                "success": False,
                "error": "Invalid JSON structure - expected dictionary",
                "nearest_aps": []
            }
        
        # Handle two possible formats:
        # Format 1: {"nearest_aps": [...]} - list format
        # Format 2: {ap_serial: {nearest_aps: [...], ...}, ...} - nested dict format from Agent 2
        
        nearest_aps = []
        
        if "nearest_aps" in data:
            # Format 1: List format
            nearest_aps = data.get("nearest_aps", [])
            timestamp = data.get("timestamp", "unknown")
        else:
            # Format 2: Nested dict format (Agent 2 output)
            # Extract nearest_aps for each source AP
            for ap_serial, ap_data in data.items():
                if isinstance(ap_data, dict) and "nearest_aps" in ap_data:
                    nearest_aps.append({
                        "source_ap_serial": ap_serial,
                        "source_ap_name": ap_data.get("ap_name", "Unknown"),
                        "candidates": ap_data.get("nearest_aps", []),
                        "timestamp": ap_data.get("last_updated", "unknown")
                    })
            
            # Use latest timestamp from any AP
            timestamps = [
                ap_data.get("last_updated", "unknown")
                for ap_data in data.values()
                if isinstance(ap_data, dict)
            ]
            timestamp = max(timestamps) if timestamps else "unknown"
        
        return {
            "success": True,
            "file_path": str(file_path),
            "timestamp": timestamp,
            "total_source_aps": len(nearest_aps),
            "nearest_aps": nearest_aps
        }
    
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON parsing error: {str(e)}",
            "nearest_aps": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}",
            "nearest_aps": []
        }


def get_nearest_for_ap(nearest_aps_data: List[Dict], ap_serial: str) -> Optional[Dict]:
    """
    Get nearest AP candidates for a specific AP
    
    Args:
        nearest_aps_data: List of nearest AP data from Agent 2
        ap_serial: Serial number of the source AP
    
    Returns:
        Dictionary with nearest AP candidates, or None if not found
    """
    for ap_data in nearest_aps_data:
        if ap_data.get("source_ap_serial") == ap_serial:
            return ap_data
    
    return None


def filter_candidates_by_criteria(
    candidates: List[Dict],
    min_rssi: float = -75.0,
    max_distance: float = 50.0,
    prefer_same_floor: bool = True
) -> List[Dict]:
    """
    Filter failover candidates by policy criteria
    
    Args:
        candidates: List of candidate APs
        min_rssi: Minimum acceptable RSSI (dBm)
        max_distance: Maximum distance in meters
        prefer_same_floor: If True, prioritize same floor candidates
    
    Returns:
        Filtered and sorted list of candidates
    """
    if not candidates:
        return []
    
    # Apply filters
    filtered = [
        ap for ap in candidates
        if ap.get("rssi_dbm", -100) >= min_rssi and
           ap.get("distance_meters", 999) <= max_distance
    ]
    
    # Sort: same floor first, then by composite score
    if prefer_same_floor:
        filtered.sort(
            key=lambda x: (
                not x.get("same_floor", False),  # False first (same floor)
                -x.get("composite_score", 0)  # Then by score descending
            )
        )
    else:
        filtered.sort(key=lambda x: -x.get("composite_score", 0))
    
    return filtered


if __name__ == "__main__":
    # Test the function
    result = read_nearest_aps()
    
    if result["success"]:
        print(f"✅ Successfully read nearest APs for {result['total_source_aps']} source APs")
        print(f"📁 File: {result['file_path']}")
        print(f"🕒 Timestamp: {result['timestamp']}")
        
        # Show sample data
        for ap_data in result["nearest_aps"][:3]:  # First 3
            print(f"\n📡 Source AP: {ap_data.get('source_ap_name', 'Unknown')} ({ap_data.get('source_ap_serial', 'N/A')})")
            
            candidates = ap_data.get("candidates", [])
            filtered = filter_candidates_by_criteria(candidates)
            
            print(f"   Found {len(candidates)} candidates, {len(filtered)} meet criteria")
            
            if filtered:
                top = filtered[0]
                print(f"   🎯 Top candidate: {top.get('ap_name', 'Unknown')}")
                print(f"      Distance: {top.get('distance_meters', 0):.1f}m")
                print(f"      RSSI: {top.get('rssi_dbm', 0):.1f} dBm")
                print(f"      Same floor: {top.get('same_floor', False)}")
    else:
        print(f"❌ Error: {result['error']}")
