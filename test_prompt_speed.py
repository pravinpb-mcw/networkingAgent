#!/usr/bin/env python3
"""
Test simplified evaluation prompt speed
"""

import os
import time
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL")

print("Testing Simplified vs Detailed Prompts")
print("=" * 80)

# Test 1: Detailed prompt (current)
print("Test 1: DETAILED evaluation prompt")
print("-" * 80)

detailed_prompt = """You are evaluating if an AI agent's response contains hallucinations or is factual.

[Input]
Calculate risk scores for all APs

[Reference - Ground Truth Context]
API returned: SNR=15.7dB, retransmissions=60/min, clientCount=2

[Agent's Output to Evaluate]
Risk score: 56 based on retransmissions (score 100), SNR (score 80), load (score 20)

Provide a DETAILED explanation covering:
1. **What action/decision the agent made**: Describe what the agent is doing or claiming
2. **Why this action was taken**: What reasoning or data led to this action
3. **Reference grounding**: Is this information found in the reference context?
4. **Hallucination check**: Any invented facts, numbers, or details not in reference?
5. **Final assessment**: Is the output factual or hallucinated?

After your detailed analysis, provide your label as either "factual" or "hallucinated".
"""

start = time.time()
try:
    response = requests.post(
        f"{base_url}/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": detailed_prompt}]
        },
        timeout=60
    )
    elapsed = time.time() - start
    print(f"Time: {elapsed:.2f}s")
    if response.status_code == 200:
        result = response.json()
        text = result.get('content', [{}])[0].get('text', '')
        print(f"Response: {len(text)} chars")
    else:
        print(f"Failed: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test 2: Simplified prompt (new)
print("Test 2: SIMPLIFIED evaluation prompt")
print("-" * 80)

simplified_prompt = """Evaluate if this AI agent output is factual or hallucinated.

[Input]
Calculate risk scores for all APs

[Reference - Ground Truth]
API returned: SNR=15.7dB, retransmissions=60/min, clientCount=2

[Output to Evaluate]
Risk score: 56 based on retransmissions (score 100), SNR (score 80), load (score 20)

Check:
1. Does the output use ONLY data from the reference?
2. Are there any invented metrics, numbers, or facts?
3. Are calculations shown correctly?

Provide brief explanation then label as "factual" or "hallucinated".
"""

start = time.time()
try:
    response = requests.post(
        f"{base_url}/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": simplified_prompt}]
        },
        timeout=60
    )
    elapsed = time.time() - start
    print(f"Time: {elapsed:.2f}s")
    if response.status_code == 200:
        result = response.json()
        text = result.get('content', [{}])[0].get('text', '')
        print(f"Response: {len(text)} chars")
    else:
        print(f"Failed: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 80)
print("Expected: Simplified should be ~50% faster (15-20s vs 30s)")
