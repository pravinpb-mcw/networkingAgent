"""
Get Service Impact Predictions Tool
Returns comprehensive service impact predictions including trend analysis,
failover candidates, and execution plans from the mock data.
"""

import json
import logging
from typing import Dict, Any, Optional
from meraki_client import MerakiAPIClient

logger = logging.getLogger(__name__)


async def get_service_impact_predictions(
    network_id: str,
    use_mock: bool = True
) -> Dict[str, Any]:
    """
    Get comprehensive service impact predictions for a network.
    
    This data includes:
    - Risk classification and recovery likelihood
    - Trend analysis (channel utilization, SNR, retransmissions, etc.)
    - Current vs threshold comparisons
    - Ranked failover candidates with scores
    - Execution plan for client migration
    - Application impact predictions
    
    Args:
        network_id: The Meraki network ID
        use_mock: Whether to use mock server (default True)
        
    Returns:
        Dict containing service impact predictions and analysis
    """
    try:
        client = MerakiAPIClient()
        
        # Build the endpoint URL
        endpoint = f"/networks/{network_id}/serviceImpactPredictions"
        
        # Make the API call
        result = await client._make_request(
            endpoint=endpoint,
            tool_name="get_service_impact_predictions"
        )
        
        if result:
            return {
                "success": True,
                "network_id": network_id,
                "predictions": result,
                "tool": "get_service_impact_predictions"
            }
        else:
            # Try to read directly from comprehensive_api_data.json
            try:
                import os
                mock_data_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "mock_data",
                    "comprehensive_api_data.json"
                )
                
                with open(mock_data_path, 'r') as f:
                    data = json.load(f)
                
                predictions = data.get("service_impact_predictions", {}).get(network_id, {})
                
                if predictions:
                    return {
                        "success": True,
                        "network_id": network_id,
                        "predictions": predictions,
                        "tool": "get_service_impact_predictions",
                        "source": "local_file"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"No service impact predictions found for network {network_id}",
                        "tool": "get_service_impact_predictions"
                    }
                    
            except Exception as file_error:
                logger.error(f"Error reading from file: {file_error}")
                return {
                    "success": False,
                    "error": str(file_error),
                    "tool": "get_service_impact_predictions"
                }
                
    except Exception as e:
        logger.error(f"Error getting service impact predictions: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool": "get_service_impact_predictions"
        }
