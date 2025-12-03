"""
Alerts query adapter for Alertmanager/Grafana.

Queries active alerts from Alertmanager or Grafana alerting API.
"""

import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..config import Config

logger = logging.getLogger(__name__)


async def alerts_list(
    active_only: bool = True,
    silenced: bool = False,
    namespace: Optional[str] = None,
    severity: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query alerts from Alertmanager.
    
    Args:
        active_only: Only return active (firing) alerts
        silenced: Include silenced alerts
        namespace: Filter by Kubernetes namespace
        severity: Filter by severity label
        
    Returns:
        Dict containing:
            - success: bool
            - alerts: List of alerts
            - error: Optional error message
    """
    url = f"{Config.ALERTMANAGER_URL}/api/v2/alerts"
    
    # Build parameters
    params = {
        "active": "true" if active_only else "false",
        "silenced": "true" if silenced else "false",
        "inhibited": "false"
    }
    
    # Build matchers for filter param
    matchers = []
    if namespace:
        matchers.append(f'namespace="{namespace}"')
    if severity:
        matchers.append(f'severity="{severity}"')
    
    if matchers:
        params["filter"] = matchers
    
    try:
        async with httpx.AsyncClient(timeout=Config.ALERTMANAGER_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            alerts_data = response.json()
            
            # Parse alerts
            alerts = []
            for alert in alerts_data:
                alerts.append({
                    "name": alert.get("labels", {}).get("alertname", "Unknown"),
                    "state": alert.get("status", {}).get("state", "unknown"),
                    "severity": alert.get("labels", {}).get("severity", "unknown"),
                    "namespace": alert.get("labels", {}).get("namespace"),
                    "labels": alert.get("labels", {}),
                    "annotations": alert.get("annotations", {}),
                    "starts_at": alert.get("startsAt"),
                    "ends_at": alert.get("endsAt"),
                    "fingerprint": alert.get("fingerprint"),
                    "receivers": [r.get("name") for r in alert.get("receivers", [])]
                })
            
            return {
                "success": True,
                "alerts": alerts,
                "count": len(alerts)
            }
            
    except httpx.TimeoutException:
        logger.error("Alertmanager query timeout")
        return {
            "success": False,
            "error": f"Query timeout after {Config.ALERTMANAGER_TIMEOUT}s",
            "alerts": []
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"Alertmanager HTTP error: {e.response.status_code}")
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "alerts": []
        }
    except Exception as e:
        logger.error(f"Alertmanager query error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "alerts": []
        }


async def grafana_alerts_list(
    dashboard_uid: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query alerts from Grafana Alerting API.
    
    Args:
        dashboard_uid: Filter by dashboard UID
        state: Filter by state (alerting, ok, pending, nodata)
        
    Returns:
        Dict containing alerts from Grafana
    """
    if not Config.GRAFANA_API_KEY:
        return {
            "success": False,
            "error": "Grafana API key not configured",
            "alerts": []
        }
    
    url = f"{Config.GRAFANA_URL}/api/alerts"
    
    params = {}
    if dashboard_uid:
        params["dashboardUID"] = dashboard_uid
    if state:
        params["state"] = state
    
    headers = {
        "Authorization": f"Bearer {Config.GRAFANA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=Config.GRAFANA_TIMEOUT) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            alerts_data = response.json()
            
            alerts = []
            for alert in alerts_data:
                alerts.append({
                    "id": alert.get("id"),
                    "name": alert.get("name"),
                    "state": alert.get("state"),
                    "dashboard_uid": alert.get("dashboardUid"),
                    "panel_id": alert.get("panelId"),
                    "message": alert.get("message"),
                    "eval_date": alert.get("evalDate"),
                    "new_state_date": alert.get("newStateDate")
                })
            
            return {
                "success": True,
                "alerts": alerts,
                "count": len(alerts),
                "source": "grafana"
            }
            
    except Exception as e:
        logger.error(f"Grafana alerts query error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "alerts": []
        }


async def get_alert_summary(namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a summary of current alert state.
    
    Args:
        namespace: Optional namespace filter
        
    Returns:
        Dict with alert summary statistics
    """
    result = await alerts_list(active_only=True, namespace=namespace)
    
    if not result["success"]:
        return result
    
    alerts = result["alerts"]
    
    # Calculate summary
    summary = {
        "total": len(alerts),
        "by_severity": {},
        "by_namespace": {},
        "critical_alerts": []
    }
    
    for alert in alerts:
        # Count by severity
        severity = alert.get("severity", "unknown")
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        # Count by namespace
        ns = alert.get("namespace", "unknown")
        summary["by_namespace"][ns] = summary["by_namespace"].get(ns, 0) + 1
        
        # Track critical alerts
        if severity in ["critical", "error"]:
            summary["critical_alerts"].append({
                "name": alert["name"],
                "namespace": alert.get("namespace"),
                "message": alert.get("annotations", {}).get("summary") or alert.get("annotations", {}).get("description")
            })
    
    return {
        "success": True,
        "summary": summary
    }
