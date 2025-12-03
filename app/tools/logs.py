"""
Logs query adapter for Loki/Elastic.

Currently a stub implementation - will be enhanced with real Loki/Elastic integration.
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..config import Config

logger = logging.getLogger(__name__)


async def logs_query(
    query: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    namespace: Optional[str] = None,
    pod: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query logs from Loki.
    
    Args:
        query: LogQL query string
        start_time: Start time for query
        end_time: End time for query
        limit: Maximum number of log lines to return
        namespace: Kubernetes namespace filter
        pod: Pod name filter
        
    Returns:
        Dict containing:
            - success: bool
            - logs: List of log entries
            - error: Optional error message
    """
    # Default time range
    if end_time is None:
        end_time = datetime.utcnow()
    if start_time is None:
        start_time = end_time - timedelta(minutes=Config.DEFAULT_LOOKBACK_MINUTES)
    
    # Build LogQL query with filters
    logql_query = query
    
    # Add namespace/pod filters if not already in query
    if namespace and "namespace=" not in query:
        if "{" in logql_query:
            logql_query = logql_query.replace("{", f'{{namespace="{namespace}",', 1)
        else:
            logql_query = f'{{namespace="{namespace}"}} {logql_query}'
    
    if pod and "pod=" not in query:
        if "{" in logql_query:
            logql_query = logql_query.replace("{", f'{{pod=~"{pod}",', 1)
        else:
            logql_query = f'{{pod=~"{pod}"}} {logql_query}'
    
    url = f"{Config.LOKI_URL}/loki/api/v1/query_range"
    
    params = {
        "query": logql_query,
        "start": int(start_time.timestamp() * 1e9),  # Loki uses nanoseconds
        "end": int(end_time.timestamp() * 1e9),
        "limit": limit,
        "direction": "backward"  # Most recent first
    }
    
    try:
        async with httpx.AsyncClient(timeout=Config.LOKI_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("status") == "success":
                # Parse Loki response
                logs = []
                data = result.get("data", {})
                
                for stream in data.get("result", []):
                    stream_labels = stream.get("stream", {})
                    
                    for entry in stream.get("values", []):
                        timestamp_ns, log_line = entry
                        logs.append({
                            "timestamp": datetime.fromtimestamp(int(timestamp_ns) / 1e9).isoformat(),
                            "line": log_line,
                            "labels": stream_labels
                        })
                
                return {
                    "success": True,
                    "logs": logs,
                    "count": len(logs),
                    "query": logql_query,
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                }
            else:
                error_msg = result.get("error", "Unknown Loki error")
                logger.error(f"Loki query failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "query": logql_query,
                    "logs": []
                }
                
    except httpx.TimeoutException:
        logger.error(f"Loki query timeout: {logql_query}")
        return {
            "success": False,
            "error": f"Query timeout after {Config.LOKI_TIMEOUT}s",
            "query": logql_query,
            "logs": []
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"Loki HTTP error: {e.response.status_code}")
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "query": logql_query,
            "logs": []
        }
    except Exception as e:
        logger.error(f"Loki query error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": logql_query,
            "logs": []
        }


def build_logql_query(
    namespace: Optional[str] = None,
    pod: Optional[str] = None,
    container: Optional[str] = None,
    level: Optional[str] = None,
    search_term: Optional[str] = None
) -> str:
    """
    Helper to build LogQL queries.
    
    Args:
        namespace: Kubernetes namespace
        pod: Pod name (supports regex)
        container: Container name
        level: Log level filter (error, warn, info, etc.)
        search_term: Text to search for in logs
        
    Returns:
        LogQL query string
    """
    labels = []
    
    if namespace:
        labels.append(f'namespace="{namespace}"')
    if pod:
        labels.append(f'pod=~"{pod}"')
    if container:
        labels.append(f'container="{container}"')
    
    # Build base query
    if labels:
        query = f'{{{",".join(labels)}}}'
    else:
        query = '{job="kubernetes-pods"}'
    
    # Add filters
    filters = []
    if level:
        filters.append(f'|~ "(?i)(level|severity).*{level}"')
    if search_term:
        filters.append(f'|~ "{search_term}"')
    
    if filters:
        query += " " + " ".join(filters)
    
    return query
