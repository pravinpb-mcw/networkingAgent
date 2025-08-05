# Setup Guide for Cisco Meraki MCP Server with LLM Integration

## Understanding Your Project

This is an **MCP (Model Context Protocol) server** that provides tools for interacting with Cisco Meraki Dashboard API, with **Gemini LLM integration** for automated insights. It's designed to be used by MCP clients, not as a standalone application.

## Step 1: Create Environment File

Create a `.env` file in the project root with your API configuration:

```bash
# Cisco Meraki API Configuration
MERAKI_API_KEY=your_meraki_api_key_here
BASE_URL=https://api.meraki.com/api/v1
NETWORK_ID=your_network_id
ORGANIZATION_ID=your_organization_id
SERIAL=your_device_serial
IP=your_device_ip
PRODUCT_TYPE=appliance
TIMESPAN=86400

# Gemini LLM Configuration
GEMINI_API_KEY=your_gemini_api_key_here
```

### How to get these values:

1. **MERAKI_API_KEY**: 
   - Go to your Meraki Dashboard
   - Navigate to Organization > Settings > API access
   - Generate a new API key

2. **NETWORK_ID**: 
   - In Meraki Dashboard, go to any network
   - The network ID is in the URL: `https://dashboard.meraki.com/n/network_id/...`

3. **ORGANIZATION_ID**: 
   - In Meraki Dashboard, go to Organization > Settings
   - The organization ID is in the URL: `https://dashboard.meraki.com/o/organization_id/...`

4. **SERIAL**: 
   - Device serial number (found on the device or in Dashboard)

5. **IP**: 
   - Device IP address

6. **PRODUCT_TYPE**: 
   - Common values: `appliance`, `switch`, `wireless`, `systemsManager`, `camera`, `cellularGateway`

7. **GEMINI_API_KEY**: 
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key for Gemini

## Step 2: Test Your Setup

Run the test scripts to verify everything works:

```bash
# Test basic Meraki tools
python test/test_tools.py

# Test LLM integration
python test/test_llm_integration.py
```

This will:
- Test your API connection
- Run all 5 tools and show their JSON output
- Test Gemini LLM integration
- Verify your configuration is correct

## Step 3: Understanding How to Use

### Option A: Direct Tool Testing
Use the test scripts to run tools directly:

```bash
# Test all tools with full JSON output
python test/test_tools.py

# Or run the demo for a quick overview
python test/demo.py
```

### Option B: LLM Integration (Recommended)
Run automated insights collection with Gemini:

```bash
# Single run - collect data and get insights
python llm_integration/meraki_insights.py

# Scheduled runs - every 10 minutes
python llm_integration/scheduler.py
```

### Option C: MCP Server Mode
Run as an MCP server (requires MCP client):

```bash
python main.py
```

The MCP server will:
- Start and wait for MCP client connections
- Not execute tools automatically
- Only execute tools when requested by an MCP client

## Available Tools

1. **get_network_clients** - Get connected devices
2. **get_network_traffic** - Analyze traffic patterns  
3. **get_device_loss_and_latency_history** - Device performance data
4. **get_organization_vpn_stats** - VPN statistics
5. **get_network_events** - Network events and alerts

## LLM Integration Features

- **Automated Data Collection**: Collects data from all 5 Meraki tools
- **Gemini AI Analysis**: Uses Google's Gemini Pro model for insights
- **Security Analysis**: Identifies security concerns and unusual patterns
- **Performance Analysis**: Detects performance issues and bottlenecks
- **Actionable Recommendations**: Provides specific actions to take
- **Scheduled Collection**: Runs every 10 minutes automatically
- **Insights Storage**: Saves insights to JSON files with timestamps

## Troubleshooting

### "MERAKI_API_KEY not found"
- Make sure you created the `.env` file
- Check that the API key is correct

### "NETWORK_ID not found" 
- Add your network ID to the `.env` file
- Verify the network ID is correct

### "API request failed"
- Check your internet connection
- Verify your API key has the right permissions
- Make sure the network/organization IDs are correct

### "GEMINI_API_KEY not found"
- Add your Gemini API key to the `.env` file
- Get a key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### "Failed to get insights from Gemini"
- Check your internet connection
- Verify your Gemini API key is valid
- Check the Gemini API quota and limits

## Next Steps

1. Create your `.env` file with real values
2. Run `python test/test_tools.py` to test basic functionality
3. Run `python test/test_llm_integration.py` to test LLM integration
4. Start automated insights collection: `python llm_integration/scheduler.py` 