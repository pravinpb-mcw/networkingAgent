"""
Update Network Wireless Settings Tool
Updates wireless settings for a specific network with interactive group policy synchronization
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Union

from meraki_client import MerakiAPIClient

logger = logging.getLogger("update-network-wireless-settings-tool")

def check_existing_group_policies_for_traffic_shaping() -> Dict[str, Any]:
    """
    Check the networks.json file for existing group policies and their trafficShapingEnabled status.
    Returns information about policies that have trafficShapingEnabled set to false.
    """
    try:
        # Path to the networks.json file
        networks_file_path = os.path.join("mock_data", "networks.json")
        
        if not os.path.exists(networks_file_path):
            logger.info("networks.json file not found, no existing policies to check")
            return {"found_policies": False, "policies_with_disabled_traffic_shaping": []}
        
        with open(networks_file_path, 'r') as f:
            networks_data = json.load(f)
        
        policies_with_disabled_traffic_shaping = []
        
        # Check all networks for group policies
        for network_id, network_data in networks_data.items():
            if "groupPolicies" in network_data:
                for policy_id, policy_data in network_data["groupPolicies"].items():
                    # Check if trafficShapingEnabled exists and is false
                    firewall_and_traffic_shaping = policy_data.get("firewallAndTrafficShaping", {})
                    settings = firewall_and_traffic_shaping.get("settings", {})
                    traffic_shaping_enabled = settings.get("trafficShapingEnabled", None)
                    
                    if traffic_shaping_enabled is False:
                        policies_with_disabled_traffic_shaping.append({
                            "network_id": network_id,
                            "policy_id": policy_id,
                            "policy_name": policy_data.get("name", "Unknown"),
                            "current_status": traffic_shaping_enabled
                        })
        
        return {
            "found_policies": len(policies_with_disabled_traffic_shaping) > 0,
            "policies_with_disabled_traffic_shaping": policies_with_disabled_traffic_shaping,
            "total_policies_checked": sum(len(network_data.get("groupPolicies", {})) for network_data in networks_data.values())
        }
        
    except Exception as e:
        logger.error(f"Error checking existing group policies: {e}")
        return {"found_policies": False, "policies_with_disabled_traffic_shaping": [], "error": str(e)}

async def update_network_wireless_settings(settings_data: Union[Dict[str, Any], str], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Update network wireless settings for your configured network with interactive group policy synchronization.
    Uses NETWORK_ID from .env file.
    
    This function implements an interactive call chain:
    1) First checks existing group policies for trafficShapingEnabled status
    2) If any policies have trafficShapingEnabled=false, asks user if they want to enable it
    3) Then collects wireless settings input (but doesn't apply yet)
    4) Then asks user for group policy settings input
    5) Applies group policy first
    6) Finally applies wireless settings
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
        
        # STEP 1: Check existing group policies for trafficShapingEnabled status
        logger.info("Step 1: Checking existing group policies for trafficShapingEnabled status...")
        policy_check_result = check_existing_group_policies_for_traffic_shaping()
        
        # Build the response message
        response_parts = []
        response_parts.append("🔍 **GROUP POLICY TRAFFIC SHAPING CHECK**")
        response_parts.append("=" * 50)
        
        if policy_check_result["found_policies"]:
            disabled_policies = policy_check_result["policies_with_disabled_traffic_shaping"]
            response_parts.append(f"📋 Found {len(disabled_policies)} group policy(ies) with trafficShapingEnabled=false:")
            
            for policy in disabled_policies:
                response_parts.append(f"   • Policy ID: {policy['policy_id']}")
                response_parts.append(f"     Name: {policy['policy_name']}")
                response_parts.append(f"     Network: {policy['network_id']}")
                response_parts.append(f"     Current Status: Traffic Shaping DISABLED")
                response_parts.append("")
            
            response_parts.append("❓ **QUESTION:** Do you want to enable traffic shaping for these policies?")
            response_parts.append("   Reply with:")
            response_parts.append("   • 'YES' or 'ENABLE' - to enable traffic shaping for all policies")
            response_parts.append("   • 'NO' or 'SKIP' - to continue without enabling traffic shaping")
            response_parts.append("   • 'POLICY_ID:YES' or 'POLICY_NAME' - to enable for specific policy")
            response_parts.append("     Examples: 'policy_1:YES', 'Updated Staff Policy', 'policy_1'")
            response_parts.append("")
            
            # Show available policy IDs and names to help users
            response_parts.append("📋 **AVAILABLE POLICIES:**")
            for policy in disabled_policies:
                response_parts.append(f"   • ID: {policy['policy_id']} | Name: {policy['policy_name']} | Network: {policy['network_id']}")
            response_parts.append("")
            response_parts.append("📝 **NEXT STEP:** After answering, I'll collect your wireless settings.")
            
        else:
            response_parts.append("✅ All existing group policies have trafficShapingEnabled=true or no policies found.")
            response_parts.append("📝 **NEXT STEP:** I'll now collect your wireless settings.")
        
        response_parts.append("")
        response_parts.append("🛑 **STOP-AND-WAIT:** Please respond to the traffic shaping question above.")
        
        return [
            {
                "type": "text", 
                "text": "\n".join(response_parts)
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

async def handle_traffic_shaping_response(user_response: str, wireless_settings: Dict[str, Any], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Handle user response to traffic shaping question and proceed with wireless settings.
    
    Args:
        user_response: User's response to traffic shaping question
        wireless_settings: Wireless settings that were collected earlier
        use_mock: Whether to use mock server mode
    """
    try:
        # Clean up potentially duplicated input
        user_response_clean = user_response.strip()
        
        # Handle common duplication patterns
        if user_response_clean.endswith(user_response_clean[:len(user_response_clean)//2]):
            # Input is duplicated, take the first half
            user_response_clean = user_response_clean[:len(user_response_clean)//2]
            logger.info(f"Detected duplicated input, cleaned to: '{user_response_clean}'")
        
        # Handle specific duplication patterns
        if user_response_clean == "YESYES":
            user_response_clean = "YES"
            logger.info("Detected 'YESYES', cleaned to 'YES'")
        elif user_response_clean == "NONO":
            user_response_clean = "NO"
            logger.info("Detected 'NONO', cleaned to 'NO'")
        elif "policy_2:YESpolicy_2:YES" in user_response_clean:
            user_response_clean = "policy_2:YES"
            logger.info("Detected duplicated policy response, cleaned to 'policy_2:YES'")
        
        user_response_lower = user_response_clean.lower().strip()
        
        # More flexible input processing - handle any input format
        logger.info(f"Processing user response: '{user_response_clean}' (cleaned from '{user_response}')")
        
        # Enhanced input processing - handle any format intelligently
        # Check if input contains a policy ID or policy name (even if duplicated)
        policy_check_result = check_existing_group_policies_for_traffic_shaping()
        available_policies = policy_check_result.get("policies_with_disabled_traffic_shaping", [])
        
        # Get all available policy IDs and names from JSON
        all_policies = []
        try:
            with open("mock_data/networks.json", 'r') as f:
                networks_data = json.load(f)
            
            for network_id, network_data in networks_data.items():
                if "groupPolicies" in network_data:
                    for policy_id, policy_data in network_data["groupPolicies"].items():
                        policy_name = policy_data.get("name", "Unknown")
                        all_policies.append({
                            "policy_id": policy_id,
                            "policy_name": policy_name,
                            "network_id": network_id
                        })
        except Exception as e:
            logger.error(f"Error reading networks.json: {e}")
        
        # Check if user input contains any policy ID or policy name (even if duplicated)
        detected_policy_id = None
        detected_policy_name = None
        
        # First check for policy IDs
        for policy in all_policies:
            if policy["policy_id"] in user_response_clean:
                detected_policy_id = policy["policy_id"]
                detected_policy_name = policy["policy_name"]
                break
        
        # If no policy ID found, check for policy names
        if not detected_policy_id:
            for policy in all_policies:
                if policy["policy_name"].lower() in user_response_clean.lower():
                    detected_policy_id = policy["policy_id"]
                    detected_policy_name = policy["policy_name"]
                    break
        
        # If we detected a policy ID or name, treat it as "enable for this policy"
        if detected_policy_id:
            logger.info(f"Detected policy '{detected_policy_name}' (ID: {detected_policy_id}) in user input, treating as enable request")
            user_response_lower = f"{detected_policy_id}:yes"
        
        # Check if user wants to enable traffic shaping
        if user_response_lower in ['yes', 'enable', 'y']:
            # Enable traffic shaping for all policies with disabled status
            policy_check_result = check_existing_group_policies_for_traffic_shaping()
            enabled_count = 0
            
            if policy_check_result["found_policies"]:
                # Always call the API (will use mock responses when use_mock=True)
                client = MerakiAPIClient(use_mock=use_mock)
                
                for policy in policy_check_result["policies_with_disabled_traffic_shaping"]:
                    try:
                        # Update the policy to enable traffic shaping
                        policy_update_data = {
                            "firewallAndTrafficShaping": {
                                "settings": {
                                    "trafficShapingEnabled": True
                                }
                            }
                        }
                        
                        # Call the update_network_group_policy function
                        from update_network_group_policy import update_network_group_policy
                        await update_network_group_policy(policy["policy_id"], policy_update_data, use_mock=use_mock)
                        enabled_count += 1
                        logger.info(f"Enabled traffic shaping for policy {policy['policy_id']} via API")
                        
                    except Exception as e:
                        logger.error(f"Failed to enable traffic shaping for policy {policy['policy_id']}: {e}")
                
                # Also update JSON file for consistency in mock mode
                if use_mock:
                    try:
                        with open("mock_data/networks.json", 'r') as f:
                            networks_data = json.load(f)
                        
                        for network_id, network_data in networks_data.items():
                            if "groupPolicies" in network_data:
                                for policy_id, policy_data in network_data["groupPolicies"].items():
                                    # Check if this policy has disabled traffic shaping
                                    firewall_settings = policy_data.get("firewallAndTrafficShaping", {})
                                    settings = firewall_settings.get("settings", {})
                                    if not settings.get("trafficShapingEnabled", True):
                                        # Enable traffic shaping in JSON
                                        if "firewallAndTrafficShaping" not in policy_data:
                                            policy_data["firewallAndTrafficShaping"] = {}
                                        if "settings" not in policy_data["firewallAndTrafficShaping"]:
                                            policy_data["firewallAndTrafficShaping"]["settings"] = {}
                                        policy_data["firewallAndTrafficShaping"]["settings"]["trafficShapingEnabled"] = True
                                        logger.info(f"Updated traffic shaping for policy {policy_id} in JSON file")
                        
                        # Save updated JSON file
                        with open("mock_data/networks.json", 'w') as f:
                            json.dump(networks_data, f, indent=2)
                        logger.info("Updated networks.json file with traffic shaping enabled")
                        
                    except Exception as e:
                        logger.error(f"Error updating JSON file: {e}")
                
                # Continue directly with wireless settings
                response_parts = []
                response_parts.append("✅ **TRAFFIC SHAPING UPDATE COMPLETED**")
                response_parts.append("=" * 50)
                response_parts.append(f"Successfully enabled traffic shaping for {enabled_count} policy(ies).")
                response_parts.append("")
                response_parts.append("🚀 **APPLYING WIRELESS SETTINGS...**")
                response_parts.append("=" * 50)
                
                # Apply wireless settings directly
                try:
                    client = MerakiAPIClient(use_mock=use_mock)
                    wireless_result = await client.update_network_wireless_settings(settings_data=wireless_settings)
                    
                    response_parts.append("✅ **WIRELESS SETTINGS APPLIED SUCCESSFULLY**")
                    response_parts.append("")
                    response_parts.append("📋 **Applied Settings:**")
                    if wireless_settings.get("enabled"):
                        response_parts.append(f"   • Wireless: ENABLED")
                    if wireless_settings.get("ssid"):
                        response_parts.append(f"   • SSID: {wireless_settings['ssid']}")
                    if wireless_settings.get("bandwidth"):
                        bandwidth = wireless_settings["bandwidth"]
                        if bandwidth.get("limitUp"):
                            response_parts.append(f"   • Upload Limit: {bandwidth['limitUp']} Mbps")
                        if bandwidth.get("limitDown"):
                            response_parts.append(f"   • Download Limit: {bandwidth['limitDown']} Mbps")
                    
                    response_parts.append("")
                    response_parts.append("🎉 **WORKFLOW COMPLETED SUCCESSFULLY!**")
                    response_parts.append("• Traffic shaping enabled for existing policies")
                    response_parts.append("• Wireless settings applied")
                    
                except Exception as e:
                    response_parts.append(f"❌ **ERROR APPLYING WIRELESS SETTINGS:** {str(e)}")
                
                return [{"type": "text", "text": "\n".join(response_parts)}]
            else:
                # No policies to update - continue with wireless settings
                response_parts = []
                response_parts.append("ℹ️ **TRAFFIC SHAPING STATUS**")
                response_parts.append("=" * 50)
                response_parts.append("No policies found with disabled traffic shaping.")
                response_parts.append("")
                response_parts.append("🚀 **APPLYING WIRELESS SETTINGS...**")
                response_parts.append("=" * 50)
                
                # Apply wireless settings directly
                try:
                    client = MerakiAPIClient(use_mock=use_mock)
                    wireless_result = await client.create_network_wireless_settings(settings_data=wireless_settings)
                    
                    response_parts.append("✅ **WIRELESS SETTINGS APPLIED SUCCESSFULLY**")
                    response_parts.append("")
                    response_parts.append("📋 **Applied Settings:**")
                    if wireless_settings.get("enabled"):
                        response_parts.append(f"   • Wireless: ENABLED")
                    if wireless_settings.get("ssid"):
                        response_parts.append(f"   • SSID: {wireless_settings['ssid']}")
                    if wireless_settings.get("bandwidth"):
                        bandwidth = wireless_settings["bandwidth"]
                        if bandwidth.get("limitUp"):
                            response_parts.append(f"   • Upload Limit: {bandwidth['limitUp']} Mbps")
                        if bandwidth.get("limitDown"):
                            response_parts.append(f"   • Download Limit: {bandwidth['limitDown']} Mbps")
                    
                    response_parts.append("")
                    response_parts.append("🎉 **WORKFLOW COMPLETED SUCCESSFULLY!**")
                    response_parts.append("• Wireless settings applied")
                    
                except Exception as e:
                    response_parts.append(f"❌ **ERROR APPLYING WIRELESS SETTINGS:** {str(e)}")
                
                return [{"type": "text", "text": "\n".join(response_parts)}]
        
        elif user_response_lower in ['no', 'skip', 'n']:
            # User chose not to enable traffic shaping - continue with wireless settings
            response_parts = []
            response_parts.append("ℹ️ **TRAFFIC SHAPING SKIPPED**")
            response_parts.append("=" * 50)
            response_parts.append("You chose not to enable traffic shaping for existing policies.")
            response_parts.append("")
            response_parts.append("🚀 **APPLYING WIRELESS SETTINGS...**")
            response_parts.append("=" * 50)
            
            # Apply wireless settings directly
            try:
                client = MerakiAPIClient(use_mock=use_mock)
                wireless_result = await client.create_network_wireless_settings(settings_data=wireless_settings)
                
                response_parts.append("✅ **WIRELESS SETTINGS APPLIED SUCCESSFULLY**")
                response_parts.append("")
                response_parts.append("📋 **Applied Settings:**")
                if wireless_settings.get("enabled"):
                    response_parts.append(f"   • Wireless: ENABLED")
                if wireless_settings.get("ssid"):
                    response_parts.append(f"   • SSID: {wireless_settings['ssid']}")
                if wireless_settings.get("bandwidth"):
                    bandwidth = wireless_settings["bandwidth"]
                    if bandwidth.get("limitUp"):
                        response_parts.append(f"   • Upload Limit: {bandwidth['limitUp']} Mbps")
                    if bandwidth.get("limitDown"):
                        response_parts.append(f"   • Download Limit: {bandwidth['limitDown']} Mbps")
                
                response_parts.append("")
                response_parts.append("🎉 **WORKFLOW COMPLETED SUCCESSFULLY!**")
                response_parts.append("• Wireless settings applied")
                
            except Exception as e:
                response_parts.append(f"❌ **ERROR APPLYING WIRELESS SETTINGS:** {str(e)}")
            
            return [{"type": "text", "text": "\n".join(response_parts)}]
        
        elif ':' in user_response_lower:
            # User wants to enable for specific policy
            try:
                policy_id, action = user_response_lower.split(':', 1)
                policy_id = policy_id.strip()
                action = action.strip()
                
                if action in ['yes', 'enable', 'y']:
                    # Always call the API (will use mock responses when use_mock=True)
                    client = MerakiAPIClient(use_mock=use_mock)
                    
                    # Update the specific policy to enable traffic shaping
                    policy_update_data = {
                        "firewallAndTrafficShaping": {
                            "settings": {
                                "trafficShapingEnabled": True
                            }
                        }
                    }
                    
                    # Call the update_network_group_policy function
                    from update_network_group_policy import update_network_group_policy
                    await update_network_group_policy(policy_id, policy_update_data, use_mock=use_mock)
                    logger.info(f"Enabled traffic shaping for policy {policy_id} via API")
                    
                    # Also update JSON file for consistency in mock mode
                    if use_mock:
                        try:
                            with open("mock_data/networks.json", 'r') as f:
                                networks_data = json.load(f)
                            
                            # Find and update the specific policy
                            for network_id, network_data in networks_data.items():
                                if "groupPolicies" in network_data and policy_id in network_data["groupPolicies"]:
                                    policy_data = network_data["groupPolicies"][policy_id]
                                    if "firewallAndTrafficShaping" not in policy_data:
                                        policy_data["firewallAndTrafficShaping"] = {}
                                    if "settings" not in policy_data["firewallAndTrafficShaping"]:
                                        policy_data["firewallAndTrafficShaping"]["settings"] = {}
                                    policy_data["firewallAndTrafficShaping"]["settings"]["trafficShapingEnabled"] = True
                                    logger.info(f"Updated traffic shaping for policy {policy_id} in JSON file")
                                    break
                            
                            # Save updated JSON file
                            with open("mock_data/networks.json", 'w') as f:
                                json.dump(networks_data, f, indent=2)
                            logger.info("Updated networks.json file with traffic shaping enabled")
                            
                        except Exception as e:
                            logger.error(f"Error updating JSON file: {e}")
                    
                    # Continue directly with wireless settings
                    response_parts = []
                    response_parts.append("✅ **TRAFFIC SHAPING UPDATE COMPLETED**")
                    response_parts.append("=" * 50)
                    response_parts.append(f"Successfully enabled traffic shaping for policy: {policy_id}")
                    response_parts.append("")
                    response_parts.append("🚀 **APPLYING WIRELESS SETTINGS...**")
                    response_parts.append("=" * 50)
                    
                    # Apply wireless settings directly
                    try:
                        client = MerakiAPIClient(use_mock=use_mock)
                        wireless_result = await client.create_network_wireless_settings(settings_data=wireless_settings)
                        
                        response_parts.append("✅ **WIRELESS SETTINGS APPLIED SUCCESSFULLY**")
                        response_parts.append("")
                        response_parts.append("📋 **Applied Settings:**")
                        if wireless_settings.get("enabled"):
                            response_parts.append(f"   • Wireless: ENABLED")
                        if wireless_settings.get("ssid"):
                            response_parts.append(f"   • SSID: {wireless_settings['ssid']}")
                        if wireless_settings.get("bandwidth"):
                            bandwidth = wireless_settings["bandwidth"]
                            if bandwidth.get("limitUp"):
                                response_parts.append(f"   • Upload Limit: {bandwidth['limitUp']} Mbps")
                            if bandwidth.get("limitDown"):
                                response_parts.append(f"   • Download Limit: {bandwidth['limitDown']} Mbps")
                        
                        response_parts.append("")
                        response_parts.append("🎉 **WORKFLOW COMPLETED SUCCESSFULLY!**")
                        response_parts.append("• Traffic shaping enabled for specific policy")
                        response_parts.append("• Wireless settings applied")
                        
                    except Exception as e:
                        response_parts.append(f"❌ **ERROR APPLYING WIRELESS SETTINGS:** {str(e)}")
                    
                    return [{"type": "text", "text": "\n".join(response_parts)}]
                else:
                    return [{"type": "text", "text": "Invalid action. Please use 'YES' or 'NO' after the policy ID."}]
                    
            except Exception as e:
                return [{"type": "text", "text": f"Error processing specific policy update: {str(e)}"}]
        
        else:
            # More helpful error message with examples
            error_message = "I couldn't understand your response. Please try one of these formats:\n"
            error_message += "• 'YES' or 'ENABLE' - to enable traffic shaping for all policies\n"
            error_message += "• 'NO' or 'SKIP' - to continue without enabling traffic shaping\n"
            error_message += "• 'policy_1' or 'Updated Staff Policy' or 'policy_1:YES' - to enable for specific policy\n"
            
            # Show available policies with both IDs and names
            if all_policies:
                error_message += "\n📋 **ALL AVAILABLE POLICIES:**\n"
                for policy in all_policies:
                    error_message += f"• ID: {policy['policy_id']} | Name: {policy['policy_name']} | Network: {policy['network_id']}\n"
            else:
                error_message += f"\nAvailable policy IDs: {', '.join([p['policy_id'] for p in all_policies])}"
            
            return [{"type": "text", "text": error_message}]
        
    except Exception as e:
        logger.error(f"Error handling traffic shaping response: {e}")
        return [{"type": "text", "text": f"Error processing traffic shaping response: {str(e)}"}]



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
            wireless_result = await client.create_network_wireless_settings(settings_data=wireless_settings)
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
            wireless_result = await client.create_network_wireless_settings(settings_data=wireless_settings)
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

