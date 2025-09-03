#!/usr/bin/env python3
"""
Quick Network Problem Injector
Automatically injects 6 random network problems for testing.
"""

from inject_network_problems import NetworkProblemInjector

def main():
    print("🚨 QUICK NETWORK PROBLEM INJECTOR")
    print("=" * 50)
    print("Injecting 6 random problems to YOUR network...")
    print("=" * 50)
    
    injector = NetworkProblemInjector()
    problems = injector.inject_random_problems(6)
    
    print(f"\n🎉 Done! Your agent now has {len(problems)} problems to fix!")
    print("Run your agent with 'monitor' or 'analyze' to detect and fix them!")

if __name__ == "__main__":
    main()
