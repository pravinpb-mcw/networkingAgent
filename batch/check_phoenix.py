"""Check if Phoenix server is ready"""
import requests
import time
import sys

max_tries = 15
for i in range(max_tries):
    try:
        response = requests.get("http://localhost:6006", timeout=2)
        if response.status_code == 200:
            print(f"✅ Phoenix is ready! (took {i+1} checks)")
            sys.exit(0)
    except:
        pass
    
    print(f"⏳ Waiting for Phoenix... ({i+1}/{max_tries})")
    time.sleep(0.5)

print("❌ Phoenix did not start in time")
sys.exit(1)
