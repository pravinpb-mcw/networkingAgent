# Cisco Meraki MCP Server

A Model Context Protocol (MCP) server that exposes 5 specific Cisco Meraki Dashboard API endpoints as tools for network observability.

## Features

This MCP server provides the following tools:

### Monitoring Tools (6):
1. **get_network_clients** - Retrieve clients connected to your configured network
2. **get_network_traffic** - Analyze network traffic patterns and bandwidth usage
3. **get_device_loss_and_latency_history** - Get loss and latency history for your configured device
4. **get_organization_vpn_stats** - Retrieve VPN statistics for your configured organization
5. **get_network_events** - Retrieve events for your configured network
6. **get_organization_uplinks_statuses** - Get device uplink status and failover information

### Configuration Tools (6):
7. **create_network_appliance_settings** - Create network infrastructure settings (DHCP, VLAN, etc.)
8. **create_network_wireless_settings** - Create WiFi/SSID settings with traffic shaping check
9. **handle_traffic_shaping_response** - Handle traffic shaping decisions during wireless setup
10. **continue_wireless_update_after_policy** - Continue wireless update after group policy
11. **update_network_group_policy** - Update existing user group policies
12. **delete_network_group_policy** - Delete existing user group policies

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

## Enhanced Traffic Shaping Check

The `create_network_wireless_settings` tool now includes intelligent traffic shaping management:

### How It Works:
1. **Automatic Detection**: Checks `mock_data/networks.json` for existing group policies
2. **Traffic Shaping Analysis**: Identifies policies with `trafficShapingEnabled=false`
3. **User Interaction**: Asks users if they want to enable traffic shaping
4. **Flexible Options**: Users can enable for all policies, skip, or enable for specific policies
5. **Seamless Integration**: Continues with wireless settings after traffic shaping decisions

### User Response Options:
- `YES` or `ENABLE` - Enable traffic shaping for all policies with disabled status
- `NO` or `SKIP` - Continue without enabling traffic shaping
- `POLICY_ID:YES` - Enable traffic shaping for a specific policy (e.g., `policy_1:YES`)

### Example Workflow:
```bash
# 1. User calls wireless settings
create_network_wireless_settings("Enable wireless with SSID MyNetwork")

# 2. Tool checks existing policies and asks:
"Found 2 group policy(ies) with trafficShapingEnabled=false:
   • Policy ID: policy_1
   • Policy ID: policy_2
Do you want to enable traffic shaping for these policies?"

# 3. User responds:
"YES"

# 4. Tool enables traffic shaping and continues with wireless setup
```

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
