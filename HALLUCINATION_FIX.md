# Hallucination Fix - Risk Score Agent

## Problem Detected
The Phoenix hallucination evaluator (using Anthropic GLM-4.5 API) correctly identified that the agent was **hallucinating** when calculating risk scores.

### What the Agent Hallucinated:
1. **Invented metrics** not in API responses:
   - "Latency" (actually exists, but was mislabeled)
   - "Jitter" (doesn't exist in API)
   - "Auth Failures" (doesn't exist in API)

2. **Fabricated scoring system**:
   - Made up score values without showing calculations
   - Listed individual scores (20, 20, 100, 100, 20, 20) that sum to 280
   - But then claimed "RISK SCORE: 57" (completely wrong math!)

3. **Invented classifications**:
   - "CRITICAL FAILURE PATTERN" with no threshold defined
   - "MINIMAL DATA" without explaining what it means

### Why It Happened:
The system prompt had the formula but wasn't strict enough about:
- Which exact API fields to use
- Showing calculation steps
- NOT inventing metrics that don't exist

## Solution Applied

### Updated System Prompt (risk_score_agent.py)

**Added strict requirements:**

1. **List ONLY available API fields:**
   ```
   From get_wireless_usage_history:
   - avgSignalToNoise (dB)
   - retransmissionsPerMinute (count/min)
   - clientCount (number)
   
   From get_wireless_latency_history:
   - avg (ms)
   
   From get_device_clients:
   - count of current clients
   ```

2. **Require showing calculations:**
   ```
   AP: Q2XX-ABCD-1234
   Raw Metrics from API:
     - Latency: 45 ms → Score: 50
     - Retransmissions: 60/min → Score: 100
     - SNR: 15.7 dB → Score: 80
     - Client Count: 2 → Score: 20
   
   Calculation:
     RISK_SCORE = (0.25 × 50) + (0.20 × 20) + (0.20 × 100) + 
                  (0.15 × 80) + (0.10 × 20) + (0.10 × 20)
     RISK_SCORE = 12.5 + 4 + 20 + 12 + 2 + 2
     FINAL SCORE: 52.5
   ```

3. **Explicit warnings:**
   - "CRITICAL: ONLY USE METRICS FROM API RESPONSES - DO NOT INVENT METRICS!"
   - "NO HALLUCINATIONS!"
   - "EXTRACT ONLY REAL API FIELDS"

## Result

The agent will now:
✅ Use ONLY fields that exist in API responses
✅ Show step-by-step calculations with real math
✅ Not invent metric names or scoring systems
✅ Be caught by Phoenix if it tries to hallucinate

## Testing

To verify the fix:
1. Run the agent: `python agents/risk_score_agent.py`
2. Check Phoenix dashboard at http://localhost:6006
3. Look for "Hallucination" annotations
4. Verify the evaluation says "factual" instead of "hallucinated"

## Prevention

**For ALL agents:**
- Always list exact API field names in system prompt
- Require showing calculations/reasoning
- Warn against inventing data
- Use Phoenix evaluations to catch hallucinations automatically
