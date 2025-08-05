"""
Cisco Meraki MCP Server Package
Exposes 5 key Meraki API endpoints as MCP tools for network observability
"""

from .meraki_client import MerakiAPIClient
from .get_network_clients import get_network_clients
from .get_network_traffic import get_network_traffic
from .get_device_loss_and_latency_history import get_device_loss_and_latency_history
from .get_network_vpn_stats import get_organization_vpn_stats
from .get_network_events import get_network_events

__all__ = [
    "MerakiAPIClient",
    "get_network_clients",
    "get_network_traffic",
    "get_device_loss_and_latency_history",
    "get_organization_vpn_stats",
    "get_network_events"
] 