"""
Read Risk Scores Script
Pure data reading - NO LLM, NO calculations

Reads risk scores produced by Agent 1 from agent_data/risk_scores.json
Returns structured data for Agent 3 to process
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path


def read_risk_scores(file_path: Optional[str] = None) -> Dict:
    """
    Read risk scores from JSON file produced by Agent 1
    
    Args:
        file_path: Path to risk_scores.json (optional, defaults to agent_data/risk_scores.json)
    
    Returns:
        Dictionary containing risk scores for all APs
    """
    # Default path
    if file_path is None:
        script_dir = Path(__file__).parent.parent
        file_path = script_dir / "agent_data" / "risk_scores.json"
    
    file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        return {
            "success": False,
            "error": f"Risk scores file not found: {file_path}",
            "risk_scores": []
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        if not isinstance(data, dict):
            return {
                "success": False,
                "error": "Invalid JSON structure - expected dictionary",
                "risk_scores": []
            }
        
        # Handle two possible formats:
        # Format 1: {"risk_scores": [...]} - list format
        # Format 2: {ap_serial: {current: {...}}, ...} - nested dict format from Agent 1
        
        risk_scores = []
        
        if "risk_scores" in data:
            # Format 1: List format
            risk_scores = data.get("risk_scores", [])
            timestamp = data.get("timestamp", "unknown")
        else:
            # Format 2: Nested dict format (Agent 1 output)
            # Extract current risk score for each AP
            for ap_serial, ap_data in data.items():
                if isinstance(ap_data, dict) and "current" in ap_data:
                    current = ap_data["current"]
                    risk_scores.append({
                        "ap_serial": ap_serial,
                        "ap_name": ap_data.get("ap_name", "Unknown"),
                        "risk_score": current.get("risk_score", 0),
                        "risk_category": current.get("risk_classification", "Unknown"),
                        "timestamp": current.get("timestamp", "unknown"),
                        "metrics": current.get("metrics", {})
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
            "total_aps": len(risk_scores),
            "risk_scores": risk_scores
        }
    
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON parsing error: {str(e)}",
            "risk_scores": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}",
            "risk_scores": []
        }


def filter_by_threshold(risk_scores: List[Dict], min_threshold: float = 41.0) -> List[Dict]:
    """
    Filter APs by minimum risk threshold
    
    Args:
        risk_scores: List of AP risk score dictionaries
        min_threshold: Minimum risk score to include (default 41 = Sustained Degradation)
    
    Returns:
        List of APs with risk score >= threshold
    """
    if not risk_scores:
        return []
    
    filtered = [
        ap for ap in risk_scores 
        if ap.get("risk_score", 0) >= min_threshold
    ]
    
    return sorted(filtered, key=lambda x: x.get("risk_score", 0), reverse=True)


def categorize_by_severity(risk_scores: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Categorize APs by risk severity
    
    Returns:
        Dictionary with categories: stable, temporary, sustained, critical
    """
    categories = {
        "stable": [],
        "temporary_degradation": [],
        "sustained_degradation": [],
        "likely_failure": []
    }
    
    for ap in risk_scores:
        risk_score = ap.get("risk_score", 0)
        
        if risk_score <= 20:
            categories["stable"].append(ap)
        elif risk_score <= 40:
            categories["temporary_degradation"].append(ap)
        elif risk_score <= 70:
            categories["sustained_degradation"].append(ap)
        else:
            categories["likely_failure"].append(ap)
    
    return categories


if __name__ == "__main__":
    # Test the function
    result = read_risk_scores()
    
    if result["success"]:
        print(f"✅ Successfully read {result['total_aps']} AP risk scores")
        print(f"📁 File: {result['file_path']}")
        print(f"🕒 Timestamp: {result['timestamp']}")
        
        # Filter high-risk APs
        high_risk = filter_by_threshold(result["risk_scores"], min_threshold=41)
        print(f"\n⚠️  High-risk APs (≥41): {len(high_risk)}")
        
        for ap in high_risk:
            print(f"  - {ap.get('ap_name', 'Unknown')} ({ap.get('ap_serial', 'N/A')}): "
                  f"Risk {ap.get('risk_score', 0):.1f} - {ap.get('risk_category', 'Unknown')}")
        
        # Categorize
        categories = categorize_by_severity(result["risk_scores"])
        print("\n📊 Risk Distribution:")
        print(f"  🟢 Stable: {len(categories['stable'])}")
        print(f"  🟡 Temporary: {len(categories['temporary_degradation'])}")
        print(f"  🟠 Sustained: {len(categories['sustained_degradation'])}")
        print(f"  🔴 Critical: {len(categories['likely_failure'])}")
    else:
        print(f"❌ Error: {result['error']}")
