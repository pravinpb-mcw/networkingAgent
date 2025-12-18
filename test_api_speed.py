#!/usr/bin/env python3
"""
Test the actual speed of Anthropic z.ai API
"""

import os
import time
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL")

print("Testing z.ai API Speed")
print("=" * 80)
print(f"Endpoint: {base_url}")
print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
print()

# Test 1: Simple completion
print("Test 1: Simple message (should be fast)")
print("-" * 80)

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
            "max_tokens": 50,
            "messages": [{
                "role": "user",
                "content": "Say 'hello' in one word"
            }]
        },
        timeout=60
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        print(f"✅ Success in {elapsed:.2f}s")
        result = response.json()
        print(f"Response: {result.get('content', [{}])[0].get('text', 'N/A')}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    elapsed = time.time() - start
    print(f"❌ Error after {elapsed:.2f}s: {e}")

print()

# Test 2: Hallucination evaluation (similar to Phoenix)
print("Test 2: Hallucination evaluation prompt (Phoenix-like)")
print("-" * 80)

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
            "messages": [{
                "role": "user",
                "content": """Evaluate if this is factual or hallucinated.

Input: Calculate risk score for AP
Reference: API returned SNR=15.7, retransmissions=60
Output: Risk score is 56 based on SNR and retransmissions

Answer with 'factual' or 'hallucinated' and explain why."""
            }]
        },
        timeout=60
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        print(f"✅ Success in {elapsed:.2f}s")
        result = response.json()
        text = result.get('content', [{}])[0].get('text', 'N/A')
        print(f"Response length: {len(text)} chars")
        print(f"First 200 chars: {text[:200]}...")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    elapsed = time.time() - start
    print(f"❌ Error after {elapsed:.2f}s: {e}")

print()
print("=" * 80)
print("Summary:")
print("If both tests took >20s each, the z.ai endpoint is very slow.")
print("If test 1 was fast but test 2 was slow, it's the evaluation prompt size.")
print("Expected: <2s for simple messages, <5s for evaluation prompts")
