"""
Cisco Meraki API Client
Shared client for interacting with Cisco Meraki Dashboard API
"""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("meraki-client")

class MerakiAPIClient:
    """Client for interacting with Cisco Meraki Dashboard API"""
    
    def __init__(self, api_key: str = None, base_url: str = None, use_mock: bool = False):
        # Keep constructor signature for backward compatibility, but support
        # method-based routing (GET -> Meraki, POST/PUT/DELETE -> localhost mock)

        # API key (may be None if only using mock for writes)
        self.api_key = api_key or os.getenv("MERAKI_API_KEY")

        # Base URLs for real Meraki and local mock
        # Preserve original behavior if a single base_url was passed in
        self.real_base_url = os.getenv("BASE_URL", "https://api.meraki.com/api/v1")
        self.mock_base_url = os.getenv("MOCK_BASE_URL", "http://127.0.0.1:5000")
        self.base_url = base_url or (self.mock_base_url if use_mock else self.real_base_url)
        self.use_mock = use_mock

        # Headers for real vs mock
        self.headers_real = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            # Only add API key header when available
            self.headers_real["X-Cisco-Meraki-API-Key"] = self.api_key
        self.headers_mock = {
            "Content-Type": "application/json"
        }
        
        # Load other configuration from .env
        self.network_id = os.getenv("NETWORK_ID")
        self.organization_id = os.getenv("ORGANIZATION_ID")
        self.serial = os.getenv("SERIAL")
        self.ip = os.getenv("IP")
        self.product_type = os.getenv("PRODUCT_TYPE")
        # Handle TIMESPAN with better error handling
        timespan_str = os.getenv("TIMESPAN", "86400")
        try:
            self.timespan = int(timespan_str)
        except (ValueError, TypeError):
            # If TIMESPAN is not a valid integer, use default
            self.timespan = 86400
            logger.warning(f"Invalid TIMESPAN value '{timespan_str}', using default 86400")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None, method: str = "GET", data: Optional[Dict] = None, tool_name: str = None) -> Dict[str, Any]:
        """Make HTTP request with method-based routing.

        - GET -> real Meraki API (requires MERAKI_API_KEY)
        - POST/PUT/DELETE -> localhost mock server
        """
        # Optional global overrides
        force_mock = os.getenv("FORCE_MOCK_ALL", "false").lower() == "true"
        force_real = os.getenv("FORCE_REAL_ALL", "false").lower() == "true"

        if force_real:
            base = self.real_base_url
            headers = self.headers_real
        elif force_mock:
            base = self.mock_base_url
            headers = self.headers_mock
        else:
            if method.upper() == "GET":
                base = self.real_base_url
                headers = self.headers_real
                if not self.api_key:
                    raise ValueError("MERAKI_API_KEY not found in environment or .env file for GET requests")
            else:
                base = self.mock_base_url
                headers = self.headers_mock

        url = f"{base}{endpoint}"

        # Log GET requests to show which tool is being used
        if method.upper() == "GET" and tool_name:
            logger.info(f"🔍 GET API CALL: Using tool '{tool_name}' to fetch data from endpoint: {endpoint}")

        async with httpx.AsyncClient() as client:
            try:
                method_upper = method.upper()
                if method_upper == "GET":
                    response = await client.get(url, headers=headers, params=params or {})
                elif method_upper == "PUT":
                    response = await client.put(url, headers=headers, json=data or {})
                elif method_upper == "POST":
                    response = await client.post(url, headers=headers, json=data or {})
                elif method_upper == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise Exception(f"API request failed: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise Exception(f"Request failed: {str(e)}")

    async def get_network_clients(self, network_id: str = None, timespan: int = None) -> List[Dict[str, Any]]:
        """Get clients connected to a network"""
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file. Please create a .env file with NETWORK_ID=your_network_id")
        span = timespan or self.timespan
        params = {"timespan": span}
        return await self._make_request(f"/networks/{net_id}/clients", params, tool_name="get_network_clients")
    
    async def get_network_traffic(self, network_id: str = None, timespan: int = None) -> List[Dict[str, Any]]:
        """Get network traffic analysis"""
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        span = timespan or self.timespan
        params = {"timespan": span}
        return await self._make_request(f"/networks/{net_id}/traffic", params, tool_name="get_network_traffic")
    
    async def get_device_loss_and_latency_history(self, serial: str = None, ip: str = None) -> List[Dict[str, Any]]:
        """Get device loss and latency history"""
        device_serial = serial or self.serial
        device_ip = ip or self.ip
        if not device_serial:
            raise ValueError("SERIAL not found in .env file. Please create a .env file with SERIAL=your_device_serial")
        if not device_ip:
            raise ValueError("IP not found in .env file. Please create a .env file with IP=your_device_ip")
        params = {"ip": device_ip}
        return await self._make_request(f"/devices/{device_serial}/lossAndLatencyHistory", params, tool_name="get_device_loss_and_latency_history")
    
    async def get_organization_vpn_stats(self, organization_id: str = None, timespan: int = None) -> List[Dict[str, Any]]:
        """Get organization VPN statistics"""
        org_id = organization_id or self.organization_id
        if not org_id:
            raise ValueError("ORGANIZATION_ID not found in .env file")
        span = timespan or self.timespan
        params = {"timespan": span}
        return await self._make_request(f"/organizations/{org_id}/appliance/vpn/stats", params, tool_name="get_organization_vpn_stats")
    
    async def get_network_events(self, network_id: str = None, product_type: str = None) -> List[Dict[str, Any]]:
        """Get network events"""
        net_id = network_id or self.network_id
        prod_type = product_type or self.product_type
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file. Please create a .env file with NETWORK_ID=your_network_id")
        if not prod_type:
            raise ValueError("PRODUCT_TYPE not found in .env file. Please create a .env file with PRODUCT_TYPE=appliance")
        params = {"productType": prod_type}
        return await self._make_request(f"/networks/{net_id}/events", params, tool_name="get_network_events") 

    async def get_network_settings(self, network_id: str = None) -> Dict[str, Any]:
        """Get network-wide configuration settings"""
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        return await self._make_request(f"/networks/{net_id}/settings", tool_name="get_network_settings")

    async def get_organization_uplinks_statuses(
        self,
        organization_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get device uplink status and failover information for an organization.

        This calls the Meraki endpoint:
        GET /organizations/{organizationId}/uplinks/statuses

        Minimal implementation without filters. If you need filters (e.g., by
        networkIds or serials), extend this method to accept and forward those
        query parameters.
        """
        org_id = organization_id or self.organization_id
        if not org_id:
            raise ValueError("ORGANIZATION_ID not found in .env file")

        # No query params by default; add filters here if needed
        return await self._make_request(f"/organizations/{org_id}/uplinks/statuses", tool_name="get_organization_uplinks_statuses")

    async def create_network_appliance_settings(
        self, 
        network_id: str = None, 
        settings_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create new network appliance settings
        
        POST /networks/{networkId}/appliance/settings
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not settings_data:
            raise ValueError("settings_data is required")
        
        return await self._make_request(
            f"/networks/{net_id}/appliance/settings",
            method="POST",
            data=settings_data
        )


    async def create_network_wireless_settings(
        self, 
        network_id: str = None, 
        settings_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create new network wireless settings
        
        POST /networks/{networkId}/wireless/settings
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not settings_data:
            raise ValueError("settings_data is required")
        
        return await self._make_request(
            f"/networks/{net_id}/wireless/settings",
            method="POST",
            data=settings_data
        )

    async def update_network_settings(
        self, 
        network_id: str = None, 
        settings_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update network-wide configuration settings
        
        PUT /networks/{networkId}/settings
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not settings_data:
            raise ValueError("settings_data is required")
        
        return await self._make_request(
            f"/networks/{net_id}/settings",
            method="PUT",
            data=settings_data
        )

    async def create_network_group_policy(
        self, 
        network_id: str = None, 
        policy_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new group policy for a network
        
        PUT /networks/{networkId}/groupPolicies
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not policy_data:
            raise ValueError("policy_data is required")
        
        return await self._make_request(
            f"/networks/{net_id}/groupPolicies",
            method="PUT",
            data=policy_data
        )

    async def update_network_group_policy(
        self, 
        policy_id: str,
        network_id: str = None, 
        policy_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update an existing group policy for a network
        
        PUT /networks/{networkId}/groupPolicies/{policyId}
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not policy_data:
            raise ValueError("policy_data is required")
        if not policy_id:
            raise ValueError("policy_id is required")
        
        return await self._make_request(
            f"/networks/{net_id}/groupPolicies/{policy_id}",
            method="PUT",
            data=policy_data
        )

    async def delete_network_group_policy(
        self, 
        policy_id: str,
        network_id: str = None
    ) -> Dict[str, Any]:
        """Delete an existing group policy for a network
        
        DELETE /networks/{networkId}/groupPolicies/{policyId}
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not policy_id:
            raise ValueError("policy_id is required")
        
        return await self._make_request(
            f"/networks/{net_id}/groupPolicies/{policy_id}",
            method="DELETE"
        )

    async def get_organization_networks(
        self, 
        organization_id: str = None
    ) -> Dict[str, Any]:
        """Get all networks in an organization
        
        GET /organizations/{organizationId}/networks
        """
        org_id = organization_id or self.organization_id
        if not org_id:
            raise ValueError("ORGANIZATION_ID not found in .env file")
        
        return await self._make_request(
            f"/organizations/{org_id}/networks",
            method="GET",
            tool_name="get_organization_networks"
        )

    async def create_organization_network(
        self, 
        organization_id: str = None,
        network_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new network in an organization
        
        POST /organizations/{organizationId}/networks
        """
        org_id = organization_id or self.organization_id
        if not org_id:
            raise ValueError("ORGANIZATION_ID not found in .env file")
        if not network_data:
            raise ValueError("network_data is required")
        
        return await self._make_request(
            f"/organizations/{org_id}/networks",
            method="POST",
            data=network_data
        )

    # Connectivity Monitoring
    async def get_connectivity_monitoring_destinations(
        self, 
        network_id: str = None
    ) -> Dict[str, Any]:
        """Get connectivity monitoring destinations for a network
        
        GET /networks/{networkId}/appliance/connectivityMonitoringDestinations
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        
        return await self._make_request(
            f"/networks/{net_id}/appliance/connectivityMonitoringDestinations",
            method="GET",
            tool_name="get_connectivity_monitoring_destinations"
        )

    async def update_connectivity_monitoring_destinations(
        self, 
        network_id: str = None,
        monitoring_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update connectivity monitoring destinations for a network
        
        PUT /networks/{networkId}/appliance/connectivityMonitoringDestinations
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not monitoring_data:
            raise ValueError("monitoring_data is required")
        
        return await self._make_request(
            f"/networks/{net_id}/appliance/connectivityMonitoringDestinations",
            method="PUT",
            data=monitoring_data
        )

    # Access Control Lists
    async def get_network_access_control_lists(
        self, 
        network_id: str = None
    ) -> Dict[str, Any]:
        """Get network access control lists
        
        GET /networks/{networkId}/switch/accessControlLists
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        
        return await self._make_request(
            f"/networks/{net_id}/switch/accessControlLists",
            method="GET",
            tool_name="get_network_access_control_lists"
        )

    async def update_network_access_control_lists(
        self, 
        network_id: str = None,
        acl_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update network access control lists
        
        PUT /networks/{networkId}/switch/accessControlLists
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not acl_data:
            raise ValueError("acl_data is required")
        
        return await self._make_request(
            f"/networks/{net_id}/switch/accessControlLists",
            method="PUT",
            data=acl_data
        )

    # Login Security
    async def get_organization_login_security(
        self, 
        organization_id: str = None
    ) -> Dict[str, Any]:
        """Get organization login security settings
        
        GET /organizations/{organizationId}/loginSecurity
        """
        org_id = organization_id or self.organization_id
        if not org_id:
            raise ValueError("ORGANIZATION_ID not found in .env file")
        
        return await self._make_request(
            f"/organizations/{org_id}/loginSecurity",
            method="GET",
            tool_name="get_organization_login_security"
        )

    async def update_organization_login_security(
        self, 
        organization_id: str = None,
        security_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update organization login security settings
        
        PUT /organizations/{organizationId}/loginSecurity
        """
        org_id = organization_id or self.organization_id
        if not org_id:
            raise ValueError("ORGANIZATION_ID not found in .env file")
        if not security_data:
            raise ValueError("security_data is required")
        
        return await self._make_request(
            f"/organizations/{org_id}/loginSecurity",
            method="PUT",
            data=security_data
        )

    # Security Intrusion
    async def get_network_security_intrusion(
        self, 
        network_id: str = None
    ) -> Dict[str, Any]:
        """Get network security intrusion settings
        
        GET /networks/{id}/appliance/security/intrusion
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        
        return await self._make_request(
            f"/networks/{net_id}/appliance/security/intrusion",
            method="GET",
            tool_name="get_network_security_intrusion"
        )

    async def update_network_security_intrusion(
        self, 
        network_id: str = None,
        intrusion_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update network security intrusion settings
        
        PUT /networks/{id}/appliance/security/intrusion
        """
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not intrusion_data:
            raise ValueError("intrusion_data is required")
        
        return await self._make_request(
            f"/networks/{net_id}/appliance/security/intrusion",
            method="PUT",
            data=intrusion_data
        )