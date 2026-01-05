"""
Diagnose Phoenix Tracing Issues
Checks package versions and tests if instrumentation actually works
"""
import sys

print("="*80)
print("PHOENIX TRACING DIAGNOSTICS")
print("="*80)
print()

# Check Python version
print("🐍 Python Version:")
print(f"   {sys.version}")
print()

# Check critical package versions
print("📦 Package Versions:")
packages = [
    'arize-phoenix',
    'openinference-instrumentation-langchain',
    'opentelemetry-sdk',
    'opentelemetry-exporter-otlp',
    'langchain',
    'langchain-core',
    'langchain-anthropic',
    'langchain-mcp-adapters'
]

import importlib.metadata
for pkg in packages:
    try:
        version = importlib.metadata.version(pkg)
        print(f"   ✅ {pkg}: {version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"   ❌ {pkg}: NOT INSTALLED")
print()

# Test if instrumentation can hook into LangChain
print("🔧 Testing LangChain Instrumentation:")
try:
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from opentelemetry import trace
    from opentelemetry.sdk import trace as trace_sdk
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    
    # Set up tracer
    resource = Resource.create({"service.name": "test-tracing"})
    tracer_provider = trace_sdk.TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:6006/v1/traces")
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    
    # Try to instrument
    instrumentor = LangChainInstrumentor()
    instrumentor.instrument(tracer_provider=tracer_provider)
    print("   ✅ LangChainInstrumentor initialized successfully")
    
    # Check what it can instrument
    print("\n   Checking instrumentation capabilities...")
    
    # Test if it can see LangChain imports
    try:
        from langchain.agents import create_agent
        print("   ✅ Can import langchain.agents.create_agent")
    except Exception as e:
        print(f"   ❌ Cannot import create_agent: {e}")
    
    try:
        from langchain.chat_models import init_chat_model
        print("   ✅ Can import langchain.chat_models.init_chat_model")
    except Exception as e:
        print(f"   ❌ Cannot import init_chat_model: {e}")
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        print("   ✅ Can import langchain_mcp_adapters.client.MultiServerMCPClient")
    except Exception as e:
        print(f"   ❌ Cannot import MultiServerMCPClient: {e}")
    
    # Clean up
    instrumentor.uninstrument()
    print("\n   ✅ Instrumentation test completed")
    
except Exception as e:
    print(f"   ❌ Instrumentation failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Check Phoenix connection
print("🔗 Phoenix Server Connection:")
try:
    import requests
    response = requests.get("http://localhost:6006", timeout=3)
    if response.status_code == 200:
        print("   ✅ Phoenix is running and responding")
        
        # Try OTLP endpoint
        try:
            # POST empty data to test endpoint
            otlp_response = requests.post(
                "http://localhost:6006/v1/traces",
                json={"resourceSpans": []},
                headers={"Content-Type": "application/json"},
                timeout=3
            )
            print(f"   ✅ OTLP endpoint accessible (status: {otlp_response.status_code})")
        except Exception as e:
            print(f"   ⚠️ OTLP endpoint test failed: {e}")
    else:
        print(f"   ⚠️ Phoenix returned status {response.status_code}")
except Exception as e:
    print(f"   ❌ Cannot connect to Phoenix: {e}")

print()

# Check if there are existing traces
print("📊 Existing Traces Check:")
try:
    from phoenix.session.client import Client as PhoenixClient
    client = PhoenixClient(endpoint="http://localhost:6006")
    
    # Try to get spans
    try:
        spans_df = client.get_spans_dataframe()
        print(f"   ✅ Found {len(spans_df)} existing spans in Phoenix")
        
        if len(spans_df) > 0:
            print("\n   Recent traces:")
            if 'name' in spans_df.columns:
                trace_names = spans_df['name'].value_counts().head(5)
                for name, count in trace_names.items():
                    print(f"      - {name}: {count} spans")
        else:
            print("   ⚠️ No traces found - agents may not be sending data")
    except Exception as e:
        print(f"   ⚠️ Could not retrieve spans: {e}")
        
except Exception as e:
    print(f"   ⚠️ Could not check traces: {e}")

print()
print("="*80)
print("DIAGNOSIS SUMMARY")
print("="*80)
print()
print("Next steps:")
print("1. Compare package versions between working and non-working systems")
print("2. If versions differ, sync them using requirements.txt")
print("3. If versions match, check Windows Firewall / antivirus blocking OTLP")
print("4. Try running agents with: python -X dev agent_1_risk_calculation.py")
print("   (Shows more detailed errors)")
print()
