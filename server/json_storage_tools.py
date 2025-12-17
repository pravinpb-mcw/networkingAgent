#!/usr/bin/env python3
"""
JSON Storage Tools for Agent Data
Provides MCP tools for reading/writing risk scores and nearest AP data
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from mcp.types import TextContent

logger = logging.getLogger("json-storage-tools")

# Define storage paths
STORAGE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "agent_data"
RISK_SCORES_FILE = STORAGE_DIR / "risk_scores.json"
NEAREST_APS_FILE = STORAGE_DIR / "nearest_aps.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON file or return empty dict if not exists"""
    try:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
    return {}


def _save_json(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save data to JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")
        return False


# ============ Risk Score Storage ============

def _normalize_classification(classification: str) -> str:
    """Normalize risk classification to standard values"""
    classification = classification.strip().lower()
    
    if 'likely' in classification or 'failure' in classification or 'critical' in classification:
        return 'Likely Failure'
    elif 'sustained' in classification:
        return 'Sustained Degradation'
    elif 'temporary' in classification or 'degradation' in classification or 'degrading' in classification:
        return 'Temporary Degradation'
    else:
        return 'Stable'


async def update_risk_score(
    ap_serial: str,
    risk_score: float,
    risk_classification: str,
    metrics: Dict[str, Any],
    timestamp: Optional[str] = None
) -> List[TextContent]:
    """
    Update risk score for an AP in the risk_scores.json file
    
    Args:
        ap_serial: AP serial number
        risk_score: Calculated risk score (0-100)
        risk_classification: Classification (Stable/Temporary/Sustained/Likely Failure)
        metrics: Individual metric scores and values
        timestamp: ISO timestamp (auto-generated if not provided)
    
    Returns:
        List[TextContent] with operation result
    """
    try:
        # Normalize the classification to handle LLM variations
        risk_classification = _normalize_classification(risk_classification)
        
        data = _load_json(RISK_SCORES_FILE)
        
        ts = timestamp or datetime.now().isoformat()
        
        # Initialize AP entry if not exists
        if ap_serial not in data:
            data[ap_serial] = {
                "ap_serial": ap_serial,
                "history": []
            }
        
        # Create new score entry
        score_entry = {
            "timestamp": ts,
            "risk_score": risk_score,
            "risk_classification": risk_classification,
            "metrics": metrics
        }
        
        # Add to history (keep last 100 entries)
        data[ap_serial]["history"].append(score_entry)
        data[ap_serial]["history"] = data[ap_serial]["history"][-100:]
        
        # Update current values
        data[ap_serial]["current"] = score_entry
        data[ap_serial]["last_updated"] = ts
        
        # Save
        success = _save_json(RISK_SCORES_FILE, data)
        
        result = {
            "success": success,
            "tool": "update_risk_score",
            "ap_serial": ap_serial,
            "risk_score": risk_score,
            "risk_classification": risk_classification,
            "timestamp": ts
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error updating risk score: {e}")
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2))]


async def get_risk_scores(
    ap_serial: Optional[str] = None,
    include_history: bool = False
) -> List[TextContent]:
    """
    Get risk scores from the risk_scores.json file
    
    Args:
        ap_serial: Specific AP serial (optional, gets all if not provided)
        include_history: Whether to include historical data
    
    Returns:
        List[TextContent] with risk score data
    """
    try:
        data = _load_json(RISK_SCORES_FILE)
        
        if ap_serial:
            if ap_serial in data:
                ap_data = data[ap_serial].copy()
                if not include_history:
                    ap_data.pop("history", None)
                result = {
                    "success": True,
                    "tool": "get_risk_scores",
                    "ap_serial": ap_serial,
                    "data": ap_data
                }
            else:
                result = {
                    "success": False,
                    "message": f"No risk data for AP {ap_serial}"
                }
        else:
            # Get all current risk scores
            summary = {}
            for serial, ap_data in data.items():
                entry = {
                    "current": ap_data.get("current", {}),
                    "last_updated": ap_data.get("last_updated")
                }
                if include_history:
                    entry["history"] = ap_data.get("history", [])
                summary[serial] = entry
            
            result = {
                "success": True,
                "tool": "get_risk_scores",
                "ap_count": len(summary),
                "data": summary
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error getting risk scores: {e}")
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2))]


async def get_at_risk_aps(
    min_risk_score: float = 40.0
) -> List[TextContent]:
    """
    Get all APs with risk score above threshold
    
    Args:
        min_risk_score: Minimum risk score to include (default 40 = Sustained Degradation)
    
    Returns:
        List[TextContent] with at-risk APs
    """
    try:
        data = _load_json(RISK_SCORES_FILE)
        
        at_risk = []
        for serial, ap_data in data.items():
            current = ap_data.get("current", {})
            score = current.get("risk_score", 0)
            if score >= min_risk_score:
                at_risk.append({
                    "ap_serial": serial,
                    "risk_score": score,
                    "risk_classification": current.get("risk_classification", "Unknown"),
                    "last_updated": ap_data.get("last_updated"),
                    "metrics": current.get("metrics", {})
                })
        
        # Sort by risk score descending
        at_risk.sort(key=lambda x: x["risk_score"], reverse=True)
        
        result = {
            "success": True,
            "tool": "get_at_risk_aps",
            "threshold": min_risk_score,
            "count": len(at_risk),
            "at_risk_aps": at_risk
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error getting at-risk APs: {e}")
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2))]


# ============ Nearest AP Storage ============

async def update_nearest_aps(
    ap_serial: str,
    nearest_aps: List[Dict[str, Any]],
    timestamp: Optional[str] = None
) -> List[TextContent]:
    """
    Update nearest AP recommendations for an AP
    
    Args:
        ap_serial: Source AP serial number
        nearest_aps: List of nearby APs with ranking data
        timestamp: ISO timestamp (auto-generated if not provided)
    
    Returns:
        List[TextContent] with operation result
    """
    try:
        data = _load_json(NEAREST_APS_FILE)
        
        ts = timestamp or datetime.now().isoformat()
        
        data[ap_serial] = {
            "ap_serial": ap_serial,
            "last_updated": ts,
            "nearest_aps": nearest_aps
        }
        
        success = _save_json(NEAREST_APS_FILE, data)
        
        result = {
            "success": success,
            "tool": "update_nearest_aps",
            "ap_serial": ap_serial,
            "nearest_count": len(nearest_aps),
            "timestamp": ts
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error updating nearest APs: {e}")
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2))]


async def get_nearest_aps(
    ap_serial: Optional[str] = None
) -> List[TextContent]:
    """
    Get nearest AP recommendations
    
    Args:
        ap_serial: Specific AP serial (optional, gets all if not provided)
    
    Returns:
        List[TextContent] with nearest AP data
    """
    try:
        data = _load_json(NEAREST_APS_FILE)
        
        if ap_serial:
            if ap_serial in data:
                result = {
                    "success": True,
                    "tool": "get_nearest_aps",
                    "ap_serial": ap_serial,
                    "data": data[ap_serial]
                }
            else:
                result = {
                    "success": False,
                    "message": f"No nearest AP data for {ap_serial}"
                }
        else:
            result = {
                "success": True,
                "tool": "get_nearest_aps",
                "ap_count": len(data),
                "data": data
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error getting nearest APs: {e}")
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2))]


async def get_failover_recommendation(
    source_ap_serial: str
) -> List[TextContent]:
    """
    Get the best failover AP recommendation for a source AP
    
    Args:
        source_ap_serial: The AP that needs failover
    
    Returns:
        List[TextContent] with the best failover AP
    """
    try:
        data = _load_json(NEAREST_APS_FILE)
        
        if source_ap_serial not in data:
            result = {
                "success": False,
                "message": f"No failover data available for {source_ap_serial}"
            }
        else:
            ap_data = data[source_ap_serial]
            nearest = ap_data.get("nearest_aps", [])
            
            if not nearest:
                result = {
                    "success": False,
                    "message": f"No nearby APs found for {source_ap_serial}"
                }
            else:
                # Return top 3 recommendations
                top_recommendations = nearest[:3]
                result = {
                    "success": True,
                    "tool": "get_failover_recommendation",
                    "source_ap": source_ap_serial,
                    "last_updated": ap_data.get("last_updated"),
                    "top_recommendations": top_recommendations,
                    "best_failover_ap": top_recommendations[0] if top_recommendations else None
                }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error getting failover recommendation: {e}")
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2))]


# ============ Bulk Operations ============

async def clear_agent_data(
    data_type: str = "all"
) -> List[TextContent]:
    """
    Clear agent data files
    
    Args:
        data_type: "risk_scores", "nearest_aps", or "all"
    
    Returns:
        List[TextContent] with operation result
    """
    try:
        cleared = []
        
        if data_type in ["risk_scores", "all"]:
            _save_json(RISK_SCORES_FILE, {})
            cleared.append("risk_scores")
        
        if data_type in ["nearest_aps", "all"]:
            _save_json(NEAREST_APS_FILE, {})
            cleared.append("nearest_aps")
        
        result = {
            "success": True,
            "tool": "clear_agent_data",
            "cleared": cleared
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error clearing agent data: {e}")
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2))]
