#!/usr/bin/env python3
"""
Standalone Nearest AP Calculation Script
=========================================

This script calculates the nearest APs for a given source AP based on distance, signal strength, 
and other factors. NO LLM, NO MCP calls - just pure distance and ranking calculations.

Usage:
    As a module:
        from calculate_nearest_aps import calculate_nearest_aps_for_ap
        result = calculate_nearest_aps_for_ap(source_ap, all_aps)
    
    As a CLI tool:
        python calculate_nearest_aps.py --source-serial Q2XX-1234 --aps '[{...}]'
"""

import json
import sys
import argparse
import math
from typing import Dict, Any, List, Optional
from datetime import datetime


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in meters.
    """
    # Earth radius in meters
    R = 6371000
    
    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    # Haversine formula
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def estimate_rssi(distance_meters: float) -> int:
    """
    Estimate RSSI based on distance.
    Simple path loss model: RSSI = -40 - 20*log10(distance)
    """
    if distance_meters < 1:
        return -40
    rssi = -40 - (20 * math.log10(distance_meters))
    return int(rssi)


def calculate_composite_score(
    distance_meters: float,
    rssi_dbm: int,
    client_load: int,
    channel_overlap: bool,
    same_floor: bool
) -> float:
    """
    Calculate composite score for AP ranking (0-100, higher = better candidate).
    
    Factors:
    - Distance: closer is better
    - RSSI: stronger signal is better  
    - Client load: fewer clients is better
    - Channel overlap: no overlap is better
    - Same floor: same floor is better
    """
    score = 100.0
    
    # Distance penalty (0-30 points)
    # < 10m: 0 penalty, 10-20m: -10, 20-30m: -20, >30m: -30
    if distance_meters < 10:
        distance_penalty = 0
    elif distance_meters < 20:
        distance_penalty = 10
    elif distance_meters < 30:
        distance_penalty = 20
    else:
        distance_penalty = 30
    score -= distance_penalty
    
    # RSSI penalty (0-25 points)
    # > -60dBm: 0, -60 to -70: -10, -70 to -80: -20, < -80: -25
    if rssi_dbm > -60:
        rssi_penalty = 0
    elif rssi_dbm > -70:
        rssi_penalty = 10
    elif rssi_dbm > -80:
        rssi_penalty = 20
    else:
        rssi_penalty = 25
    score -= rssi_penalty
    
    # Client load penalty (0-15 points)
    # < 10: 0, 10-30: -5, 30-50: -10, > 50: -15
    if client_load < 10:
        load_penalty = 0
    elif client_load < 30:
        load_penalty = 5
    elif client_load < 50:
        load_penalty = 10
    else:
        load_penalty = 15
    score -= load_penalty
    
    # Channel overlap penalty (0-20 points)
    if channel_overlap:
        score -= 20
    
    # Different floor penalty (0-10 points)
    if not same_floor:
        score -= 10
    
    return max(0, score)


def calculate_nearest_aps_for_ap(
    source_ap: Dict[str, Any],
    all_aps: List[Dict[str, Any]],
    max_candidates: int = 5
) -> Dict[str, Any]:
    """
    Calculate nearest APs for a source AP.
    
    Args:
        source_ap: Source AP with {serial, name, lat, lng, floor, channel, client_count}
        all_aps: List of all APs with same structure
        max_candidates: Maximum number of nearest APs to return
        
    Returns:
        Dictionary with ranked nearest APs
    """
    source_serial = source_ap.get("serial")
    source_name = source_ap.get("name", source_serial)
    source_lat = source_ap.get("lat", 0)
    source_lng = source_ap.get("lng", 0)
    source_floor = source_ap.get("floor", 1)
    source_channel = source_ap.get("channel", 0)
    
    candidates = []
    
    # Calculate score for each other AP
    for ap in all_aps:
        ap_serial = ap.get("serial")
        
        # Skip self
        if ap_serial == source_serial:
            continue
        
        ap_lat = ap.get("lat", 0)
        ap_lng = ap.get("lng", 0)
        ap_floor = ap.get("floor", 1)
        ap_channel = ap.get("channel", 0)
        ap_client_count = ap.get("client_count", 0)
        ap_name = ap.get("name", ap_serial)
        
        # Calculate distance
        distance = calculate_distance(source_lat, source_lng, ap_lat, ap_lng)
        
        # Estimate RSSI
        rssi = estimate_rssi(distance)
        
        # Check if same floor
        same_floor = (ap_floor == source_floor)
        
        # Check channel overlap (same or adjacent channels)
        channel_overlap = False
        if source_channel and ap_channel:
            channel_overlap = abs(source_channel - ap_channel) <= 1
        
        # Calculate composite score
        composite_score = calculate_composite_score(
            distance_meters=distance,
            rssi_dbm=rssi,
            client_load=ap_client_count,
            channel_overlap=channel_overlap,
            same_floor=same_floor
        )
        
        candidates.append({
            "ap_serial": ap_serial,
            "ap_name": ap_name,
            "distance_meters": round(distance, 1),
            "rssi_dbm": rssi,
            "client_load": ap_client_count,
            "channel_overlap": channel_overlap,
            "same_floor": same_floor,
            "composite_score": round(composite_score, 2)
        })
    
    # Sort by composite score (descending - higher is better)
    candidates.sort(key=lambda x: x["composite_score"], reverse=True)
    
    # Take top candidates and add rank
    top_candidates = candidates[:max_candidates]
    for idx, candidate in enumerate(top_candidates, start=1):
        candidate["rank"] = idx
    
    return {
        "success": True,
        "source_ap_serial": source_serial,
        "source_ap_name": source_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_candidates": len(candidates),
        "nearest_aps": top_candidates,
        "recommended_failover": top_candidates[0] if top_candidates else None
    }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Calculate nearest APs for failover planning")
    parser.add_argument("--source-serial", required=True, help="Source AP serial number")
    parser.add_argument("--source-name", help="Source AP name")
    parser.add_argument("--source-lat", type=float, required=True, help="Source AP latitude")
    parser.add_argument("--source-lng", type=float, required=True, help="Source AP longitude")
    parser.add_argument("--source-floor", type=int, default=1, help="Source AP floor")
    parser.add_argument("--source-channel", type=int, default=0, help="Source AP channel")
    parser.add_argument("--all-aps", required=True, help="JSON array of all APs")
    parser.add_argument("--max-candidates", type=int, default=5, help="Max candidates to return")
    parser.add_argument("--pretty", action="store_true", help="Pretty print output")
    
    args = parser.parse_args()
    
    # Parse all APs
    all_aps = json.loads(args.all_aps)
    
    # Build source AP
    source_ap = {
        "serial": args.source_serial,
        "name": args.source_name or args.source_serial,
        "lat": args.source_lat,
        "lng": args.source_lng,
        "floor": args.source_floor,
        "channel": args.source_channel
    }
    
    # Calculate
    result = calculate_nearest_aps_for_ap(source_ap, all_aps, args.max_candidates)
    
    # Output
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
