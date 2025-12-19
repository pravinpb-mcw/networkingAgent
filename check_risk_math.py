"""
Check risk_scores.json for math mismatches
"""
import json
from pathlib import Path

risk_scores_path = Path(__file__).parent / "agent_data" / "risk_scores.json"

if not risk_scores_path.exists():
    print(f"File not found: {risk_scores_path}")
    exit(1)

with open(risk_scores_path, 'r') as f:
    data = json.load(f)

print("\n" + "="*80)
print("RISK SCORE MATH VERIFICATION")
print("="*80 + "\n")

weights = {
    'latency_score': 0.25,
    'jitter_score': 0.20,
    'retrans_score': 0.20,
    'snr_score': 0.15,
    'load_score': 0.10,
    'auth_score': 0.10
}

mismatches = []
matches = []

for ap_serial, ap_data in data.items():
    if isinstance(ap_data, dict) and 'current' in ap_data:
        current = ap_data['current']
        reported_risk = current.get('risk_score', 0)
        metrics = current.get('metrics', {})
        
        # Calculate risk from metrics
        calculated_risk = 0
        for metric, weight in weights.items():
            score = metrics.get(metric, 0)
            calculated_risk += score * weight
        
        diff = abs(calculated_risk - reported_risk)
        
        if diff > 2.0:
            mismatches.append((ap_serial, reported_risk, calculated_risk, diff, metrics))
            status = "MISMATCH"
            symbol = "X"
        else:
            matches.append((ap_serial, reported_risk, calculated_risk, diff))
            status = "OK"
            symbol = "OK"
        
        print(f"{symbol} {ap_serial}")
        print(f"   Reported: {reported_risk:.1f}")
        print(f"   Calculated: {calculated_risk:.1f}")
        print(f"   Diff: {diff:.1f}")
        if diff > 2.0:
            print(f"   Metrics: {metrics}")
        print()

print("="*80)
print(f"SUMMARY:")
print(f"  OK Matches: {len(matches)}")
print(f"  X Mismatches: {len(mismatches)}")
print(f"  Pass Rate: {len(matches)/(len(matches)+len(mismatches))*100:.1f}%")
print("="*80)

if mismatches:
    print("\nMISMATCHES IN DETAIL:\n")
    for ap_serial, reported, calculated, diff, metrics in mismatches:
        print(f"X {ap_serial}")
        print(f"   Reported: {reported:.1f}")
        print(f"   Calculated: {calculated:.1f}")
        print(f"   Diff: {diff:.1f}")
        print(f"   Metrics:")
        for metric, value in metrics.items():
            weight = weights.get(metric, 0)
            contribution = value * weight
            print(f"      {metric}: {value} x {weight} = {contribution:.1f}")
        print()
