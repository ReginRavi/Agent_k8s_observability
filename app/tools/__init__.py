"""
Tool adapters for the K8s Observability Agent.

Each adapter provides a specific capability:
- prometheus: Query metrics from Prometheus
- k8s_state: Query Kubernetes API for pod/node state
- logs: Query logs from Loki/Elastic
- alerts: Query alerts from Alertmanager/Grafana
- kb: Search knowledge base (runbooks, docs)
"""

from .prometheus import metrics_query, instant_query
from .k8s_state import k8s_state_query_pods, k8s_state_query_events
from .logs import logs_query
from .alerts import alerts_list
from .kb import kb_search

__all__ = [
    "metrics_query",
    "instant_query",
    "k8s_state_query_pods",
    "k8s_state_query_events",
    "logs_query",
    "alerts_list",
    "kb_search",
]
