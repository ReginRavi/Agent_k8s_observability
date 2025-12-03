"""
Agent orchestrator with Gemini 3 integration.

This module implements the core agent logic:
1. Receives user questions
2. Determines which tools to call
3. Calls observability backends (metrics, logs, K8s, alerts)
4. Sends context to Gemini 3 for reasoning
5. Returns structured response
"""

import httpx
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from .config import Config
from .models import ChatRequest, AgentResponse, ToolResult
from .prompts import get_system_prompt
from .tools import (
    metrics_query,
    instant_query,
    k8s_state_query_pods,
    k8s_state_query_events,
    logs_query,
    alerts_list,
    kb_search
)

logger = logging.getLogger(__name__)



class ObservabilityAgent:
    """Main agent orchestrator."""
    
    def __init__(self):
        self.gemini_api_key = Config.GEMINI_API_KEY
        self.gemini_model = Config.GEMINI_MODEL
        self.gemini_endpoint = Config.GEMINI_API_ENDPOINT
    
    async def process_query(self, request: ChatRequest) -> AgentResponse:
        """
        Process a user query through the agent pipeline.
        
        Args:
            request: ChatRequest with user question and context
            
        Returns:
            AgentResponse with answer and tool results
        """
        logger.info(f"Processing query: {request.question}")
        
        # Step 1: Determine which tools to call based on the question
        tools_to_call = self._determine_tools(request)
        
        # Step 2: Execute tool calls
        tool_results = await self._execute_tools(tools_to_call, request)
        
        # Step 3: Build context for Gemini
        context = self._build_context(request, tool_results)
        
        # Step 4: Call Gemini for reasoning
        gemini_response = await self._call_gemini(request.question, context)
        
        # Step 5: Parse response and extract recommendations
        answer, recommendations, confidence = self._parse_gemini_response(gemini_response)
        
        return AgentResponse(
            answer=answer,
            tool_results=tool_results,
            confidence=confidence,
            recommendations=recommendations,
            metadata={
                "model": self.gemini_model,
                "tools_used": [t.tool_name for t in tool_results],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _determine_tools(self, request: ChatRequest) -> List[str]:
        """
        Determine which tools to call based on the question.
        
        This is a simple heuristic-based approach. Could be enhanced with
        an LLM-based tool selection in the future.
        """
        question_lower = request.question.lower()
        tools = []
        
        # Always check K8s state and alerts
        tools.append("k8s_pods")
        tools.append("alerts")
        
        # Check for metrics-related keywords
        if any(keyword in question_lower for keyword in [
            "cpu", "memory", "latency", "throughput", "rate", "metric",
            "performance", "slow", "high", "low", "usage", "current",
            "disk", "storage", "filesystem", "network", "traffic", "bandwidth",
            "process", "processes", "load", "interrupt", "context"
        ]):
            # Check if user is asking for current/instant values
            if any(keyword in question_lower for keyword in [
                "current", "now", "right now", "at the moment", "present"
            ]):
                tools.append("metrics_instant")
            else:
                tools.append("metrics")
        
        # Check for logs-related keywords
        if request.include_logs or any(keyword in question_lower for keyword in [
            "log", "error", "exception", "crash", "failure", "message"
        ]):
            tools.append("logs")
        
        # Check for events-related keywords
        if any(keyword in question_lower for keyword in [
            "event", "restart", "killed", "evicted", "scheduled", "failed"
        ]):
            tools.append("k8s_events")
        
        # Check for runbook/knowledge base keywords
        if any(keyword in question_lower for keyword in [
            "how to", "runbook", "procedure", "steps", "guide"
        ]):
            tools.append("kb")
        
        logger.info(f"Selected tools: {tools}")
        return tools
    
    async def _execute_tools(
        self,
        tools: List[str],
        request: ChatRequest
    ) -> List[ToolResult]:
        """Execute all selected tools and collect results."""
        results = []
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=request.time_range_minutes)
        
        # Execute tools
        for tool_name in tools:
            start = time.time()
            
            try:
                if tool_name == "k8s_pods":
                    data = await k8s_state_query_pods(
                        namespace=request.namespace,
                        pod_name=request.service
                    )
                    success = data.get("success", False)
                    error = data.get("error")
                
                elif tool_name == "k8s_events":
                    data = await k8s_state_query_events(
                        namespace=request.namespace,
                        involved_object_name=request.service,
                        lookback_minutes=request.time_range_minutes
                    )
                    success = data.get("success", False)
                    error = data.get("error")
                
                elif tool_name == "alerts":
                    data = await alerts_list(
                        namespace=request.namespace
                    )
                    success = data.get("success", False)
                    error = data.get("error")
                
                elif tool_name == "metrics":
                    # Build a relevant metrics query
                    query = self._build_metrics_query(request)
                    data = await metrics_query(
                        query=query,
                        start_time=start_time,
                        end_time=end_time
                    )
                    success = data.get("success", False)
                    error = data.get("error")
                
                elif tool_name == "metrics_instant":
                    # Build a relevant metrics query for instant values
                    query = self._build_metrics_query(request)
                    data = await instant_query(query=query)
                    success = data.get("success", False)
                    error = data.get("error")
                
                elif tool_name == "logs":
                    # Build a logs query
                    query = self._build_logs_query(request)
                    data = await logs_query(
                        query=query,
                        start_time=start_time,
                        end_time=end_time,
                        namespace=request.namespace,
                        pod=request.service
                    )
                    success = data.get("success", False)
                    error = data.get("error")
                
                elif tool_name == "kb":
                    data = await kb_search(query=request.question, top_k=3)
                    success = data.get("success", False)
                    error = data.get("error")
                
                else:
                    data = {"error": f"Unknown tool: {tool_name}"}
                    success = False
                    error = f"Unknown tool: {tool_name}"
                
                execution_time = (time.time() - start) * 1000
                
                results.append(ToolResult(
                    tool_name=tool_name,
                    success=success,
                    data=data if success else None,
                    error=error,
                    execution_time_ms=execution_time
                ))
                
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {str(e)}")
                execution_time = (time.time() - start) * 1000
                results.append(ToolResult(
                    tool_name=tool_name,
                    success=False,
                    data=None,
                    error=str(e),
                    execution_time_ms=execution_time
                ))
        
        return results
    
    def _build_metrics_query(self, request: ChatRequest) -> str:
        """Build a Prometheus query based on the request."""
        question_lower = request.question.lower()
        
        # CPU Metrics
        if "cpu" in question_lower or "load" in question_lower:
            if "node" in question_lower or "idle" in question_lower or "system" in question_lower:
                if "idle" in question_lower:
                    return 'rate(node_cpu_seconds_total{mode="idle"}[1m])'
                elif "load" in question_lower:
                    if "1" in question_lower or "1m" in question_lower:
                        return 'node_load1'
                    elif "5" in question_lower or "5m" in question_lower:
                        return 'node_load5'
                    elif "15" in question_lower or "15m" in question_lower:
                        return 'node_load15'
                    else:
                        return 'node_load1'
                else:
                    return 'rate(node_cpu_seconds_total[5m])'
            elif request.service:
                return f'rate(container_cpu_usage_seconds_total{{pod=~"{request.service}.*"}}[5m])'
            else:
                return 'rate(container_cpu_usage_seconds_total[5m])'
        
        # Memory Metrics
        elif "memory" in question_lower or "mem" in question_lower or "ram" in question_lower:
            if "node" in question_lower or "system" in question_lower or "available" in question_lower:
                if "available" in question_lower:
                    return 'node_memory_MemAvailable_bytes'
                elif "total" in question_lower:
                    return 'node_memory_MemTotal_bytes'
                elif "usage" in question_lower or "used" in question_lower:
                    return '(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)'
                elif "percentage" in question_lower or "percent" in question_lower:
                    return '100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))'
                elif "cache" in question_lower:
                    return 'node_memory_Cached_bytes'
                elif "buffer" in question_lower:
                    return 'node_memory_Buffers_bytes'
                else:
                    return 'node_memory_MemAvailable_bytes'
            elif request.service:
                return f'container_memory_usage_bytes{{pod=~"{request.service}.*"}}'
            else:
                return 'container_memory_usage_bytes'
        
        # Disk/Storage Metrics
        elif "disk" in question_lower or "storage" in question_lower or "filesystem" in question_lower:
            if "read" in question_lower:
                return 'rate(node_disk_read_bytes_total[5m])'
            elif "write" in question_lower or "written" in question_lower:
                return 'rate(node_disk_written_bytes_total[5m])'
            elif "usage" in question_lower or "used" in question_lower or "space" in question_lower:
                if "percentage" in question_lower or "percent" in question_lower:
                    return '100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)'
                else:
                    return 'node_filesystem_avail_bytes{mountpoint="/"}'
            elif "iops" in question_lower:
                return 'rate(node_disk_reads_completed_total[5m]) + rate(node_disk_writes_completed_total[5m])'
            else:
                return 'rate(node_disk_read_bytes_total[5m])'
        
        # Network Metrics
        elif "network" in question_lower or "traffic" in question_lower or "bandwidth" in question_lower:
            if "receive" in question_lower or "rx" in question_lower or "download" in question_lower or "incoming" in question_lower:
                if "error" in question_lower:
                    return 'rate(node_network_receive_errs_total[5m])'
                elif "packet" in question_lower:
                    return 'rate(node_network_receive_packets_total[5m])'
                else:
                    return 'rate(node_network_receive_bytes_total[5m])'
            elif "transmit" in question_lower or "tx" in question_lower or "upload" in question_lower or "outgoing" in question_lower:
                if "error" in question_lower:
                    return 'rate(node_network_transmit_errs_total[5m])'
                elif "packet" in question_lower:
                    return 'rate(node_network_transmit_packets_total[5m])'
                else:
                    return 'rate(node_network_transmit_bytes_total[5m])'
            elif "error" in question_lower:
                return 'rate(node_network_receive_errs_total[5m]) + rate(node_network_transmit_errs_total[5m])'
            else:
                return 'rate(node_network_receive_bytes_total[5m])'
        
        # Process Metrics
        elif "process" in question_lower or "proc" in question_lower:
            if "running" in question_lower:
                return 'node_procs_running'
            elif "blocked" in question_lower:
                return 'node_procs_blocked'
            else:
                return 'node_procs_running'
        
        # System Metrics
        elif "context" in question_lower and "switch" in question_lower:
            return 'rate(node_context_switches_total[5m])'
        elif "interrupt" in question_lower:
            return 'rate(node_intr_total[5m])'
        elif "systemd" in question_lower:
            return 'node_systemd_unit_state'
        
        # Hardware Metrics
        elif "temperature" in question_lower or "temp" in question_lower:
            return 'node_hwmon_temp_celsius'
        elif "fan" in question_lower:
            return 'node_hwmon_fan_rpm'
        
        # Default: Pod restart count
        else:
            if request.service:
                return f'kube_pod_container_status_restarts_total{{pod=~"{request.service}.*"}}'
            else:
                return 'kube_pod_container_status_restarts_total'

    
    def _build_logs_query(self, request: ChatRequest) -> str:
        """Build a LogQL query based on the request."""
        question_lower = request.question.lower()
        
        # Look for error-related keywords
        if any(keyword in question_lower for keyword in ["error", "exception", "fail"]):
            return '{job="kubernetes-pods"} |~ "(?i)(error|exception|fail)"'
        else:
            return '{job="kubernetes-pods"}'
    
    def _build_context(
        self,
        request: ChatRequest,
        tool_results: List[ToolResult]
    ) -> str:
        """Build context string for Gemini from tool results."""
        context_parts = []
        
        context_parts.append("## User Question")
        context_parts.append(request.question)
        context_parts.append("")
        
        if request.namespace or request.service:
            context_parts.append("## Context")
            if request.namespace:
                context_parts.append(f"- Namespace: {request.namespace}")
            if request.service:
                context_parts.append(f"- Service/Pod: {request.service}")
            context_parts.append(f"- Time Range: Last {request.time_range_minutes} minutes")
            context_parts.append("")
        
        context_parts.append("## Tool Results")
        context_parts.append("")
        
        for result in tool_results:
            context_parts.append(f"### {result.tool_name}")
            if result.success:
                # Serialize data as JSON
                data_json = json.dumps(result.data, indent=2, default=str)
                context_parts.append(f"```json\n{data_json}\n```")
            else:
                context_parts.append(f"**Error**: {result.error}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def _call_gemini(self, question: str, context: str) -> str:
        """
        Call Gemini API for reasoning.
        
        Args:
            question: User's question
            context: Context built from tool results
            
        Returns:
            Gemini's response text
        """
        url = f"{self.gemini_endpoint}/models/{self.gemini_model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Build the prompt using centralized prompt management
        system_prompt = get_system_prompt("default")
        full_prompt = f"{system_prompt}\n\n{context}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,  # Lower temperature for more factual responses
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    params={"key": self.gemini_api_key},
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract text from response
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            return parts[0]["text"]
                
                logger.error(f"Unexpected Gemini response format: {result}")
                return "Error: Could not parse Gemini response"
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API error: {e.response.status_code} - {e.response.text}")
            return f"Error calling Gemini API: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Error calling Gemini: {str(e)}")
            return f"Error calling Gemini: {str(e)}"
    
    def _parse_gemini_response(self, response: str) -> tuple[str, List[str], str]:
        """
        Parse Gemini response to extract answer, recommendations, and confidence.
        
        Returns:
            Tuple of (answer, recommendations, confidence)
        """
        # Simple parsing - could be enhanced with structured output
        recommendations = []
        confidence = "medium"
        
        # Look for recommendations section
        if "Recommendations:" in response or "Next steps:" in response:
            lines = response.split("\n")
            in_recommendations = False
            
            for line in lines:
                if "Recommendations:" in line or "Next steps:" in line:
                    in_recommendations = True
                    continue
                
                if in_recommendations:
                    line = line.strip()
                    if line and (line.startswith("-") or line.startswith("*") or line[0].isdigit()):
                        # Remove bullet points and numbering
                        clean_line = line.lstrip("-*0123456789. ")
                        if clean_line:
                            recommendations.append(clean_line)
        
        # Determine confidence based on response content
        response_lower = response.lower()
        if any(word in response_lower for word in ["clearly", "definitely", "confirmed"]):
            confidence = "high"
        elif any(word in response_lower for word in ["unclear", "insufficient", "need more"]):
            confidence = "low"
        
        return response, recommendations, confidence
