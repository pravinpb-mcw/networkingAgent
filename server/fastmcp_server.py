"""
FastMCP server exposing Cisco Meraki tools.

This wraps the existing async tool functions under FastMCP's decorator API
so clients can connect over stdio using the Model Context Protocol.
"""

import os
import asyncio
import logging
from typing import Any, Dict

from dotenv import load_dotenv

# FastMCP
try:
    from fastmcp import FastMCP
except Exception as e:  # pragma: no cover
    raise RuntimeError("fastmcp is required. Install with `pip install fastmcp`.") from e

# Local imports (keep relative and absolute fallback like existing server)
try:
    from .get_organizations import get_organizations
    from .get_network_clients import get_network_clients
    from .get_network_traffic import get_network_traffic
    from .get_device_loss_and_latency_history import get_device_loss_and_latency_history
    from .get_network_vpn_stats import get_network_vpn_stats
    from .get_network_events import get_network_events
    from .get_network_settings import get_network_settings
    from .update_network_settings import update_network_settings
    from .update_appliance_settings import update_appliance_settings
    from .get_organization_uplinks_statuses import get_organization_uplinks_statuses
    from .update_uplink import update_uplink
    from .get_network_group_policies import get_network_group_policies
    from .create_network_wireless_settings import create_network_wireless_settings
    from .update_network_group_policy import update_network_group_policy
    from .get_organization_networks import get_organization_networks
    from .create_organization_network import create_organization_network
    from .get_connectivity_monitoring import get_connectivity_monitoring_destinations
    from .get_access_control_lists import get_network_access_control_lists
    from .get_login_security import get_organization_login_security
    from .get_security_intrusion import get_network_security_intrusion
    from .update_connectivity_monitoring import update_connectivity_monitoring_destinations
    from .update_access_control_lists import update_network_access_control_lists
    from .update_login_security import update_organization_login_security
    from .update_security_intrusion import update_network_security_intrusion
except Exception:
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
    from create_organization_network import create_organization_network
    from get_connectivity_monitoring import get_connectivity_monitoring_destinations
    from get_access_control_lists import get_network_access_control_lists
    from get_login_security import get_organization_login_security
    from get_security_intrusion import get_network_security_intrusion
    from update_connectivity_monitoring import update_connectivity_monitoring_destinations
    from update_access_control_lists import update_network_access_control_lists
    from update_login_security import update_organization_login_security
    from update_security_intrusion import update_network_security_intrusion


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastmcp-meraki")

USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"


mcp = FastMCP("cisco-meraki-observability-fastmcp")


# Read-only tools
@mcp.tool(description="Get Cisco Meraki organizations")
async def get_organizations_tool() -> Any:
    return await get_organizations()


@mcp.tool(description="Get clients connected to the network")
async def get_network_clients_tool() -> Any:
    return await get_network_clients()


@mcp.tool(description="Get network traffic analysis")
async def get_network_traffic_tool() -> Any:
    return await get_network_traffic()


@mcp.tool(description="Get device loss and latency history")
async def get_device_loss_and_latency_history_tool() -> Any:
    return await get_device_loss_and_latency_history()


@mcp.tool(description="Get organization VPN stats")
async def get_organization_vpn_stats_tool() -> Any:
    return await get_network_vpn_stats()


@mcp.tool(description="Get network events")
async def get_network_events_tool() -> Any:
    return await get_network_events()


@mcp.tool(description="Get network-wide configuration settings")
async def get_network_settings_tool() -> Any:
    return await get_network_settings()


@mcp.tool(description="Get organization uplinks statuses")
async def get_organization_uplinks_statuses_tool() -> Any:
    return await get_organization_uplinks_statuses()


@mcp.tool(description="Get network group policies")
async def get_network_group_policies_tool() -> Any:
    return await get_network_group_policies()


@mcp.tool(description="Get connectivity monitoring destinations")
async def get_connectivity_monitoring_destinations_tool(network_id: str | None = None) -> Any:
    return await get_connectivity_monitoring_destinations(network_id, use_mock=USE_MOCK)


@mcp.tool(description="Get network access control lists")
async def get_network_access_control_lists_tool(network_id: str | None = None) -> Any:
    return await get_network_access_control_lists(network_id, use_mock=USE_MOCK)


@mcp.tool(description="Get organization login security settings")
async def get_organization_login_security_tool(organization_id: str | None = None) -> Any:
    return await get_organization_login_security(organization_id, use_mock=USE_MOCK)


@mcp.tool(description="Get network security intrusion settings")
async def get_network_security_intrusion_tool(network_id: str | None = None) -> Any:
    return await get_network_security_intrusion(network_id, use_mock=USE_MOCK)


# Mutating tools
@mcp.tool(description="Update network-wide configuration settings")
async def update_network_settings_tool(settings_data: str) -> Any:
    return await update_network_settings(settings_data, use_mock=USE_MOCK)


@mcp.tool(description="Update appliance settings including degradedLinks status")
async def update_appliance_settings_tool(settings_data: str) -> Any:
    return await update_appliance_settings(settings_data, use_mock=USE_MOCK)


@mcp.tool(description="Move devices between WAN interfaces (wan1/wan2/wan3)")
async def update_uplink_tool(uplink_data: str) -> Any:
    return await update_uplink(uplink_data, use_mock=USE_MOCK)


@mcp.tool(description="Create network appliance settings")
async def create_network_appliance_settings_tool(settings_data: str) -> Any:
    from .create_network_appliance_settings import create_network_appliance_settings as _create
    return await _create(settings_data, use_mock=USE_MOCK)


@mcp.tool(description="Create network wireless settings")
async def create_network_wireless_settings_tool(settings_data: str) -> Any:
    return await create_network_wireless_settings(settings_data, use_mock=USE_MOCK)


@mcp.tool(description="Update user group policy by ID")
async def update_network_group_policy_tool(policy_id: str, policy_data: str | dict) -> Any:
    return await update_network_group_policy(policy_id, policy_data, use_mock=USE_MOCK)


@mcp.tool(description="Get organization networks")
async def get_organization_networks_tool(organization_id: str | None = None) -> Any:
    return await get_organization_networks(organization_id, use_mock=USE_MOCK)


@mcp.tool(description="Create organization network")
async def create_organization_network_tool(network_data: str | dict, organization_id: str | None = None) -> Any:
    return await create_organization_network(network_data, organization_id, use_mock=USE_MOCK)


@mcp.tool(description="Update connectivity monitoring destinations")
async def update_connectivity_monitoring_destinations_tool(monitoring_data: str | dict, network_id: str | None = None) -> Any:
    return await update_connectivity_monitoring_destinations(monitoring_data, network_id, use_mock=USE_MOCK)


@mcp.tool(description="Update network ACLs")
async def update_network_access_control_lists_tool(acl_data: str | dict, network_id: str | None = None) -> Any:
    return await update_network_access_control_lists(acl_data, network_id, use_mock=USE_MOCK)


@mcp.tool(description="Update organization login security settings")
async def update_organization_login_security_tool(security_data: str | dict, organization_id: str | None = None) -> Any:
    return await update_organization_login_security(security_data, organization_id, use_mock=USE_MOCK)


@mcp.tool(description="Update network security intrusion settings")
async def update_network_security_intrusion_tool(intrusion_data: str | dict, network_id: str | None = None) -> Any:
    return await update_network_security_intrusion(intrusion_data, network_id, use_mock=USE_MOCK)


def run() -> None:
    mcp.run()


if __name__ == "__main__":
    run()


