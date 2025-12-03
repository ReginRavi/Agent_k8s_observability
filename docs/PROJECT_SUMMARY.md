# K8s Observability AI Agent - Project Summary

## What We Built

A complete **Kubernetes-aware Observability AI Agent** that uses **Gemini 3** to provide intelligent insights into system health, incidents, and performance issues.

## Key Components

### 1. **Core Application** (`app.py`)
- FastAPI-based HTTP server
- `/chat` endpoint for natural language queries
- `/health` endpoint for monitoring
- CORS support for web clients
- Global exception handling

### 2. **Agent Orchestrator** (`agent.py`)
- Intelligent tool selection based on question analysis
- Parallel tool execution
- Context building from observability data
- Gemini 3 integration with specialized system prompt
- Response parsing and recommendation extraction

### 3. **Configuration** (`config.py`)
- Environment-based configuration
- Kubernetes client manager (in-cluster and local modes)
- Validation and defaults

### 4. **Data Models** (`models.py`)
- Pydantic models for type safety
- Request/response schemas
- Tool result structures

### 5. **Tool Adapters** (`tools/`)

#### Prometheus Adapter (`prometheus.py`)
- Range and instant queries
- PromQL query builder for K8s metrics
- Async HTTP client
- Error handling and timeouts

#### Kubernetes Adapter (`k8s_state.py`)
- Pod state queries with detailed status
- Event queries with time filtering
- Node state queries
- Container status extraction

#### Loki Adapter (`logs.py`)
- LogQL query execution
- Automatic namespace/pod filtering
- Query builder helper

#### Alertmanager Adapter (`alerts.py`)
- Active alert queries
- Grafana alerting support
- Alert summary statistics

#### Knowledge Base Adapter (`kb.py`)
- Stub for future vector DB integration
- Runbook search interface
- Incident history search

## Architecture Highlights

### Multi-Source Integration
The agent queries multiple observability backends:
- **Prometheus** for metrics
- **Kubernetes API** for resource state
- **Loki** for logs
- **Alertmanager** for alerts
- **Knowledge Base** for runbooks (future)

### AI-Powered Analysis
- Uses **Gemini 3** as the reasoning engine
- Specialized **system prompt** for SRE use cases
- Structured responses (summary, observations, recommendations)
- Confidence scoring

### Kubernetes-Native
- Runs inside K8s with in-cluster config
- RBAC-ready with minimal permissions
- Can also run locally for development
- Understands K8s concepts (pods, namespaces, events)

## API Example

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why is my app pod restarting?",
    "namespace": "production",
    "service": "my-app",
    "time_range_minutes": 30,
    "include_logs": true
  }'
```

**Response:**
```json
{
  "response": {
    "answer": "Based on the analysis of pod state, events, and logs...",
    "tool_results": [...],
    "confidence": "high",
    "recommendations": [
      "Check application logs for OOMKilled events",
      "Review memory limits and requests",
      "Examine liveness probe configuration"
    ],
    "metadata": {
      "model": "gemini-3.0-pro",
      "tools_used": ["k8s_pods", "k8s_events", "logs", "alerts"]
    }
  },
  "request_id": "uuid",
  "timestamp": "2025-12-01T12:00:00Z"
}
```

## Deployment Options

### Local Development
```bash
./quickstart.sh
python app.py
```

### Docker
```bash
docker build -t k8s-observability-agent:latest .
docker run -p 8000:8000 --env-file .env k8s-observability-agent:latest
```

### Kubernetes
```bash
kubectl apply -f deploy/kubernetes.yaml
```

## What Makes This Special

1. **Natural Language Interface**: Ask questions in plain English, not PromQL or LogQL
2. **Context-Aware**: Understands Kubernetes concepts and correlates data across sources
3. **Actionable Insights**: Provides specific recommendations, not just data dumps
4. **Production-Ready**: Includes health checks, RBAC, error handling, and monitoring
5. **Extensible**: Easy to add new tools and data sources

## Example Use Cases

- **Incident Response**: "What's wrong with the payment service?"
- **Performance Analysis**: "Why is CPU usage high in the API namespace?"
- **Troubleshooting**: "Why are pods in the database StatefulSet not starting?"
- **Capacity Planning**: "Are we hitting resource limits anywhere?"
- **Alert Investigation**: "What's causing the high memory alert?"

## Technology Stack

- **Language**: Python 3.9+
- **Web Framework**: FastAPI
- **HTTP Client**: httpx (async)
- **K8s Client**: kubernetes-python
- **AI Model**: Gemini 3
- **Data Sources**: Prometheus, Loki, Alertmanager, K8s API

## Project Files

```
k8s-observability-agent/
├── app.py                      # FastAPI application
├── agent.py                    # Agent orchestrator
├── config.py                   # Configuration
├── models.py                   # Pydantic models
├── tools/                      # Tool adapters
│   ├── __init__.py
│   ├── prometheus.py
│   ├── k8s_state.py
│   ├── logs.py
│   ├── alerts.py
│   └── kb.py
├── deploy/                     # K8s manifests
│   ├── kubernetes.yaml
│   └── README.md
├── requirements.txt            # Dependencies
├── Dockerfile                  # Container image
├── .env.example                # Config template
├── .gitignore                  # Git ignore
├── quickstart.sh               # Setup script
├── example_usage.py            # Usage examples
├── test_agent.py               # Tests
├── README.md                   # Main documentation
├── DEVELOPMENT.md              # Dev guide
└── PROJECT_SUMMARY.md          # This file
```

## Next Steps

### Immediate
1. Set up your environment with `./quickstart.sh`
2. Configure your Gemini API key in `.env`
3. Run the agent: `python app.py`
4. Test with `example_usage.py`

### Short Term
- Add more sophisticated tool selection (LLM-based)
- Implement caching for frequently accessed data
- Add metrics export for the agent itself
- Build a Grafana panel plugin

### Long Term
- Vector DB integration for runbooks
- Trace analysis (Tempo/Jaeger)
- Auto-remediation capabilities
- Multi-cluster support
- Learning from past incidents

## Success Metrics

The agent is successful if it:
- ✅ Reduces mean time to detection (MTTD)
- ✅ Reduces mean time to resolution (MTTR)
- ✅ Provides accurate root cause analysis
- ✅ Suggests actionable next steps
- ✅ Correlates data across multiple sources
- ✅ Understands Kubernetes-specific issues

## Contributing

We welcome contributions! See `DEVELOPMENT.md` for guidelines.

## License

MIT License - See LICENSE file

---

**Built for SREs, by SREs** 🚀
