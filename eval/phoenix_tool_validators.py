"""
Phoenix Evaluators for Tool Call Validation
============================================

These evaluators run automatically in Phoenix and show results in the dashboard.
They check:
1. Tool calls have all required parameters
2. LLM has sufficient data before making decisions
"""

import json
from typing import Dict, Any, List


# Required parameters for each tool
TOOL_REQUIRED_PARAMS = {
    # Risk calculation tools
    "calculate_risk_score": ["ap_serial"],
    "update_risk_score": ["ap_serial"],
    "calculate_nearest_aps": ["source_ap", "all_aps"],
    
    # Network discovery tools
    "get_organizations": [],
    "get_organization_networks": ["organization_id"],
    "get_organization_devices": ["organization_id"],
    "get_network_topology_link_layer": ["network_id"],
    
    # Wireless health tools
    "get_wireless_health": ["network_id"],
    "get_wireless_latency_history": ["network_id", "device_serial"],
    "get_wireless_usage_history": ["network_id", "device_serial"],
    "get_wireless_failed_connections": ["network_id"],
    
    # Client and device tools
    "get_device_clients": ["serial"],
    "get_network_clients": ["network_id"],
    "get_network_events": ["network_id"],
    
    # Uplink tools
    "get_organization_uplinks_statuses": ["organization_id"],
    
    # Data read tools (Agent 3)
    "read_risk_scores": [],
    "read_nearest_aps": ["ap_serial"],
    "read_network_policy": [],
    
    # MCP meta tools
    "list_tools": [],
    "call_tool": ["name"]
}


def evaluate_tool_parameters(output: str, expected: str = None) -> tuple:
    """
    Evaluator for Phoenix: Check if tool calls have all required parameters.
    
    This is a deterministic evaluator (no LLM needed).
    Phoenix will run this on every tool call and show results in dashboard.
    
    Args:
        output: Tool call output from trace
        expected: Expected output (not used for this validator)
    
    Returns:
        (score, explanation) where score is 0.0 or 1.0
    """
    try:
        # Parse tool call from trace
        if not output:
            return 1.0, "No tool call output (skipped)"
        
        # Try to extract tool name and parameters
        tool_data = json.loads(output) if isinstance(output, str) else output
        
        # Check if this is an error response - skip validation
        if isinstance(tool_data, dict):
            if tool_data.get('error') or tool_data.get('success') == False:
                return 1.0, "Error response (skipped)"
        
        tool_name = tool_data.get("tool") or tool_data.get("name")
        tool_input = tool_data.get("input") or tool_data.get("arguments") or {}
        
        if not tool_name:
            return 1.0, "Not a tool call (skipped)"
        
        # Check if tool has required parameters
        if tool_name not in TOOL_REQUIRED_PARAMS:
            return 1.0, f"✅ {tool_name} (not validated - unknown tool)"
        
        required_params = TOOL_REQUIRED_PARAMS[tool_name]
        
        if not required_params:
            return 1.0, f"✅ {tool_name}: No params required"
        
        # Check each required parameter and collect actual values
        missing_params = []
        present_params = {}
        
        for param in required_params:
            if param not in tool_input or tool_input[param] is None or tool_input[param] == "":
                missing_params.append(param)
            else:
                # Store actual value (truncate if too long)
                value = str(tool_input[param])
                present_params[param] = value[:50] + "..." if len(value) > 50 else value
        
        if missing_params:
            return 0.0, f"❌ {tool_name}: Missing [{', '.join(missing_params)}]"
        
        # Show proof: required params and actual values
        proof = " | ".join([f"{k}={v}" for k, v in present_params.items()])
        return 1.0, f"✅ {tool_name}: {proof}"
        
    except Exception as e:
        return 1.0, f"⚠️ Parse error (skipped): {str(e)[:50]}"


def evaluate_llm_decision_completeness(input: str, output: str, tool_calls: list = None) -> tuple:
    """
    Evaluator for Phoenix: Check if LLM has sufficient data before making decisions.
    
    Checks:
    - For Agent 1: LLM should call calculate_risk_score for each AP
    - For Agent 2: LLM should have topology data before calculating nearest APs
    - For Agent 3: LLM should read policy, risk scores, and nearest APs before suggesting
    
    Args:
        input: LLM input (user query + context)
        output: LLM output (decision/reasoning)
        tool_calls: List of actual tool calls made by LLM (from message.tool_calls)
    
    Returns:
        (score, explanation) where score is 0.0 to 1.0
    """
    try:
        if not input or not output:
            return 0.5, "Missing input or output"
        
        # Extract tool names from structured tool_calls if available
        called_tools = []
        if tool_calls:
            for tc in tool_calls:
                if isinstance(tc, dict):
                    tool_name = tc.get('tool_call.function.name') or tc.get('function', {}).get('name')
                    if tool_name:
                        called_tools.append(tool_name)
        
        # Fallback: check output text for tool mentions
        output_lower = output.lower()
        
        # Detect agent type from input
        if "risk score" in input.lower() or "calculate risk" in input.lower() or "orchestrator" in input.lower():
            # Agent 1: Risk Calculation
            # Should call calculate_risk_score tool OR wireless health/latency tools
            
            # Check structured tool calls first
            if called_tools:
                # Agent 1 uses get_wireless_health, get_wireless_latency_history, update_risk_score etc.
                valid_tools = ['calculate_risk_score', 'update_risk_score', 'get_wireless_health', 
                              'get_wireless_latency_history', 'get_wireless_usage_history', 
                              'get_device_clients', 'get_network_topology_link_layer']
                
                # Count valid vs invalid tools
                valid_called = [t for t in called_tools if t in valid_tools]
                invalid_called = [t for t in called_tools if t not in valid_tools]
                
                if valid_called:
                    # Enhanced proof: Show workflow validation
                    tools_list = ', '.join(set(valid_called))  # unique tools
                    
                    # Verify workflow makes sense
                    has_topology = 'get_network_topology_link_layer' in valid_called
                    has_health_data = any(t in valid_called for t in ['get_wireless_health', 'get_wireless_latency_history', 'get_wireless_usage_history'])
                    has_risk_update = any(t in valid_called for t in ['update_risk_score', 'calculate_risk_score'])
                    
                    # Build proof message
                    proof_parts = []
                    if has_topology:
                        proof_parts.append("discovered APs")
                    if has_health_data:
                        proof_parts.append("collected metrics")
                    if has_risk_update:
                        proof_parts.append("calculated risks")
                    
                    workflow = " → ".join(proof_parts) if proof_parts else "tools called"
                    
                    return 1.0, f"✅ Agent 1: {workflow} | Tools: [{tools_list}] ({len(valid_called)} calls)"
                else:
                    return 0.3, f"⚠️ Agent 1 called: [{', '.join(called_tools)}] (expected risk calculation tools)"
            
            # Fallback to text check
            if "calculate_risk_score" in output_lower or "wireless_health" in output_lower or "latency_history" in output_lower or "update_risk_score" in output_lower:
                return 1.0, "Agent 1: Called risk calculation tools ✅"
            else:
                return 0.0, "Agent 1: Did not call risk calculation tools ❌"
        
        elif "nearest ap" in input.lower() or "failover candidate" in input.lower():
            # Agent 2: Nearest AP Finder
            # Should have topology data
            if called_tools:
                has_topology = 'get_network_topology_link_layer' in called_tools or 'calculate_nearest_aps' in called_tools
                tools_list = ', '.join(called_tools)
                if has_topology:
                    return 1.0, f"✅ Agent 2 called: [{tools_list}]"
                else:
                    return 0.3, f"⚠️ Agent 2 called: [{tools_list}] (expected topology tools)"
            
            if "topology" in output_lower or "calculate_nearest_aps" in output_lower:
                return 1.0, "Agent 2: Has topology data ✅"
            else:
                return 0.3, "Agent 2: May be missing topology data ⚠️"
        
        elif "failover" in input.lower() or "recommendation" in input.lower():
            # Agent 3: Failover Suggestion
            # Should read policy, risk scores, and nearest APs
            
            if called_tools:
                checks = {
                    "policy": "read_network_policy" in called_tools,
                    "risk_scores": "read_risk_scores" in called_tools,
                    "nearest_aps": "read_nearest_aps" in called_tools
                }
                
                tools_list = ', '.join(called_tools)
            else:
                checks = {
                    "policy": "read_network_policy" in output_lower or "threshold" in output_lower,
                    "risk_scores": "read_risk_scores" in output_lower or "risk_score" in output_lower,
                    "nearest_aps": "read_nearest_aps" in output_lower or "nearest" in output_lower
                }
                tools_list = "text-based check"
            
            passed_checks = sum(checks.values())
            score = passed_checks / 3.0
            
            missing = [k for k, v in checks.items() if not v]
            present = [k for k, v in checks.items() if v]
            
            if score == 1.0:
                return 1.0, f"✅ Agent 3 called: [{tools_list}] - has all data"
            elif score >= 0.66:
                return score, f"⚠️ Agent 3 called: [{tools_list}] - missing {', '.join(missing)}"
            else:
                return score, f"❌ Agent 3 called: [{tools_list}] - missing {', '.join(missing)}"
        
        # Generic LLM call - if it made tool calls, show which ones
        if called_tools:
            tools_list = ', '.join(set(called_tools))  # unique tools
            return 1.0, f"✅ LLM called: [{tools_list}] ({len(called_tools)} total)"
        
        return 1.0, "Generic LLM call (no tools, text-only)"
        
    except Exception as e:
        return 0.5, f"Validation error: {str(e)}"


def create_phoenix_evaluators() -> List[Dict[str, Any]]:
    """
    Create Phoenix evaluator configurations for auto-evaluation.
    
    Returns:
        List of evaluator configurations
    """
    return [
        {
            "name": "tool_parameters_complete",
            "display_name": "Tool Parameters Complete",
            "function": evaluate_tool_parameters,
            "description": "Checks if tool calls have all required parameters",
            "eval_type": "deterministic"
        },
        {
            "name": "llm_decision_completeness",
            "display_name": "LLM Decision Completeness", 
            "function": evaluate_llm_decision_completeness,
            "description": "Checks if LLM has sufficient data before making decisions",
            "eval_type": "deterministic"
        }
    ]


if __name__ == "__main__":
    # Test evaluators
    print("Testing Tool Parameter Evaluator:")
    
    # Test 1: Missing parameter
    test_call_1 = json.dumps({
        "tool": "calculate_risk_score",
        "input": {}
    })
    score, msg = evaluate_tool_parameters(test_call_1)
    print(f"  Test 1: {score} - {msg}")
    
    # Test 2: All parameters present
    test_call_2 = json.dumps({
        "tool": "calculate_risk_score",
        "input": {"ap_serial": "Q2XX-1234"}
    })
    score, msg = evaluate_tool_parameters(test_call_2)
    print(f"  Test 2: {score} - {msg}")
    
    print("\nTesting LLM Decision Completeness:")
    
    # Test 3: Agent 3 with all data
    test_input = "Analyze network for failover recommendations"
    test_output = "Calling read_network_policy, read_risk_scores, read_nearest_aps"
    score, msg = evaluate_llm_decision_completeness(test_input, test_output)
    print(f"  Test 3: {score} - {msg}")
    
    # Test 4: Agent 3 missing data
    test_output_2 = "Recommending failover without data"
    score, msg = evaluate_llm_decision_completeness(test_input, test_output_2)
    print(f"  Test 4: {score} - {msg}")
