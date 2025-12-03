#!/usr/bin/env python3
"""
Test script to verify enhanced metrics support in the agent.
Tests all metric categories: CPU, Memory, Disk, Network, Processes, System.
"""

import asyncio
import httpx
import json

# Agent endpoint
AGENT_URL = "http://localhost:8081/chat"

# Test queries for each metric category
TEST_QUERIES = {
    "CPU": [
        "What is the CPU idle rate?",
        "Show me the system load",
        "What is the CPU usage?",
    ],
    "Memory": [
        "What is the available memory?",
        "Show me memory usage percentage",
        "How much cache memory is being used?",
    ],
    "Disk": [
        "What is the disk usage?",
        "Show me disk read rate",
        "What is the disk write speed?",
    ],
    "Network": [
        "Show me network traffic",
        "What is the network receive rate?",
        "Are there any network errors?",
    ],
    "Processes": [
        "How many processes are running?",
        "Show me blocked processes",
    ],
    "System": [
        "What is the context switch rate?",
        "Show me interrupt rate",
    ],
}


async def test_query(question: str) -> dict:
    """Send a test query to the agent."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                AGENT_URL,
                json={"question": question, "context": {}},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}


async def main():
    """Run all test queries."""
    print("=" * 80)
    print("Enhanced Metrics Agent Test Suite")
    print("=" * 80)
    print()

    total_tests = sum(len(queries) for queries in TEST_QUERIES.values())
    passed = 0
    failed = 0

    for category, queries in TEST_QUERIES.items():
        print(f"\n📊 Testing {category} Metrics")
        print("-" * 80)

        for query in queries:
            print(f"\n  Question: {query}")
            result = await test_query(query)

            if "error" in result:
                print(f"  ❌ FAILED: {result['error']}")
                failed += 1
            else:
                # Check if metrics were actually queried
                response_data = result.get("response", {})
                tools_used = response_data.get("metadata", {}).get("tools_used", [])
                if "metrics" in tools_used or "metrics_instant" in tools_used:
                    print(f"  ✅ PASSED")
                    print(f"  Tools: {', '.join(tools_used)}")
                    passed += 1
                else:
                    print(f"  ⚠️  WARNING: No metrics tool used")
                    print(f"  Tools: {', '.join(tools_used)}")
                    failed += 1

    print("\n" + "=" * 80)
    print(f"Test Results: {passed}/{total_tests} passed, {failed}/{total_tests} failed")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
