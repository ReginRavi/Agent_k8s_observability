# Getting Started with K8s Observability AI Agent

This guide will help you get the K8s Observability AI Agent up and running in **5 minutes**.

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.9+** installed
- ✅ **Gemini API Key** ([Get one here](https://ai.google.dev/))
- ✅ **Kubernetes cluster** access (local or remote)
- ✅ **Prometheus** endpoint accessible
- ✅ (Optional) **Loki** and **Alertmanager** endpoints

## Quick Start (5 Minutes)

### Step 1: Get the Code

```bash
cd /Users/reginravi/Documents/Agent_k8s_observability
```

### Step 2: Run the Setup Script

```bash
./quickstart.sh
```

This script will:
- Create a Python virtual environment
- Install all dependencies
- Create a `.env` file from the template
- Validate your configuration

### Step 3: Configure Your Environment

Edit the `.env` file and set your Gemini API key:

```bash
nano .env
```

**Required settings:**
```env
GEMINI_API_KEY=your-actual-gemini-api-key-here
```

**Optional settings** (update if different from defaults):
```env
PROMETHEUS_URL=http://localhost:9090
LOKI_URL=http://localhost:3100
ALERTMANAGER_URL=http://localhost:9093
IN_CLUSTER=false  # Set to true when running in K8s
```

### Step 4: Start the Agent

```bash
source venv/bin/activate
python app.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Test the Agent

Open a new terminal and try the example queries:

```bash
# Activate the virtual environment
source venv/bin/activate

# Run the example script
python example_usage.py
```

Or test manually with curl:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Are there any alerts firing right now?",
    "time_range_minutes": 15
  }'
```

## What's Next?

### Explore the API

Visit the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Try Different Queries

Ask the agent questions like:

1. **General Health**
   ```json
   {
     "question": "What's the overall health of the cluster?"
   }
   ```

2. **Namespace-Specific**
   ```json
   {
     "question": "Are there any issues in the production namespace?",
     "namespace": "production"
   }
   ```

3. **Service-Specific**
   ```json
   {
     "question": "Why is my app pod restarting?",
     "namespace": "default",
     "service": "my-app",
     "include_logs": true
   }
   ```

4. **Performance Analysis**
   ```json
   {
     "question": "Is there high CPU usage anywhere?",
     "time_range_minutes": 30
   }
   ```

### Deploy to Kubernetes

Once you've tested locally, deploy to your cluster:

```bash
# Update the Gemini API key in deploy/kubernetes.yaml
nano deploy/kubernetes.yaml

# Apply the manifests
kubectl apply -f deploy/kubernetes.yaml

# Check the deployment
kubectl get pods -l app=observability-agent
kubectl logs -l app=observability-agent -f
```

See `deploy/README.md` for detailed deployment instructions.

## Common Issues

### "GEMINI_API_KEY must be set"

**Solution**: Make sure you've set `GEMINI_API_KEY` in your `.env` file with a valid API key.

### "Failed to initialize Kubernetes client"

**Solution**: 
- If running locally, ensure `IN_CLUSTER=false` in `.env`
- Check that `kubectl` is configured: `kubectl cluster-info`
- Verify your kubeconfig path is correct

### "Prometheus query timeout"

**Solution**:
- Verify Prometheus is running: `curl http://localhost:9090/-/healthy`
- Update `PROMETHEUS_URL` in `.env` if it's different
- Check network connectivity

### "Module not found" errors

**Solution**:
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Understanding the Response

The agent returns structured responses:

```json
{
  "response": {
    "answer": "Natural language explanation of findings",
    "tool_results": [
      {
        "tool_name": "k8s_pods",
        "success": true,
        "data": {...},
        "execution_time_ms": 123.45
      }
    ],
    "confidence": "high|medium|low",
    "recommendations": [
      "Specific action to take",
      "Another recommendation"
    ],
    "metadata": {
      "model": "gemini-3.0-pro",
      "tools_used": ["k8s_pods", "alerts", "metrics"]
    }
  },
  "request_id": "unique-id",
  "timestamp": "2025-12-01T12:00:00Z"
}
```

**Key fields:**
- `answer`: The AI's analysis and explanation
- `tool_results`: Raw data from each tool (for debugging)
- `confidence`: How confident the AI is in its analysis
- `recommendations`: Specific next steps to take
- `metadata`: Information about the query execution

## Configuration Options

All configuration is done via environment variables in `.env`:

### Required
- `GEMINI_API_KEY`: Your Gemini API key

### Observability Endpoints
- `PROMETHEUS_URL`: Prometheus endpoint (default: `http://prometheus:9090`)
- `LOKI_URL`: Loki endpoint (default: `http://loki:3100`)
- `ALERTMANAGER_URL`: Alertmanager endpoint (default: `http://alertmanager:9093`)
- `GRAFANA_URL`: Grafana endpoint (default: `http://grafana:3000`)

### Kubernetes
- `IN_CLUSTER`: Set to `true` when running in K8s (default: `true`)
- `KUBECONFIG_PATH`: Path to kubeconfig for local development

### Agent Settings
- `AGENT_PORT`: Port to run on (default: `8000`)
- `AGENT_LOG_LEVEL`: Logging level - `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)
- `DEFAULT_LOOKBACK_MINUTES`: Default time range for queries (default: `15`)

## Development Mode

For development with auto-reload:

```bash
source venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Changes to Python files will automatically restart the server.

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest test_agent.py -v

# Run with coverage
pip install pytest-cov
pytest test_agent.py --cov=. --cov-report=html
```

## Next Steps

1. **Read the full documentation**: See `README.md`
2. **Learn about development**: See `DEVELOPMENT.md`
3. **Deploy to Kubernetes**: See `deploy/README.md`
4. **Understand the architecture**: See `PROJECT_SUMMARY.md`

## Getting Help

- **Documentation**: Check `README.md` and `DEVELOPMENT.md`
- **Examples**: See `example_usage.py`
- **API Docs**: Visit http://localhost:8000/docs
- **Issues**: Open a GitHub issue

## Tips for Best Results

1. **Be specific**: "Why is the payment-service pod in the production namespace restarting?" is better than "Why is my pod restarting?"

2. **Provide context**: Use the `namespace` and `service` fields to focus the analysis

3. **Adjust time range**: For recent issues, use a shorter time range (5-15 minutes). For historical analysis, use longer ranges (30-60 minutes)

4. **Enable logs**: Set `include_logs: true` for error investigation

5. **Review tool results**: The raw data is included in the response for transparency

## Architecture Overview

```
User Question
     ↓
Agent Orchestrator
     ↓
Tool Selection (based on keywords)
     ↓
Parallel Tool Execution
  ├─ Prometheus (metrics)
  ├─ Kubernetes API (pods, events)
  ├─ Loki (logs)
  └─ Alertmanager (alerts)
     ↓
Context Building
     ↓
Gemini 3 (AI reasoning)
     ↓
Response Parsing
     ↓
Structured Response
```

## Success! 🎉

You now have a working K8s Observability AI Agent!

The agent can help you:
- ✅ Diagnose pod issues
- ✅ Investigate performance problems
- ✅ Understand alert root causes
- ✅ Correlate metrics, logs, and events
- ✅ Get actionable recommendations

Happy troubleshooting! 🚀
