"""
Check Phoenix traces for math verification failures
"""
import sqlite3
from pathlib import Path
import json
from datetime import datetime

# Connect to Phoenix database
db_path = Path(__file__).parent / ".phoenix" / "phoenix_traces.db"

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# First, check what tables exist
print("\nAvailable tables:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"   - {table[0]}")

# Check evaluations table schema
print("\nTable schemas:")
for table in tables:
    table_name = table[0]
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    print(f"\n{table_name}:")
    for col in cols:
        print(f"   {col[1]} ({col[2]})")

# Get all math verification evaluations
query = """
SELECT *
FROM trace_annotations
WHERE name = 'risk_math_verification'
ORDER BY created_at DESC
LIMIT 10
"""

cursor.execute(query)
results = cursor.fetchall()

print(f"\n{'='*80}")
print(f"RISK MATH VERIFICATION - Last 20 Evaluations")
print(f"{'='*80}\n")

if not results:
    print("❌ No math verification evaluations found")
else:
    failed = []
    passed = []
    
    for eval_name, label, score, explanation, span_name, attributes in results:
        status = "✅" if score >= 0.8 else "❌"
        print(f"{status} Score: {score:.2f} | {label}")
        print(f"   Span: {span_name}")
        print(f"   {explanation}")
        
        # Parse attributes to see the actual data
        try:
            attrs = json.loads(attributes)
            output_val = attrs.get('output', {}).get('value', '')
            
            if output_val:
                # Try to parse output
                if isinstance(output_val, str):
                    try:
                        output_data = json.loads(output_val)
                        if 'content' in output_data:
                            content_str = output_data['content']
                            if isinstance(content_str, str):
                                content = json.loads(content_str)
                            else:
                                content = content_str
                        else:
                            content = output_data
                        
                        if 'ap_serial' in content:
                            print(f"   AP: {content.get('ap_serial')}")
                        if 'risk_score' in content:
                            print(f"   AI Risk Score: {content.get('risk_score')}")
                    except:
                        pass
        except:
            pass
        
        print()
        
        if score < 0.8:
            failed.append((span_name, score, explanation))
        else:
            passed.append((span_name, score, explanation))
    
    print(f"{'='*80}")
    print(f"SUMMARY:")
    print(f"  ✅ Passed: {len(passed)}")
    print(f"  ❌ Failed: {len(failed)}")
    print(f"  📊 Pass Rate: {len(passed)/(len(passed)+len(failed))*100:.1f}%")
    print(f"{'='*80}\n")
    
    if failed:
        print("\n🔍 FAILURES IN DETAIL:\n")
        for span_name, score, explanation in failed:
            print(f"❌ {span_name} (score: {score:.2f})")
            print(f"   {explanation}\n")

conn.close()
