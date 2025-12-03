# Service Validation System

## Overview

The K8s Observability AI Agent now includes a comprehensive service validation system that checks all required services before starting the agent. This ensures a smooth startup and helps identify issues early.

## 🎯 Purpose

**Why Service Validation?**

The agent depends on multiple external services:
- **Prometheus** - For metrics queries
- **Kubernetes API** - For cluster state
- **Loki** - For log aggregation
- **Alertmanager** - For alert management
- **Grafana** - For visualization (optional)

Starting the agent when critical services are down leads to:
- ❌ Runtime errors
- ❌ Confusing error messages
- ❌ Poor user experience
- ❌ Wasted debugging time

**Solution**: Validate all services upfront with detailed health checks and remediation guidance.

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                   User Interface                         │
│              (./start.sh or validate.sh)                 │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│            scripts/validate_services.py                  │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Service Check Orchestrator                    │    │
│  │  - Runs checks concurrently                    │    │
│  │  - Aggregates results                          │    │
│  │  - Determines exit code                        │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Individual Service Checkers                   │    │
│  │  - check_prometheus()                          │    │
│  │  - check_loki()                                │    │
│  │  - check_alertmanager()                        │    │
│  │  - check_grafana()                             │    │
│  │  - check_kubernetes()                          │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              External Services                           │
│  - Prometheus (/-/healthy, /-/ready, /api/v1/query)     │
│  - Loki (/ready, /loki/api/v1/labels)                   │
│  - Alertmanager (/-/healthy, /api/v2/alerts)            │
│  - Grafana (/api/health)                                │
│  - Kubernetes API (namespaces)                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔍 Service Criticality

Services are classified by criticality:

### 🔴 CRITICAL
**Required for agent to function**

| Service | Why Critical | Without It |
|---------|--------------|------------|
| **Prometheus** | Source of metrics data | Cannot answer any metrics-related queries |
| **Kubernetes API** | Source of cluster state | Cannot query pods, nodes, events |

If any critical service is down → **Exit Code 1** (Cannot start agent)

### 🟡 IMPORTANT
**Needed for most features**

| Service | Why Important | Without It |
|---------|---------------|------------|
| **Loki** | Log aggregation | Cannot search logs or correlate with events |
| **Alertmanager** | Alert management | Cannot query active/silenced alerts |

If important services are down → **Exit Code 2** (Warning, limited functionality)

### 🟢 OPTIONAL
**Nice to have**

| Service | Purpose | Without It |
|---------|---------|------------|
| **Grafana** | Visualization | Agent still works, but no dashboard integration |

Optional services don't affect exit code.

---

## 📋 Health Check Details

### Prometheus
```python
✓ Health endpoint:   /-/healthy
✓ Readiness:         /-/ready  
✓ API availability:  /api/v1/query?query=up
✓ Version info:      /api/v1/status/buildinfo
```

**Success Criteria**:
- All endpoints return 200 OK
- API accepts queries

**Typical Response Time**: 20-100ms

---

### Loki
```python
✓ Readiness:        /ready
✓ API availability: /loki/api/v1/labels
✓ Version info:     /loki/api/v1/status/buildinfo
```

**Success Criteria**:
- Ready endpoint returns 200
- Labels API accessible

**Typical Response Time**: 15-80ms

---

### Alertmanager
```python
✓ Health endpoint: /-/healthy
✓ Readiness:       /-/ready
✓ API:             /api/v2/alerts
```

**Success Criteria**:
- All endpoints return 200
- Can list alerts

**Typical Response Time**: 10-50ms

---

### Grafana
```python
✓ Health endpoint: /api/health
✓ API access:      /api/org (if API key provided)
```

**Success Criteria**:
- Health endpoint returns 200
- Database status OK

**Typical Response Time**: 10-40ms

---

### Kubernetes API
```python
✓ Cluster connectivity
✓ Namespace access
✓ RBAC permissions
```

**Success Criteria**:
- Can connect to cluster
- Can list namespaces

**Typical Response Time**: N/A (synchronous)

---

## 🚦 Exit Codes

The validation script uses exit codes for automation:

| Code | Status | Meaning | Action |
|------|--------|---------|--------|
| `0` | ✅ Success | All services healthy | Start agent |
| `1` | ❌ Error | Critical services down | Fix services, cannot start |
| `2` | ⚠️ Warning | Optional services down | Can start with limited features |

### Usage in Scripts

```bash
#!/bin/bash

python scripts/validate_services.py

case $? in
    0)
        echo "All systems go!"
        python -m app.main
        ;;
    1)
        echo "Critical failure - cannot start"
        exit 1
        ;;
    2)
        echo "Degraded mode - starting anyway"
        python -m app.main
        ;;
esac
```

---

## 🎨 Output Format

### Color Coding

- 🟢 **Green**: Healthy services, success messages
- 🔴 **Red**: Unhealthy services, errors
- 🟡 **Yellow**: Warnings, degraded state
- 🔵 **Blue**: Informational, section headers
- 🔷 **Cyan**: URLs, configuration values

### Sections

1. **Configuration Check**
   - Gemini API key verification
   - Python version check
   
2. **Service Endpoints**
   - Display configured URLs
   
3. **Health Checks**
   - Individual service results
   - Response times
   - Versions
   
4. **Validation Summary**
   - Services by criticality
   - Overall status
   
5. **Remediation Tips** (if failures)
   - Service-specific fix suggestions
   
6. **Next Steps**
   - What to do based on results

---

## 🛠️ Usage Examples

### 1. Standalone Validation

```bash
# Full validation with detailed output
python scripts/validate_services.py

# Quick validation
./scripts/validate.sh
```

### 2. Automatic Validation (via start.sh)

```bash
# Runs validation automatically before starting
./start.sh
```

The start script will:
1. ✅ Check Python and dependencies
2. ✅ Verify configuration
3. ✅ Run service validation
4. ✅ Start agent only if validation passes

### 3. CI/CD Integration

```yaml
# GitHub Actions
- name: Validate Services
  run: |
    python scripts/validate_services.py
  continue-on-error: false

- name: Start Agent
  if: success()
  run: |
    python -m app.main
```

### 4. Pre-Deployment Check

```bash
#!/bin/bash
# deploy.sh

echo "Pre-deployment validation..."
python scripts/validate_services.py

if [ $? -eq 0 ]; then
    kubectl apply -f deploy/kubernetes.yaml
else
    echo "Validation failed - aborting deployment"
    exit 1
fi
```

---

## 🔧 Configuration

The validation script reads from `.env`:

```bash
# Service URLs
PROMETHEUS_URL=http://localhost:19090
LOKI_URL=http://localhost:3100
ALERTMANAGER_URL=http://localhost:9093
GRAFANA_URL=http://localhost:3000

# Optional
GRAFANA_API_KEY=your-api-key-here
KUBECONFIG_PATH=/path/to/kubeconfig
```

**Note**: URLs default to standard ports if not specified.

---

## 🐛 Troubleshooting

### All Services Show as Down

**Cause**: Services running in cluster, not locally

**Fix**:
```bash
# Use port-forward helper
python scripts/fix_connections.py

# Then validate
python scripts/validate_services.py
```

---

### Validation Hangs

**Cause**: Timeout waiting for unresponsive service

**Fix**: The script has 10-second timeout per service. If hanging:
1. Check if service is accessible: `curl http://localhost:19090/-/healthy`
2. Verify firewall/network settings
3. Check service logs

---

### False Negatives

**Cause**: Service responds but unhealthy

**Example**: Loki responds 503 (starting up)

**Fix**: Wait a few seconds and retry. Services take time to become ready after startup.

---

### Kubernetes Connection Refused

**Cause**: No active cluster

**Fix**:
```bash
# Check cluster status
kubectl cluster-info

# Start minikube if needed
minikube start

# Or set correct context
kubectl config use-context my-cluster
```

---

## 📊 Performance

**Validation Speed**:
- All checks run concurrently
- Typical total time: **1-3 seconds**
- Timeout per service: **10 seconds max**

**Resource Usage**:
- Memory: ~50MB
- CPU: Minimal (I/O bound)
- Network: ~10-20 HTTP requests

---

## 🔄 Future Enhancements

### Planned Features

- [ ] **Service auto-start**: Attempt to start failed services
- [ ] **Dependency graphing**: Show service dependencies
- [ ] **Historical tracking**: Log validation results over time
- [ ] **Alerting**: Notify when services go down
- [ ] **Web UI**: Browser-based validation dashboard
- [ ] **Metrics export**: Export validation metrics to Prometheus
- [ ] **Custom checks**: User-defined health checks

### Extensibility

To add a new service check:

1. Create check function following the pattern
2. Add to `main()` concurrent gather
3. Update remediation tips
4. Document in scripts/README.md

Example:
```python
async def check_myservice(url: str) -> ServiceCheck:
    # Your implementation
    pass
```

---

## 📚 Related Documentation

- **[scripts/README.md](./scripts/README.md)** - Detailed script documentation
- **[README.md](./README.md)** - Project overview
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Quick reference guide

---

## ✅ Best Practices

### 1. **Always Validate Before Starting**
```bash
# Good
./scripts/validate.sh && python -m app.main

# Bad
python -m app.main  # May fail silently
```

### 2. **Check Exit Codes in Scripts**
```bash
python scripts/validate_services.py
if [ $? -ne 0 ]; then
    echo "Fix services first"
    exit 1
fi
```

### 3. **Use in CI/CD**
Never deploy without validation passing.

### 4. **Monitor Validation Logs**
Review validation output to catch degraded services early.

---

**Created**: December 2, 2025  
**Author**: K8s Observability Agent Team  
**Version**: 1.0
