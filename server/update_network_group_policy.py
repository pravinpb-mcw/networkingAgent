"""
Update Network Group Policy Tool
Updates existing group policies for a specific network
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from meraki_client import MerakiAPIClient
from natural_language_converter import convert_natural_language_to_policy_data
import os

logger = logging.getLogger("update-network-group-policy-tool")

async def update_network_group_policy(policy_id: str, policy_data: Union[Dict[str, Any], str] = None, use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Update an existing network group policy for your configured network.
    Uses NETWORK_ID from .env file.
    
    Args:
        policy_id: ID of the existing policy to update
        policy_data: Dictionary or JSON string containing the policy updates
        use_mock: Whether to use mock server mode
    """
    try:
        # Validate that policy_id is provided
        if policy_id is None or policy_id.strip() == "":
            raise ValueError("policy_id is required")
        
        # Clean up potentially duplicated policy_id
        policy_id_clean = policy_id.strip()
        
        # Handle common duplication patterns for policy IDs
        if policy_id_clean.endswith(policy_id_clean[:len(policy_id_clean)//2]):
            # Policy ID is duplicated, take the first half
            policy_id_clean = policy_id_clean[:len(policy_id_clean)//2]
            logger.info(f"Detected duplicated policy ID, cleaned to: '{policy_id_clean}'")
        
        # Handle specific duplication patterns
        if policy_id_clean == "policy_2policy_2":
            policy_id_clean = "policy_2"
            logger.info("Detected 'policy_2policy_2', cleaned to 'policy_2'")
        elif policy_id_clean == "policy_1policy_1":
            policy_id_clean = "policy_1"
            logger.info("Detected 'policy_1policy_1', cleaned to 'policy_1'")
        
        # Use the cleaned policy ID
        policy_id = policy_id_clean
        
        # Handle natural language input by converting it to structured data
        if isinstance(policy_data, str):
            # Convert natural language to structured policy data
            policy_data = convert_natural_language_to_policy_data(policy_data)
            logger.info("Successfully converted natural language input to policy data")
        
        # Ensure policy_data is a dict
        if not isinstance(policy_data, dict):
            raise ValueError("policy_data must be a dictionary or valid JSON string")

        client = MerakiAPIClient(use_mock=use_mock)
        
        # Update the existing group policy
        logger.info(f"Updating existing group policy {policy_id}")
        
        try:
            # For mock server, we'll actually call the mock server to persist changes
            if use_mock:
                # In mock mode, call the mock server to actually update the JSON files
                update_result = await client.update_network_group_policy(policy_id, network_id=None, policy_data=policy_data)
            else:
                # For real Meraki API, call the update endpoint
                update_result = await client.update_network_group_policy(policy_id, network_id=None, policy_data=policy_data)
            
            result = {
                "tool": "update_network_group_policy",
                "timestamp": datetime.now().isoformat(),
                "network_id": client.network_id,
                "policy_id": policy_id,
                "status": "success",
                "message": f"Group policy {policy_id} updated successfully",
                "updated_policy": update_result
            }

            logger.info(f"Successfully updated group policy {policy_id}")
            
            return [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]

        except Exception as e:
            logger.error(f"Failed to update group policy {policy_id}: {e}")
            error_result = {
                "tool": "update_network_group_policy",
                "timestamp": datetime.now().isoformat(),
                "network_id": client.network_id,
                "policy_id": policy_id,
                "status": "error",
                "message": f"Failed to update group policy {policy_id}: {str(e)}"
            }
            return [{"type": "text", "text": json.dumps(error_result, indent=2, default=str)}]

    except Exception as e:
        logger.error(f"update_network_group_policy failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing update_network_group_policy: {str(e)}"}]
