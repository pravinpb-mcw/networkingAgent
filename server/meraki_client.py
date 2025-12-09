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
# Try to find .env in parent directories
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv() # Fallback to default search

logger = logging.getLogger("meraki-client")

class MerakiAPIClient:
    """Client for interacting with Cisco Meraki Dashboard API"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        # If no API key provided, try to get it from environment
        if api_key is None:
            api_key = os.getenv("MERAKI_API_KEY")
            if not api_key:
                raise ValueError("MERAKI_API_KEY not found in environment or .env file")
        
        # If no base_url provided, get it from environment
        if base_url is None:
            base_url = os.getenv("BASE_URL", "https://api.meraki.com/api/v1")
        
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-Cisco-Meraki-API-Key": api_key,
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
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Meraki API with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params or {})
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise Exception(f"API request failed: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise Exception(f"Request failed: {str(e)}")

    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Get all organizations"""
        return await self._make_request("/organizations")

    async def get_network_clients(self, network_id: str = None, timespan: int = None) -> List[Dict[str, Any]]:
        """Get clients connected to a network"""
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        span = timespan or self.timespan
        params = {"timespan": span}
        return await self._make_request(f"/networks/{net_id}/clients", params)
    
    async def get_network_traffic(self, network_id: str = None, timespan: int = None) -> List[Dict[str, Any]]:
        """Get network traffic analysis"""
        net_id = network_id or self.network_id
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        span = timespan or self.timespan
        params = {"timespan": span}
        return await self._make_request(f"/networks/{net_id}/traffic", params)
    
    async def get_device_loss_and_latency_history(self, serial: str = None, ip: str = None) -> List[Dict[str, Any]]:
        """Get device loss and latency history"""
        device_serial = serial or self.serial
        device_ip = ip or self.ip
        if not device_serial:
            raise ValueError("SERIAL not found in .env file")
        if not device_ip:
            raise ValueError("IP not found in .env file")
        params = {"ip": device_ip}
        return await self._make_request(f"/devices/{device_serial}/lossAndLatencyHistory", params)
    
    async def get_organization_vpn_stats(self, organization_id: str = None, timespan: int = None) -> List[Dict[str, Any]]:
        """Get organization VPN statistics"""
        org_id = organization_id or self.organization_id
        if not org_id:
            raise ValueError("ORGANIZATION_ID not found in .env file")
        span = timespan or self.timespan
        params = {"timespan": span}
        return await self._make_request(f"/organizations/{org_id}/appliance/vpn/stats", params)
    
    async def get_network_events(self, network_id: str = None, product_type: str = None) -> List[Dict[str, Any]]:
        """Get network events"""
        net_id = network_id or self.network_id
        prod_type = product_type or self.product_type
        if not net_id:
            raise ValueError("NETWORK_ID not found in .env file")
        if not prod_type:
            raise ValueError("PRODUCT_TYPE not found in .env file")
        params = {"productType": prod_type}
        return await self._make_request(f"/networks/{net_id}/events", params) 
