# Networking Agent Troubleshooting Guide

## Connection Issues - "Connection closed" Error

If you're seeing "Connection closed" errors when trying to use the networking agent, follow these steps:

### Step 1: Run the Diagnostic Script

```bash
python restart_and_test.py
```

This script will:
- ✅ Set up environment variables
- ✅ Check required files
- ✅ Test server imports
- ✅ Verify mock data
- ✅ Create a .env file

### Step 2: Check Environment Variables

The agent needs these environment variables to work:

```bash
# Required for mock mode
USE_MOCK=true
BASE_URL=http://127.0.0.1:5000
MERAKI_API_KEY=demo_api_key_for_mock_mode
NETWORK_ID=main_network
ORGANIZATION_ID=demo_org_id

# Optional for real API mode
GEMINI_API_KEY=your_actual_gemini_key
```

### Step 3: Verify File Structure

Make sure these files exist:
```
networkingAgent/
├── server/
│   ├── meraki_server.py
│   ├── meraki_client.py
│   └── update_network_wireless_settings.py
├── mock_data/
│   ├── networks.json
│   └── common_data.json
├── mcp-inspector-config.json
└── .env (will be created by restart_and_test.py)
```

### Step 4: Test Individual Components

#### Test Server Import:
```bash
python -c "from server.meraki_server import app; print('Server import successful')"
```

#### Test Mock Data:
```bash
python -c "import json; json.load(open('mock_data/networks.json')); print('Mock data accessible')"
```

### Step 5: Start the Agent

After running the diagnostic script, try starting the agent:

```bash
# Option 1: MCP Client
python client/mcp_client.py

# Option 2: Dashboard
streamlit run dashboard.py
```

## Common Issues and Solutions

### Issue 1: Import Errors
**Error**: `ModuleNotFoundError: No module named 'server'`

**Solution**: 
- Make sure you're running from the project root directory
- Check that the `server/` directory exists
- Run `python restart_and_test.py` to fix path issues

### Issue 2: Missing Environment Variables
**Error**: `KeyError: 'MERAKI_API_KEY'`

**Solution**:
- Run `python restart_and_test.py` to create the .env file
- Or manually set environment variables

### Issue 3: Mock Data Not Found
**Error**: `FileNotFoundError: mock_data/networks.json`

**Solution**:
- Check that the `mock_data/` directory exists
- Verify `networks.json` and `common_data.json` are present
- Run `python restart_and_test.py` to verify file structure

### Issue 4: MCP Server Connection Failed
**Error**: `Connection closed` or `Failed to connect to MCP server`

**Solution**:
1. Check the MCP configuration in `mcp-inspector-config.json`
2. Verify Python path in the config file
3. Make sure all required packages are installed
4. Run `python restart_and_test.py` to diagnose issues

## Quick Fix Commands

```bash
# 1. Run diagnostic script
python restart_and_test.py

# 2. Install missing packages (if needed)
pip install streamlit plotly pandas nest-asyncio mcp

# 3. Test the agent
python client/mcp_client.py
```

## What Was Fixed

The recent cleanup removed unused functions from `update_network_wireless_settings.py`:

### Removed Functions:
- ❌ `execute_wireless_and_group_policy_sync` (unused)
- ❌ `update_network_wireless_settings_complete` (unused)

### Kept Functions:
- ✅ `check_existing_group_policies_for_traffic_shaping` (used)
- ✅ `update_network_wireless_settings` (main function)
- ✅ `handle_traffic_shaping_response` (used)
- ✅ `update_network_wireless_settings_with_group_policy` (used)
- ✅ `continue_wireless_update_after_policy` (used)

The import error in `meraki_server.py` has been fixed to remove the reference to the deleted function.

## Still Having Issues?

If you're still experiencing problems after following these steps:

1. Check the console output for specific error messages
2. Verify all required Python packages are installed
3. Make sure you're using Python 3.8+ 
4. Try running the test script: `python test_server_connection.py`

For additional help, check the logs in the console output for specific error messages.
