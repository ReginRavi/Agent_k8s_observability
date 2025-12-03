# Development Guide

This guide covers development workflows, testing, and contribution guidelines for the K8s Observability Agent.

## Development Setup

### Prerequisites

- Python 3.9+
- Access to a Kubernetes cluster (local or remote)
- Docker (for building images)
- kubectl configured

### Initial Setup

Use the quickstart script:

```bash
./quickstart.sh
```

Or manually:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

## Project Structure

```
k8s-observability-agent/
├── app.py                 # FastAPI application
├── agent.py               # Agent orchestrator + Gemini integration
├── config.py              # Configuration management
├── models.py              # Pydantic models
├── tools/                 # Tool adapters
│   ├── prometheus.py      # Metrics queries
│   ├── k8s_state.py       # K8s API queries
│   ├── logs.py            # Log queries
│   ├── alerts.py          # Alert queries
│   └── kb.py              # Knowledge base (stub)
├── deploy/                # Kubernetes manifests
├── test_agent.py          # Tests
└── example_usage.py       # Usage examples
```

## Running Locally

### Option 1: Direct Python

```bash
source venv/bin/activate
python app.py
```

### Option 2: Uvicorn with auto-reload

```bash
source venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Docker

```bash
docker build -t k8s-observability-agent:dev .
docker run -p 8000:8000 --env-file .env k8s-observability-agent:dev
```

## Testing

### Run all tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest test_agent.py -v
```

### Run specific tests

```bash
pytest test_agent.py::TestObservabilityAgent::test_determine_tools_basic -v
```

### Test with coverage

```bash
pip install pytest-cov
pytest test_agent.py --cov=. --cov-report=html
```

## Development Workflow

### Adding a New Tool Adapter

1. **Create the adapter file** in `tools/`:

```python
# tools/my_new_tool.py
async def my_new_query(param: str) -> Dict[str, Any]:
    """Query description."""
    try:
        # Implementation
        return {
            "success": True,
            "data": {...}
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

2. **Export it** in `tools/__init__.py`:

```python
from .my_new_tool import my_new_query

__all__ = [..., "my_new_query"]
```

3. **Update the agent** in `agent.py`:

```python
# In _determine_tools():
if "my_keyword" in question_lower:
    tools.append("my_new_tool")

# In _execute_tools():
elif tool_name == "my_new_tool":
    data = await my_new_query(...)
```

4. **Add tests** in `test_agent.py`

### Modifying the System Prompt

The system prompt is in `agent.py` as `SYSTEM_PROMPT`. Edit it to change how Gemini interprets and responds to queries.

Key sections:
- Role definition
- Available tools
- Response structure
- Guidelines

### Adding New API Endpoints

1. **Define the endpoint** in `app.py`:

```python
@app.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

2. **Add request/response models** in `models.py` if needed

3. **Update documentation** in README.md

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints
- Write docstrings for all functions
- Keep functions focused and small

### Formatting

Use `black` for formatting:

```bash
pip install black
black .
```

### Linting

Use `flake8`:

```bash
pip install flake8
flake8 . --max-line-length=100
```

### Type Checking

Use `mypy`:

```bash
pip install mypy
mypy . --ignore-missing-imports
```

## Debugging

### Enable Debug Logging

Set in `.env`:
```
AGENT_LOG_LEVEL=DEBUG
```

### Debug Tool Execution

Add logging in tool adapters:

```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Executing query: {query}")
```

### Debug Gemini Calls

The full prompt sent to Gemini is logged at DEBUG level. Check logs to see what context is being sent.

### Use the Interactive API Docs

FastAPI provides interactive docs at `http://localhost:8000/docs`

## Performance Optimization

### Parallel Tool Execution

Tools are currently executed sequentially. For better performance, consider using `asyncio.gather()`:

```python
results = await asyncio.gather(
    metrics_query(...),
    k8s_state_query_pods(...),
    alerts_list(...)
)
```

### Caching

Consider adding caching for:
- Prometheus queries (short TTL)
- K8s resource lists
- Alert states

### Connection Pooling

The current implementation creates new HTTP clients for each request. Consider using a persistent client pool.

## Common Development Tasks

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### Build Docker Image

```bash
docker build -t k8s-observability-agent:$(git rev-parse --short HEAD) .
```

### Test Against Local Prometheus

If you have Prometheus running locally:

```bash
# In .env
PROMETHEUS_URL=http://localhost:9090
IN_CLUSTER=false
```

### Test Against Local Kubernetes

```bash
# Make sure kubectl is configured
kubectl cluster-info

# In .env
IN_CLUSTER=false
KUBECONFIG_PATH=~/.kube/config
```

## Troubleshooting

### "Kubernetes client initialization failed"

- Check that kubectl works: `kubectl get pods`
- Verify KUBECONFIG_PATH in .env
- If in-cluster, check ServiceAccount permissions

### "Gemini API error"

- Verify API key is correct
- Check API quota/limits
- Review Gemini API status

### "Import errors"

- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### "Tool timeout"

- Increase timeout in config.py
- Check network connectivity to backends
- Review backend performance

## Contributing

### Contribution Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests
5. Run tests: `pytest`
6. Format code: `black .`
7. Commit: `git commit -m "Add my feature"`
8. Push: `git push origin feature/my-feature`
9. Create a Pull Request

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `chore`: Maintenance

Example:
```
feat: Add support for custom metrics queries

- Add custom_metrics_query function
- Update agent to handle custom queries
- Add tests for custom queries

Closes #123
```

## Release Process

1. Update version in `app.py` and `README.md`
2. Update CHANGELOG.md
3. Create a git tag: `git tag v0.2.0`
4. Build and push Docker image with version tag
5. Create GitHub release

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [Prometheus API](https://prometheus.io/docs/prometheus/latest/querying/api/)
- [Loki API](https://grafana.com/docs/loki/latest/api/)
- [Gemini API](https://ai.google.dev/docs)
