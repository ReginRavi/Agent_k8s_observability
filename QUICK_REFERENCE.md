# 🚀 K8s Observability Agent - Quick Reference

## ⚡ Start the Agent

```bash
./start.sh
```

or

```bash
python -m app.main
```

---

## 📁 Project Layout

```
📦 k8s-observability-agent/
│
├── 📂 app/                    👈 Core application code
│   ├── main.py               # FastAPI server
│   ├── agent.py              # AI orchestrator
│   ├── config.py             # Configuration
│   ├── models.py             # Data models
│   ├── prompts.py            # AI prompts
│   └── tools/                # Data source adapters
│
├── 📂 scripts/                👈 Utility scripts
│   ├── chat.py               # Chat with agent
│   ├── check_prerequisites.py
│   └── fix_connections.py
│
├── 📂 tests/                  👈 Test suite
│   ├── test_agent.py
│   ├── test_current_metrics.py
│   └── example_usage.py
│
├── 📂 docs/                   👈 Documentation
│   ├── USER_GUIDE.md         # Main guide
│   ├── GETTING_STARTED.md
│   ├── DEVELOPMENT.md
│   └── PROJECT_SUMMARY.md
│
└── 📂 deploy/                 👈 Kubernetes configs
    ├── kubernetes.yaml
    └── README.md
```

---

## 🎯 Common Tasks

### Start & Monitor

```bash
# Quick start (auto-setup with validation)
./start.sh

# Validate services first
./scripts/validate.sh
# or
python scripts/validate_services.py

# Manual start
python -m app.main

# Chat with agent
python scripts/chat.py
```

### Port-Forward (if cluster services)

```bash
# In one terminal
python scripts/fix_connections.py

# In another terminal
./start.sh
```

### Testing

```bash
# Run all tests
pytest tests/

# Test current metrics
python tests/test_current_metrics.py

# Example usage
python tests/example_usage.py
```

---

## 🌐 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/chat` | POST | Ask questions |
| `/docs` | GET | Swagger UI |
| `/redoc` | GET | API docs |

### Example Request

```bash
curl -X POST http://localhost:8081/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the current CPU usage?",
    "namespace": "default"
  }'
```

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](./README.md) | Project overview |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | Detailed structure |
| [docs/USER_GUIDE.md](./docs/USER_GUIDE.md) | Complete guide |
| [RESTRUCTURING_SUMMARY.md](./RESTRUCTURING_SUMMARY.md) | What changed |

---

## 🔧 Configuration

Edit `.env` file:

```bash
# Required
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.5-flash

# Services
PROMETHEUS_URL=http://localhost:19090
LOKI_URL=http://localhost:3100
ALERTMANAGER_URL=http://localhost:9093

# Agent
AGENT_PORT=8081
```

---

## 🐳 Docker

```bash
# Build
docker build -t k8s-agent .

# Run
docker run -d -p 8081:8081 --env-file .env k8s-agent
```

---

## ☸️ Kubernetes

```bash
# Deploy
kubectl apply -f deploy/kubernetes.yaml

# Port-forward
kubectl port-forward svc/observability-agent 8081:8081

# Check logs
kubectl logs -f deployment/observability-agent
```

---

## 💡 Quick Tips

1. **Always run `./start.sh`** - It checks prerequisites automatically
2. **Port 8081** is the default (configurable via `AGENT_PORT`)
3. **Cluster services?** Run `scripts/fix_connections.py` first
4. **Chat interactively**: `python scripts/chat.py`
5. **API docs**: http://localhost:8081/docs

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port in use | `lsof -ti:8081 \| xargs kill -9` |
| Missing deps | `pip install -r requirements.txt` |
| Can't find module | Run from project root |
| K8s connection failed | `kubectl cluster-info` |
| Prometheus unreachable | Check URL in `.env` |

---

**Need more help?** See [docs/USER_GUIDE.md](./docs/USER_GUIDE.md)
