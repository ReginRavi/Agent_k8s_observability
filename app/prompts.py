"""
Prompts for K8s Observability AI Agent.

This module contains all prompts used by the agent for interacting with Gemini.
Centralizing prompts makes them easier to customize, version, and A/B test.
"""

from typing import Dict, Any, List


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

SYSTEM_PROMPT = """You are an expert Kubernetes and observability AI assistant for SREs.

You have access to Prometheus metrics, Kubernetes API, Loki logs, and Alertmanager alerts.

**Response Format:**
1. **Summary** (2-3 sentences max): Key findings and current state
2. **Key Metrics**: Most important values only
3. **Action Required** (if any): Brief next steps

**Guidelines:**
- Be concise and direct
- Focus on actionable insights
- Highlight only critical anomalies
- Skip obvious or redundant information
- Use bullet points, not paragraphs
- State current values with units clearly

Remember: SREs need fast, actionable information - not essays.
"""


# Alternative system prompts for different use cases
SYSTEM_PROMPT_CONCISE = """You are a Kubernetes observability expert. Analyze the provided metrics, logs, and events, then give concise, actionable recommendations. Focus on root causes and next steps. Be brief but thorough."""


SYSTEM_PROMPT_DETAILED = """You are an expert SRE specialized in Kubernetes observability and incident response.

Your expertise includes:
- Deep understanding of Kubernetes internals (scheduling, networking, storage)
- Prometheus metrics analysis and PromQL
- Log analysis and pattern recognition
- Alert correlation and root cause analysis
- Performance optimization and capacity planning

When analyzing issues:
1. Start with the most likely causes based on symptoms
2. Correlate data across multiple sources (metrics, logs, events, alerts)
3. Consider both application-level and infrastructure-level factors
4. Think about recent changes, deployments, or configuration updates
5. Evaluate resource constraints (CPU, memory, network, storage)
6. Check for common Kubernetes issues (image pull errors, probe failures, OOM kills)

Provide detailed analysis with:
- Clear problem statement
- Evidence from data
- Step-by-step reasoning
- Multiple hypotheses if applicable
- Prioritized remediation steps
- Preventive measures for the future
"""


# =============================================================================
# TOOL SELECTION PROMPTS (for future LLM-based tool selection)
# =============================================================================

TOOL_SELECTION_PROMPT = """Given the following user question about a Kubernetes system, determine which tools should be called to gather relevant information.

Available tools:
1. **k8s_pods**: Query pod state (status, restarts, resource usage, conditions)
2. **k8s_events**: Query Kubernetes events (pod lifecycle, scheduling, errors)
3. **metrics**: Query Prometheus for time-series metrics (CPU, memory, network, custom metrics)
4. **metrics_instant**: Query Prometheus for current/instant metric values
5. **logs**: Query Loki for application and system logs
6. **alerts**: Query Alertmanager for active firing alerts
7. **kb**: Search knowledge base for runbooks and documentation

User Question: {question}
Context: {context}

Return a JSON array of tool names to call, in order of priority.
Example: ["k8s_pods", "k8s_events", "metrics", "alerts"]

Consider:
- Always include k8s_pods for pod-related questions
- Use metrics_instant for "current" or "now" questions
- Use metrics for trends and historical analysis
- Include logs if errors, exceptions, or crashes are mentioned
- Include k8s_events for restart, scheduling, or lifecycle issues
- Include alerts to check for known issues
- Include kb for "how to" or procedural questions

Selected tools (JSON array):"""


# =============================================================================
# QUERY BUILDING PROMPTS
# =============================================================================

PROMETHEUS_QUERY_BUILDER_PROMPT = """Given the user's question and context, generate an appropriate PromQL query.

User Question: {question}
Namespace: {namespace}
Service: {service}
Context: {context}

Available metrics examples:
- CPU: container_cpu_usage_seconds_total, node_cpu_seconds_total, node_load1, node_load5, node_load15
- Memory: container_memory_usage_bytes, container_memory_working_set_bytes, node_memory_MemTotal_bytes, node_memory_MemAvailable_bytes, node_memory_Cached_bytes, node_memory_Buffers_bytes
- Network: node_network_receive_bytes_total, node_network_transmit_bytes_total, node_network_receive_errs_total, node_network_transmit_errs_total
- Disk: node_disk_read_bytes_total, node_disk_written_bytes_total, node_filesystem_avail_bytes, node_filesystem_size_bytes
- Processes: node_procs_running, node_procs_blocked
- System: node_context_switches_total, node_intr_total, node_systemd_unit_state
- Pod restarts: kube_pod_container_status_restarts_total
- Pod status: kube_pod_status_phase

Return only the PromQL query, nothing else.
Example: rate(container_cpu_usage_seconds_total{{namespace="production"}}[5m])

PromQL Query:"""


LOGQL_QUERY_BUILDER_PROMPT = """Given the user's question and context, generate an appropriate LogQL query.

User Question: {question}
Namespace: {namespace}
Pod: {pod}
Context: {context}

LogQL syntax:
- Label filters: {{namespace="prod", pod=~"api.*"}}
- Line filters: |~ "error" or |= "exception"
- JSON parsing: | json | level="error"
- Regex: |~ "(?i)(error|exception|fail)"

Return only the LogQL query, nothing else.
Example: {{namespace="production", pod=~"api.*"}} |~ "(?i)(error|exception)"

LogQL Query:"""


# =============================================================================
# RESPONSE PARSING PROMPTS
# =============================================================================

RECOMMENDATION_EXTRACTION_PROMPT = """Given the following AI response about a Kubernetes issue, extract the key recommendations as a bullet-point list.

AI Response:
{response}

Return only the recommendations, one per line, starting with a dash (-).
Example:
- Check pod logs for OutOfMemory errors
- Increase memory limits in deployment spec
- Review application memory usage patterns

Recommendations:"""


CONFIDENCE_ASSESSMENT_PROMPT = """Based on the following analysis and available data, assess the confidence level of the diagnosis.

Analysis: {analysis}
Data Quality: {data_quality}

Return one of: high, medium, low

Criteria:
- High: Clear evidence, consistent data, known issue pattern
- Medium: Some evidence, partial data, probable cause identified
- Low: Insufficient data, conflicting signals, multiple possibilities

Confidence:"""


# =============================================================================
# SPECIALIZED PROMPTS FOR SPECIFIC SCENARIOS
# =============================================================================

POD_RESTART_ANALYSIS_PROMPT = """Analyze the following data about pod restarts and provide a root cause analysis.

Pod State: {pod_state}
Events: {events}
Metrics: {metrics}
Logs: {logs}

Focus on:
1. Restart patterns (frequency, timing, affected containers)
2. Exit codes and termination reasons (OOMKilled, CrashLoopBackOff, Error)
3. Resource constraints (CPU throttling, memory pressure)
4. Liveness/readiness probe failures
5. Application errors in logs

Provide:
- Root cause (most likely)
- Supporting evidence
- Remediation steps
"""


HIGH_CPU_ANALYSIS_PROMPT = """Analyze the following data about high CPU usage and provide insights.

Current CPU Metrics: {current_metrics}
CPU Trends: {cpu_trends}
Pod State: {pod_state}
Alerts: {alerts}

Determine:
1. Which pods/containers have high CPU
2. Is this normal for the workload?
3. Recent changes or traffic spikes
4. CPU throttling occurring?
5. Application-level issues (inefficient code, loops)

Provide:
- Current state assessment
- Trend analysis (increasing/stable/decreasing)
- Recommended actions
"""


MEMORY_LEAK_ANALYSIS_PROMPT = """Analyze the following data for potential memory leaks.

Memory Trends: {memory_trends}
OOMKill Events: {oom_events}
Pod Restarts: {restarts}
Container Memory Limits: {limits}

Look for:
1. Steady memory growth over time
2. Memory not being released
3. Correlation between memory growth and restarts
4. Difference between working set and RSS
5. Container memory limits and requests

Provide:
- Is this a memory leak? (Yes/No/Possibly)
- Evidence supporting the conclusion
- Immediate actions
- Long-term solutions
"""


ALERT_TRIAGE_PROMPT = """Triage the following alerts and prioritize them for investigation.

Active Alerts: {alerts}
System State: {system_state}

For each alert, provide:
1. Severity assessment (Critical/High/Medium/Low)
2. Potential impact
3. Likely root cause
4. Investigation priority (1-5, 1 being highest)
5. Immediate action required

Format as a prioritized list.
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_system_prompt(style: str = "default") -> str:
    """
    Get the system prompt based on the specified style.
    
    Args:
        style: One of "default", "concise", "detailed"
        
    Returns:
        The corresponding system prompt string
    """
    prompts = {
        "default": SYSTEM_PROMPT,
        "concise": SYSTEM_PROMPT_CONCISE,
        "detailed": SYSTEM_PROMPT_DETAILED,
    }
    return prompts.get(style, SYSTEM_PROMPT)


def format_tool_selection_prompt(question: str, context: Dict[str, Any]) -> str:
    """
    Format the tool selection prompt with the given question and context.
    
    Args:
        question: User's question
        context: Additional context (namespace, service, etc.)
        
    Returns:
        Formatted prompt string
    """
    return TOOL_SELECTION_PROMPT.format(
        question=question,
        context=context
    )


def format_prometheus_query_prompt(
    question: str,
    namespace: str = None,
    service: str = None,
    context: Dict[str, Any] = None
) -> str:
    """
    Format the Prometheus query builder prompt.
    
    Args:
        question: User's question
        namespace: Kubernetes namespace
        service: Service/pod name
        context: Additional context
        
    Returns:
        Formatted prompt string
    """
    return PROMETHEUS_QUERY_BUILDER_PROMPT.format(
        question=question,
        namespace=namespace or "None",
        service=service or "None",
        context=context or {}
    )


def format_logql_query_prompt(
    question: str,
    namespace: str = None,
    pod: str = None,
    context: Dict[str, Any] = None
) -> str:
    """
    Format the LogQL query builder prompt.
    
    Args:
        question: User's question
        namespace: Kubernetes namespace
        pod: Pod name
        context: Additional context
        
    Returns:
        Formatted prompt string
    """
    return LOGQL_QUERY_BUILDER_PROMPT.format(
        question=question,
        namespace=namespace or "None",
        pod=pod or "None",
        context=context or {}
    )


def format_scenario_prompt(
    scenario: str,
    data: Dict[str, Any]
) -> str:
    """
    Format a specialized scenario prompt with data.
    
    Args:
        scenario: Scenario type (pod_restart, high_cpu, memory_leak, alert_triage)
        data: Data dictionary with relevant information
        
    Returns:
        Formatted prompt string
    """
    scenario_prompts = {
        "pod_restart": POD_RESTART_ANALYSIS_PROMPT,
        "high_cpu": HIGH_CPU_ANALYSIS_PROMPT,
        "memory_leak": MEMORY_LEAK_ANALYSIS_PROMPT,
        "alert_triage": ALERT_TRIAGE_PROMPT,
    }
    
    prompt_template = scenario_prompts.get(scenario)
    if not prompt_template:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    return prompt_template.format(**data)


# =============================================================================
# PROMPT VERSIONS (for A/B testing)
# =============================================================================

PROMPT_VERSIONS = {
    "v1": SYSTEM_PROMPT,
    "v2_concise": SYSTEM_PROMPT_CONCISE,
    "v3_detailed": SYSTEM_PROMPT_DETAILED,
}


def get_prompt_version(version: str = "v1") -> str:
    """
    Get a specific version of the system prompt.
    
    Useful for A/B testing different prompt variations.
    
    Args:
        version: Version identifier (v1, v2_concise, v3_detailed)
        
    Returns:
        The prompt for that version
    """
    return PROMPT_VERSIONS.get(version, PROMPT_VERSIONS["v1"])
