"""
Configuration module for K8s Observability Agent.

Handles:
- Environment variable loading
- Kubernetes client initialization (in-cluster or kubeconfig)
- Service endpoint configuration
"""

import os
from typing import Optional
from dotenv import load_dotenv
from kubernetes import client, config as k8s_config

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration for the observability agent."""
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.0-pro")
    GEMINI_API_ENDPOINT: str = os.getenv(
        "GEMINI_API_ENDPOINT",
        "https://generativelanguage.googleapis.com/v1beta"
    )
    
    # Prometheus Configuration
    PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
    PROMETHEUS_TIMEOUT: int = int(os.getenv("PROMETHEUS_TIMEOUT", "30"))
    
    # Loki Configuration
    LOKI_URL: str = os.getenv("LOKI_URL", "http://loki:3100")
    LOKI_TIMEOUT: int = int(os.getenv("LOKI_TIMEOUT", "30"))
    
    # Alertmanager Configuration
    ALERTMANAGER_URL: str = os.getenv("ALERTMANAGER_URL", "http://alertmanager:9093")
    ALERTMANAGER_TIMEOUT: int = int(os.getenv("ALERTMANAGER_TIMEOUT", "10"))
    
    # Grafana Configuration (for alerts API)
    GRAFANA_URL: str = os.getenv("GRAFANA_URL", "http://grafana:3000")
    GRAFANA_API_KEY: str = os.getenv("GRAFANA_API_KEY", "")
    GRAFANA_TIMEOUT: int = int(os.getenv("GRAFANA_TIMEOUT", "10"))
    
    # Knowledge Base / Vector DB Configuration
    KB_ENABLED: bool = os.getenv("KB_ENABLED", "false").lower() == "true"
    KB_ENDPOINT: str = os.getenv("KB_ENDPOINT", "")
    
    # Agent Configuration
    AGENT_PORT: int = int(os.getenv("AGENT_PORT", "8000"))
    AGENT_LOG_LEVEL: str = os.getenv("AGENT_LOG_LEVEL", "INFO")
    
    # Kubernetes Configuration
    IN_CLUSTER: bool = os.getenv("IN_CLUSTER", "true").lower() == "true"
    KUBECONFIG_PATH: Optional[str] = os.getenv("KUBECONFIG_PATH", None)
    
    # Default query parameters
    DEFAULT_LOOKBACK_MINUTES: int = int(os.getenv("DEFAULT_LOOKBACK_MINUTES", "15"))
    DEFAULT_STEP_SECONDS: int = int(os.getenv("DEFAULT_STEP_SECONDS", "60"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY must be set")
        
        if not cls.PROMETHEUS_URL:
            raise ValueError("PROMETHEUS_URL must be set")


class KubernetesClientManager:
    """Manages Kubernetes client initialization."""
    
    _core_v1_api: Optional[client.CoreV1Api] = None
    _apps_v1_api: Optional[client.AppsV1Api] = None
    _batch_v1_api: Optional[client.BatchV1Api] = None
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize Kubernetes client based on environment."""
        try:
            if Config.IN_CLUSTER:
                # Running inside a Kubernetes cluster
                k8s_config.load_incluster_config()
            else:
                # Running locally, use kubeconfig
                k8s_config.load_kube_config(config_file=Config.KUBECONFIG_PATH)
            
            # Initialize API clients
            cls._core_v1_api = client.CoreV1Api()
            cls._apps_v1_api = client.AppsV1Api()
            cls._batch_v1_api = client.BatchV1Api()
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Kubernetes client: {e}")
    
    @classmethod
    def get_core_v1_api(cls) -> client.CoreV1Api:
        """Get CoreV1Api client."""
        if cls._core_v1_api is None:
            cls.initialize()
        return cls._core_v1_api
    
    @classmethod
    def get_apps_v1_api(cls) -> client.AppsV1Api:
        """Get AppsV1Api client."""
        if cls._apps_v1_api is None:
            cls.initialize()
        return cls._apps_v1_api
    
    @classmethod
    def get_batch_v1_api(cls) -> client.BatchV1Api:
        """Get BatchV1Api client."""
        if cls._batch_v1_api is None:
            cls.initialize()
        return cls._batch_v1_api
