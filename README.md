# Cisco Meraki MCP Server

A Model Context Protocol (MCP) server that exposes 5 specific Cisco Meraki Dashboard API endpoints as tools for network observability.

## Features

This MCP server provides the following tools:

1. **get_network_clients** - Retrieve clients connected to your configured network
2. **get_network_traffic** - Analyze network traffic patterns and bandwidth usage
3. **get_device_loss_and_latency_history** - Get loss and latency history for your configured device
4. **get_organization_vpn_stats** - Retrieve VPN statistics for your configured organization
5. **get_network_events** - Retrieve events for your configured network

## Project Structure

```
networkingAgent/
├── main.py                 # Main entry point
├── .env                    # Environment variables (create this file)
├── server/
│   ├── __init__.py        # Package initialization
│   ├── meraki_client.py   # Shared Meraki API client
│   ├── meraki_server.py   # Main MCP server that combines all tools
│   ├── get_network_clients.py
│   ├── get_network_traffic.py
│   ├── get_device_loss_and_latency_history.py
│   ├── get_network_vpn_stats.py
│   └── get_network_events.py
├── requirements.txt
└── README.md
```

## Modular Design

Each API endpoint is implemented as a separate tool file in the `server/` directory:

- **meraki_client.py**: Shared API client for all tools
- **get_network_clients.py**: Tool for retrieving network clients
- **get_network_traffic.py**: Tool for retrieving network traffic data
- **get_device_loss_and_latency_history.py**: Tool for retrieving device loss and latency history
- **get_network_vpn_stats.py**: Tool for retrieving organization VPN statistics
- **get_network_events.py**: Tool for retrieving network events

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with your configuration:
   ```bash
   # Cisco Meraki API Configuration
   MERAKI_API_KEY=your_meraki_api_key_here
   BASE_URL=https://api.meraki.com/api/v1
   NETWORK_ID=your_network_id
   ORGANIZATION_ID=your_organization_id
   SERIAL=your_device_serial
   IP=your_device_ip
   PRODUCT_TYPE=your_product_type
   TIMESPAN=86400
   ```

3. Run the server:
   ```bash
   python main.py
   ```

## Usage

The server exposes tools that can be called via MCP. Each tool returns structured JSON data with:

- Tool name and timestamp
- Configuration values used (from .env)
- API response data
- Summary information

### Example Tool Calls

```python
# Get network clients (uses NETWORK_ID and TIMESPAN from .env)
await get_network_clients()

# Get network traffic (uses NETWORK_ID and TIMESPAN from .env)
await get_network_traffic()

# Get device loss and latency history (uses SERIAL and IP from .env)
await get_device_loss_and_latency_history()

# Get organization VPN statistics (uses ORGANIZATION_ID and TIMESPAN from .env)
await get_organization_vpn_stats()

# Get network events (uses NETWORK_ID and PRODUCT_TYPE from .env)
await get_network_events()
```

## Configuration

All tools automatically use the configuration from your `.env` file:

- **MERAKI_API_KEY**: Your Cisco Meraki Dashboard API key
- **BASE_URL**: Meraki API base URL (default: https://api.meraki.com/api/v1)
- **NETWORK_ID**: Your network ID
- **ORGANIZATION_ID**: Your organization ID
- **SERIAL**: Your device serial number
- **IP**: Your device IP address
- **PRODUCT_TYPE**: Your product type
- **TIMESPAN**: Time span in seconds for data queries (default: 86400 = 24 hours)

## API Requirements

- Valid Cisco Meraki Dashboard API key
- Network access to api.meraki.com
- Appropriate permissions for the API endpoints being accessed

## Error Handling

Each tool includes comprehensive error handling for:
- Missing configuration in .env file
- Network connectivity issues
- API authentication failures
- Invalid parameters
- API rate limiting
- Device not found errors

## Logging

The server uses structured logging with different loggers for:
- Main server operations
- Individual tool operations
- API client operations

Logs include timestamps, error details, and operation summaries.
