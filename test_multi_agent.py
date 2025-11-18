#!/usr/bin/env python3
"""
Test script for multi-agent setup
Tests the Network Monitor Agent calling the Mitigation Strategy Agent
"""

import asyncio
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test-multi-agent")

async def test_mitigation_agent_standalone():
    """Test the mitigation agent independently"""
    from mitigation_strategy_agent import MitigationStrategyAgent
    
    print("\n" + "="*80)
    print("TEST 1: Mitigation Strategy Agent (Standalone)")
    print("="*80)
    
    agent = MitigationStrategyAgent()
    
    if not await agent.initialize():
        logger.error("❌ Failed to initialize mitigation agent")
        return False
    
    try:
        result = await agent.generate_mitigation_strategy(
            issue_type="High Latency",
            severity="warning",
            metrics={
                "latency_ms": 75.5,
                "packet_loss_pct": 0.5,
                "jitter_ms": 15.3,
                "goodput": 88.0
            },
            device_serial="Q2MN-Q3J9-YJHW",
            network_id="L_3947405073390239794",
            additional_context="Latency spike detected during monitoring cycle"
        )
        
        if result["success"]:
            print("\n✅ Mitigation agent generated strategy successfully")
            print("\nStrategy Preview (first 500 chars):")
            print("-" * 80)
            print(result["strategy"][:500] + "...")
            print("-" * 80)
            return True
        else:
            logger.error(f"❌ Failed to generate strategy: {result.get('error')}")
            return False
    
    finally:
        await agent.close()


async def test_network_monitor_with_mitigation():
    """Test the network monitor agent with mitigation tool integration"""
    from network_monitor_agent import NetworkChangeDetector
    
    print("\n" + "="*80)
    print("TEST 2: Network Monitor Agent with Mitigation Tool")
    print("="*80)
    
    detector = NetworkChangeDetector()
    
    if not await detector.initialize():
        logger.error("❌ Failed to initialize network monitor")
        return False
    
    try:
        # Verify the mitigation tool is available
        if detector.mitigation_agent:
            print("\n✅ Mitigation agent is initialized and available as a tool")
        else:
            logger.error("❌ Mitigation agent not initialized")
            return False
        
        print("\n🔍 Running single network check with mitigation capability...")
        result = await detector.single_check()
        
        if result["success"]:
            print("\n✅ Network monitor executed successfully with mitigation tool available")
            return True
        else:
            logger.error(f"❌ Network check failed: {result.get('error')}")
            return False
    
    finally:
        await detector.close()


async def main():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        MULTI-AGENT SYSTEM TEST SUITE                         ║
║                                                              ║
║  Testing Network Monitor + Mitigation Strategy Agents        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # Test 1: Mitigation agent standalone
    try:
        result1 = await test_mitigation_agent_standalone()
        results.append(("Mitigation Agent Standalone", result1))
    except Exception as e:
        logger.error(f"Test 1 failed with exception: {e}")
        results.append(("Mitigation Agent Standalone", False))
    
    # Test 2: Network monitor with mitigation tool
    try:
        result2 = await test_network_monitor_with_mitigation()
        results.append(("Network Monitor with Mitigation Tool", result2))
    except Exception as e:
        logger.error(f"Test 2 failed with exception: {e}")
        results.append(("Network Monitor with Mitigation Tool", False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 All tests PASSED! Multi-agent system is working correctly.")
    else:
        print("⚠️  Some tests FAILED. Check the logs above for details.")
    print("="*80)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
