"""
Natural Language to Structured Data Converter
Converts human-readable input to the expected JSON structures for various tools
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("natural-language-converter")

def convert_natural_language_to_policy_data(natural_language: str) -> Dict[str, Any]:
    """
    Convert natural language input to structured policy data.
    This function parses common phrases and converts them to the expected JSON structure.
    """
    policy_data = {}
    natural_language = natural_language.lower()
    
    # Parse bandwidth settings
    if "bandwidth" in natural_language or "limit" in natural_language:
        bandwidth = {}
        
        # Upload limits
        if "500" in natural_language and ("upload" in natural_language or "up" in natural_language):
            bandwidth["limitUp"] = 500
        elif "1000" in natural_language and ("upload" in natural_language or "up" in natural_language):
            bandwidth["limitUp"] = 1000
        elif "2000" in natural_language and ("upload" in natural_language or "up" in natural_language):
            bandwidth["limitUp"] = 2000
        
        # Download limits
        if "1000" in natural_language and ("download" in natural_language or "down" in natural_language):
            bandwidth["limitDown"] = 1000
        elif "10000" in natural_language and ("download" in natural_language or "down" in natural_language):
            bandwidth["limitDown"] = 10000
        elif "2000" in natural_language and ("download" in natural_language or "down" in natural_language):
            bandwidth["limitDown"] = 2000
        
        if bandwidth:
            policy_data["bandwidth"] = bandwidth
    
    # Parse traffic shaping
    if "traffic shaping" in natural_language or "traffic" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            policy_data["firewallAndTrafficShaping"] = {
                "settings": {
                    "trafficShapingEnabled": True
                }
            }
        elif "disable" in natural_language or "off" in natural_language:
            policy_data["firewallAndTrafficShaping"] = {
                "settings": {
                    "trafficShapingEnabled": False
                }
            }
    
    # Parse content filtering
    if "content filter" in natural_language or "filtering" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            policy_data["contentFiltering"] = {"enabled": True}
        elif "disable" in natural_language or "off" in natural_language:
            policy_data["contentFiltering"] = {"enabled": False}
    
    # Parse scheduling
    if "schedule" in natural_language or "scheduling" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            policy_data["scheduling"] = {"enabled": True}
        elif "disable" in natural_language or "off" in natural_language:
            policy_data["scheduling"] = {"enabled": False}
    
    # Parse VLAN tagging
    if "vlan" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            policy_data["vlanTagging"] = {"settings": "allowed"}
        elif "disable" in natural_language or "off" in natural_language:
            policy_data["vlanTagging"] = {"settings": "not allowed"}
    
    # Parse Bonjour forwarding
    if "bonjour" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            policy_data["bonjourForwarding"] = {"enabled": True}
        elif "disable" in natural_language or "off" in natural_language:
            policy_data["bonjourForwarding"] = {"enabled": False}
    
    # Parse splash auth settings
    if "splash" in natural_language:
        if "bypass" in natural_language:
            policy_data["splashAuthSettings"] = "bypass"
        elif "network" in natural_language:
            policy_data["splashAuthSettings"] = "network"
    
    # Set default values for required fields if not specified
    if "name" not in policy_data:
        policy_data["name"] = "New Policy"
    if "scheduling" not in policy_data:
        policy_data["scheduling"] = {"enabled": False}
    if "contentFiltering" not in policy_data:
        policy_data["contentFiltering"] = {"enabled": False}
    if "splashAuthSettings" not in policy_data:
        policy_data["splashAuthSettings"] = "bypass"
    if "vlanTagging" not in policy_data:
        policy_data["vlanTagging"] = {"settings": "not allowed"}
    if "bonjourForwarding" not in policy_data:
        policy_data["bonjourForwarding"] = {"enabled": False}
    
    logger.info(f"Converted natural language to policy data: {policy_data}")
    return policy_data

def convert_natural_language_to_appliance_settings(natural_language: str) -> Dict[str, Any]:
    """
    Convert natural language input to structured appliance settings data.
    """
    settings_data = {}
    natural_language = natural_language.lower()
    
    # Parse DHCP settings
    if "dhcp" in natural_language:
        dhcp = {}
        if "enable" in natural_language or "on" in natural_language:
            dhcp["enabled"] = True
        elif "disable" in natural_language or "off" in natural_language:
            dhcp["enabled"] = False
        
        # Parse lease time
        if "24" in natural_language and ("hour" in natural_language or "86400" in natural_language):
            dhcp["leaseTime"] = 86400
        elif "12" in natural_language and ("hour" in natural_language or "43200" in natural_language):
            dhcp["leaseTime"] = 43200
        
        if dhcp:
            settings_data["dhcp"] = dhcp
    
    # Parse VLAN settings
    if "vlan" in natural_language:
        vlan = {}
        if "enable" in natural_language or "on" in natural_language:
            vlan["enabled"] = True
        elif "disable" in natural_language or "off" in natural_language:
            vlan["enabled"] = False
        
        # Parse VLAN ID
        if "100" in natural_language:
            vlan["id"] = 100
        elif "200" in natural_language:
            vlan["id"] = 200
        
        if vlan:
            settings_data["vlan"] = vlan
    
    logger.info(f"Converted natural language to appliance settings: {settings_data}")
    return settings_data

def convert_natural_language_to_wireless_settings(natural_language: str) -> Dict[str, Any]:
    """
    Convert natural language input to structured wireless settings data.
    """
    settings_data = {}
    natural_language = natural_language.lower()
    
    # Parse wireless enable/disable
    if "wireless" in natural_language or "wifi" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            settings_data["enabled"] = True
        elif "disable" in natural_language or "off" in natural_language:
            settings_data["enabled"] = False
    
    # Parse SSID
    if "ssid" in natural_language:
        # Extract SSID name from natural language
        if "my_ssid" in natural_language or "my ssid" in natural_language:
            settings_data["ssid"] = "My_SSID"
        elif "main" in natural_language and "network" in natural_language:
            settings_data["ssid"] = "Main_Network"
    
    # Parse bandwidth settings
    if "bandwidth" in natural_language or "limit" in natural_language:
        bandwidth = {}
        
        # Upload limits
        if "1000" in natural_language and ("upload" in natural_language or "up" in natural_language):
            bandwidth["limitUp"] = 1000
        elif "500" in natural_language and ("upload" in natural_language or "up" in natural_language):
            bandwidth["limitUp"] = 500
        
        # Download limits
        if "1000" in natural_language and ("download" in natural_language or "down" in natural_language):
            bandwidth["limitDown"] = 1000
        elif "500" in natural_language and ("download" in natural_language or "down" in natural_language):
            bandwidth["limitDown"] = 500
        
        if bandwidth:
            settings_data["bandwidth"] = bandwidth
    
    logger.info(f"Converted natural language to wireless settings: {settings_data}")
    return settings_data
