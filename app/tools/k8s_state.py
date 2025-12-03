"""
Kubernetes state query adapter.

Provides async interface to query Kubernetes API for pod/node state, events, etc.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from kubernetes.client.rest import ApiException

from ..config import Config, KubernetesClientManager

logger = logging.getLogger(__name__)


async def k8s_state_query_pods(
    namespace: Optional[str] = None,
    label_selector: Optional[str] = None,
    field_selector: Optional[str] = None,
    pod_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query Kubernetes API for pod state information.
    
    Args:
        namespace: Namespace to query (None = all namespaces)
        label_selector: Label selector (e.g., "app=myapp")
        field_selector: Field selector (e.g., "status.phase=Running")
        pod_name: Specific pod name to query
        
    Returns:
        Dict containing:
            - success: bool
            - pods: List of pod information
            - error: Optional error message
    """
    try:
        core_v1 = KubernetesClientManager.get_core_v1_api()
        
        # Query pods
        if pod_name and namespace:
            # Get specific pod
            try:
                pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
                pods = [pod]
            except ApiException as e:
                if e.status == 404:
                    return {
                        "success": True,
                        "pods": [],
                        "message": f"Pod {pod_name} not found in namespace {namespace}"
                    }
                raise
        elif namespace:
            # List pods in namespace
            pod_list = core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector,
                field_selector=field_selector
            )
            pods = pod_list.items
        else:
            # List pods across all namespaces
            pod_list = core_v1.list_pod_for_all_namespaces(
                label_selector=label_selector,
                field_selector=field_selector
            )
            pods = pod_list.items
        
        # Extract relevant pod information
        pod_info = []
        for pod in pods:
            info = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "conditions": [],
                "container_statuses": [],
                "restart_count": 0,
                "node": pod.spec.node_name,
                "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                "labels": pod.metadata.labels or {},
            }
            
            # Pod conditions
            if pod.status.conditions:
                for condition in pod.status.conditions:
                    info["conditions"].append({
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                        "last_transition": condition.last_transition_time.isoformat() if condition.last_transition_time else None
                    })
            
            # Container statuses
            if pod.status.container_statuses:
                for container_status in pod.status.container_statuses:
                    container_info = {
                        "name": container_status.name,
                        "ready": container_status.ready,
                        "restart_count": container_status.restart_count,
                        "image": container_status.image,
                        "state": {}
                    }
                    
                    info["restart_count"] += container_status.restart_count
                    
                    # Container state
                    if container_status.state:
                        if container_status.state.running:
                            container_info["state"] = {
                                "status": "running",
                                "started_at": container_status.state.running.started_at.isoformat() if container_status.state.running.started_at else None
                            }
                        elif container_status.state.waiting:
                            container_info["state"] = {
                                "status": "waiting",
                                "reason": container_status.state.waiting.reason,
                                "message": container_status.state.waiting.message
                            }
                        elif container_status.state.terminated:
                            container_info["state"] = {
                                "status": "terminated",
                                "reason": container_status.state.terminated.reason,
                                "exit_code": container_status.state.terminated.exit_code,
                                "message": container_status.state.terminated.message
                            }
                    
                    info["container_statuses"].append(container_info)
            
            pod_info.append(info)
        
        return {
            "success": True,
            "pods": pod_info,
            "count": len(pod_info)
        }
        
    except ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        return {
            "success": False,
            "error": f"Kubernetes API error: {e.status} - {e.reason}",
            "pods": []
        }
    except Exception as e:
        logger.error(f"Error querying pod state: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "pods": []
        }


async def k8s_state_query_events(
    namespace: Optional[str] = None,
    field_selector: Optional[str] = None,
    involved_object_name: Optional[str] = None,
    lookback_minutes: int = 15
) -> Dict[str, Any]:
    """
    Query Kubernetes events.
    
    Args:
        namespace: Namespace to query (None = all namespaces)
        field_selector: Field selector
        involved_object_name: Filter by involved object name (e.g., pod name)
        lookback_minutes: How far back to look for events
        
    Returns:
        Dict containing:
            - success: bool
            - events: List of events
            - error: Optional error message
    """
    try:
        core_v1 = KubernetesClientManager.get_core_v1_api()
        
        # Build field selector
        selectors = []
        if field_selector:
            selectors.append(field_selector)
        if involved_object_name:
            selectors.append(f"involvedObject.name={involved_object_name}")
        
        combined_selector = ",".join(selectors) if selectors else None
        
        # Query events
        if namespace:
            event_list = core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=combined_selector
            )
        else:
            event_list = core_v1.list_event_for_all_namespaces(
                field_selector=combined_selector
            )
        
        # Filter by time and extract relevant info
        cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
        events = []
        
        for event in event_list.items:
            # Check if event is recent
            last_timestamp = event.last_timestamp or event.event_time
            if last_timestamp and last_timestamp.replace(tzinfo=None) < cutoff_time:
                continue
            
            events.append({
                "namespace": event.metadata.namespace,
                "name": event.metadata.name,
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "count": event.count,
                "first_timestamp": event.first_timestamp.isoformat() if event.first_timestamp else None,
                "last_timestamp": last_timestamp.isoformat() if last_timestamp else None,
                "involved_object": {
                    "kind": event.involved_object.kind,
                    "name": event.involved_object.name,
                    "namespace": event.involved_object.namespace
                } if event.involved_object else None,
                "source": {
                    "component": event.source.component if event.source else None
                }
            })
        
        # Sort by last timestamp (most recent first)
        events.sort(key=lambda x: x.get("last_timestamp", ""), reverse=True)
        
        return {
            "success": True,
            "events": events,
            "count": len(events)
        }
        
    except ApiException as e:
        logger.error(f"Kubernetes API error querying events: {e}")
        return {
            "success": False,
            "error": f"Kubernetes API error: {e.status} - {e.reason}",
            "events": []
        }
    except Exception as e:
        logger.error(f"Error querying events: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "events": []
        }


async def k8s_state_query_nodes() -> Dict[str, Any]:
    """
    Query Kubernetes node state.
    
    Returns:
        Dict containing node information
    """
    try:
        core_v1 = KubernetesClientManager.get_core_v1_api()
        node_list = core_v1.list_node()
        
        nodes = []
        for node in node_list.items:
            node_info = {
                "name": node.metadata.name,
                "conditions": [],
                "capacity": node.status.capacity,
                "allocatable": node.status.allocatable,
                "labels": node.metadata.labels or {},
                "created": node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else None
            }
            
            if node.status.conditions:
                for condition in node.status.conditions:
                    node_info["conditions"].append({
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message
                    })
            
            nodes.append(node_info)
        
        return {
            "success": True,
            "nodes": nodes,
            "count": len(nodes)
        }
        
    except Exception as e:
        logger.error(f"Error querying nodes: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "nodes": []
        }
