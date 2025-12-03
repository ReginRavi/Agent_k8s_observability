# Service Validation Scripts

This directory contains utility scripts for checking, managing, and validating the K8s Observability Agent environment.

## 📋 Scripts Overview

### `validate_services.py` - Comprehensive Service Validation

**Purpose**: Validates all required services (Grafana, Prometheus, Loki, Alertmanager) before starting the agent.

**Features**:
- ✅ Health checks for all observability services
- ⚡ Response time measurements
- 🔍 Version detection
- 🎨 Color-coded output
- 📊 Service criticality classification
- 💡 Automatic remediation suggestions
- 🚦 Exit codes for automation

**Usage**:
```bash
# Run validation
python scripts/validate_services.py

# Use in automation
python scripts/validate_services.py
if [ $? -eq 0 ]; then
    echo "All services ready"
fi
```

**Exit Codes**:
- `0`: All services healthy ✅
- `1`: Critical services unavailable ❌
- `2`: Optional services down (warning) ⚠️

**What it checks**:

| Service | Criticality | Endpoints Checked |
|---------|-------------|-------------------|
| Prometheus | CRITICAL | `/-/healthy`, `/-/ready`, `/api/v1/query` |
| Kubernetes API | CRITICAL | Cluster connectivity, namespace access |
| Loki | IMPORTANT | `/ready`, `/loki/api/v1/labels` |
| Alertmanager | IMPORTANT | `/-/healthy`, `/-/ready`, `/api/v2/alerts` |
| Grafana | OPTIONAL | `/api/health`, `/api/org` (if API key) |

**Example Output**:
```
================================================================================
K8s Observability Agent - Service Validation
================================================================================

📋 Configuration Check
────────────────────────────────────────────────────────────────────────────────
✅ Gemini API Key: Set
✅ Python Version: 3.11.5

📋 Service Endpoints
────────────────────────────────────────────────────────────────────────────────
Prometheus:    http://localhost:19090
Loki:          http://localhost:3100
Alertmanager:  http://localhost:9093
Grafana:       http://localhost:3000

📋 Health Checks
────────────────────────────────────────────────────────────────────────────────
✅ Prometheus [CRITICAL]
   URL: http://localhost:19090
   Response Time: 45ms
   Version: 2.47.0
   
✅ Loki [IMPORTANT]
   URL: http://localhost:3100
   Response Time: 32ms
   Version: 2.9.3

✅ All services are operational!
```

---



### `fix_connections.py` - Port-Forward Helper

**Purpose**: Helps port-forward cluster services to localhost.

**Usage**:
```bash
# Run interactive port-forwarding
python scripts/fix_connections.py
```

**What it does**:
- Port-forwards Prometheus (9090 → 19090)
- Port-forwards Loki (3100)
- Port-forwards Alertmanager (9093)
- Port-forwards Grafana (3000)

---

### `chat.py` - Interactive CLI Client

**Purpose**: Interactive chat interface for the agent.

**Usage**:
```bash
# Start chat session
python scripts/chat.py

# Use with custom endpoint
python scripts/chat.py --url http://localhost:8081
```

**Features**:
- Interactive question/answer
- Command history
- Pretty-printed responses
- Exit with `quit` or `exit`

---

## 🚀 Quick Start Workflow

### 1. Validate Services
```bash
python scripts/validate_services.py
```

### 2. Fix Issues (if any)
```bash
# For cluster services
python scripts/fix_connections.py

# For local services
brew services start prometheus
brew services start grafana
docker run -d -p 3100:3100 grafana/loki
```

### 3. Start Agent
```bash
./start.sh
# or
python -m app.main
```

### 4. Chat with Agent
```bash
python scripts/chat.py
```

---

## 🔧 Environment Variables

The validation script reads from `.env`:

```bash
# Required
GEMINI_API_KEY=your-api-key

# Services
PROMETHEUS_URL=http://localhost:19090
LOKI_URL=http://localhost:3100
ALERTMANAGER_URL=http://localhost:9093
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=optional-api-key

# Kubernetes
KUBECONFIG_PATH=/path/to/kubeconfig  # optional
IN_CLUSTER=false
```

---

## 📊 Service Criticality Levels

### CRITICAL ⛔
Required for agent to function. Script exits with code 1 if down.
- Prometheus
- Kubernetes API

### IMPORTANT ⚠️
Needed for most features. Script returns warning if down.
- Loki
- Alertmanager

### OPTIONAL ℹ️
Nice to have, doesn't affect core functionality.
- Grafana

---

## 🐛 Troubleshooting

### Prometheus Unreachable

```bash
# Check if running
brew services list | grep prometheus

# Start Prometheus
brew services start prometheus

# Or use Docker
docker run -d -p 19090:9090 prom/prometheus

# For cluster Prometheus
kubectl port-forward -n monitoring svc/prometheus 19090:9090
```

### Loki Unreachable

```bash
# Check if running
docker ps | grep loki

# Start Loki
docker run -d -p 3100:3100 grafana/loki

# For cluster Loki
kubectl port-forward -n monitoring svc/loki 3100:3100
```

### Kubernetes Access Failed

```bash
# Check cluster status
kubectl cluster-info

# Start minikube
minikube start

# Check context
kubectl config current-context
```

### All Services Down

```bash
# Use port-forward helper
python scripts/fix_connections.py

# Run in background, then start agent
```

---

## 🔄 Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Validate Services
  run: |
    python scripts/validate_services.py
    
- name: Start Agent
  if: success()
  run: |
    python -m app.main &
    sleep 5
    
- name: Run Tests
  run: |
    pytest tests/
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-push

python scripts/validate_services.py
if [ $? -ne 0 ]; then
    echo "Service validation failed. Fix services before deploying."
    exit 1
fi
```

---

## 📝 Adding New Service Checks

To add a new service validation:

1. **Create check function** in `validate_services.py`:
```python
async def check_myservice(url: str) -> ServiceCheck:
    """Validate MyService"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{url}/health")
            
            return ServiceCheck(
                name="MyService",
                url=url,
                status=ServiceStatus.HEALTHY if response.status_code == 200 else ServiceStatus.UNHEALTHY,
                criticality=ServiceCriticality.IMPORTANT,
                response_time_ms=response.elapsed.total_seconds() * 1000
            )
    except Exception as e:
        return ServiceCheck(
            name="MyService",
            url=url,
            status=ServiceStatus.UNHEALTHY,
            criticality=ServiceCriticality.IMPORTANT,
            error_message=str(e)
        )
```

2. **Add to main()** function:
```python
results = await asyncio.gather(
    check_prometheus(prometheus_url),
    check_loki(loki_url),
    check_myservice(myservice_url),  # Add here
    # ...
)
```

3. **Add remediation tips**:
```python
tips = {
    # ...
    "MyService": [
        "• Check if running: systemctl status myservice",
        "• Start service: systemctl start myservice"
    ]
}
```

---

## 📚 Related Documentation

- [Main README](../README.md)
- [Project Structure](../PROJECT_STRUCTURE.md)
- [User Guide](../docs/USER_GUIDE.md)
- [Quick Reference](../QUICK_REFERENCE.md)

---

**Last Updated**: December 2, 2025
