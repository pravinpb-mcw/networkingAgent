"""
Create Network Group Policy Tool
Creates a new group policy for a specific network
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from meraki_client import MerakiAPIClient

logger = logging.getLogger("create-network-group-policy-tool")

async def create_network_group_policy(policy_data: Union[Dict[str, Any], str], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Create a new group policy for your configured network.
    Uses NETWORK_ID from .env file.
    
    Args:
        policy_data: Dictionary or JSON string containing the group policy configuration
        use_mock: Whether to use mock server mode
    """
    try:
        # Handle both dictionary and JSON string inputs
        if isinstance(policy_data, str):
            try:
                # Parse JSON string to dictionary
                policy_data = json.loads(policy_data)
                logger.info("Successfully parsed JSON string input to dictionary")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string: {e}")
        
        # Ensure policy_data is a dict
        if not isinstance(policy_data, dict):
            raise ValueError("policy_data must be a dictionary or valid JSON string")
        
        client = MerakiAPIClient(use_mock=use_mock)
        data = await client.create_network_group_policy(policy_data=policy_data)
        
        result = {
            "tool": "create_network_group_policy",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "policy_data": policy_data,
            "response": data,
            "summary": f"Successfully created group policy for network {client.network_id}"
        }
        
        json_output = json.dumps(result, indent=2, default=str)
        logger.info(f"create_network_group_policy completed successfully for network {client.network_id}")
        
        return [{"type": "text", "text": json_output}]
        
    except Exception as e:
        logger.error(f"create_network_group_policy failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing create_network_group_policy: {str(e)}"}] 