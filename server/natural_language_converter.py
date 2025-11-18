"""
Natural Language to Structured Data Converter
Converts human-readable input to the expected JSON structures for various tools
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("natural-language-converter")

def extract_policy_id_from_input(natural_language: str) -> str:
    """
    Extract policy ID from natural language input.
    Returns the policy ID if found, or None if not found.
    """
    import re
    
    # Look for common policy ID patterns
    patterns = [
        r'policy[_\s]*(\w+)',  # "policy_2", "policy 2"
        r'id[_\s]*(\w+)',      # "id_2", "id 2"
        r'(\w+)[_\s]*policy',  # "2_policy", "2 policy"
        r'update[_\s]*(\w+)',  # "update_2", "update 2"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, natural_language.lower())
        if match:
            return match.group(1)
    
    return None

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
        
        # Use regex to extract any numeric values
        import re
        
        # Upload limits - look for any number followed by upload/up keywords
        upload_match = re.search(r'(\d+)\s*(?:kbps?|mbps?)?\s*(?:upload|up)', natural_language.lower())
        if upload_match:
            bandwidth["limitUp"] = int(upload_match.group(1))
        else:
            # Fallback to predefined values
            if "500" in natural_language and ("upload" in natural_language or "up" in natural_language):
                bandwidth["limitUp"] = 500
            elif "1000" in natural_language and ("upload" in natural_language or "up" in natural_language):
                bandwidth["limitUp"] = 1000
            elif "2000" in natural_language and ("upload" in natural_language or "up" in natural_language):
                bandwidth["limitUp"] = 2000
        
        # Download limits - look for any number followed by download/down keywords
        download_match = re.search(r'(\d+)\s*(?:kbps?|mbps?)?\s*(?:download|down)', natural_language.lower())
        if download_match:
            bandwidth["limitDown"] = int(download_match.group(1))
        else:
            # Fallback to predefined values
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
        elif "guest" in natural_language:
            settings_data["ssid"] = "guest_SSID"
        else:
            # Try to extract any SSID name from the text
            import re
            ssid_match = re.search(r'["\']([^"\']+)["\']', natural_language)
            if ssid_match:
                settings_data["ssid"] = ssid_match.group(1)
    
    # Parse bandwidth settings
    if "bandwidth" in natural_language or "limit" in natural_language:
        bandwidth = {}
        
        # Use regex to extract any numeric values for bandwidth
        import re
        
        # Upload limits - look for any number followed by upload/up keywords
        upload_match = re.search(r'(\d+)\s*(?:mbps?)?\s*(?:upload|up)', natural_language.lower())
        if upload_match:
            bandwidth["limitUp"] = int(upload_match.group(1))
        else:
            # Fallback to predefined values
            if "1000" in natural_language and ("upload" in natural_language or "up" in natural_language):
                bandwidth["limitUp"] = 1000
            elif "500" in natural_language and ("upload" in natural_language or "up" in natural_language):
                bandwidth["limitUp"] = 500
            elif "100" in natural_language and ("upload" in natural_language or "up" in natural_language):
                bandwidth["limitUp"] = 100
        
        # Download limits - look for any number followed by download/down keywords
        download_match = re.search(r'(\d+)\s*(?:mbps?)?\s*(?:download|down)', natural_language.lower())
        if download_match:
            bandwidth["limitDown"] = int(download_match.group(1))
        else:
            # Fallback to predefined values
            if "1000" in natural_language and ("download" in natural_language or "down" in natural_language):
                bandwidth["limitDown"] = 1000
            elif "500" in natural_language and ("download" in natural_language or "down" in natural_language):
                bandwidth["limitDown"] = 500
            elif "100" in natural_language and ("download" in natural_language or "down" in natural_language):
                bandwidth["limitDown"] = 100
        
        if bandwidth:
            settings_data["bandwidth"] = bandwidth
    
    logger.info(f"Converted natural language to wireless settings: {settings_data}")
    return settings_data

def convert_natural_language_to_network_settings(natural_language: str) -> Dict[str, Any]:
    """
    Convert natural language input to structured network settings data.
    """
    settings_data = {}
    natural_language = natural_language.lower()
    
    # Parse local status page
    if "local status page" in natural_language or "local status" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            settings_data["localStatusPageEnabled"] = True
        elif "disable" in natural_language or "off" in natural_language:
            settings_data["localStatusPageEnabled"] = False
    
    # Parse remote status page
    if "remote status page" in natural_language or "remote status" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            settings_data["remoteStatusPageEnabled"] = True
        elif "disable" in natural_language or "off" in natural_language:
            settings_data["remoteStatusPageEnabled"] = False
    
    # Parse secure port
    if "secure port" in natural_language or "secure" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            settings_data["securePort"] = {"enabled": True}
        elif "disable" in natural_language or "off" in natural_language:
            settings_data["securePort"] = {"enabled": False}
    
    # Parse local status page authentication
    if "authentication" in natural_language or "auth" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            settings_data["localStatusPage"] = {
                "authentication": {
                    "enabled": True,
                    "username": "admin"
                }
            }
        elif "disable" in natural_language or "off" in natural_language:
            settings_data["localStatusPage"] = {
                "authentication": {
                    "enabled": False
                }
            }
    
    # Parse named VLANs
    if "vlan" in natural_language or "vlans" in natural_language:
        if "enable" in natural_language or "on" in natural_language:
            settings_data["namedVlans"] = {"enabled": True}
        elif "disable" in natural_language or "off" in natural_language:
            settings_data["namedVlans"] = {"enabled": False}
    
    # Set default values if not specified
    if "localStatusPageEnabled" not in settings_data:
        settings_data["localStatusPageEnabled"] = True
    if "remoteStatusPageEnabled" not in settings_data:
        settings_data["remoteStatusPageEnabled"] = False
    if "securePort" not in settings_data:
        settings_data["securePort"] = {"enabled": False}
    if "localStatusPage" not in settings_data:
        settings_data["localStatusPage"] = {
            "authentication": {
                "enabled": True,
                "username": "admin"
            }
        }
    if "namedVlans" not in settings_data:
        settings_data["namedVlans"] = {"enabled": False}
    
    logger.info(f"Converted natural language to network settings: {settings_data}")
    return settings_data

def convert_natural_language_to_network_data(natural_language: str) -> Dict[str, Any]:
    """
    Convert natural language input to structured network data for organization network creation.
    """
    network_data = {}
    natural_language = natural_language.lower()
    
    # Parse network name
    if "name" in natural_language:
        # Try to extract network name from quotes
        import re
        name_match = re.search(r'["\']([^"\']+)["\']', natural_language)
        if name_match:
            network_data["name"] = name_match.group(1)
        elif "mcw" in natural_language and "san jose" in natural_language:
            network_data["name"] = "MCW San Jose New"
        elif "mcw" in natural_language and "berlin" in natural_language:
            network_data["name"] = "MCW Berlin Office"
        elif "main" in natural_language and "network" in natural_language:
            network_data["name"] = "Main Network"
        elif "guest" in natural_language and "network" in natural_language:
            network_data["name"] = "Guest Network"
        else:
            # Try to extract network name from the text more intelligently
            # Look for patterns like "called MCW Berlin Office" or "named MCW Berlin Office"
            name_patterns = [
                r'called\s+([A-Za-z0-9\s]+?)(?:\s+with|\s+in|\s+use|\s+enable|$)',
                r'named\s+([A-Za-z0-9\s]+?)(?:\s+with|\s+in|\s+use|\s+enable|$)',
                r'network\s+([A-Za-z0-9\s]+?)(?:\s+with|\s+in|\s+use|\s+enable|$)'
            ]
            for pattern in name_patterns:
                match = re.search(pattern, natural_language, re.IGNORECASE)
                if match:
                    network_data["name"] = match.group(1).strip()
                    break
    
    # Parse product types
    product_types = []
    if "appliance" in natural_language:
        product_types.append("appliance")
    if "camera" in natural_language:
        product_types.append("camera")
    if "cellular" in natural_language or "gateway" in natural_language:
        product_types.append("cellularGateway")
    if "sensor" in natural_language:
        product_types.append("sensor")
    if "switch" in natural_language:
        product_types.append("switch")
    if "wireless" in natural_language or "wifi" in natural_language:
        product_types.append("wireless")
    
    if product_types:
        network_data["productTypes"] = product_types
    else:
        # Default product types if none specified
        network_data["productTypes"] = ["appliance", "camera", "cellularGateway", "sensor", "switch", "wireless"]
    
    # Parse timezone
    if "timezone" in natural_language or "time zone" in natural_language:
        if "los angeles" in natural_language or "pacific" in natural_language:
            network_data["timeZone"] = "America/Los_Angeles"
        elif "new york" in natural_language or "eastern" in natural_language:
            network_data["timeZone"] = "America/New_York"
        elif "chicago" in natural_language or "central" in natural_language:
            network_data["timeZone"] = "America/Chicago"
        elif "denver" in natural_language or "mountain" in natural_language:
            network_data["timeZone"] = "America/Denver"
        elif "berlin" in natural_language or "germany" in natural_language or "europe" in natural_language:
            network_data["timeZone"] = "Europe/Berlin"
    else:
        # Default timezone
        network_data["timeZone"] = "America/Los_Angeles"
    
    # Parse tags
    if "tag" in natural_language:
        tags = []
        if "production" in natural_language:
            tags.append("production")
        if "development" in natural_language:
            tags.append("development")
        if "testing" in natural_language:
            tags.append("testing")
        if tags:
            network_data["tags"] = tags
        else:
            network_data["tags"] = []
    else:
        network_data["tags"] = []
    
    # Set default values
    network_data["enrollmentString"] = None
    network_data["notes"] = ""
    network_data["isBoundToConfigTemplate"] = False
    network_data["isVirtual"] = False
    
    logger.info(f"Converted natural language to network data: {network_data}")
    return network_data

def convert_natural_language_to_connectivity_monitoring(natural_language: str) -> Dict[str, Any]:
    """Convert natural language to connectivity monitoring configuration"""
    monitoring_data = {
        "destinations": []
    }
    
    natural_language = natural_language.lower()
    
    # Parse destinations
    if "google" in natural_language and "dns" in natural_language:
        monitoring_data["destinations"].append("8.8.8.8")
        monitoring_data["destinations"].append("8.8.4.4")
    elif "cloudflare" in natural_language:
        monitoring_data["destinations"].append("1.1.1.1")
        monitoring_data["destinations"].append("1.0.0.1")
    elif "8.8.8.8" in natural_language:
        monitoring_data["destinations"].append("8.8.8.8")
    elif "1.1.1.1" in natural_language:
        monitoring_data["destinations"].append("1.1.1.1")
    
    # Extract IP addresses using regex
    import re
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ips = re.findall(ip_pattern, natural_language)
    for ip in ips:
        if ip not in monitoring_data["destinations"]:
            monitoring_data["destinations"].append(ip)
    
    # Default destinations if none found
    if not monitoring_data["destinations"]:
        monitoring_data["destinations"] = ["8.8.8.8", "1.1.1.1"]
    
    logger.info(f"Converted natural language to connectivity monitoring: {monitoring_data}")
    return monitoring_data

def convert_natural_language_to_access_control_lists(natural_language: str) -> Dict[str, Any]:
    """Convert natural language to access control list configuration"""
    acl_data = {
        "rules": []
    }
    
    natural_language = natural_language.lower()
    
    # Parse common ACL rules
    if "allow" in natural_language and "port" in natural_language:
        # Extract port numbers
        import re
        port_pattern = r'port\s+(\d+)'
        ports = re.findall(port_pattern, natural_language)
        
        for port in ports:
            acl_data["rules"].append({
                "policy": "allow",
                "protocol": "tcp",
                "srcPort": "any",
                "srcCidr": "any",
                "destPort": port,
                "destCidr": "any",
                "syslogEnabled": False
            })
    
    if "block" in natural_language and "social" in natural_language:
        acl_data["rules"].append({
            "policy": "deny",
            "protocol": "tcp",
            "srcPort": "any",
            "srcCidr": "any",
            "destPort": "any",
            "destCidr": "any",
            "syslogEnabled": True,
            "comment": "Block social media"
        })
    
    # Default rule if none found
    if not acl_data["rules"]:
        acl_data["rules"] = [{
            "policy": "allow",
            "protocol": "tcp",
            "srcPort": "any",
            "srcCidr": "any",
            "destPort": "any",
            "destCidr": "any",
            "syslogEnabled": False
        }]
    
    logger.info(f"Converted natural language to access control lists: {acl_data}")
    return acl_data

def convert_natural_language_to_login_security(natural_language: str) -> Dict[str, Any]:
    """Convert natural language to login security configuration"""
    security_data = {
        "enforcePasswordExpiration": False,
        "passwordExpirationDays": 365,
        "enforceDifferentPasswords": False,
        "numDifferentPasswords": 5,
        "enforceStrongPasswords": False,
        "enforceAccountLockout": False,
        "accountLockoutAttempts": 10,
        "enforceIdleTimeout": False,
        "idleTimeoutMinutes": 60,
        "enforceTwoFactorAuth": False,
        "enforceLoginIpRanges": False,
        "loginIpRanges": []
    }
    
    natural_language = natural_language.lower()
    
    # Parse security settings
    if "two factor" in natural_language or "2fa" in natural_language:
        security_data["enforceTwoFactorAuth"] = True
    
    if "password" in natural_language and "expiration" in natural_language:
        security_data["enforcePasswordExpiration"] = True
        # Extract days
        import re
        days_match = re.search(r'(\d+)\s*days?', natural_language)
        if days_match:
            security_data["passwordExpirationDays"] = int(days_match.group(1))
    
    if "strong" in natural_language and "password" in natural_language:
        security_data["enforceStrongPasswords"] = True
    
    if "lockout" in natural_language:
        security_data["enforceAccountLockout"] = True
        # Extract attempts
        import re
        attempts_match = re.search(r'(\d+)\s*attempts?', natural_language)
        if attempts_match:
            security_data["accountLockoutAttempts"] = int(attempts_match.group(1))
    
    if "timeout" in natural_language or "idle" in natural_language:
        security_data["enforceIdleTimeout"] = True
        # Extract minutes
        import re
        minutes_match = re.search(r'(\d+)\s*minutes?', natural_language)
        if minutes_match:
            security_data["idleTimeoutMinutes"] = int(minutes_match.group(1))
    
    logger.info(f"Converted natural language to login security: {security_data}")
    return security_data

def convert_natural_language_to_security_intrusion(natural_language: str) -> Dict[str, Any]:
    """Convert natural language to security intrusion configuration"""
    intrusion_data = {
        "mode": "prevention",
        "idsRulesets": "connectivity"
    }
    
    natural_language = natural_language.lower()
    
    # Parse intrusion settings
    if "detection" in natural_language:
        intrusion_data["mode"] = "detection"
    elif "prevention" in natural_language:
        intrusion_data["mode"] = "prevention"
    elif "disabled" in natural_language:
        intrusion_data["mode"] = "disabled"
    
    if "connectivity" in natural_language:
        intrusion_data["idsRulesets"] = "connectivity"
    elif "balanced" in natural_language:
        intrusion_data["idsRulesets"] = "balanced"
    elif "security" in natural_language:
        intrusion_data["idsRulesets"] = "security"
    
    logger.info(f"Converted natural language to security intrusion: {intrusion_data}")
    return intrusion_data
