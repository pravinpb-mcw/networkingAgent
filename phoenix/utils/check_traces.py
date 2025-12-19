#!/usr/bin/env python3
"""Check actual tool traces from Phoenix"""

from phoenix.session.client import Client
import pandas as pd
import json

client = Client(endpoint='http://localhost:6006')
df = client.get_spans_dataframe()

if df is None or df.empty:
    print("No traces found")
    exit()

# Get LLM spans to understand what data is available
llm_spans = df[df['span_kind'] == 'LLM'].tail(3)

print("=== RECENT LLM SPANS ===\n")

for idx, row in llm_spans.iterrows():
    print(f"Span ID: {idx}")
    print(f"Name: {row.get('name', 'N/A')}")
    
    # Check all available columns
    print(f"\nAvailable attributes:")
    for col in row.index:
        if 'llm' in col.lower() or 'tool' in col.lower() or 'input' in col.lower() or 'output' in col.lower():
            val = row.get(col, '')
            if val and str(val) != 'nan':
                print(f"  {col}: {str(val)[:200]}")
    
    print("-" * 100 + "\n")

# Get all column names
print("\n=== ALL AVAILABLE COLUMNS ===\n")
tool_cols = [col for col in df.columns if 'tool' in col.lower()]
llm_cols = [col for col in df.columns if 'llm' in col.lower()]

print("Tool-related columns:")
for col in tool_cols:
    print(f"  {col}")

print("\nLLM-related columns:")
for col in llm_cols:
    print(f"  {col}")


