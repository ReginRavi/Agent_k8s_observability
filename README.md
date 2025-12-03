# K8s Observability AI Agent

A Kubernetes-aware observability AI agent that uses Gemini 3 to provide intelligent insights into system health, incidents, and performance issues.

## 🚀 Quick Start

**Option 1: Automatic (Recommended)**
```bash
cd /Users/reginravi/Documents/Agent_k8s_observability
./start.sh
```

**Option 2: Validate Services First**
```bash
# Check if all services are running
./scripts/validate.sh

# Then start the agent
./start.sh
```

**📖 For complete setup, configuration, and usage instructions, see [USER_GUIDE.md](./USER_GUIDE.md)**

---

## Overview

This agent sits on top of your observability platform (Prometheus, Loki, Alertmanager, Grafana, Kubernetes API) and uses a large language model (Gemini 3) as the reasoning engine to answer natural-language questions about your system.

### Key Features

- 🤖 **AI-Powered Analysis**: Uses Gemini 3 to interpret observability data and provide actionable insights
- 🔍 **Multi-Source Integration**: Queries Prometheus, Kubernetes API, Loki, and Alertmanager
- 🎯 **Context-Aware**: Understands Kubernetes-specific concepts (pods, namespaces, events, etc.)
- 📊 **SRE-Focused**: Provides responses structured for operational use (summary, observations, recommendations)
- 🚀 **Easy Integration**: Simple HTTP API that can be consumed from Grafana, Slack, or any client
- ⚡ **Current Metrics**: Intelligent detection of instant vs historical metric queries

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                          │
│  (Grafana Panel, Slack Bot, CLI, Web UI)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTP API
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              K8s Observability Agent (FastAPI)               │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Agent Orchestrator                         │   │
│  │  - Tool Selection                                    │   │
│  │  - Context Building                                  │   │
│  │  - Gemini Integration                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Tool Adapters                           │   │
│  │  - Prometheus (metrics)                              │   │
│  │  - Kubernetes API (pods, events, nodes)              │   │
│  │  - Loki (logs)                                       │   │
│  │  - Alertmanager (alerts)                             │   │
│  │  - Knowledge Base (runbooks)                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Observability Platform                          │
│  - Prometheus/Mimir (metrics)                                │
│  - Loki (logs)                                               │
│  - Alertmanager/Grafana (alerts)                             │
│  - Kubernetes API                                            │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
k8s-observability-agent/
├── app/                          # Core Application Package
│   ├── main.py                  # FastAPI application entry point
│   ├── agent.py                 # Agent orchestrator + Gemini integration
│   ├── config.py                # Configuration & K8s client initialization
│   ├── models.py                # Pydantic models for API
│   ├── prompts.py               # AI prompts (system, scenarios, queries)
│   └── tools/                   # Tool adapters
│       ├── prometheus.py        # Prometheus metrics adapter
│       ├── k8s_state.py         # Kubernetes API queries
│       ├── logs.py              # Loki logs adapter
│       ├── alerts.py            # Alertmanager adapter
│       └── kb.py                # Knowledge base (stub)
├── scripts/                      # Utility Scripts
│   ├── check_prerequisites.py   # Prerequisites checker
│   ├── fix_connections.py       # Port-forward helper
│   └── chat.py                  # Interactive CLI client
├── tests/                        # Test Suite
│   ├── test_agent.py            # Agent unit tests
│   ├── test_current_metrics.py  # Current metrics tests
│   └── example_usage.py         # Usage examples
├── docs/                         # Documentation
│   ├── USER_GUIDE.md            # Complete user guide
│   ├── GETTING_STARTED.md       # Setup walkthrough
│   ├── DEVELOPMENT.md           # Developer guide
│   └── PROJECT_SUMMARY.md       # Technical overview
├── deploy/                       # Deployment Configurations
│   ├── kubernetes.yaml          # K8s manifests
│   └── README.md                # Deployment instructions
├── .env.example                  # Environment template
├── Dockerfile                    # Container image
├── requirements.txt              # Python dependencies
├── start.sh                      # Quick start script
├── PROJECT_STRUCTURE.md          # Detailed structure guide
└── README.md                     # This file
```

**📖 For detailed structure documentation, see [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)**

## Installation

### Prerequisites

- Python 3.9+
- Access to a Kubernetes cluster
- Prometheus/Mimir endpoint
- Loki endpoint (optional)
- Alertmanager endpoint (optional)
- Gemini API key

### Local Development Setup

1. **Clone the repository**:
   ```bash
   cd /Users/reginravi/Documents/Agent_k8s_observability
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   export PROMETHEUS_URL="http://localhost:19090"
   export LOKI_URL="http://localhost:3100"
   export ALERTMANAGER_URL="http://localhost:9093"
   export IN_CLUSTER="false"  # Set to true when running in K8s
   ```

5. **Run the agent**:
   ```bash
   python app.py
   ```

   The agent will start on `http://localhost:8000`

## Configuration

Configuration is done via environment variables:

### Required

- `GEMINI_API_KEY`: Your Gemini API key

### Observability Endpoints

- `PROMETHEUS_URL`: Prometheus endpoint (default: `http://prometheus:9090`)
- `LOKI_URL`: Loki endpoint (default: `http://loki:3100`)
- `ALERTMANAGER_URL`: Alertmanager endpoint (default: `http://alertmanager:9093`)
- `GRAFANA_URL`: Grafana endpoint (default: `http://grafana:3000`)
- `GRAFANA_API_KEY`: Grafana API key (optional)

### Kubernetes

- `IN_CLUSTER`: Set to `true` when running inside K8s (default: `true`)
- `KUBECONFIG_PATH`: Path to kubeconfig file for local development

### Agent Settings

- `AGENT_PORT`: Port to run on (default: `8000`)
- `AGENT_LOG_LEVEL`: Logging level (default: `INFO`)
- `DEFAULT_LOOKBACK_MINUTES`: Default time range for queries (default: `15`)

## API Usage

### POST /chat

Ask a natural language question about your system.

**Request**:
```json
{
  "question": "Why is my app pod restarting?",
  "namespace": "production",
  "service": "my-app",
  "time_range_minutes": 30,
  "include_logs": true
}
```

**Response**:
```json
{
  "response": {
    "answer": "Based on the analysis...",
    "tool_results": [...],
    "confidence": "high",
    "recommendations": [
      "Check application logs for errors",
      "Review memory limits"
    ],
    "metadata": {
      "model": "gemini-3.0-pro",
      "tools_used": ["k8s_pods", "k8s_events", "logs"]
    }
  },
  "request_id": "uuid",
  "timestamp": "2025-12-01T12:00:00Z"
}
```

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "checks": {
    "agent": true,
    "kubernetes": true,
    "prometheus": true
  },
  "timestamp": "2025-12-01T12:00:00Z"
}
```

## Example Queries

### Current/Instant Metrics
- **"What is the current CPU usage?"** - Get real-time CPU values
- **"Show me the current memory usage for the api pod"** - Instant memory metrics
- **"What are the current metrics right now?"** - Latest resource usage
- **"Is CPU high at the moment?"** - Real-time status check

See [CURRENT_METRICS_GUIDE.md](./CURRENT_METRICS_GUIDE.md) for detailed usage.

### Troubleshooting & Investigation
- "Why is my app pod restarting?"
- "What's causing high CPU usage in the production namespace?"
- "Are there any alerts firing right now?"
- "Show me recent errors in the api-service logs"
- "What happened to the database pod in the last hour?"
- "Is there memory pressure on any nodes?"


## Deployment

### Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t k8s-observability-agent:latest .
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-key \
  -e PROMETHEUS_URL=http://prometheus:9090 \
  k8s-observability-agent:latest
```

### Kubernetes

Create a deployment manifest (see `deploy/` directory for full examples):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: observability-agent
spec:
  replicas: 1
  template:
    spec:
      serviceAccountName: observability-agent
      containers:
      - name: agent
        image: k8s-observability-agent:latest
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secret
              key: api-key
        - name: IN_CLUSTER
          value: "true"
```

## Development

### Adding New Tools

1. Create a new adapter in `tools/`
2. Implement the async query function
3. Export it in `tools/__init__.py`
4. Update `agent.py` to call the new tool

### Enhancing Tool Selection

The current tool selection uses simple keyword matching. You can enhance this by:
- Using an LLM to select tools
- Implementing a classifier
- Adding user preferences

### Customizing the System Prompt

Edit the `SYSTEM_PROMPT` in `agent.py` to customize how Gemini interprets and responds to queries.

## Roadmap

- [ ] Vector DB integration for runbooks and documentation
- [ ] Trace analysis (Tempo/Jaeger integration)
- [ ] Auto-remediation capabilities
- [ ] Grafana panel plugin
- [ ] Slack/Teams bot integration
- [ ] Query history and learning
- [ ] Custom tool definitions via config
- [ ] Multi-cluster support

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.

---

Built with ❤️ for SREs and Platform Engineers
