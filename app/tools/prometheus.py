"""
Prometheus metrics query adapter.

Provides async interface to query Prometheus for metrics data.
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..config import Config

logger = logging.getLogger(__name__)


async def metrics_query(
    query: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    step: str = "60s",
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Query Prometheus for metrics data.
    
    Args:
        query: PromQL query string
        start_time: Start time for range query (defaults to lookback from now)
        end_time: End time for range query (defaults to now)
        step: Query resolution step (e.g., "60s", "5m")
        timeout: Request timeout in seconds
        
    Returns:
        Dict containing:
            - success: bool
            - data: Prometheus query result
            - error: Optional error message
            - query: The executed query
    """
    if timeout is None:
        timeout = Config.PROMETHEUS_TIMEOUT
    
    # Default time range
    if end_time is None:
        end_time = datetime.utcnow()
    if start_time is None:
        start_time = end_time - timedelta(minutes=Config.DEFAULT_LOOKBACK_MINUTES)
    
    # Build query URL
    url = f"{Config.PROMETHEUS_URL}/api/v1/query_range"
    
    params = {
        "query": query,
        "start": start_time.timestamp(),
        "end": end_time.timestamp(),
        "step": step,
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("status") == "success":
                return {
                    "success": True,
                    "data": result.get("data", {}),
                    "query": query,
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "step": step
                    }
                }
            else:
                error_msg = result.get("error", "Unknown Prometheus error")
                logger.error(f"Prometheus query failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "query": query
                }
                
    except httpx.TimeoutException:
        logger.error(f"Prometheus query timeout: {query}")
        return {
            "success": False,
            "error": f"Query timeout after {timeout}s",
            "query": query
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"Prometheus HTTP error: {e.response.status_code}")
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "query": query
        }
    except Exception as e:
        logger.error(f"Prometheus query error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


async def instant_query(query: str, time: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Execute an instant Prometheus query.
    
    Args:
        query: PromQL query string
        time: Evaluation timestamp (defaults to now)
        
    Returns:
        Dict containing query result
    """
    url = f"{Config.PROMETHEUS_URL}/api/v1/query"
    
    params = {"query": query}
    if time:
        params["time"] = time.timestamp()
    
    try:
        async with httpx.AsyncClient(timeout=Config.PROMETHEUS_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("status") == "success":
                return {
                    "success": True,
                    "data": result.get("data", {}),
                    "query": query
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "query": query
                }
                
    except Exception as e:
        logger.error(f"Instant query error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


def build_k8s_metric_query(
    metric_name: str,
    namespace: Optional[str] = None,
    pod: Optional[str] = None,
    container: Optional[str] = None,
    additional_labels: Optional[Dict[str, str]] = None
) -> str:
    """
    Helper to build PromQL queries for Kubernetes metrics.
    
    Args:
        metric_name: Base metric name (e.g., "container_cpu_usage_seconds_total")
        namespace: Kubernetes namespace filter
        pod: Pod name filter (supports regex)
        container: Container name filter
        additional_labels: Additional label filters
        
    Returns:
        PromQL query string
    """
    labels = []
    
    if namespace:
        labels.append(f'namespace="{namespace}"')
    if pod:
        labels.append(f'pod=~"{pod}"')
    if container:
        labels.append(f'container="{container}"')
    if additional_labels:
        for key, value in additional_labels.items():
            labels.append(f'{key}="{value}"')
    
    if labels:
        return f'{metric_name}{{{",".join(labels)}}}'
    else:
        return metric_name
