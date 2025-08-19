"""
Update Network Wireless Settings Tool
Updates wireless settings for a specific network with interactive group policy synchronization
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-network-wireless-settings-tool")

async def update_network_wireless_settings(settings_data: Union[Dict[str, Any], str], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Update network wireless settings for your configured network with interactive group policy synchronization.
    Uses NETWORK_ID from .env file.
    
    This function implements an interactive call chain:
    1) First collects wireless settings input (but doesn't apply yet)
    2) Then asks user for group policy settings input
    3) Applies group policy first
    4) Finally applies wireless settings
    """
    try:
        # Handle natural language input by converting it to structured data
        if isinstance(settings_data, str):
            # Convert natural language to structured wireless settings
            from natural_language_converter import convert_natural_language_to_wireless_settings
            settings_data = convert_natural_language_to_wireless_settings(settings_data)
        
        # Validate settings data
        if not isinstance(settings_data, dict):
            raise ValueError("settings_data must be a dictionary")
        
        # Store wireless settings for later use
        wireless_settings = settings_data.copy()
        
        # CRITICAL: Stop execution and wait for user input for group policy
        critical_stop_message = (
            "🛑 STOP-AND-WAIT: Wireless settings collected successfully!\n\n"
            "📋 NOW I need you to provide group policy data before I can proceed.\n\n"
            "Please tell me what group policy settings you want to create/update.\n"
            "Example: 'Create a policy called Guest Policy with 500 Kbps upload and 1000 Kbps download'"
        )
        
        return [
            {
                "type": "text", 
                "text": critical_stop_message
            }
        ]
        
    except Exception as e:
        logger.error(f"Error in update_network_wireless_settings: {e}")
        return [
            {
                "type": "text",
                "text": f"❌ Error updating wireless settings: {str(e)}"
            }
        ]




async def update_network_wireless_settings_with_group_policy(wireless_settings: Dict[str, Any], group_policy_data: Dict[str, Any], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Complete the wireless settings update with group policy synchronization.
    This function applies group policy first, then wireless settings.
    
    Args:
        wireless_settings: Wireless settings to apply
        group_policy_data: Group policy settings to apply
        use_mock: Whether to use mock server mode
    """
    try:
        client = MerakiAPIClient(use_mock=use_mock)
        
        # STEP 1: Apply group policy first
        logger.info("Step 1: Applying group policy settings...")
        try:
            # Note: create_network_group_policy tool has been removed
            # Group policy creation is now handled through update_network_group_policy only
            group_policy_result = {"message": "Group policy creation tool removed - use update_network_group_policy instead"}
            group_policy_status = "skipped"
        except Exception as e:
            logger.error(f"Failed to apply group policy: {e}")
            group_policy_result = {"error": f"Group policy application failed: {e}"}
            group_policy_status = "failed"
        
        # STEP 2: Apply wireless settings
        logger.info("Step 2: Applying wireless settings...")
        try:
            wireless_result = await client.update_network_wireless_settings(settings_data=wireless_settings)
            wireless_status = "completed"
        except Exception as e:
            logger.error(f"Failed to apply wireless settings: {e}")
            wireless_result = {"error": f"Wireless settings application failed: {e}"}
            wireless_status = "failed"
        
        # Prepare final result
        final_result = {
            "tool": "wireless_and_group_policy_sync_execution",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "execution_flow": "Group Policy → Wireless Settings",
            "step1_group_policy": {
                "status": group_policy_status,
                "policy_data": group_policy_data,
                "response": group_policy_result
            },
            "step2_wireless": {
                "status": wireless_status,
                "settings_data": wireless_settings,
                "response": wireless_result
            },
            "overall_status": "completed" if group_policy_status == "completed" and wireless_status == "completed" else "partial_failure",
            "summary": f"Synchronization completed for network {client.network_id}. Group Policy: {group_policy_status}, Wireless: {wireless_status}."
        }

        logger.info(f"Final synchronization completed for network {client.network_id}")
        
        return [{"type": "text", "text": json.dumps(final_result, indent=2, default=str)}]

    except Exception as e:
        logger.error(f"update_network_wireless_settings_with_group_policy failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing final synchronization: {str(e)}"}]

async def continue_wireless_update_after_policy(wireless_settings: Dict[str, Any], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Continue wireless settings update after group policy has been completed.
    This function applies the wireless settings that were collected earlier.
    
    Args:
        wireless_settings: Wireless settings that were collected earlier
        use_mock: Whether to use mock server mode
    """
    try:
        client = MerakiAPIClient(use_mock=use_mock)
        
        logger.info("Continuing wireless settings update after group policy completion...")
        
        # Apply wireless settings
        try:
            wireless_result = await client.update_network_wireless_settings(settings_data=wireless_settings)
            wireless_status = "completed"
        except Exception as e:
            logger.error(f"Failed to apply wireless settings: {e}")
            wireless_result = {"error": f"Wireless settings application failed: {e}"}
            wireless_status = "failed"
        
        # Prepare final result
        final_result = {
            "tool": "continue_wireless_update_after_policy",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "execution_flow": "Group Policy Completed → Wireless Settings Applied",
            "wireless_settings": {
                "status": wireless_status,
                "settings_data": wireless_settings,
                "response": wireless_result
            },
            "overall_status": "completed" if wireless_status == "completed" else "failed",
            "summary": f"Wireless settings applied for network {client.network_id}. Status: {wireless_status}."
        }
        
        logger.info(f"Wireless settings update completed for network {client.network_id}")
        
        return [{"type": "text", "text": json.dumps(final_result, indent=2, default=str)}]
        
    except Exception as e:
        logger.error(f"continue_wireless_update_after_policy failed: {str(e)}")
        return [{"type": "text", "text": f"Error continuing wireless update: {str(e)}"}]

async def update_network_wireless_settings_complete(wireless_settings: Union[Dict[str, Any], str], group_policy_data: Union[Dict[str, Any], str], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Complete wireless settings update with group policy synchronization in ONE call.
    This function requires BOTH wireless settings AND group policy data from the start.
    
    Args:
        wireless_settings: Wireless settings to apply (dict or JSON string)
        group_policy_data: Group policy settings to apply (dict or JSON string)
        use_mock: Whether to use mock server mode
    """
    try:
        # Handle natural language input by converting it to structured data
        if isinstance(wireless_settings, str):
            # Convert natural language to structured wireless settings data
            from natural_language_converter import convert_natural_language_to_wireless_settings
            wireless_settings = convert_natural_language_to_wireless_settings(wireless_settings)
            logger.info("Successfully converted natural language input to wireless settings")
        
        if isinstance(group_policy_data, str):
            # Convert natural language to structured group policy data
            from natural_language_converter import convert_natural_language_to_policy_data
            group_policy_data = convert_natural_language_to_policy_data(group_policy_data)
            logger.info("Successfully converted natural language input to group policy data")
        
        # Ensure both inputs are dicts
        if not isinstance(wireless_settings, dict):
            raise ValueError("wireless_settings must be a dictionary or valid JSON string")
        if not isinstance(group_policy_data, dict):
            raise ValueError("group_policy_data must be a dictionary or valid JSON string")

        client = MerakiAPIClient(use_mock=use_mock)
        
        # STEP 1: Apply group policy first
        logger.info("Step 1: Applying group policy settings...")
        try:
            # Note: create_network_group_policy tool has been removed
            # Group policy creation is now handled through update_network_group_policy only
            group_policy_result = {"message": "Group policy creation tool removed - use update_network_group_policy instead"}
            group_policy_status = "skipped"
        except Exception as e:
            logger.error(f"Failed to apply group policy: {e}")
            group_policy_result = {"error": f"Group policy application failed: {e}"}
            group_policy_status = "failed"
        
        # STEP 2: Apply wireless settings
        logger.info("Step 2: Applying wireless settings...")
        try:
            wireless_result = await client.update_network_wireless_settings(settings_data=wireless_settings)
            wireless_status = "completed"
        except Exception as e:
            logger.error(f"Failed to apply wireless settings: {e}")
            wireless_result = {"error": f"Wireless settings application failed: {e}"}
            wireless_status = "failed"
        
        # Prepare final result
        final_result = {
            "tool": "update_network_wireless_settings_complete",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "execution_flow": "Group Policy → Wireless Settings",
            "step1_group_policy": {
                "status": group_policy_status,
                "policy_data": group_policy_data,
                "response": group_policy_result
            },
            "step2_wireless": {
                "status": wireless_status,
                "settings_data": wireless_settings,
                "response": wireless_result
            },
            "overall_status": "completed" if group_policy_status == "completed" and wireless_status == "completed" else "partial_failure",
            "summary": f"Synchronization completed for network {client.network_id}. Group Policy: {group_policy_status}, Wireless: {wireless_status}."
        }

        logger.info(f"Complete synchronization finished for network {client.network_id}")
        
        return [{"type": "text", "text": json.dumps(final_result, indent=2, default=str)}]

    except Exception as e:
        logger.error(f"update_network_wireless_settings_complete failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing complete synchronization: {str(e)}"}]

async def execute_wireless_and_group_policy_sync(wireless_settings: Dict[str, Any], group_policy_data: Dict[str, Any], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Execute the final synchronization after both inputs are collected.
    This function applies group policy first, then wireless settings.
    
    Args:
        wireless_settings: Wireless settings to apply
        group_policy_data: Group policy settings to apply
        use_mock: Whether to use mock server mode
    """
    try:
        client = MerakiAPIClient(use_mock=use_mock)
        
        # STEP 1: Apply group policy first
        logger.info("Step 1: Applying group policy settings...")
        try:
            # Note: create_network_group_policy tool has been removed
            # Group policy creation is now handled through update_network_group_policy only
            group_policy_result = {"message": "Group policy creation tool removed - use update_network_group_policy instead"}
            group_policy_status = "skipped"
        except Exception as e:
            logger.error(f"Failed to apply group policy: {e}")
            group_policy_result = {"error": f"Group policy application failed: {e}"}
            group_policy_status = "failed"
        
        # STEP 2: Apply wireless settings
        logger.info("Step 2: Applying wireless settings...")
        try:
            wireless_result = await client.update_network_wireless_settings(settings_data=wireless_settings)
            wireless_status = "completed"
        except Exception as e:
            logger.error(f"Failed to apply wireless settings: {e}")
            wireless_result = {"error": f"Wireless settings application failed: {e}"}
            wireless_status = "failed"
        
        # Prepare final result
        final_result = {
            "tool": "wireless_and_group_policy_sync_execution",
            "timestamp": datetime.now().isoformat(),
            "network_id": client.network_id,
            "execution_flow": "Group Policy → Wireless Settings",
            "step1_group_policy": {
                "status": group_policy_status,
                "policy_data": group_policy_data,
                "response": group_policy_result
            },
            "step2_wireless": {
                "status": wireless_status,
                "settings_data": wireless_settings,
                "response": wireless_result
            },
            "overall_status": "completed" if group_policy_status == "completed" and wireless_status == "completed" else "partial_failure",
            "summary": f"Synchronization completed for network {client.network_id}. Group Policy: {group_policy_status}, Wireless: {wireless_status}."
        }

        logger.info(f"Final synchronization completed for network {client.network_id}")
        
        return [{"type": "text", "text": json.dumps(final_result, indent=2, default=str)}]

    except Exception as e:
        logger.error(f"execute_wireless_and_group_policy_sync failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing final synchronization: {str(e)}"}]
