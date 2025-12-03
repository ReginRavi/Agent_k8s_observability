#!/usr/bin/env python3
"""
Test script to demonstrate current metrics queries.

This script shows how the agent handles questions about current/instant metrics
vs historical/trend metrics.
"""

import asyncio
import httpx
import json
from datetime import datetime


import os

# Read port from env or default to 8000
PORT = os.getenv("AGENT_PORT", "8000")
BASE_URL = f"http://localhost:{PORT}"


async def ask_question(question: str, namespace: str = None, service: str = None):
    """
    Send a question to the agent and print the response.
    """
    print(f"\n{'='*80}")
    print(f"Question: {question}")
    print(f"{'='*80}")
    
    payload = {
        "question": question,
        "namespace": namespace,
        "service": service,
        "time_range_minutes": 15,
        "include_logs": False
    }
    
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{BASE_URL}/chat", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Print the response
            print(f"\n📊 Response:")
            print(f"{result['response']['answer']}\n")
            
            print(f"🔧 Tools Used:")
            for tool in result['response']['tool_results']:
                status = "✅" if tool['success'] else "❌"
                print(f"  {status} {tool['tool_name']} ({tool['execution_time_ms']:.0f}ms)")
            
            if result['response']['recommendations']:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(result['response']['recommendations'], 1):
                    print(f"  {i}. {rec}")
            
            print(f"\n🎯 Confidence: {result['response'].get('confidence', 'unknown')}")
            
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def main():
    """
    Run example queries demonstrating current vs historical metrics.
    """
    
    print("=" * 80)
    print("K8s Observability Agent - Current Metrics Test")
    print("=" * 80)
    print("\nThis script demonstrates how the agent handles current metric queries.")
    print("Make sure the agent is running on http://localhost:8000")
    print()
    
    # Test 1: Current CPU usage (instant query)
    await ask_question(
        question="What is the current CPU usage?",
        namespace="default"
    )
    
    # Test 2: Current memory usage for a specific pod (instant query)
    await ask_question(
        question="Show me the current memory usage for the api pod",
        namespace="production",
        service="api"
    )
    
    # Test 3: CPU usage trend (range query)
    await ask_question(
        question="How has CPU usage changed in the last 15 minutes?",
        namespace="default"
    )
    
    # Test 4: Current vs normal comparison
    await ask_question(
        question="What is the current memory usage right now?",
        namespace="production"
    )
    
    # Test 5: Multiple current metrics
    await ask_question(
        question="What are the current CPU and memory metrics?",
        namespace="default"
    )
    
    # Test 6: Current metric with threshold question
    await ask_question(
        question="Is the current CPU usage high?",
        namespace="production"
    )
    
    print(f"\n{'='*80}")
    print("Test complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
