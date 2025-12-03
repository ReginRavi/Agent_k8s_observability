# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the K8s Observability Agent.

## Prerequisites

1. A running Kubernetes cluster
2. `kubectl` configured to access your cluster
3. Prometheus, Loki, and Alertmanager deployed in your cluster
4. A Gemini API key

## Quick Start

1. **Update the Gemini API key** in `kubernetes.yaml`:
   ```yaml
   stringData:
     api-key: "YOUR_GEMINI_API_KEY_HERE"
   ```

2. **Update service endpoints** in the ConfigMap if needed:
   ```yaml
   data:
     PROMETHEUS_URL: "http://prometheus-server:9090"
     LOKI_URL: "http://loki:3100"
     # ... etc
   ```

3. **Build and push the Docker image**:
   ```bash
   cd ..
   docker build -t k8s-observability-agent:latest .
   
   # If using a registry:
   docker tag k8s-observability-agent:latest your-registry/k8s-observability-agent:latest
   docker push your-registry/k8s-observability-agent:latest
   ```

4. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -f kubernetes.yaml
   ```

5. **Verify the deployment**:
   ```bash
   kubectl get pods -l app=observability-agent
   kubectl logs -l app=observability-agent
   ```

6. **Test the agent**:
   ```bash
   kubectl port-forward svc/observability-agent 8000:8000
   
   # In another terminal:
   curl http://localhost:8000/health
   ```

## Components

The manifest includes:

- **ServiceAccount**: `observability-agent` - Identity for the agent pod
- **ClusterRole**: Permissions to read K8s resources (pods, events, nodes, etc.)
- **ClusterRoleBinding**: Binds the role to the service account
- **Secret**: Stores the Gemini API key
- **ConfigMap**: Configuration for observability endpoints
- **Deployment**: Runs the agent (1 replica by default)
- **Service**: ClusterIP service for internal access

## RBAC Permissions

The agent requires read-only access to:
- Pods and pod logs
- Events
- Nodes
- Namespaces
- Deployments, StatefulSets, DaemonSets
- Jobs and CronJobs

These are defined in the ClusterRole.

## Scaling

To run multiple replicas:
```bash
kubectl scale deployment observability-agent --replicas=3
```

Note: The agent is stateless, so multiple replicas can run concurrently.

## Exposing the Service

### Option 1: Port Forward (for testing)
```bash
kubectl port-forward svc/observability-agent 8000:8000
```

### Option 2: Ingress
Create an Ingress resource:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: observability-agent
spec:
  rules:
    - host: agent.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: observability-agent
                port:
                  number: 8000
```

### Option 3: LoadBalancer
Change the Service type:
```yaml
spec:
  type: LoadBalancer
```

## Monitoring the Agent

The agent exposes a `/health` endpoint that can be used for monitoring:

```bash
kubectl exec -it <agent-pod> -- curl localhost:8000/health
```

## Troubleshooting

### Check logs
```bash
kubectl logs -l app=observability-agent --tail=100 -f
```

### Check RBAC permissions
```bash
kubectl auth can-i list pods --as=system:serviceaccount:default:observability-agent
```

### Test connectivity to Prometheus
```bash
kubectl exec -it <agent-pod> -- curl http://prometheus-server:9090/-/healthy
```

### Common Issues

1. **"Failed to initialize Kubernetes client"**
   - Check that the ServiceAccount and RBAC are properly configured
   - Verify `IN_CLUSTER=true` is set

2. **"Prometheus query timeout"**
   - Check that PROMETHEUS_URL is correct
   - Verify network connectivity between agent and Prometheus

3. **"Gemini API error"**
   - Verify the API key is correct in the Secret
   - Check agent logs for specific error messages

## Updating the Deployment

After making changes to the code:

1. Build a new image with a version tag:
   ```bash
   docker build -t k8s-observability-agent:v0.2.0 .
   docker push your-registry/k8s-observability-agent:v0.2.0
   ```

2. Update the deployment:
   ```bash
   kubectl set image deployment/observability-agent agent=your-registry/k8s-observability-agent:v0.2.0
   ```

3. Or edit the manifest and reapply:
   ```bash
   kubectl apply -f kubernetes.yaml
   ```

## Security Considerations

1. **API Key Storage**: The Gemini API key is stored in a Kubernetes Secret. Consider using a secret management solution like:
   - HashiCorp Vault
   - AWS Secrets Manager
   - Google Secret Manager
   - Sealed Secrets

2. **Network Policies**: Consider adding NetworkPolicies to restrict traffic to/from the agent

3. **RBAC**: The agent has read-only cluster-wide access. Review the ClusterRole to ensure it meets your security requirements

4. **TLS**: For production, use TLS for all communications (Ingress, service mesh, etc.)
