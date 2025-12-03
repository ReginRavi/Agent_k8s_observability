#!/usr/bin/env python3
"""
Interactive Chat Client for K8s Observability Agent
"""

import asyncio
import httpx
import sys
import os
import json

# Configuration
AGENT_PORT = os.getenv("AGENT_PORT", "8081")
BASE_URL = f"http://localhost:{AGENT_PORT}"

async def chat_session():
    print(f"\n🤖 K8s Observability Agent (Port {AGENT_PORT})")
    print("==========================================")
    print("Type 'quit', 'exit', or Ctrl+C to stop.")
    print("Type 'clear' to clear the screen.")
    print("==========================================\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Check health first
        try:
            resp = await client.get(f"{BASE_URL}/health")
            resp.raise_for_status()
            print("✅ Connected to agent successfully!\n")
        except Exception as e:
            print(f"❌ Could not connect to agent at {BASE_URL}")
            print(f"Error: {e}")
            print("\nMake sure the agent is running!")
            return

        while True:
            try:
                question = input("You: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit']:
                    print("\nGoodbye! 👋")
                    break
                
                if question.lower() == 'clear':
                    os.system('clear')
                    continue

                print("\n🤖 Agent is thinking...", end="", flush=True)
                
                response = await client.post(
                    f"{BASE_URL}/chat",
                    json={
                        "question": question,
                        "namespace": "default" # Default namespace
                    }
                )
                
                print("\r" + " " * 20 + "\r", end="", flush=True) # Clear "thinking" line
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("response", {}).get("answer", "No answer provided.")
                    print(f"🤖 Agent:\n{answer}\n")
                    
                    # Show tools used if any
                    tools = data.get("response", {}).get("tool_results", [])
                    if tools:
                        tool_names = [t["tool_name"] for t in tools]
                        print(f"[Tools used: {', '.join(tool_names)}]\n")
                        
                else:
                    print(f"❌ Error {response.status_code}: {response.text}\n")

            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    try:
        asyncio.run(chat_session())
    except KeyboardInterrupt:
        pass
