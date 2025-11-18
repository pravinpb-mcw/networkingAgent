# Troubleshooting Guide - Multi-Agent System

## Issue: MCPAgent initialization failed with "unexpected keyword argument 'additional_tools'"

### Problem
When trying to initialize the Network Monitor Agent with the Mitigation Strategy Agent as a tool, the following error occurred:

```
MCPAgent.__init__() got an unexpected keyword argument 'additional_tools'
```

### Root Cause
The `MCPAgent` class from `mcp_use` library does not support an `additional_tools` parameter. This is not a standard parameter in the MCPAgent constructor.

### Solution
Instead of passing tools as a parameter to `MCPAgent`, we bind the tools directly to the LLM using LangChain's `bind_tools()` method before passing the LLM to MCPAgent.

**Before (Incorrect):**
```python
# This does NOT work
self.agent = MCPAgent(
    llm=self.llm,
    client=self.client,
    max_steps=20,
    memory_enabled=True,
    verbose=False,
    additional_tools=[mitigation_tool]  # ❌ Invalid parameter
)
```

**After (Correct):**
```python
# This WORKS
mitigation_tool = self._create_mitigation_tool()

# Bind the tool to the LLM first
llm_with_tools = self.llm.bind_tools([mitigation_tool])

# Then pass the enhanced LLM to MCPAgent
self.agent = MCPAgent(
    llm=llm_with_tools,  # ✅ LLM with tools bound
    client=self.client,
    max_steps=20,
    memory_enabled=True,
    verbose=False
)
```

### How LangChain Tool Binding Works

1. **Tool Definition**: Create a tool using the `@tool` decorator:
   ```python
   from langchain.tools import tool
   
   @tool("tool_name", description="Tool description")
   def my_tool(arg1: str, arg2: int) -> str:
       # Tool implementation
       return result
   ```

2. **Bind to LLM**: Use `bind_tools()` to attach tools to the LLM:
   ```python
   llm_with_tools = llm.bind_tools([tool1, tool2, tool3])
   ```

3. **LLM Gains Awareness**: The LLM can now:
   - See the tool in its available tools list
   - Understand when to call it based on the description
   - Format tool calls correctly
   - Receive tool results

4. **Use in Agent**: Pass the enhanced LLM to any agent framework:
   ```python
   agent = MCPAgent(llm=llm_with_tools, ...)
   ```

### Verification

Run the test suite to verify the fix:
```bash
python test_multi_agent.py
```

Expected output:
```
✅ Mitigation Agent Standalone: PASSED
✅ Network Monitor with Mitigation Tool: PASSED
🎉 All tests PASSED! Multi-agent system is working correctly.
```

### Key Takeaways

1. **Check Library Documentation**: Always verify the exact parameters supported by library classes
2. **Use Tool Binding**: For LangChain-based agents, bind tools to the LLM rather than passing them separately
3. **Test Integration**: Always test multi-agent integrations to catch initialization issues early
4. **Read Error Messages**: The error message clearly indicated which parameter was invalid

---

## Common Multi-Agent Issues

### Issue: Tool not being called by agent

**Symptoms:**
- Agent doesn't invoke the mitigation tool when issues are detected
- Agent makes decisions without consulting specialist agents

**Solutions:**
1. **Improve tool description**: Make it clear WHEN to use the tool
2. **Explicit prompting**: Tell agent to call tool in specific scenarios
3. **Check tool binding**: Verify tool is properly bound to LLM
4. **Review agent logs**: Check if tool appears in available tools list

### Issue: Context not passed correctly to subagent

**Symptoms:**
- Subagent generates incorrect strategies
- Missing information in subagent responses

**Solutions:**
1. **Validate tool parameters**: Ensure all required parameters are passed
2. **Check parameter types**: Verify parameter types match tool signature
3. **Add debugging**: Log what's being passed to the tool
4. **Test tool standalone**: Verify subagent works independently first

### Issue: Agent timeout or excessive steps

**Symptoms:**
- Agent runs out of steps before completing task
- Execution times are very long

**Solutions:**
1. **Increase max_steps**: Adjust based on task complexity
2. **Optimize prompts**: Make instructions clearer and more direct
3. **Reduce tool calls**: Guide agent to only call necessary tools
4. **Use streaming**: Enable streaming for better visibility

---

## Testing Checklist

Before deploying multi-agent systems:

- [ ] Test each agent independently
- [ ] Test tool calling mechanism
- [ ] Test with normal network conditions
- [ ] Test with network issues (trigger mitigation)
- [ ] Test error handling
- [ ] Test with missing environment variables
- [ ] Test continuous monitoring mode
- [ ] Verify alerts are sent correctly
- [ ] Check mitigation strategies are actionable
- [ ] Validate tool binding works correctly

---

## Debugging Tips

### Enable Verbose Logging
```python
self.agent = MCPAgent(
    llm=llm_with_tools,
    client=self.client,
    verbose=True,  # Enable to see agent thoughts
    ...
)
```

### Check Available Tools
```python
# After binding tools to LLM
print("Tools bound to LLM:", llm_with_tools.bound)
```

### Test Tool Directly
```python
# Test the tool function independently
result = await mitigation_tool._run(
    issue_type="High Latency",
    severity="warning",
    current_latency_ms=75.0,
    ...
)
print("Tool result:", result)
```

### Monitor API Calls
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
```

---

**Last Updated:** November 13, 2025
**Status:** Resolved ✅
