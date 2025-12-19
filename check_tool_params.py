"""
Check which tool calls are failing parameter validation
"""
import json
from pathlib import Path

# Import the validator
import sys
sys.path.insert(0, str(Path(__file__).parent / "eval"))
from phoenix_tool_validators import TOOL_REQUIRED_PARAMS, evaluate_tool_parameters

# Check recent Agent 1 traces
print("\n" + "="*80)
print("CHECKING TOOL PARAMETER COMPLETENESS")
print("="*80 + "\n")

# Simulate checking traces (we'll read from a sample or check the actual validator logic)
print("Required parameters for each tool:")
print("-" * 80)
for tool_name, params in TOOL_REQUIRED_PARAMS.items():
    if params:
        print(f"{tool_name}: {params}")
    else:
        print(f"{tool_name}: (no params required)")

print("\n" + "="*80)
print("\nCommon issues that cause 76% pass rate:")
print("-" * 80)
print("1. Tools not in TOOL_REQUIRED_PARAMS dict → counted as failures")
print("2. Parameters with None values → counted as missing")
print("3. Parameters in nested objects → not extracted properly")
print("4. Tool calls during errors → incomplete parameters")

print("\n" + "="*80)
print("\nChecking which tools might be missing from the dict:")
print("-" * 80)

# Common MCP tools that might be called
common_tools = [
    "get_organizations",
    "get_organization_networks", 
    "get_organization_devices",
    "get_network_clients",
    "get_network_events",
    "get_wireless_failed_connections",
    "get_organization_uplinks_statuses",
    "list_tools",
    "call_tool"
]

for tool in common_tools:
    if tool not in TOOL_REQUIRED_PARAMS:
        print(f"❌ MISSING: {tool}")
    else:
        print(f"✅ Present: {tool}")

print("\n" + "="*80)
print("\nRECOMMENDATION:")
print("-" * 80)
print("Check Phoenix dashboard for specific tool calls with missing params.")
print("Look for tools with label='fail' in tool_parameters_complete evaluation.")
print("Add any missing tools to TOOL_REQUIRED_PARAMS dict.")
print("="*80)
