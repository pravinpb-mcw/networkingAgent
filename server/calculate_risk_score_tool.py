#!/usr/bin/env python3
"""
MCP Tool: Calculate Risk Score
Wrapper around the standalone risk calculation script
"""

import json
import logging
import sys
from pathlib import Path
from typing import List
from mcp.types import TextContent

# Add scripts directory to path
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from calculate_risk_score import calculate_ap_risk_score

logger = logging.getLogger("calculate-risk-score-tool")


async def calculate_risk_score(
    ap_serial: str,
    ap_name: str,
    latency_ms: float = None,
    jitter_ms: float = None,
    retrans_per_min: float = None,
    snr_db: float = None,
    client_count: int = None
) -> List[TextContent]:
    """
    Calculate risk score for an AP using the standalone calculation script.
    
    This tool does ALL the math - the LLM just passes parameters!
    
    Args:
        ap_serial: AP serial number (REQUIRED)
        ap_name: AP name (REQUIRED)
        latency_ms: Average latency in milliseconds (optional)
        jitter_ms: Jitter in milliseconds (optional)
        retrans_per_min: Retransmissions per minute (optional)
        snr_db: Signal-to-noise ratio in dB (optional)
        client_count: Number of connected clients (optional)
        
    Returns:
        List[TextContent] containing risk score calculation results
    """
    try:
        logger.info(f"Calculating risk score for AP {ap_serial} ({ap_name})")
        logger.info(f"  Parameters: latency={latency_ms}, jitter={jitter_ms}, retrans={retrans_per_min}, snr={snr_db}, clients={client_count}")
        
        # Call the calculation script (does ALL the math!)
        result = calculate_ap_risk_score(
            ap_serial=ap_serial,
            ap_name=ap_name,
            latency_ms=latency_ms,
            jitter_ms=jitter_ms,
            retrans_per_min=retrans_per_min,
            snr_db=snr_db,
            client_count=client_count
        )
        
        logger.info(f"  Result: risk_score={result['risk_score']}, classification={result['risk_classification']}")
        
        # Return complete calculation result
        response = {
            "success": True,
            "tool": "calculate_risk_score",
            "ap_serial": ap_serial,
            "ap_name": ap_name,
            **result  # Include all calculation details
        }
        
        json_output = json.dumps(response, indent=2, default=str)
        return [TextContent(type="text", text=json_output)]
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {e}")
        import traceback
        traceback.print_exc()
        error_result = {
            "success": False,
            "tool": "calculate_risk_score",
            "error": str(e),
            "ap_serial": ap_serial,
            "ap_name": ap_name
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
