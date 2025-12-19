"""
Generate Failover Suggestions Script
Pure decision logic - NO LLM, NO MCP calls

Reads data from Agent 1 (risk scores) and Agent 2 (nearest APs)
Applies policy rules to generate failover suggestions
Returns deterministic, explainable recommendations
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


def generate_failover_suggestions(
    risk_scores: List[Dict],
    nearest_aps_data: List[Dict],
    policy: Dict
) -> Dict:
    """
    Generate failover suggestions based on risk scores, nearest APs, and policy
    
    Args:
        risk_scores: List of AP risk scores from Agent 1
        nearest_aps_data: List of nearest AP data from Agent 2
        policy: Network policy configuration
    
    Returns:
        Dictionary with failover suggestions and reasoning
    """
    # Extract policy criteria
    failover_criteria = policy.get("failover_criteria", {})
    min_risk_threshold = failover_criteria.get("minimum_risk_score_for_failover", 41.0)
    min_risk_improvement = failover_criteria.get("minimum_risk_improvement_required", 15.0)
    max_distance = failover_criteria.get("maximum_distance_meters", 50.0)
    min_rssi = failover_criteria.get("minimum_rssi_dbm", -75.0)
    prefer_same_floor = failover_criteria.get("prefer_same_floor", True)
    
    suggestions = []
    
    # Process each at-risk AP
    for ap_risk in risk_scores:
        ap_serial = ap_risk.get("ap_serial")
        ap_name = ap_risk.get("ap_name")
        risk_score = ap_risk.get("risk_score", 0)
        risk_category = ap_risk.get("risk_category", "Unknown")
        
        # Check if AP exceeds risk threshold
        if risk_score < min_risk_threshold:
            continue  # Skip APs below threshold
        
        # Find nearest APs for this source AP
        nearest_data = None
        for ap_data in nearest_aps_data:
            if ap_data.get("source_ap_serial") == ap_serial:
                nearest_data = ap_data
                break
        
        if not nearest_data:
            # No failover candidates available
            suggestions.append({
                "source_ap_serial": ap_serial,
                "source_ap_name": ap_name,
                "current_risk_score": risk_score,
                "risk_category": risk_category,
                "action": "manual_investigation",
                "recommendation": "URGENT: No suitable failover candidates found",
                "reasoning": [
                    f"AP {ap_name} has risk score {risk_score:.1f} ({risk_category})",
                    f"Risk exceeds threshold ({min_risk_threshold})",
                    "No nearest AP data available from Agent 2",
                    "Recommend manual site survey and investigation"
                ],
                "suggested_failover_ap": None,
                "urgency": "high" if risk_score >= 71 else "medium"
            })
            continue
        
        # Filter candidates by policy criteria
        candidates = nearest_data.get("candidates", [])
        suitable_candidates = []
        
        for candidate in candidates:
            # Check distance
            if candidate.get("distance_meters", 999) > max_distance:
                continue
            
            # Check RSSI
            if candidate.get("rssi_dbm", -100) < min_rssi:
                continue
            
            # Find risk score for candidate AP
            candidate_serial = candidate.get("ap_serial")
            candidate_risk = None
            
            for risk_data in risk_scores:
                if risk_data.get("ap_serial") == candidate_serial:
                    candidate_risk = risk_data.get("risk_score", 0)
                    break
            
            # Skip if candidate risk is unknown or not better enough
            if candidate_risk is None:
                continue
            
            risk_improvement = risk_score - candidate_risk
            if risk_improvement < min_risk_improvement:
                continue
            
            # Add to suitable candidates
            suitable_candidates.append({
                **candidate,
                "candidate_risk_score": candidate_risk,
                "risk_improvement": risk_improvement
            })
        
        # Sort candidates: same floor first, then by risk improvement, then by composite score
        if prefer_same_floor:
            suitable_candidates.sort(
                key=lambda x: (
                    not x.get("same_floor", False),  # Same floor first
                    -x.get("risk_improvement", 0),  # Higher improvement better
                    -x.get("composite_score", 0)  # Higher score better
                )
            )
        else:
            suitable_candidates.sort(
                key=lambda x: (
                    -x.get("risk_improvement", 0),
                    -x.get("composite_score", 0)
                )
            )
        
        if not suitable_candidates:
            # No suitable candidates meet criteria
            suggestions.append({
                "source_ap_serial": ap_serial,
                "source_ap_name": ap_name,
                "current_risk_score": risk_score,
                "risk_category": risk_category,
                "action": "alert_only",
                "recommendation": "Monitor closely - no suitable failover candidates available",
                "reasoning": [
                    f"AP {ap_name} has risk score {risk_score:.1f} ({risk_category})",
                    f"Risk exceeds threshold ({min_risk_threshold})",
                    f"Found {len(candidates)} nearby APs but none meet failover criteria:",
                    f"  - Must be within {max_distance}m",
                    f"  - Must have RSSI ≥ {min_rssi} dBm",
                    f"  - Must have risk improvement ≥ {min_risk_improvement}",
                    "Recommend monitoring and manual intervention if degradation continues"
                ],
                "suggested_failover_ap": None,
                "nearby_aps_count": len(candidates),
                "urgency": "high" if risk_score >= 71 else "medium"
            })
            continue
        
        # Select best candidate
        best_candidate = suitable_candidates[0]
        
        # Determine urgency
        if risk_score >= 71:
            urgency = "critical"
            action = "urgent_failover"
        elif risk_score >= 41:
            urgency = "high"
            action = "failover_recommendation"
        else:
            urgency = "medium"
            action = "monitor"
        
        # Build reasoning
        reasoning = [
            f"SOURCE AP: {ap_name} ({ap_serial})",
            f"  Current Risk: {risk_score:.1f} ({risk_category})",
            f"  Status: Exceeds failover threshold ({min_risk_threshold})",
            "",
            f"RECOMMENDED FAILOVER AP: {best_candidate.get('ap_name', 'Unknown')} ({best_candidate.get('ap_serial', 'N/A')})",
            f"  Risk Score: {best_candidate.get('candidate_risk_score', 0):.1f}",
            f"  Risk Improvement: {best_candidate.get('risk_improvement', 0):.1f} points",
            f"  Distance: {best_candidate.get('distance_meters', 0):.1f} meters",
            f"  Estimated RSSI: {best_candidate.get('rssi_dbm', 0):.1f} dBm",
            f"  Same Floor: {'Yes' if best_candidate.get('same_floor') else 'No'}",
            f"  Channel Overlap: {'Yes' if best_candidate.get('channel_overlap') else 'No'}",
            f"  Client Load: {best_candidate.get('client_load', 0)} clients",
            "",
            f"CRITERIA VALIDATION:",
            f"  ✓ Within {max_distance}m ({best_candidate.get('distance_meters', 0):.1f}m)",
            f"  ✓ RSSI ≥ {min_rssi} dBm ({best_candidate.get('rssi_dbm', 0):.1f} dBm)",
            f"  ✓ Risk improvement ≥ {min_risk_improvement} ({best_candidate.get('risk_improvement', 0):.1f})",
            "",
            f"SUGGESTED ACTION:",
            f"  1. Verify {best_candidate.get('ap_name')} is operational",
            f"  2. Gradually migrate clients from {ap_name} to {best_candidate.get('ap_name')}",
            f"  3. Monitor performance during migration",
            f"  4. Investigate root cause of degradation on {ap_name}"
        ]
        
        suggestions.append({
            "source_ap_serial": ap_serial,
            "source_ap_name": ap_name,
            "current_risk_score": risk_score,
            "risk_category": risk_category,
            "action": action,
            "urgency": urgency,
            "recommendation": f"Failover to {best_candidate.get('ap_name')} - Risk improvement: {best_candidate.get('risk_improvement', 0):.1f} points",
            "suggested_failover_ap": {
                "ap_serial": best_candidate.get("ap_serial"),
                "ap_name": best_candidate.get("ap_name"),
                "risk_score": best_candidate.get("candidate_risk_score"),
                "distance_meters": best_candidate.get("distance_meters"),
                "rssi_dbm": best_candidate.get("rssi_dbm"),
                "same_floor": best_candidate.get("same_floor"),
                "channel_overlap": best_candidate.get("channel_overlap"),
                "client_load": best_candidate.get("client_load"),
                "risk_improvement": best_candidate.get("risk_improvement"),
                "composite_score": best_candidate.get("composite_score")
            },
            "reasoning": reasoning,
            "alternative_candidates_count": len(suitable_candidates) - 1
        })
    
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "policy_threshold": min_risk_threshold,
        "total_aps_analyzed": len(risk_scores),
        "aps_exceeding_threshold": len([ap for ap in risk_scores if ap.get("risk_score", 0) >= min_risk_threshold]),
        "suggestions_generated": len(suggestions),
        "suggestions": suggestions,
        "policy_criteria_applied": {
            "minimum_risk_score_for_failover": min_risk_threshold,
            "minimum_risk_improvement_required": min_risk_improvement,
            "maximum_distance_meters": max_distance,
            "minimum_rssi_dbm": min_rssi,
            "prefer_same_floor": prefer_same_floor
        }
    }


if __name__ == "__main__":
    # Test with sample data
    from read_risk_scores import read_risk_scores
    from read_nearest_aps import read_nearest_aps
    from read_network_policy import read_network_policy
    
    print("🔍 Loading data...")
    
    # Load risk scores
    risk_result = read_risk_scores()
    if not risk_result["success"]:
        print(f"❌ Failed to load risk scores: {risk_result['error']}")
        exit(1)
    
    # Load nearest APs
    nearest_result = read_nearest_aps()
    if not nearest_result["success"]:
        print(f"❌ Failed to load nearest APs: {nearest_result['error']}")
        exit(1)
    
    # Load policy
    policy_result = read_network_policy()
    if not policy_result["success"]:
        print(f"❌ Failed to load policy: {policy_result['error']}")
        exit(1)
    
    print("✅ Data loaded successfully\n")
    
    # Generate suggestions
    result = generate_failover_suggestions(
        risk_scores=risk_result["risk_scores"],
        nearest_aps_data=nearest_result["nearest_aps"],
        policy=policy_result["policy"]
    )
    
    print(f"📊 Analysis Results:")
    print(f"  Total APs: {result['total_aps_analyzed']}")
    print(f"  APs exceeding threshold: {result['aps_exceeding_threshold']}")
    print(f"  Suggestions generated: {result['suggestions_generated']}")
    print(f"  Policy threshold: {result['policy_threshold']}")
    
    print(f"\n{'='*80}")
    
    for i, suggestion in enumerate(result["suggestions"], 1):
        print(f"\n🚨 SUGGESTION {i} - Urgency: {suggestion['urgency'].upper()}")
        print(f"{'='*80}")
        print("\n".join(suggestion["reasoning"]))
        
        if suggestion["alternative_candidates_count"] > 0:
            print(f"\n📋 Alternative candidates available: {suggestion['alternative_candidates_count']}")
        
        print(f"{'='*80}")
