"""
Example usage of the K8s Observability Agent.

This script demonstrates how to interact with the agent API.
"""

import httpx
import asyncio
import json


async def ask_agent(question: str, namespace: str = None, service: str = None):
    """
    Ask the agent a question.
    
    Args:
        question: Natural language question
        namespace: Optional Kubernetes namespace
        service: Optional service/pod name
    """
    url = "http://localhost:8000/chat"
    
    payload = {
        "question": question,
        "time_range_minutes": 30,
        "include_logs": True
    }
    
    if namespace:
        payload["namespace"] = namespace
    if service:
        payload["service"] = service
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


async def main():
    """Run example queries."""
    
    print("=" * 80)
    print("K8s Observability Agent - Example Usage")
    print("=" * 80)
    print()
    
    # Example 1: General question
    print("Example 1: General cluster health")
    print("-" * 80)
    result = await ask_agent("Are there any alerts firing right now?")
    print(f"Answer: {result['response']['answer'][:200]}...")
    print(f"Tools used: {result['response']['metadata']['tools_used']}")
    print()
    
    # Example 2: Namespace-specific question
    print("Example 2: Namespace-specific query")
    print("-" * 80)
    result = await ask_agent(
        "What's the status of pods in this namespace?",
        namespace="default"
    )
    print(f"Answer: {result['response']['answer'][:200]}...")
    print(f"Recommendations: {result['response']['recommendations']}")
    print()
    
    # Example 3: Service-specific question
    print("Example 3: Service-specific troubleshooting")
    print("-" * 80)
    result = await ask_agent(
        "Why is this pod restarting?",
        namespace="default",
        service="my-app"
    )
    print(f"Answer: {result['response']['answer'][:200]}...")
    print(f"Confidence: {result['response']['confidence']}")
    print()
    
    # Example 4: Performance question
    print("Example 4: Performance analysis")
    print("-" * 80)
    result = await ask_agent(
        "Is there high CPU usage anywhere?",
        namespace="default"
    )
    print(f"Answer: {result['response']['answer'][:200]}...")
    print()
    
    print("=" * 80)
    print("Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
