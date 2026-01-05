"""
Verify Phoenix Tracing Setup
Tests if Phoenix is properly configured for agent tracing
"""
import sys
import time
import requests
from pathlib import Path

def check_phoenix_server():
    """Check if Phoenix server is running"""
    print("🔍 Checking Phoenix server...")
    try:
        response = requests.get("http://localhost:6006", timeout=3)
        if response.status_code == 200:
            print("✅ Phoenix server is running on http://localhost:6006")
            return True
        else:
            print(f"❌ Phoenix returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Phoenix is NOT running - cannot connect to localhost:6006")
        print("   Start Phoenix first: python phoenix\\server.py")
        return False
    except Exception as e:
        print(f"❌ Error checking Phoenix: {e}")
        return False

def check_phoenix_otlp():
    """Check if Phoenix OTLP endpoint is accessible"""
    print("\n🔍 Checking Phoenix OTLP endpoint...")
    try:
        # Try to access the traces endpoint (should return 405 for GET)
        response = requests.get("http://localhost:6006/v1/traces", timeout=3)
        # 405 Method Not Allowed is expected (it wants POST)
        if response.status_code in [200, 405, 404]:
            print("✅ Phoenix OTLP endpoint is accessible")
            return True
        else:
            print(f"⚠️ OTLP endpoint returned unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OTLP endpoint not accessible: {e}")
        return False

def check_database():
    """Check if Phoenix database exists"""
    print("\n🔍 Checking Phoenix database...")
    db_path = Path(".phoenix/phoenix_traces.db")
    if db_path.exists():
        size_kb = db_path.stat().st_size / 1024
        print(f"✅ Phoenix database exists: {db_path}")
        print(f"   Size: {size_kb:.1f} KB")
        return True
    else:
        print(f"⚠️ Phoenix database not found at: {db_path}")
        print("   It will be created when Phoenix starts")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n🔍 Checking Python dependencies...")
    
    required = {
        'phoenix': 'arize-phoenix',
        'openinference.instrumentation.langchain': 'openinference-instrumentation-langchain',
        'opentelemetry': 'opentelemetry-sdk',
        'langchain': 'langchain',
        'requests': 'requests'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module.split('.')[0])
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_env_vars():
    """Check environment variables"""
    print("\n🔍 Checking environment variables...")
    import os
    
    checks = {
        'PHOENIX_PORT': '6006',
        'PHOENIX_WORKING_DIR': None,
        'PHOENIX_SQL_DATABASE_URL': None
    }
    
    all_ok = True
    for var, expected in checks.items():
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}={value}")
        else:
            print(f"⚠️ {var} not set (will use defaults)")
            if expected:
                all_ok = False
    
    return all_ok

def test_instrumentation():
    """Test if LangChain instrumentation works"""
    print("\n🔍 Testing LangChain instrumentation...")
    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from opentelemetry import trace
        from opentelemetry.sdk import trace as trace_sdk
        from opentelemetry.sdk.resources import Resource
        
        # Create a simple tracer
        resource = Resource.create({"service.name": "test-instrumentation"})
        tracer_provider = trace_sdk.TracerProvider(resource=resource)
        
        # Try to instrument
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        print("✅ LangChain instrumentation can be initialized")
        
        # Clean up
        LangChainInstrumentor().uninstrument()
        return True
        
    except Exception as e:
        print(f"❌ LangChain instrumentation failed: {e}")
        return False

def main():
    print("="*80)
    print("PHOENIX TRACING VERIFICATION")
    print("="*80)
    print()
    
    results = []
    
    # Check dependencies first
    deps_ok, missing = check_dependencies()
    results.append(("Dependencies", deps_ok))
    
    if not deps_ok:
        print("\n" + "="*80)
        print("❌ MISSING DEPENDENCIES")
        print("="*80)
        print("\nInstall missing packages:")
        for pkg in missing:
            print(f"  pip install {pkg}")
        print()
        return False
    
    # Check Phoenix server
    phoenix_running = check_phoenix_server()
    results.append(("Phoenix Server", phoenix_running))
    
    if phoenix_running:
        # Check OTLP endpoint
        otlp_ok = check_phoenix_otlp()
        results.append(("OTLP Endpoint", otlp_ok))
    else:
        print("\n⚠️ Cannot check OTLP endpoint - Phoenix not running")
        results.append(("OTLP Endpoint", False))
    
    # Check database
    db_exists = check_database()
    results.append(("Database", db_exists))
    
    # Check env vars
    env_ok = check_env_vars()
    results.append(("Environment Variables", env_ok))
    
    # Test instrumentation
    instr_ok = test_instrumentation()
    results.append(("LangChain Instrumentation", instr_ok))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for check, status in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {check}")
    
    all_passed = all(status for _, status in results)
    
    print()
    if all_passed:
        print("="*80)
        print("🎉 ALL CHECKS PASSED!")
        print("="*80)
        print("\nYour Phoenix tracing setup is working correctly.")
        print("\nNext steps:")
        print("1. Start agents with: .\\batch\\start_full_system.bat")
        print("2. Open Phoenix UI: http://localhost:6006")
        print("3. Wait 15-20 seconds for traces to appear")
        print()
        return True
    else:
        print("="*80)
        print("⚠️ SOME CHECKS FAILED")
        print("="*80)
        print("\nFix the issues above before starting agents.")
        print()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
