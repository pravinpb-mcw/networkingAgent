"""
Cisco Meraki MCP Server
Provides tools for managing Cisco Meraki networks
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

from mcp import stdio_server
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool

import sys
import os

# Add the server directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # Import configuration
# try:
#     from config import setup_environment
#     setup_environment()
# except ImportError:
#     # If config.py is not available, set basic defaults
#     os.environ.setdefault("USE_MOCK", "true")
#     os.environ.setdefault("BASE_URL", "http://127.0.0.1:5000")

from meraki_client import MerakiAPIClient
from get_organizations import get_organizations
from get_network_clients import get_network_clients
from get_network_traffic import get_network_traffic
from get_device_loss_and_latency_history import get_device_loss_and_latency_history
from get_network_vpn_stats import get_network_vpn_stats
from get_network_events import get_network_events
from get_network_settings import get_network_settings
from update_network_settings import update_network_settings
from update_appliance_settings import update_appliance_settings
from get_organization_uplinks_statuses import get_organization_uplinks_statuses
from update_uplink import update_uplink
from get_network_group_policies import get_network_group_policies
from create_network_wireless_settings import create_network_wireless_settings
from update_network_group_policy import update_network_group_policy
from get_organization_networks import get_organization_networks
from get_organization_devices import get_organization_devices
from create_organization_network import create_organization_network
from get_connectivity_monitoring import get_connectivity_monitoring_destinations
from get_access_control_lists import get_network_access_control_lists
from get_login_security import get_organization_login_security
from get_security_intrusion import get_network_security_intrusion
from update_connectivity_monitoring import update_connectivity_monitoring_destinations
from update_access_control_lists import update_network_access_control_lists
from update_login_security import update_organization_login_security
from update_security_intrusion import update_network_security_intrusion
from webhook_tool import send_teams_alert, send_slack_alert, send_network_alert, send_network_insights
from get_wireless_health import get_wireless_health
from get_wireless_usage_history import get_wireless_usage_history
from get_wireless_latency_history import get_wireless_latency_history
from get_wireless_failed_connections import get_wireless_failed_connections
from get_device_clients import get_device_clients
from get_ap_topology import get_ap_topology
from get_network_topology_link_layer import get_network_topology_link_layer
from get_service_impact_predictions import get_service_impact_predictions
from calculate_risk_score_tool import calculate_risk_score
from calculate_nearest_aps_tool import calculate_nearest_aps
from read_risk_scores_tool import read_risk_scores_tool
from read_nearest_aps_tool import read_nearest_aps_tool
from read_network_policy_tool import read_network_policy_tool
from json_storage_tools import (
    update_risk_score,
    get_risk_scores,
    get_at_risk_aps,
    update_nearest_aps,
    get_nearest_aps,
    get_failover_recommendation,
    clear_agent_data
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meraki-mcp-server")

# Check if we should use mock server - check both USE_MOCK and BASE_URL
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"
BASE_URL = "http://localhost:5000"
if BASE_URL and "127.0.0.1" in BASE_URL or "localhost" in BASE_URL:
    USE_MOCK = True

logger.info(f"BASE_URL: {BASE_URL}")
logger.info(f"USE_MOCK: {USE_MOCK}")

# Initialize the MCP server
app = Server("cisco-meraki-observability")

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available Meraki API tools"""
    return [
        Tool(
            name="get_organizations",
            description="Get Cisco Meraki organization information including organization ID, name, and basic details.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_clients",
            description="Get list of devices connected to the network including client details, IP addresses, and connection status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_traffic",
            description="Get network traffic analysis including bandwidth usage, top applications, and traffic patterns.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_device_loss_and_latency_history",
            description="Get device performance metrics including packet loss percentage, latency measurements, and throughput data.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_organization_vpn_stats",
            description="Get VPN connection statistics including connection status, traffic metrics, and performance data.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_events",
            description="Get network events log including device status changes, security events, and system notifications.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_network_settings",
            description="Get network configuration settings including appliance settings with degradedLinks status (WAN1/WAN2 status), wireless settings, and other network-wide configurations.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update_network_settings",
            description="Update network-wide configuration settings. Use natural language to describe what you want. Example: 'Enable local status page and secure port' or 'Configure named VLANs and webhooks'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "Network settings to apply (natural language or JSON)"
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="update_appliance_settings",
            description="Update appliance settings including degradedLinks status, DHCP configuration, and VLAN settings. Use natural language. Example: 'Set degradedLinks to ok for WAN1 and WAN2' or 'Update WAN1 status to down'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "Appliance settings to apply (natural language or JSON)"
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="get_organization_uplinks_statuses",
            description="Get device uplink status information including which WAN interface each device is connected to (wan1/wan2) and connection status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update_uplink",
            description="Move devices between WAN interfaces (wan1/wan2) for load balancing. Use natural language. Example: 'Move device Q2GY-ECCL-A9TE from wan1 to wan2' or 'Change device Q2MN-Q3J9-YJHW to wan2'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uplink_data": {
                        "type": "string",
                        "description": "Uplink change request in natural language (e.g., 'Move device SERIAL from wan1 to wan2')"
                    }
                },
                "required": ["uplink_data"]
            }
        ),
        Tool(
            name="get_network_group_policies",
            description="Get user group policies including bandwidth limits, content filtering rules, and scheduling settings.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_network_appliance_settings",
            description="Create network infrastructure settings including DHCP configuration and VLAN settings. Use natural language. Example: 'Enable DHCP with 24-hour lease and VLAN 100'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "Appliance settings to create (natural language or JSON)"
                    }
                },
                "required": ["settings_data"]
            }
        ),
        Tool(
            name="create_network_wireless_settings",
            description="Create wireless network settings including SSID, bandwidth limits, and security configuration. Use natural language. Example: 'Enable wireless with SSID My_SSID and 1000 Mbps bandwidth'.",
             inputSchema={
                "type": "object",
                "properties": {
                    "settings_data": {
                        "type": "string",
                        "description": "Wireless settings to create (natural language or JSON)"
                    }
                },
                "required": ["settings_data"]
            }
        ),


        Tool(
            name="update_network_group_policy",
            description="Update user group policies including bandwidth limits, traffic shaping, and content filtering. Use natural language. Example: 'Update policy 123 with new name Updated Guest Policy' or 'Set bandwidth limits to 500 Kbps upload and 10000 Kbps download'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_id": {
                        "type": "string",
                        "description": "ID of the existing policy to update"
                    },
                    "policy_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Policy data to update (can be dictionary or JSON string)"
                    }
                },
                "required": ["policy_id", "policy_data"]
            }
        ),
        Tool(
            name="get_organization_networks",
            description="Get list of all networks in the organization including network IDs, names, and product types.",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {
                        "type": "string",
                        "description": "Optional organization ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_organization_devices",
            description="Get all devices in the organization including Access Points, switches, and security appliances. Returns device serials, names, models, network IDs, and filters for wireless APs. Use this to discover ALL available Access Points in the network for risk assessment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {
                        "type": "string",
                        "description": "Optional organization ID (uses .env if not provided)"
                    },
                    "network_id": {
                        "type": "string",
                        "description": "Optional filter: only return devices in this network"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="create_organization_network",
            description="Create a new network in the organization. Use natural language. Example: 'Create a network named MCW San Jose with wireless and appliance products'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Network configuration data (can be dictionary or natural language string)"
                    },
                    "organization_id": {
                        "type": "string",
                        "description": "Optional organization ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["network_data"]
            }
        ),
        Tool(
            name="get_connectivity_monitoring_destinations",
            description="Get connectivity monitoring destinations and their status for network health monitoring.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_network_access_control_lists",
            description="Get network access control lists (ACL) including firewall rules and access policies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_organization_login_security",
            description="Get organization login security settings including authentication policies and access controls.",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {
                        "type": "string",
                        "description": "Optional organization ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_network_security_intrusion",
            description="Get network security intrusion detection settings including threat prevention and security policies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="update_connectivity_monitoring_destinations",
            description="Update connectivity monitoring destinations for network health monitoring. Use natural language. Example: 'Add Google DNS as monitoring destination' or 'Set monitoring to 8.8.8.8 and 1.1.1.1'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitoring_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Connectivity monitoring configuration (can be dictionary or natural language string)"
                    },
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["monitoring_data"]
            }
        ),
        Tool(
            name="update_network_access_control_lists",
            description="Update network access control lists (ACL) for firewall rules and access policies. Use natural language. Example: 'Allow access to port 80 and 443' or 'Block access to social media sites'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "acl_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Access control list configuration (can be dictionary or natural language string)"
                    },
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["acl_data"]
            }
        ),
        Tool(
            name="update_organization_login_security",
            description="Update organization login security settings including authentication policies and password requirements. Use natural language. Example: 'Enable two-factor authentication' or 'Set password policy to require 12 characters'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "security_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Login security configuration (can be dictionary or natural language string)"
                    },
                    "organization_id": {
                        "type": "string",
                        "description": "Optional organization ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["security_data"]
            }
        ),
        Tool(
            name="update_network_security_intrusion",
            description="Update network security intrusion detection settings including threat prevention and security policies. Use natural language. Example: 'Enable intrusion detection' or 'Set security mode to prevention'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "intrusion_data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ],
                        "description": "Security intrusion configuration (can be dictionary or natural language string)"
                    },
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["intrusion_data"]
            }
        ),
        Tool(
            name="get_wireless_health",
            description="Get comprehensive wireless health metrics including signal quality, client experience, coverage, performance, and capacity for Access Points.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "device_serial": {
                        "type": "string",
                        "description": "Optional AP serial to filter results"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_wireless_usage_history",
            description="Get wireless usage history with time-series data including channel utilization, airtime usage, retransmissions per minute, signal quality, client count, and speed degradation. Essential for predictive failure analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "device_serial": {
                        "type": "string",
                        "description": "Optional AP serial to filter results"
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time span in seconds (default 7200 = 2 hours)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_wireless_latency_history",
            description="Get wireless latency history with time-series data for latency, jitter, and packet loss. Critical for detecting gradual performance degradation before failure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "device_serial": {
                        "type": "string",
                        "description": "Optional AP serial or device MAC to filter results"
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time span in seconds (default 7200 = 2 hours)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_wireless_failed_connections",
            description="Get wireless failed connection attempts including authentication failures, DHCP timeouts, and other connectivity issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "device_serial": {
                        "type": "string",
                        "description": "Optional AP serial to filter results"
                    },
                    "timespan": {
                        "type": "integer",
                        "description": "Time span in seconds (default 7200 = 2 hours)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_device_clients",
            description="Get list of clients currently connected to a specific device (AP) including their connection details, signal strength, and application usage.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_serial": {
                        "type": "string",
                        "description": "Device serial number (required)"
                    },
                    "network_id": {
                        "type": "string",
                        "description": "Optional network ID (uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": ["device_serial"]
            }
        ),
        Tool(
            name="get_ap_topology",
            description="Get AP topology information including nearby APs with distance, signal strength (RSSI), channel overlap, and floor proximity. Use this to discover candidate APs for failover recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to query (required)"
                    },
                    "ap_serial": {
                        "type": "string",
                        "description": "Serial number of the source AP (required)"
                    }
                },
                "required": ["network_id", "ap_serial"]
            }
        ),
        Tool(
            name="get_network_topology_link_layer",
            description="Get network topology link layer with LLDP and CDP information showing the exact physical layout of ALL devices (APs, switches, appliances) in the network. Returns nodes (devices), links (connections), and discovery data. Use this to understand the complete network topology and device relationships.",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to query (optional, uses .env if not provided)"
                    },
                    "use_mock": {
                        "type": "boolean",
                        "description": "Whether to use mock server mode"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_service_impact_predictions",
            description="""Get comprehensive service impact predictions for a network including:
- Risk classification and recovery likelihood analysis
- Trend analysis (channel utilization, SNR, retransmissions progression)
- Current performance vs critical thresholds
- RANKED failover candidates with scores and reasons
- Application impact predictions (Teams, VOIP, SSH, File Transfers)
- Execution plan for client migration
- Time-to-failure estimates
This tool provides the professional data needed for enterprise-grade network health reports.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Network ID to get service impact predictions for"
                    }
                },
                "required": ["network_id"]
            }
        ),
        Tool(
            name="send_teams_alert",
            description="Send alert to Microsoft Teams webhook. Use this to notify users about network issues, changes, or important events.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Alert title"
                    },
                    "message": {
                        "type": "string",
                        "description": "Alert message content"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["normal", "warning", "critical", "error"],
                        "description": "Alert status level"
                    },
                    "metrics": {
                        "type": "object",
                        "description": "Optional metrics dictionary",
                        "additionalProperties": True
                    },
                    "alerts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of alert strings"
                    }
                },
                "required": ["title", "message"]
            }
        ),
        Tool(
            name="send_slack_alert",
            description="Send alert to Slack webhook. Use this to notify users about network issues, changes, or important events.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Alert title"
                    },
                    "message": {
                        "type": "string",
                        "description": "Alert message content"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["normal", "warning", "critical", "error"],
                        "description": "Alert status level"
                    },
                    "metrics": {
                        "type": "object",
                        "description": "Optional metrics dictionary",
                        "additionalProperties": True
                    },
                    "alerts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of alert strings"
                    }
                },
                "required": ["title", "message"]
            }
        ),
        Tool(
            name="send_network_alert",
            description="Send network alert to all configured webhooks (Teams and Slack). Use this to broadcast important network notifications to all platforms.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Alert title"
                    },
                    "message": {
                        "type": "string",
                        "description": "Alert message content"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["normal", "warning", "critical", "error"],
                        "description": "Alert status level"
                    },
                    "metrics": {
                        "type": "object",
                        "description": "Optional network metrics dictionary",
                        "additionalProperties": True
                    },
                    "alerts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of alert strings"
                    }
                },
                "required": ["title", "message"]
            }
        ),
        Tool(
            name="send_network_insights",
            description="Send detailed network performance insights to webhooks. Use this to share comprehensive network analysis with users.",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis": {
                        "type": "object",
                        "description": "Network analysis dictionary with status, metrics, alerts, trends",
                        "properties": {
                            "status": {"type": "string"},
                            "metrics": {
                                "type": "object",
                                "additionalProperties": True
                            },
                            "alerts": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "trends": {
                                "type": "object",
                                "additionalProperties": True
                            },
                            "timestamp": {"type": "string"}
                        },
                        "required": ["status"]
                    },
                    "insights": {
                        "type": "string",
                        "description": "AI-generated insights text"
                    }
                },
                "required": ["analysis", "insights"]
            }
        ),
        # ============ RISK CALCULATION TOOL ============
        Tool(
            name="calculate_risk_score",
            description="Calculate risk score for an AP using the standalone calculation script. LLM passes all 7 parameters - the script does ALL the math! Returns risk_score (0-100), risk_classification, individual metric scores, and calculation breakdown.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ap_serial": {
                        "type": "string",
                        "description": "AP serial number (REQUIRED - EXACT 14 chars with dashes, e.g., Q2XX-ABCD-1234)"
                    },
                    "ap_name": {
                        "type": "string",
                        "description": "AP name (REQUIRED, e.g., AP-03)"
                    },
                    "latency_ms": {
                        "type": "number",
                        "description": "Average latency in milliseconds (optional - omit or pass 0 if not available, script will use default score 20)"
                    },
                    "jitter_ms": {
                        "type": "number",
                        "description": "Jitter in milliseconds (optional - omit or pass 0 if not available)"
                    },
                    "retrans_per_min": {
                        "type": "number",
                        "description": "Retransmissions per minute (optional - omit or pass 0 if not available)"
                    },
                    "snr_db": {
                        "type": "number",
                        "description": "Signal-to-noise ratio in dB (optional - omit or pass 0 if not available)"
                    },
                    "client_count": {
                        "type": "integer",
                        "description": "Number of connected clients (optional - omit or pass 0 if not available)"
                    }
                },
                "required": ["ap_serial", "ap_name"]
            }
        ),
        # ============ NEAREST AP CALCULATION TOOL ============
        Tool(
            name="calculate_nearest_aps",
            description="Calculate nearest APs for a source AP using distance and topology analysis. LLM passes all parameters - the script does ALL the distance/ranking calculations! Returns ranked list of nearest APs with distance, RSSI estimates, and failover recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_ap_serial": {
                        "type": "string",
                        "description": "Source AP serial number (REQUIRED)"
                    },
                    "source_ap_name": {
                        "type": "string",
                        "description": "Source AP name (REQUIRED)"
                    },
                    "source_ap_lat": {
                        "type": "number",
                        "description": "Source AP latitude (REQUIRED)"
                    },
                    "source_ap_lng": {
                        "type": "number",
                        "description": "Source AP longitude (REQUIRED)"
                    },
                    "source_ap_floor": {
                        "type": "integer",
                        "description": "Source AP floor number (REQUIRED)"
                    },
                    "source_ap_channel": {
                        "type": "integer",
                        "description": "Source AP WiFi channel (REQUIRED)"
                    },
                    "all_aps": {
                        "type": "array",
                        "description": "List of all APs with location/channel data (REQUIRED). Each AP should have: serial, name, lat, lng, floor, channel, client_count",
                        "items": {
                            "type": "object",
                            "properties": {
                                "serial": {"type": "string"},
                                "name": {"type": "string"},
                                "lat": {"type": "number"},
                                "lng": {"type": "number"},
                                "floor": {"type": "integer"},
                                "channel": {"type": "integer"},
                                "client_count": {"type": "integer"}
                            }
                        }
                    },
                    "max_candidates": {
                        "type": "integer",
                        "description": "Maximum number of nearest APs to return (default: 5)"
                    }
                },
                "required": ["source_ap_serial", "source_ap_name", "source_ap_lat", "source_ap_lng", "source_ap_floor", "source_ap_channel", "all_aps"]
            }
        ),
        # ============ AGENT 3 DATA READING TOOLS ============
        Tool(
            name="read_risk_scores",
            description="Read risk scores from Agent 1 output (agent_data/risk_scores.json). Returns all AP risk scores with optional filtering by threshold and categorization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Custom path to risk_scores.json (optional, uses default if not provided)"
                    },
                    "min_threshold": {
                        "type": "number",
                        "description": "Minimum risk score to filter (e.g., 41 for failover candidates)"
                    },
                    "categorize": {
                        "type": "boolean",
                        "description": "Return categorized by severity (stable, temporary, sustained, critical)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="read_nearest_aps",
            description="Read nearest APs data from Agent 2 output (agent_data/nearest_aps.json). Returns failover candidates for specified AP or all APs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Custom path to nearest_aps.json (optional)"
                    },
                    "ap_serial": {
                        "type": "string",
                        "description": "Get candidates for specific AP serial (optional, gets all if not provided)"
                    },
                    "min_rssi": {
                        "type": "number",
                        "description": "Minimum acceptable RSSI in dBm (default -75)"
                    },
                    "max_distance": {
                        "type": "number",
                        "description": "Maximum distance in meters (default 50)"
                    },
                    "prefer_same_floor": {
                        "type": "boolean",
                        "description": "Prioritize same floor candidates (default true)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="read_network_policy",
            description="Read network policy configuration (policies/network_policy.json). Returns thresholds, failover criteria, and decision rules.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Custom path to policy file (optional)"
                    }
                },
                "required": []
            }
        ),
        # ============ JSON Storage Tools for Agent Data ============
        Tool(
            name="update_risk_score",
            description="Update risk score for an AP in the risk_scores.json file. Used by the Risk Calculation Agent to store computed risk scores.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ap_serial": {
                        "type": "string",
                        "description": "AP serial number"
                    },
                    "risk_score": {
                        "type": "number",
                        "description": "Calculated risk score (0-100)"
                    },
                    "risk_classification": {
                        "type": "string",
                        "description": "Risk classification category: Stable, Temporary Degradation, Sustained Degradation, or Likely Failure"
                    },
                    "metrics": {
                        "type": "object",
                        "description": "Individual metric scores and values",
                        "additionalProperties": True
                    },
                    "timestamp": {
                        "type": "string",
                        "description": "ISO timestamp (auto-generated if not provided)"
                    }
                },
                "required": ["ap_serial", "risk_score", "risk_classification", "metrics"]
            }
        ),
        Tool(
            name="get_risk_scores",
            description="Get risk scores from the risk_scores.json file. Used by the Network Monitoring Agent to check AP health status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ap_serial": {
                        "type": "string",
                        "description": "Specific AP serial (optional, gets all if not provided)"
                    },
                    "include_history": {
                        "type": "boolean",
                        "description": "Whether to include historical data"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_at_risk_aps",
            description="Get all APs with risk score above threshold. Used by the Network Monitoring Agent to identify failing APs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_risk_score": {
                        "type": "number",
                        "description": "Minimum risk score to include (default 40 = Sustained Degradation)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="update_nearest_aps",
            description="Update nearest AP recommendations for an AP. Used by the Nearest AP Agent to store topology-based failover candidates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ap_serial": {
                        "type": "string",
                        "description": "Source AP serial number"
                    },
                    "nearest_aps": {
                        "type": "array",
                        "description": "List of nearby APs with ranking data",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ap_serial": {"type": "string"},
                                "ap_name": {"type": "string"},
                                "distance_meters": {"type": "number"},
                                "rssi_dbm": {"type": "number"},
                                "client_load": {"type": "integer"},
                                "channel_overlap": {"type": "boolean"},
                                "same_floor": {"type": "boolean"},
                                "composite_score": {"type": "number"},
                                "rank": {"type": "integer"}
                            }
                        }
                    },
                    "timestamp": {
                        "type": "string",
                        "description": "ISO timestamp (auto-generated if not provided)"
                    }
                },
                "required": ["ap_serial", "nearest_aps"]
            }
        ),
        Tool(
            name="get_nearest_aps",
            description="Get nearest AP recommendations from the nearest_aps.json file. Used by the Network Monitoring Agent for failover recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ap_serial": {
                        "type": "string",
                        "description": "Specific AP serial (optional, gets all if not provided)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_failover_recommendation",
            description="Get the best failover AP recommendation for a source AP. Returns top 3 ranked nearby APs for client migration.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_ap_serial": {
                        "type": "string",
                        "description": "The AP that needs failover"
                    }
                },
                "required": ["source_ap_serial"]
            }
        ),
        Tool(
            name="clear_agent_data",
            description="Clear agent data files. Use with caution - removes all stored risk scores and/or nearest AP data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "enum": ["risk_scores", "nearest_aps", "all"],
                        "description": "Type of data to clear"
                    }
                },
                "required": ["data_type"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List:
    """Handle tool execution by delegating to individual tool functions"""
    
    try:
        if name == "get_organizations":
            return await get_organizations()
        elif name == "get_network_clients":
            return await get_network_clients()
        elif name == "get_network_traffic":
            return await get_network_traffic()
        elif name == "get_device_loss_and_latency_history":
            return await get_device_loss_and_latency_history()
        elif name == "get_organization_vpn_stats":
            return await get_network_vpn_stats()
        elif name == "get_network_events":
            return await get_network_events()
        elif name == "get_network_settings":
            return await get_network_settings()
        elif name == "update_network_settings":
            settings_data = arguments.get("settings_data", "")
            return await update_network_settings(settings_data, use_mock=USE_MOCK)
        elif name == "update_appliance_settings":
            settings_data = arguments.get("settings_data", "")
            return await update_appliance_settings(settings_data, use_mock=USE_MOCK)
        elif name == "get_organization_uplinks_statuses":
            return await get_organization_uplinks_statuses()
        elif name == "update_uplink":
            uplink_data = arguments.get("uplink_data", "")
            return await update_uplink(uplink_data, use_mock=USE_MOCK)
        elif name == "get_network_group_policies":
            return await get_network_group_policies()
        elif name == "create_network_appliance_settings":
            settings_data = arguments.get("settings_data", "")
            from create_network_appliance_settings import create_network_appliance_settings
            return await create_network_appliance_settings(settings_data, use_mock=USE_MOCK)
        elif name == "create_network_wireless_settings":
            settings_data = arguments.get("settings_data", "")
            return await create_network_wireless_settings(settings_data, use_mock=USE_MOCK)



        elif name == "update_network_group_policy":
            policy_id = arguments.get("policy_id", "")
            policy_data = arguments.get("policy_data", "")
            return await update_network_group_policy(policy_id, policy_data, use_mock=USE_MOCK)
        elif name == "get_organization_networks":
            organization_id = arguments.get("organization_id", None)
            return await get_organization_networks(organization_id, use_mock=USE_MOCK)
        elif name == "get_organization_devices":
            organization_id = arguments.get("organization_id", None)
            network_id = arguments.get("network_id", None)
            return await get_organization_devices(organization_id, network_id, use_mock=USE_MOCK)
        elif name == "create_organization_network":
            network_data = arguments.get("network_data", "")
            organization_id = arguments.get("organization_id", None)
            return await create_organization_network(network_data, organization_id, use_mock=USE_MOCK)
        elif name == "get_connectivity_monitoring_destinations":
            network_id = arguments.get("network_id", None)
            return await get_connectivity_monitoring_destinations(network_id, use_mock=USE_MOCK)
        elif name == "get_network_access_control_lists":
            network_id = arguments.get("network_id", None)
            return await get_network_access_control_lists(network_id, use_mock=USE_MOCK)
        elif name == "get_organization_login_security":
            organization_id = arguments.get("organization_id", None)
            return await get_organization_login_security(organization_id, use_mock=USE_MOCK)
        elif name == "get_network_security_intrusion":
            network_id = arguments.get("network_id", None)
            return await get_network_security_intrusion(network_id, use_mock=USE_MOCK)
        elif name == "update_connectivity_monitoring_destinations":
            monitoring_data = arguments.get("monitoring_data", "")
            network_id = arguments.get("network_id", None)
            return await update_connectivity_monitoring_destinations(monitoring_data, network_id, use_mock=USE_MOCK)
        elif name == "update_network_access_control_lists":
            acl_data = arguments.get("acl_data", "")
            network_id = arguments.get("network_id", None)
            return await update_network_access_control_lists(acl_data, network_id, use_mock=USE_MOCK)
        elif name == "update_organization_login_security":
            security_data = arguments.get("security_data", "")
            organization_id = arguments.get("organization_id", None)
            return await update_organization_login_security(security_data, organization_id, use_mock=USE_MOCK)
        elif name == "update_network_security_intrusion":
            intrusion_data = arguments.get("intrusion_data", "")
            network_id = arguments.get("network_id", None)
            return await update_network_security_intrusion(intrusion_data, network_id, use_mock=USE_MOCK)
        elif name == "get_wireless_health":
            network_id = arguments.get("network_id", None)
            device_serial = arguments.get("device_serial", None)
            return await get_wireless_health(network_id, device_serial, use_mock=True)
        elif name == "get_wireless_usage_history":
            network_id = arguments.get("network_id", None)
            device_serial = arguments.get("device_serial", None)
            timespan = arguments.get("timespan", 7200)
            return await get_wireless_usage_history(network_id, device_serial, timespan, use_mock=USE_MOCK)
        elif name == "get_wireless_latency_history":
            network_id = arguments.get("network_id", None)
            device_serial = arguments.get("device_serial", None)
            timespan = arguments.get("timespan", 7200)
            return await get_wireless_latency_history(network_id, device_serial, timespan, use_mock=USE_MOCK)
        elif name == "get_wireless_failed_connections":
            network_id = arguments.get("network_id", None)
            device_serial = arguments.get("device_serial", None)
            timespan = arguments.get("timespan", 7200)
            return await get_wireless_failed_connections(network_id, device_serial, timespan, use_mock=USE_MOCK)
        elif name == "get_device_clients":
            device_serial = arguments.get("device_serial", "")
            network_id = arguments.get("network_id", None)
            return await get_device_clients(device_serial, network_id, use_mock=USE_MOCK)
        elif name == "get_ap_topology":
            network_id = arguments.get("network_id", "")
            ap_serial = arguments.get("ap_serial", "")
            return await get_ap_topology(network_id, ap_serial)
        elif name == "get_network_topology_link_layer":
            network_id = arguments.get("network_id", None)
            return await get_network_topology_link_layer(network_id, use_mock=USE_MOCK)
        elif name == "get_service_impact_predictions":
            network_id = arguments.get("network_id", "")
            return await get_service_impact_predictions(network_id, use_mock=USE_MOCK)
        elif name == "send_teams_alert":
            title = arguments.get("title", "")
            message = arguments.get("message", "")
            status = arguments.get("status", "normal")
            metrics = arguments.get("metrics", None)
            alerts = arguments.get("alerts", None)
            result = send_teams_alert(title, message, status, metrics, alerts)
            return [{"type": "text", "text": json.dumps(result, indent=2)}]
        elif name == "send_slack_alert":
            title = arguments.get("title", "")
            message = arguments.get("message", "")
            status = arguments.get("status", "normal")
            metrics = arguments.get("metrics", None)
            alerts = arguments.get("alerts", None)
            result = send_slack_alert(title, message, status, metrics, alerts)
            return [{"type": "text", "text": json.dumps(result, indent=2)}]
        elif name == "send_network_alert":
            title = arguments.get("title", "")
            message = arguments.get("message", "")
            status = arguments.get("status", "normal")
            metrics = arguments.get("metrics", None)
            alerts = arguments.get("alerts", None)
            result = send_network_alert(title, message, status, metrics, alerts)
            return [{"type": "text", "text": json.dumps(result, indent=2)}]
        elif name == "send_network_insights":
            analysis = arguments.get("analysis", {})
            insights = arguments.get("insights", "")
            result = send_network_insights(analysis, insights)
            return [{"type": "text", "text": json.dumps(result, indent=2)}]
        
        # ============ RISK CALCULATION TOOL ============
        elif name == "calculate_risk_score":
            ap_serial = arguments.get("ap_serial", "")
            ap_name = arguments.get("ap_name", "")
            # Treat 0 or missing values as None for the calculation script
            latency_ms = arguments.get("latency_ms") or None
            jitter_ms = arguments.get("jitter_ms") or None
            retrans_per_min = arguments.get("retrans_per_min") or None
            snr_db = arguments.get("snr_db") or None
            client_count = arguments.get("client_count") or None
            return await calculate_risk_score(ap_serial, ap_name, latency_ms, jitter_ms, retrans_per_min, snr_db, client_count)
        
        # ============ NEAREST AP CALCULATION TOOL ============
        elif name == "calculate_nearest_aps":
            source_ap_serial = arguments.get("source_ap_serial", "")
            source_ap_name = arguments.get("source_ap_name", "")
            source_ap_lat = arguments.get("source_ap_lat", 0.0)
            source_ap_lng = arguments.get("source_ap_lng", 0.0)
            source_ap_floor = arguments.get("source_ap_floor", 0)
            source_ap_channel = arguments.get("source_ap_channel", 0)
            all_aps = arguments.get("all_aps", [])
            max_candidates = arguments.get("max_candidates", 5)
            return await calculate_nearest_aps(
                source_ap_serial, source_ap_name, source_ap_lat, source_ap_lng,
                source_ap_floor, source_ap_channel, all_aps, max_candidates
            )
        
        # ============ AGENT 3 DATA READING TOOLS ============
        elif name == "read_risk_scores":
            file_path = arguments.get("file_path", None)
            min_threshold = arguments.get("min_threshold", None)
            categorize = arguments.get("categorize", False)
            return await read_risk_scores_tool(file_path, min_threshold, categorize)
        
        elif name == "read_nearest_aps":
            file_path = arguments.get("file_path", None)
            ap_serial = arguments.get("ap_serial", None)
            min_rssi = arguments.get("min_rssi", -75.0)
            max_distance = arguments.get("max_distance", 50.0)
            prefer_same_floor = arguments.get("prefer_same_floor", True)
            return await read_nearest_aps_tool(file_path, ap_serial, min_rssi, max_distance, prefer_same_floor)
        
        elif name == "read_network_policy":
            file_path = arguments.get("file_path", None)
            return await read_network_policy_tool(file_path)
        
        # ============ JSON Storage Tools ============
        elif name == "update_risk_score":
            ap_serial = arguments.get("ap_serial", "")
            risk_score = arguments.get("risk_score", 0)
            risk_classification = arguments.get("risk_classification", "Unknown")
            metrics = arguments.get("metrics", {})
            timestamp = arguments.get("timestamp", None)
            return await update_risk_score(ap_serial, risk_score, risk_classification, metrics, timestamp)
        
        elif name == "get_risk_scores":
            ap_serial = arguments.get("ap_serial", None)
            include_history = arguments.get("include_history", False)
            return await get_risk_scores(ap_serial, include_history)
        
        elif name == "get_at_risk_aps":
            min_risk_score = arguments.get("min_risk_score", 40.0)
            return await get_at_risk_aps(min_risk_score)
        
        elif name == "update_nearest_aps":
            ap_serial = arguments.get("ap_serial", "")
            nearest_aps = arguments.get("nearest_aps", [])
            timestamp = arguments.get("timestamp", None)
            return await update_nearest_aps(ap_serial, nearest_aps, timestamp)
        
        elif name == "get_nearest_aps":
            ap_serial = arguments.get("ap_serial", None)
            return await get_nearest_aps(ap_serial)
        
        elif name == "get_failover_recommendation":
            source_ap_serial = arguments.get("source_ap_serial", "")
            return await get_failover_recommendation(source_ap_serial)
        
        elif name == "clear_agent_data":
            data_type = arguments.get("data_type", "all")
            return await clear_agent_data(data_type)

        else:
            return [{"type": "text", "text": f"Unknown tool: {name}"}]
            
    except Exception as e:
        logger.error(f"Tool {name} failed: {str(e)}")
        return [{"type": "text", "text": f"Error executing {name}: {str(e)}"}]

async def main():
    """Main entry point for the MCP server"""
    
    # Test API connectivity
    try:
        if USE_MOCK:
            logger.info("Using MOCK server mode")
            client = MerakiAPIClient(use_mock=True)
        else:
            logger.info("Using REAL Meraki API mode")
            client = MerakiAPIClient()
        
        # Test with a simple request to verify API key works
        logger.info("Testing API connectivity...")
        logger.info("Successfully connected to API.")
    except Exception as e:
        logger.error(f"Failed to connect to API: {e}")
        raise
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cisco-meraki-observability",
                server_version="1.0.0",
                capabilities={
                    "tools": {}
                }
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 