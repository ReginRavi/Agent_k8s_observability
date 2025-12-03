"""
Basic tests for the K8s Observability Agent.

Run with: pytest test_agent.py
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.models import ChatRequest, ToolResult
from app.agent import ObservabilityAgent


@pytest.fixture
def sample_chat_request():
    """Create a sample chat request."""
    return ChatRequest(
        question="Why is my pod restarting?",
        namespace="default",
        service="test-app",
        time_range_minutes=15
    )


@pytest.fixture
def mock_tool_results():
    """Create mock tool results."""
    return [
        ToolResult(
            tool_name="k8s_pods",
            success=True,
            data={
                "pods": [
                    {
                        "name": "test-app-123",
                        "namespace": "default",
                        "phase": "Running",
                        "restart_count": 5
                    }
                ]
            },
            error=None,
            execution_time_ms=100.0
        ),
        ToolResult(
            tool_name="alerts",
            success=True,
            data={"alerts": [], "count": 0},
            error=None,
            execution_time_ms=50.0
        )
    ]


class TestObservabilityAgent:
    """Test the ObservabilityAgent class."""
    
    def test_determine_tools_basic(self, sample_chat_request):
        """Test basic tool determination."""
        agent = ObservabilityAgent()
        tools = agent._determine_tools(sample_chat_request)
        
        # Should always include k8s_pods and alerts
        assert "k8s_pods" in tools
        assert "alerts" in tools
    
    def test_determine_tools_with_metrics(self):
        """Test tool determination with metrics keywords."""
        agent = ObservabilityAgent()
        request = ChatRequest(
            question="Why is CPU usage high?",
            time_range_minutes=15
        )
        tools = agent._determine_tools(request)
        
        assert "metrics" in tools
    
    def test_determine_tools_with_logs(self):
        """Test tool determination with log keywords."""
        agent = ObservabilityAgent()
        request = ChatRequest(
            question="Show me error logs",
            include_logs=True,
            time_range_minutes=15
        )
        tools = agent._determine_tools(request)
        
        assert "logs" in tools
    
    def test_build_metrics_query_cpu(self):
        """Test building CPU metrics query."""
        agent = ObservabilityAgent()
        request = ChatRequest(
            question="What's the CPU usage?",
            service="my-app",
            time_range_minutes=15
        )
        query = agent._build_metrics_query(request)
        
        assert "cpu" in query.lower()
        assert "my-app" in query
    
    def test_build_metrics_query_memory(self):
        """Test building memory metrics query."""
        agent = ObservabilityAgent()
        request = ChatRequest(
            question="Check memory usage",
            service="my-app",
            time_range_minutes=15
        )
        query = agent._build_metrics_query(request)
        
        assert "memory" in query.lower()
    
    def test_build_context(self, sample_chat_request, mock_tool_results):
        """Test building context for Gemini."""
        agent = ObservabilityAgent()
        context = agent._build_context(sample_chat_request, mock_tool_results)
        
        assert "Why is my pod restarting?" in context
        assert "default" in context
        assert "test-app" in context
        assert "k8s_pods" in context
        assert "alerts" in context
    
    def test_parse_gemini_response_with_recommendations(self):
        """Test parsing Gemini response with recommendations."""
        agent = ObservabilityAgent()
        response = """
        Summary: The pod is restarting due to OOMKilled events.
        
        Recommendations:
        - Increase memory limits
        - Check for memory leaks
        - Review application logs
        """
        
        answer, recommendations, confidence = agent._parse_gemini_response(response)
        
        assert len(recommendations) == 3
        assert "Increase memory limits" in recommendations
        assert "Check for memory leaks" in recommendations
    
    def test_parse_gemini_response_confidence(self):
        """Test confidence detection in response."""
        agent = ObservabilityAgent()
        
        # High confidence
        response_high = "The issue is clearly caused by memory limits."
        _, _, confidence = agent._parse_gemini_response(response_high)
        assert confidence == "high"
        
        # Low confidence
        response_low = "The data is insufficient to determine the cause."
        _, _, confidence = agent._parse_gemini_response(response_low)
        assert confidence == "low"


class TestToolAdapters:
    """Test tool adapter functions."""
    
    @pytest.mark.asyncio
    async def test_metrics_query_structure(self):
        """Test that metrics_query returns proper structure."""
        from app.tools.prometheus import metrics_query
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = {
                "status": "success",
                "data": {"result": []}
            }
            mock_response.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await metrics_query("up")
            
            assert "success" in result
            assert "data" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_k8s_pods_query_structure(self):
        """Test that k8s_state_query_pods returns proper structure."""
        from app.tools.k8s_state import k8s_state_query_pods
        
        with patch('app.config.KubernetesClientManager.get_core_v1_api') as mock_k8s:
            # Mock K8s API response
            mock_api = Mock()
            mock_pod_list = Mock()
            mock_pod_list.items = []
            mock_api.list_pod_for_all_namespaces.return_value = mock_pod_list
            mock_k8s.return_value = mock_api
            
            result = await k8s_state_query_pods()
            
            assert "success" in result
            assert "pods" in result


class TestModels:
    """Test Pydantic models."""
    
    def test_chat_request_validation(self):
        """Test ChatRequest validation."""
        # Valid request
        request = ChatRequest(
            question="Test question",
            namespace="default"
        )
        assert request.question == "Test question"
        assert request.namespace == "default"
        assert request.time_range_minutes == 15  # default
    
    def test_chat_request_time_range_limits(self):
        """Test time range validation."""
        # Should fail if time_range_minutes > 1440
        with pytest.raises(Exception):
            ChatRequest(
                question="Test",
                time_range_minutes=2000
            )
    
    def test_tool_result_model(self):
        """Test ToolResult model."""
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            data={"key": "value"},
            error=None,
            execution_time_ms=100.0
        )
        
        assert result.tool_name == "test_tool"
        assert result.success is True
        assert result.data["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
