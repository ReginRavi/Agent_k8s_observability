#!/usr/bin/env python3
"""
K8s Observability Agent - Comprehensive Service Validation Script

This script validates that all required services (Grafana, Prometheus, Loki, Alertmanager)
are running and accessible before starting the main agent.

Features:
- Health checks for all observability services
- Detailed connectivity tests
- Service-specific endpoint validation
- Color-coded output for easy reading
- Exit codes for script integration
- Detailed error reporting

Exit Codes:
- 0: All services healthy
- 1: Critical services unavailable
- 2: Optional services unavailable (warning)
"""

import sys
import os
import asyncio
import httpx
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ServiceCriticality(Enum):
    """Service criticality levels"""
    CRITICAL = "critical"      # Required for agent to function
    IMPORTANT = "important"    # Needed for most features
    OPTIONAL = "optional"      # Nice to have


@dataclass
class ServiceCheck:
    """Service check result"""
    name: str
    url: str
    status: ServiceStatus
    criticality: ServiceCriticality
    response_time_ms: Optional[float] = None
    version: Optional[str] = None
    error_message: Optional[str] = None
    additional_info: Dict = None


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header():
    """Print validation header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}K8s Observability Agent - Service Validation{Colors.RESET}")
    print(f"{Colors.CYAN}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")


def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─'*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}📋 {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'─'*80}{Colors.RESET}\n")


def status_icon(status: ServiceStatus) -> str:
    """Get status icon"""
    icons = {
        ServiceStatus.HEALTHY: f"{Colors.GREEN}✅",
        ServiceStatus.UNHEALTHY: f"{Colors.RED}❌",
        ServiceStatus.DEGRADED: f"{Colors.YELLOW}⚠️",
        ServiceStatus.UNKNOWN: f"{Colors.YELLOW}❓"
    }
    return icons.get(status, "❓") + Colors.RESET


def criticality_badge(criticality: ServiceCriticality) -> str:
    """Get criticality badge"""
    badges = {
        ServiceCriticality.CRITICAL: f"{Colors.RED}[CRITICAL]{Colors.RESET}",
        ServiceCriticality.IMPORTANT: f"{Colors.YELLOW}[IMPORTANT]{Colors.RESET}",
        ServiceCriticality.OPTIONAL: f"{Colors.CYAN}[OPTIONAL]{Colors.RESET}"
    }
    return badges.get(criticality, "")


async def check_prometheus(url: str) -> ServiceCheck:
    """
    Validate Prometheus service
    
    Checks:
    - Health endpoint (/-/healthy)
    - Readiness endpoint (/-/ready)
    - API endpoint (/api/v1/query)
    - Version information
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check health
            health_response = await client.get(f"{url.rstrip('/')}/-/healthy")
            
            if health_response.status_code != 200:
                return ServiceCheck(
                    name="Prometheus",
                    url=url,
                    status=ServiceStatus.UNHEALTHY,
                    criticality=ServiceCriticality.CRITICAL,
                    error_message=f"Health check failed (HTTP {health_response.status_code})"
                )
            
            # Check readiness
            ready_response = await client.get(f"{url.rstrip('/')}/-/ready")
            if ready_response.status_code != 200:
                return ServiceCheck(
                    name="Prometheus",
                    url=url,
                    status=ServiceStatus.DEGRADED,
                    criticality=ServiceCriticality.CRITICAL,
                    error_message="Service not ready"
                )
            
            # Try a simple query to verify API
            query_response = await client.get(
                f"{url.rstrip('/')}/api/v1/query",
                params={"query": "up"}
            )
            
            # Get build info
            buildinfo_response = await client.get(f"{url.rstrip('/')}/api/v1/status/buildinfo")
            version = None
            if buildinfo_response.status_code == 200:
                data = buildinfo_response.json()
                version = data.get("data", {}).get("version", "unknown")
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return ServiceCheck(
                name="Prometheus",
                url=url,
                status=ServiceStatus.HEALTHY if query_response.status_code == 200 else ServiceStatus.DEGRADED,
                criticality=ServiceCriticality.CRITICAL,
                response_time_ms=response_time,
                version=version,
                additional_info={"api_status": query_response.status_code}
            )
            
    except httpx.TimeoutException:
        return ServiceCheck(
            name="Prometheus",
            url=url,
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.CRITICAL,
            error_message="Connection timeout (10s)"
        )
    except Exception as e:
        return ServiceCheck(
            name="Prometheus",
            url=url,
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.CRITICAL,
            error_message=f"Connection error: {str(e)}"
        )


async def check_loki(url: str) -> ServiceCheck:
    """
    Validate Loki service
    
    Checks:
    - Ready endpoint (/ready)
    - API endpoint (/loki/api/v1/labels)
    - Version information
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check ready
            ready_response = await client.get(f"{url.rstrip('/')}/ready")
            
            if ready_response.status_code != 200:
                return ServiceCheck(
                    name="Loki",
                    url=url,
                    status=ServiceStatus.UNHEALTHY,
                    criticality=ServiceCriticality.IMPORTANT,
                    error_message=f"Ready check failed (HTTP {ready_response.status_code})"
                )
            
            # Try API endpoint
            api_response = await client.get(f"{url.rstrip('/')}/loki/api/v1/labels")
            
            # Try to get version from build info
            version_response = await client.get(f"{url.rstrip('/')}/loki/api/v1/status/buildinfo")
            version = None
            if version_response.status_code == 200:
                data = version_response.json()
                version = data.get("version", "unknown")
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return ServiceCheck(
                name="Loki",
                url=url,
                status=ServiceStatus.HEALTHY if api_response.status_code == 200 else ServiceStatus.DEGRADED,
                criticality=ServiceCriticality.IMPORTANT,
                response_time_ms=response_time,
                version=version,
                additional_info={"api_status": api_response.status_code}
            )
            
    except httpx.TimeoutException:
        return ServiceCheck(
            name="Loki",
            url=url,
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.IMPORTANT,
            error_message="Connection timeout (10s)"
        )
    except Exception as e:
        return ServiceCheck(
            name="Loki",
            url=url,
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.IMPORTANT,
            error_message=f"Connection error: {str(e)}"
        )


async def check_alertmanager(url: str) -> ServiceCheck:
    """
    Validate Alertmanager service
    
    Checks:
    - Health endpoint (/-/healthy)
    - Ready endpoint (/-/ready)
    - API endpoint (/api/v2/alerts)
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check health
            health_response = await client.get(f"{url.rstrip('/')}/-/healthy")
            
            if health_response.status_code != 200:
                return ServiceCheck(
                    name="Alertmanager",
                    url=url,
                    status=ServiceStatus.UNHEALTHY,
                    criticality=ServiceCriticality.IMPORTANT,
                    error_message=f"Health check failed (HTTP {health_response.status_code})"
                )
            
            # Check ready
            ready_response = await client.get(f"{url.rstrip('/')}/-/ready")
            
            # Check API
            api_response = await client.get(f"{url.rstrip('/')}/api/v2/alerts")
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            is_healthy = (ready_response.status_code == 200 and 
                         api_response.status_code == 200)
            
            return ServiceCheck(
                name="Alertmanager",
                url=url,
                status=ServiceStatus.HEALTHY if is_healthy else ServiceStatus.DEGRADED,
                criticality=ServiceCriticality.IMPORTANT,
                response_time_ms=response_time,
                additional_info={"api_status": api_response.status_code}
            )
            
    except httpx.TimeoutException:
        return ServiceCheck(
            name="Alertmanager",
            url=url,
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.IMPORTANT,
            error_message="Connection timeout (10s)"
        )
    except Exception as e:
        return ServiceCheck(
            name="Alertmanager",
            url=url,
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.IMPORTANT,
            error_message=f"Connection error: {str(e)}"
        )


async def check_grafana(url: str, api_key: Optional[str] = None) -> ServiceCheck:
    """
    Validate Grafana service
    
    Checks:
    - Health endpoint (/api/health)
    - API endpoint (/api/org) if API key provided
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check health
            health_response = await client.get(
                f"{url.rstrip('/')}/api/health",
                headers=headers
            )
            
            if health_response.status_code != 200:
                return ServiceCheck(
                    name="Grafana",
                    url=url,
                    status=ServiceStatus.UNHEALTHY,
                    criticality=ServiceCriticality.OPTIONAL,
                    error_message=f"Health check failed (HTTP {health_response.status_code})"
                )
            
            health_data = health_response.json()
            version = health_data.get("version", "unknown")
            
            # If API key provided, try to access API
            api_accessible = None
            if api_key:
                try:
                    api_response = await client.get(
                        f"{url.rstrip('/')}/api/org",
                        headers=headers
                    )
                    api_accessible = api_response.status_code == 200
                except:
                    api_accessible = False
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            additional_info = {
                "database": health_data.get("database", "unknown"),
                "api_accessible": api_accessible
            }
            
            return ServiceCheck(
                name="Grafana",
                url=url,
                status=ServiceStatus.HEALTHY,
                criticality=ServiceCriticality.OPTIONAL,
                response_time_ms=response_time,
                version=version,
                additional_info=additional_info
            )
            
    except httpx.TimeoutException:
        return ServiceCheck(
            name="Grafana",
            url=url,
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.OPTIONAL,
            error_message="Connection timeout (10s)"
        )
    except Exception as e:
        return ServiceCheck(
            name="Grafana",
            url=url,
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.OPTIONAL,
            error_message=f"Connection error: {str(e)}"
        )


def check_kubernetes() -> ServiceCheck:
    """Validate Kubernetes cluster access"""
    try:
        from kubernetes import client, config
        
        # Try loading config
        kubeconfig = os.getenv("KUBECONFIG_PATH")
        if kubeconfig:
            config.load_kube_config(config_file=kubeconfig)
        else:
            try:
                config.load_kube_config()
            except:
                config.load_incluster_config()
        
        # Try to list namespaces
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace(limit=1)
        
        return ServiceCheck(
            name="Kubernetes API",
            url="cluster",
            status=ServiceStatus.HEALTHY,
            criticality=ServiceCriticality.CRITICAL,
            additional_info={"accessible_namespaces": len(namespaces.items) > 0}
        )
        
    except Exception as e:
        return ServiceCheck(
            name="Kubernetes API",
            url="cluster",
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.CRITICAL,
            error_message=f"Cannot access cluster: {str(e)}"
        )


def print_check_result(check: ServiceCheck):
    """Print formatted check result"""
    status_str = status_icon(check.status)
    criticality_str = criticality_badge(check.criticality)
    
    # Service name and URL
    print(f"{status_str} {Colors.BOLD}{check.name}{Colors.RESET} {criticality_str}")
    print(f"   URL: {Colors.CYAN}{check.url}{Colors.RESET}")
    
    # Status details
    if check.status == ServiceStatus.HEALTHY:
        if check.response_time_ms:
            print(f"   Response Time: {Colors.GREEN}{check.response_time_ms:.0f}ms{Colors.RESET}")
        if check.version:
            print(f"   Version: {check.version}")
        if check.additional_info:
            for key, value in check.additional_info.items():
                if value is not None:
                    print(f"   {key.replace('_', ' ').title()}: {value}")
    else:
        if check.error_message:
            print(f"   {Colors.RED}Error: {check.error_message}{Colors.RESET}")
    
    print()  # Empty line for spacing


def print_summary(results: List[ServiceCheck]) -> Tuple[bool, bool]:
    """
    Print validation summary
    
    Returns:
        Tuple[bool, bool]: (all_critical_healthy, all_important_healthy)
    """
    print_section("Validation Summary")
    
    # Group by criticality
    critical_services = [r for r in results if r.criticality == ServiceCriticality.CRITICAL]
    important_services = [r for r in results if r.criticality == ServiceCriticality.IMPORTANT]
    optional_services = [r for r in results if r.criticality == ServiceCriticality.OPTIONAL]
    
    # Count statuses
    def count_healthy(services):
        return len([s for s in services if s.status == ServiceStatus.HEALTHY])
    
    critical_healthy = count_healthy(critical_services)
    important_healthy = count_healthy(important_services)
    optional_healthy = count_healthy(optional_services)
    
    # Print summary
    print(f"{Colors.BOLD}Critical Services:{Colors.RESET} {critical_healthy}/{len(critical_services)} healthy")
    for service in critical_services:
        print(f"  {status_icon(service.status)} {service.name}")
    
    print(f"\n{Colors.BOLD}Important Services:{Colors.RESET} {important_healthy}/{len(important_services)} healthy")
    for service in important_services:
        print(f"  {status_icon(service.status)} {service.name}")
    
    print(f"\n{Colors.BOLD}Optional Services:{Colors.RESET} {optional_healthy}/{len(optional_services)} healthy")
    for service in optional_services:
        print(f"  {status_icon(service.status)} {service.name}")
    
    # Overall status
    all_critical_healthy = critical_healthy == len(critical_services)
    all_important_healthy = important_healthy == len(important_services)
    
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    
    if all_critical_healthy and all_important_healthy:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ All services are operational!{Colors.RESET}")
        print(f"{Colors.GREEN}The agent is ready to start.{Colors.RESET}")
        return True, True
    elif all_critical_healthy:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Critical services are healthy, but some important services are down.{Colors.RESET}")
        print(f"{Colors.YELLOW}The agent can start but some features may not work.{Colors.RESET}")
        return True, False
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ Critical services are unavailable!{Colors.RESET}")
        print(f"{Colors.RED}Cannot start the agent. Please fix critical services first.{Colors.RESET}")
        return False, False


def print_remediation_tips(results: List[ServiceCheck]):
    """Print remediation tips for failed services"""
    failed_services = [r for r in results if r.status != ServiceStatus.HEALTHY]
    
    if not failed_services:
        return
    
    print_section("Remediation Tips")
    
    tips = {
        "Prometheus": [
            "• Check if Prometheus is running: brew services list | grep prometheus",
            "• Start Prometheus: brew services start prometheus",
            "• If in cluster, run port-forward: kubectl port-forward -n monitoring svc/prometheus 19090:9090",
            f"• Verify PROMETHEUS_URL in .env: {os.getenv('PROMETHEUS_URL')}"
        ],
        "Loki": [
            "• Check if Loki is running: docker ps | grep loki",
            "• Start Loki: docker run -d -p 3100:3100 grafana/loki",
            "• If in cluster, run port-forward: kubectl port-forward -n monitoring svc/loki 3100:3100",
            f"• Verify LOKI_URL in .env: {os.getenv('LOKI_URL')}"
        ],
        "Alertmanager": [
            "• Check if Alertmanager is running: brew services list | grep alertmanager",
            "• Start Alertmanager: brew services start alertmanager",
            "• If in cluster, run port-forward: kubectl port-forward -n monitoring svc/alertmanager 9093:9093",
            f"• Verify ALERTMANAGER_URL in .env: {os.getenv('ALERTMANAGER_URL')}"
        ],
        "Grafana": [
            "• Check if Grafana is running: brew services list | grep grafana",
            "• Start Grafana: brew services start grafana",
            "• Access Grafana: http://localhost:3000",
            f"• Verify GRAFANA_URL in .env: {os.getenv('GRAFANA_URL')}"
        ],
        "Kubernetes API": [
            "• Check cluster status: kubectl cluster-info",
            "• Start minikube: minikube start",
            "• Check kubeconfig: echo $KUBECONFIG",
            "• List contexts: kubectl config get-contexts"
        ]
    }
    
    for service in failed_services:
        if service.name in tips:
            print(f"{Colors.BOLD}{Colors.RED}❌ {service.name}{Colors.RESET}")
            for tip in tips[service.name]:
                print(f"   {tip}")
            print()


async def main():
    """Main validation routine"""
    print_header()
    
    # Check environment variables
    print_section("Configuration Check")
    
    # Gemini API Key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key.strip() and gemini_key != "your-gemini-api-key-here":
        print(f"{Colors.GREEN}✅{Colors.RESET} Gemini API Key: Set")
    else:
        print(f"{Colors.RED}❌{Colors.RESET} Gemini API Key: Missing or invalid")
        print(f"   {Colors.YELLOW}Set GEMINI_API_KEY in .env file{Colors.RESET}\n")
        return 1
    
    # Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 9):
        print(f"{Colors.GREEN}✅{Colors.RESET} Python Version: {python_version}")
    else:
        print(f"{Colors.RED}❌{Colors.RESET} Python Version: {python_version} (Requires 3.9+)")
        return 1
    
    # Service URLs
    print_section("Service Endpoints")
    
    prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:19090")
    loki_url = os.getenv("LOKI_URL", "http://localhost:3100")
    alertmanager_url = os.getenv("ALERTMANAGER_URL", "http://localhost:9093")
    grafana_url = os.getenv("GRAFANA_URL", "http://localhost:3000")
    grafana_api_key = os.getenv("GRAFANA_API_KEY", "")
    
    print(f"Prometheus:    {Colors.CYAN}{prometheus_url}{Colors.RESET}")
    print(f"Loki:          {Colors.CYAN}{loki_url}{Colors.RESET}")
    print(f"Alertmanager:  {Colors.CYAN}{alertmanager_url}{Colors.RESET}")
    print(f"Grafana:       {Colors.CYAN}{grafana_url}{Colors.RESET}")
    
    # Run health checks
    print_section("Health Checks")
    
    print(f"{Colors.CYAN}Running connectivity tests...{Colors.RESET}\n")
    
    # Run all checks concurrently
    results = await asyncio.gather(
        check_prometheus(prometheus_url),
        check_loki(loki_url),
        check_alertmanager(alertmanager_url),
        check_grafana(grafana_url, grafana_api_key),
    )
    
    # Add Kubernetes check (synchronous)
    results = list(results)
    results.append(check_kubernetes())
    
    # Print individual results
    for result in results:
        print_check_result(result)
    
    # Print summary
    all_critical_healthy, all_important_healthy = print_summary(results)
    
    # Print remediation tips if needed
    if not (all_critical_healthy and all_important_healthy):
        print_remediation_tips(results)
    
    # Print next steps
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}Next Steps:{Colors.RESET}\n")
    
    if all_critical_healthy:
        print(f"{Colors.GREEN}▶  Start the agent:{Colors.RESET}")
        print(f"   ./start.sh")
        print(f"\n   or\n")
        print(f"   python -m app.main")
        print(f"\n{Colors.GREEN}▶  Use interactive chat:{Colors.RESET}")
        print(f"   python scripts/chat.py")
    else:
        print(f"{Colors.RED}▶  Fix critical services first{Colors.RESET}")
        print(f"   See remediation tips above")
        print(f"\n{Colors.YELLOW}▶  Use fix_connections.py for cluster services:{Colors.RESET}")
        print(f"   python scripts/fix_connections.py")
    
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    # Return appropriate exit code
    if all_critical_healthy and all_important_healthy:
        return 0  # All good
    elif all_critical_healthy:
        return 2  # Warning - optional services down
    else:
        return 1  # Error - critical services down


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Validation cancelled by user.{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.RESET}")
        sys.exit(1)
