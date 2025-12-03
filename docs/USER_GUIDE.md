# K8s Observability AI Agent - User Guide

> **Complete guide for installation, configuration, usage, and customization**

---

## 📑 Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Using the Agent](#using-the-agent)
5. [Customizing Prompts](#customizing-prompts)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

---

## ⚡ Quick Start

### Fastest Way to Start

```bash
cd /Users/reginravi/Documents/Agent_k8s_observability
./start.sh
```

This script automatically:
- ✅ Checks prerequisites
- ✅ Sets up virtual environment
- ✅ Installs dependencies
- ✅ Verifies configuration
- ✅ Starts the agent

### Manual 3-Step Start

```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure (set your Gemini API key in .env)
nano .env

# 3. Start
python3 app.py
```

Agent runs on: **http://localhost:8000**

---

## 🔧 Installation

### Prerequisites

**Required:**
- Python 3.9+
- Kubernetes cluster access
- Prometheus running
- Gemini API key

**Optional but recommended:**
- Loki for logs
- Alertmanager for alerts
- Grafana for visualization

### Check Prerequisites

```bash
python3 check_prerequisites.py
```

### Get Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Create new API key
3. Copy it for configuration

### Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` file:

```bash
# Required
GEMINI_API_KEY=your-api-key-here

# Observability endpoints
PROMETHEUS_URL=http://localhost:9090
LOKI_URL=http://localhost:3100
ALERTMANAGER_URL=http://localhost:9093

# Kubernetes
IN_CLUSTER=false
KUBECONFIG_PATH=~/.kube/config

# Agent settings
AGENT_PORT=8000
AGENT_LOG_LEVEL=INFO
DEFAULT_LOOKBACK_MINUTES=15
```

### Minimal Configuration

Only need these to start:
```bash
GEMINI_API_KEY=your-key
PROMETHEUS_URL=http://localhost:9090
IN_CLUSTER=false
```

---

## 🚀 Using the Agent

### Ask Questions

#### Current/Instant Metrics
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the current CPU usage?",
    "namespace": "production"
  }'
```

**Keywords for instant queries:**
- "current"
- "now"
- "right now"
- "at the moment"

#### Example Questions

**Current Metrics:**
- "What is the current CPU usage?"
- "Show me current memory for api pod"
- "What are the current metrics right now?"

**Troubleshooting:**
- "Why is my pod restarting?"
- "What's causing high CPU usage?"
- "Are there any alerts firing?"
- "Show me recent errors in logs"

**Historical Analysis:**
- "How has CPU changed in the last hour?"
- "Show memory trends over time"
- "Was there a CPU spike?"

### Using Python

```python
import httpx
import asyncio

async def ask_question(question):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={"question": question, "namespace": "default"}
        )
        return response.json()

# Use it
result = asyncio.run(ask_question("What is the current CPU usage?"))
print(result['response']['answer'])
```

### Response Structure

```json
{
  "response": {
    "answer": "Detailed analysis with summary, observations, and recommendations",
    "tool_results": [
      {
        "tool_name": "metrics_instant",
        "success": true,
        "execution_time_ms": 142
      }
    ],
    "confidence": "high",
    "recommendations": [
      "Monitor api-pod as it's approaching 60% threshold",
      "Consider horizontal scaling if needed"
    ],
    "metadata": {
      "model": "gemini-3.0-pro",
      "tools_used": ["metrics_instant", "k8s_pods", "alerts"]
    }
  }
}
```

### Test Script

```bash
# Run comprehensive tests
python3 test_current_metrics.py
```

---

## 📝 Customizing Prompts

All AI prompts are centralized in `prompts.py` for easy customization.

### Available Prompt Styles

```python
from prompts import get_system_prompt

# Default - comprehensive analysis
prompt = get_system_prompt("default")

# Concise - brief responses
prompt = get_system_prompt("concise")

# Detailed - thorough investigation
prompt = get_system_prompt("detailed")
```

### Configure Prompt Style

**Via environment variable:**
```bash
export PROMPT_STYLE=concise
python3 app.py
```

**Or in config.py:**
```python
PROMPT_STYLE = os.getenv("PROMPT_STYLE", "default")
```

### Add Custom Prompts

Edit `prompts.py`:

```python
# Add your custom prompt
MY_COMPANY_PROMPT = """You are the MyCompany observability assistant.

[Your custom instructions here...]
"""

# Register it
def get_system_prompt(style: str = "default") -> str:
    prompts = {
        "default": SYSTEM_PROMPT,
        "concise": SYSTEM_PROMPT_CONCISE,
        "detailed": SYSTEM_PROMPT_DETAILED,
        "mycompany": MY_COMPANY_PROMPT,  # Add here
    }
    return prompts.get(style, SYSTEM_PROMPT)
```

### Specialized Scenario Prompts

```python
from prompts import format_scenario_prompt

# For high CPU analysis
prompt = format_scenario_prompt("high_cpu", {
    "current_metrics": cpu_data,
    "cpu_trends": trends,
    "pod_state": pods,
    "alerts": alerts
})

# Available scenarios:
# - pod_restart
# - high_cpu
# - memory_leak
# - alert_triage
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. "GEMINI_API_KEY must be set"

**Solution:**
```bash
# Edit .env file
nano .env

# Set your key
GEMINI_API_KEY=AIza...your-key

# Verify
grep GEMINI_API_KEY .env
```

#### 2. "Kubernetes client failed"

**Solutions:**

**Minikube:**
```bash
minikube start
kubectl cluster-info
```

**Docker Desktop:**
- Enable Kubernetes in settings
- Wait for it to start
- Verify: `kubectl get nodes`

#### 3. "Prometheus unreachable"

**macOS:**
```bash
brew install prometheus
brew services start prometheus
curl http://localhost:9090/-/healthy
```

**Docker:**
```bash
docker run -d -p 9090:9090 prom/prometheus
```

#### 4. Port 8000 already in use

**Solution:**
```bash
# Change port in .env
AGENT_PORT=8080

# Or via environment
export AGENT_PORT=8080
python3 app.py
```

#### 5. Module not found errors

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Setup Prometheus (if needed)

**macOS:**
```bash
brew install prometheus
brew services start prometheus
```

**Docker:**
```bash
docker run -d --name prometheus -p 9090:9090 prom/prometheus
```

**Kubernetes:**
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus
```

### Setup Loki (Optional)

**Docker:**
```bash
docker run -d --name loki -p 3100:3100 grafana/loki
```

### Debug Mode

Enable verbose logging:
```bash
export AGENT_LOG_LEVEL=DEBUG
python3 app.py
```

Check logs:
```bash
tail -f agent.log
```

---

## 📚 API Reference

### Endpoints

#### POST /chat

Ask observability questions.

**Request:**
```json
{
  "question": "What is the current CPU usage?",
  "namespace": "production",
  "service": "api",
  "time_range_minutes": 15,
  "include_logs": false
}
```

**Response:**
```json
{
  "response": {
    "answer": "...",
    "tool_results": [...],
    "confidence": "high",
    "recommendations": [...]
  },
  "request_id": "uuid",
  "timestamp": "2025-12-02T..."
}
```

#### GET /health

Health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "checks": {
    "agent": true,
    "kubernetes": true,
    "prometheus": true
  }
}
```

#### GET / 

API information.

#### GET /docs

Interactive API documentation (Swagger UI).

#### GET /redoc

Alternative API documentation (ReDoc).

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────┐
│      User Interface (HTTP)          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     FastAPI Application (app.py)    │
│  - /chat endpoint                   │
│  - /health endpoint                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Agent Orchestrator (agent.py)     │
│  - Tool selection                   │
│  - Parallel execution               │
│  - Context building                 │
│  - Gemini integration               │
└──────────────┬──────────────────────┘
               │
   ┌───────────┼───────────┐
   ▼           ▼           ▼
┌──────┐  ┌─────────┐  ┌──────┐
│ K8s  │  │Prometh- │  │ Loki │
│ API  │  │  eus    │  │      │
└──────┘  └─────────┘  └──────┘
```

### Tool Selection

**Current/instant metrics:**
- Detects: "current", "now", "right now"
- Uses: `instant_query()` → Single point-in-time value

**Historical metrics:**
- All other metric queries
- Uses: `metrics_query()` → Time series data

### File Structure

```
k8s-observability-agent/
├── app.py              # FastAPI application
├── agent.py            # Agent orchestrator
├── config.py           # Configuration
├── models.py           # Pydantic models
├── prompts.py          # AI prompts
├── tools/              # Tool adapters
│   ├── prometheus.py   # Metrics
│   ├── k8s_state.py    # Kubernetes API
│   ├── logs.py         # Loki logs
│   ├── alerts.py       # Alertmanager
│   └── kb.py           # Knowledge base
├── requirements.txt
├── .env                # Configuration
├── start.sh            # Quick start script
└── USER_GUIDE.md       # This file
```

---

## 🚢 Deployment

### Docker

```bash
# Build
docker build -t k8s-observability-agent .

# Run
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  k8s-observability-agent
```

### Kubernetes

```bash
# Deploy
kubectl apply -f deploy/kubernetes.yaml

# Access
kubectl port-forward svc/observability-agent 8000:8000

# Check status
kubectl get pods -l app=observability-agent
```

See `deploy/kubernetes.yaml` for complete manifests including:
- ServiceAccount
- RBAC (ClusterRole, ClusterRoleBinding)
- Secret (for Gemini API key)
- ConfigMap
- Deployment
- Service

---

## 🎯 Best Practices

### Query Optimization

**DO:**
- ✅ Be specific: "What is the current CPU usage in production?"
- ✅ Include namespace/service when relevant
- ✅ Use "current" for instant values
- ✅ Ask focused questions

**DON'T:**
- ❌ Too vague: "What's wrong?"
- ❌ Too broad: "Show everything"
- ❌ Multiple questions at once

### Prompt Customization

**DO:**
- ✅ Test prompt changes before production
- ✅ Version your prompts
- ✅ Document why you changed them
- ✅ Keep prompts focused

**DON'T:**
- ❌ Hardcode prompts in agent logic
- ❌ Change multiple prompts at once
- ❌ Make prompts overly complex

### Production Deployment

**Security:**
- 🔐 Use secret management (Vault, AWS Secrets)
- 🔐 Enable TLS/HTTPS
- 🔐 Add authentication
- 🔐 Implement rate limiting
- 🔐 Use network policies

**Monitoring:**
- 📊 Export agent metrics
- 📊 Set up alerts
- 📊 Track response times
- 📊 Monitor API usage

---

## 📖 Additional Resources

### Project Files
- **README.md** - Project overview
- **DEVELOPMENT.md** - Development guide
- **GETTING_STARTED.md** - Detailed setup
- **deploy/README.md** - Deployment guide

### Online Resources
- Gemini API: https://ai.google.dev/gemini-api/docs
- Prometheus: https://prometheus.io/docs/
- Kubernetes API: https://kubernetes.io/docs/reference/
- Loki: https://grafana.com/docs/loki/

---

## 🎉 Quick Reference

### Start Agent
```bash
./start.sh                    # Interactive
python3 app.py                # Direct
```

### Test
```bash
python3 check_prerequisites.py
python3 test_current_metrics.py
curl http://localhost:8000/health
```

### Common Questions
```bash
# Current metrics
"What is the current CPU usage?"
"Show current memory for api pod"

# Troubleshooting
"Why is my pod restarting?"
"Are there any alerts firing?"

# Analysis
"Show CPU trends over last hour"
"What's causing high memory usage?"
```

### API Docs
- http://localhost:8000/docs
- http://localhost:8000/redoc

---

**Need help?** Check the troubleshooting section or review `README.md` for more details.

**Ready to start?** Run `./start.sh` and ask your first question! 🚀
