#!/usr/bin/env python3
"""
Delete Network Group Policy Tool
Deletes an existing network group policy
"""

import asyncio
import logging
from typing import List, Dict, Any
from meraki_client import MerakiAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def delete_network_group_policy(policy_id: str, use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Delete an existing network group policy.
    
    Args:
        policy_id: ID of the existing policy to delete
        use_mock: Whether to use mock server mode
        
    Returns:
        List containing the result of the deletion operation
    """
    try:
        client = MerakiAPIClient(use_mock=use_mock)
        
        logger.info(f"Deleting network group policy: {policy_id}")
        
        # Delete the group policy
        try:
            result = await client.delete_network_group_policy(policy_id)
            logger.info(f"Successfully deleted group policy: {policy_id}")
            
            return [
                {
                    "type": "text",
                    "text": f"✅ Successfully deleted group policy: {policy_id}"
                }
            ]
            
        except Exception as e:
            logger.error(f"Failed to delete group policy: {e}")
            return [
                {
                    "type": "text",
                    "text": f"❌ Failed to delete group policy: {str(e)}"
                }
            ]
            
    except Exception as e:
        logger.error(f"Error in delete_network_group_policy: {e}")
        return [
            {
                "type": "text",
                "text": f"❌ Error deleting group policy: {str(e)}"
            }
        ]

if __name__ == "__main__":
    # Test the function
    async def test():
        result = await delete_network_group_policy("test_policy", use_mock=True)
        print(result)
    
    asyncio.run(test())
