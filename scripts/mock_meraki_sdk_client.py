#!/usr/bin/env python3
"""Example Meraki Dashboard SDK client wired to the local mock server.

This script exercises the predictive-telemetry routes exposed by ``mock_server.py``
so you can validate data flows (devices, wireless health, uplinks, topology, and
service-impact forecasts) without hitting the real Meraki cloud.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Callable, Dict, Iterable, Optional, Sequence

import meraki
from meraki.exceptions import APIError

DEFAULT_BASE_URL = "http://127.0.0.1:5000"
DEFAULT_API_KEY = os.getenv("MERAKI_DASHBOARD_API_KEY", "mock-api-key")
DEFAULT_ORG_ID = os.getenv("MERAKI_ORG_ID", "999781")
DEFAULT_NETWORK_ID = os.getenv("MERAKI_NETWORK_ID", "L_3947405073390239794")
DEFAULT_DEVICE_SERIAL = os.getenv("MERAKI_DEVICE_SERIAL", "Q2XX-ABCD-1234")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query the local Meraki mock server using the official SDK"
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Mock server base URL")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="Dashboard API key (mock)")
    parser.add_argument("--organization-id", default=DEFAULT_ORG_ID, help="Organization ID")
    parser.add_argument("--network-id", default=DEFAULT_NETWORK_ID, help="Network ID for telemetry")
    parser.add_argument("--device-serial", default=DEFAULT_DEVICE_SERIAL, help="Device serial to inspect")
    parser.add_argument("--max-items", type=int, default=3, help="Preview this many list rows per call")
    return parser.parse_args()


def pretty_preview(payload: Any, max_items: int) -> str:
    if isinstance(payload, list):
        sample: Iterable[Any]
        sample = payload[:max_items]
        body: Any = {
            "sample": sample,
            "total": len(payload)
        }
    else:
        body = payload
    return json.dumps(body, indent=2, default=str)


def safe_call(label: str, func: Callable[..., Any], max_items: int, *args, **kwargs) -> Any:
    print(f"\n=== {label} ===")
    try:
        data = func(*args, **kwargs)
        print(pretty_preview(data, max_items))
        return data
    except APIError as api_err:
        print(f"Meraki API error: {api_err}")
        return None
    except Exception as exc:  # pragma: no cover - diagnostic print
        print(f"Unexpected error while calling {label}: {exc}")
        return None


def custom_get(
    dashboard: meraki.DashboardAPI,
    resource: str,
    params: Optional[Dict[str, Any]] = None,
    *,
    operation: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
) -> Any:
    resource_path = resource if resource.startswith("/") else f"/{resource}"
    metadata = {
        "tags": list(tags) if tags else ["mock-demo"],
        "operation": operation or resource_path,
    }
    return dashboard._session.get(  # type: ignore[attr-defined]
        metadata,
        resource_path,
        params=params,
    )


def main() -> None:
    args = parse_args()

    dashboard = meraki.DashboardAPI(
        api_key=args.api_key,
        base_url=args.base_url,
        print_console=False,
        suppress_logging=True,
        single_request_timeout=10,
        maximum_retries=1,
    )

    org_id = args.organization_id
    network_id = args.network_id
    serial = args.device_serial
    preview = args.max_items
    appliance_serial = serial

    safe_call(
        "Organization Devices",
        dashboard.organizations.getOrganizationDevices,
        preview,
        org_id,
    )

    safe_call("Device Detail", dashboard.devices.getDevice, preview, serial)
    safe_call(
        "Wireless Status",
        lambda s: custom_get(
            dashboard,
            f"devices/{s}/wireless/status",
            operation="getDeviceWirelessStatus",
            tags=["devices", "wireless"],
        ),
        preview,
        serial,
    )

    safe_call(
        "Wireless Latency History",
        lambda nid: custom_get(
            dashboard,
            f"networks/{nid}/wireless/latencyHistory",
            operation="getNetworkWirelessLatencyHistory",
            tags=["networks", "wireless"],
        ),
        preview,
        network_id,
    )
    safe_call(
        "Wireless Failed Connections",
        lambda nid: custom_get(
            dashboard,
            f"networks/{nid}/wireless/failedConnections",
            operation="getNetworkWirelessFailedConnections",
            tags=["networks", "wireless"],
        ),
        preview,
        network_id,
    )
    safe_call(
        "Wireless Usage History",
        lambda nid: custom_get(
            dashboard,
            f"networks/{nid}/wireless/usageHistory",
            operation="getNetworkWirelessUsageHistory",
            tags=["networks", "wireless"],
        ),
        preview,
        network_id,
    )
    safe_call(
        "Wireless Health",
        lambda nid: custom_get(
            dashboard,
            f"networks/{nid}/wireless/health",
            operation="getNetworkWirelessHealth",
            tags=["networks", "wireless"],
        ),
        preview,
        network_id,
    )

    safe_call("Network Clients", dashboard.networks.getNetworkClients, preview, network_id)
    safe_call("Device Clients", dashboard.devices.getDeviceClients, preview, serial)
    safe_call(
        "Wireless Events",
        dashboard.networks.getNetworkEvents,
        preview,
        network_id,
        productType="wireless",
    )

    org_uplinks = safe_call(
        "Org Appliance Uplink Statuses",
        lambda oid: custom_get(
            dashboard,
            f"organizations/{oid}/uplinks/statuses",
            operation="getOrganizationUplinksStatuses",
            tags=["organizations", "appliance"],
        ),
        preview,
        org_id,
    )

    if isinstance(org_uplinks, list) and org_uplinks:
        candidate = next((item for item in org_uplinks if item.get("networkId") == network_id), org_uplinks[0])
        appliance_serial = candidate.get("serial", appliance_serial)

    safe_call(
        "Device Loss & Latency",
        lambda s: custom_get(
            dashboard,
            f"devices/{s}/lossAndLatencyHistory",
            params={"ip": "8.8.8.8"},
            operation="getDeviceLossAndLatencyHistory",
            tags=["devices"],
        ),
        preview,
        appliance_serial,
    )
    safe_call(
        "Device Uplink",
        lambda s: custom_get(
            dashboard,
            f"devices/{s}/uplink",
            operation="getDeviceUplink",
            tags=["devices", "appliance"],
        ),
        preview,
        appliance_serial,
    )
    safe_call(
        "Device Uplink Settings",
        lambda s: custom_get(
            dashboard,
            f"devices/{s}/appliance/uplinks/settings",
            operation="getDeviceApplianceUplinksSettings",
            tags=["devices", "appliance"],
        ),
        preview,
        appliance_serial,
    )

    safe_call(
        "Layer2 Topology",
        lambda nid: custom_get(
            dashboard,
            f"networks/{nid}/topologyLinkLayer",
            operation="getNetworkTopologyLinkLayer",
            tags=["networks"],
        ),
        preview,
        network_id,
    )
    safe_call(
        "Floor Plans",
        lambda nid: custom_get(
            dashboard,
            f"networks/{nid}/floorPlans",
            operation="getNetworkFloorPlans",
            tags=["networks"],
        ),
        preview,
        network_id,
    )
    safe_call("Traffic Analytics", dashboard.networks.getNetworkTraffic, preview, network_id)

    safe_call(
        "Service Impact Prediction",
        lambda nid: custom_get(
            dashboard,
            f"networks/{nid}/serviceImpact",
            operation="getNetworkServiceImpactPrediction",
            tags=["networks"],
        ),
        preview,
        network_id,
    )

    print("\nDemo complete. Point additional analytics at the JSON preview above.")


if __name__ == "__main__":
    main()
