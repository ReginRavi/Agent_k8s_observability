"""
Pydantic models for API requests and responses.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for /chat endpoint."""
    
    question: str = Field(
        ...,
        description="Natural language question about system health or incidents",
        min_length=1
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional context (service, namespace, time window, etc.)"
    )
    
    namespace: Optional[str] = Field(
        default=None,
        description="Kubernetes namespace to focus on"
    )
    
    service: Optional[str] = Field(
        default=None,
        description="Service or workload name to focus on"
    )
    
    time_range_minutes: Optional[int] = Field(
        default=15,
        description="Time range to look back in minutes",
        ge=1,
        le=1440  # Max 24 hours
    )
    
    include_logs: bool = Field(
        default=False,
        description="Whether to include log analysis"
    )
    
    include_traces: bool = Field(
        default=False,
        description="Whether to include trace analysis"
    )


class ToolResult(BaseModel):
    """Result from a tool adapter."""
    
    tool_name: str = Field(..., description="Name of the tool that was called")
    success: bool = Field(..., description="Whether the tool call succeeded")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Tool result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class AgentResponse(BaseModel):
    """Response from the agent orchestrator."""
    
    answer: str = Field(..., description="Natural language answer from the agent")
    
    tool_results: List[ToolResult] = Field(
        default_factory=list,
        description="Results from all tool calls"
    )
    
    confidence: Optional[str] = Field(
        default=None,
        description="Agent's confidence level (high/medium/low)"
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommended next steps"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (model used, tokens, etc.)"
    )


class ChatResponse(BaseModel):
    """Response model for /chat endpoint."""
    
    response: AgentResponse = Field(..., description="Agent response")
    request_id: str = Field(..., description="Unique request ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    version: str = Field(..., description="Agent version")
    checks: Dict[str, bool] = Field(
        default_factory=dict,
        description="Individual health checks"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


class MetricsQueryParams(BaseModel):
    """Parameters for Prometheus metrics query."""
    
    query: str = Field(..., description="PromQL query")
    start_time: Optional[datetime] = Field(default=None, description="Start time for range query")
    end_time: Optional[datetime] = Field(default=None, description="End time for range query")
    step: str = Field(default="60s", description="Query resolution step")


class LogsQueryParams(BaseModel):
    """Parameters for logs query (Loki/Elastic)."""
    
    query: str = Field(..., description="LogQL or query string")
    start_time: Optional[datetime] = Field(default=None, description="Start time")
    end_time: Optional[datetime] = Field(default=None, description="End time")
    limit: int = Field(default=100, description="Maximum number of log lines", ge=1, le=1000)
    namespace: Optional[str] = Field(default=None, description="Kubernetes namespace filter")
    pod: Optional[str] = Field(default=None, description="Pod name filter")


class K8sResourceFilter(BaseModel):
    """Filter parameters for Kubernetes resource queries."""
    
    namespace: Optional[str] = Field(default=None, description="Namespace filter")
    label_selector: Optional[str] = Field(default=None, description="Label selector")
    field_selector: Optional[str] = Field(default=None, description="Field selector")
