# K8s Observability AI Agent - Project Structure

## 📁 Directory Organization

```
k8s-observability-agent/
├── app/                          # Core Application Package
│   ├── __init__.py              # Package initializer
│   ├── main.py                  # FastAPI application entry point
│   ├── agent.py                 # AI agent orchestrator
│   ├── config.py                # Configuration management
│   ├── models.py                # Pydantic data models
│   ├── prompts.py               # AI prompts library
│   └── tools/                   # Tool adapters package
│       ├── __init__.py
│       ├── prometheus.py        # Prometheus metrics adapter
│       ├── k8s_state.py         # Kubernetes API adapter
│       ├── logs.py              # Loki logs adapter
│       ├── alerts.py            # Alertmanager adapter
│       └── kb.py                # Knowledge base adapter (stub)
│
├── scripts/                      # Utility Scripts
│   ├── validate_services.py     # Service validation script
│   ├── validate.sh              # Quick validation wrapper
│   ├── fix_connections.py       # Port-forward helper
│   └── chat.py                  # Interactive CLI client
│
├── tests/                        # Test Suite
│   ├── test_agent.py            # Agent unit tests
│   ├── test_current_metrics.py  # Current metrics tests
│   └── example_usage.py         # Usage examples
│
├── docs/                         # Documentation
│   ├── USER_GUIDE.md            # Complete user guide
│   ├── GETTING_STARTED.md       # Setup walkthrough
│   ├── DEVELOPMENT.md           # Developer guide
│   ├── PROJECT_SUMMARY.md       # Technical overview
│   ├── PROJECT_STRUCTURE.md     # This file
│   └── VALIDATION_SYSTEM.md     # Validation architecture
│
├── deploy/                       # Deployment Configurations
│   ├── kubernetes.yaml          # K8s deployment manifests
│   └── README.md                # Deployment instructions
│
├── .env.example                  # Environment template
├── .env                          # Local configuration (gitignored)
├── .gitignore                    # Git ignore rules
├── Dockerfile                    # Container image definition
├── LICENSE                       # Project license
├── README.md                     # Project overview
├── requirements.txt              # Python dependencies
└── start.sh                      # Quick start script
```

---

## 📦 Package Details

### `app/` - Core Application

**Purpose**: Contains the main application code organized as a Python package.

| File | Description |
|------|-------------|
| `main.py` | FastAPI application with HTTP endpoints |
| `agent.py` | Observability agent with tool orchestration |
| `config.py` | Configuration loader and Kubernetes client manager |
| `models.py` | Pydantic models for requests/responses |
| `prompts.py` | Centralized AI prompts for Gemini |
| `tools/` | Adapters for external data sources |

**Running**: 
```bash
python -m app.main
```

### `app/tools/` - Tool Adapters

**Purpose**: Adapters that query external observability platforms.

| Adapter | Data Source | Purpose |
|---------|-------------|---------|
| `prometheus.py` | Prometheus | Metrics queries (instant & range) |
| `k8s_state.py` | Kubernetes API | Pod/Node state, events |
| `logs.py` | Loki | Log queries via LogQL |
| `alerts.py` | Alertmanager | Active/silenced alerts |
| `kb.py` | Knowledge base | Runbooks/docs (stub) |

### `scripts/` - Utilities

**Purpose**: Helper scripts for setup, testing, and interaction.

| Script | Purpose | Usage |
|--------|---------|-------|
| `validate_services.py` | Validate all services | `python3 scripts/validate_services.py` |
| `validate.sh` | Quick validation wrapper | `./scripts/validate.sh` |
| `fix_connections.py` | Port-forward cluster services | `python3 scripts/fix_connections.py` |
| `chat.py` | Interactive CLI client | `python3 scripts/chat.py` |

### `tests/` - Test Suite

**Purpose**: Unit tests and usage examples.

| File | Purpose |
|------|---------|
| `test_agent.py` | Unit tests for agent logic |
| `test_current_metrics.py` | Tests for current metrics feature |
| `example_usage.py` | Example API usage |

**Running tests**:
```bash
pytest tests/
```

### `docs/` - Documentation

**Purpose**: Comprehensive project documentation.

| Document | Content |
|----------|---------|
| `USER_GUIDE.md` | Complete usage guide (installation, config, API) |
| `GETTING_STARTED.md` | Step-by-step setup walkthrough |
| `DEVELOPMENT.md` | Contribution guidelines |
| `PROJECT_SUMMARY.md` | Technical architecture overview |
| `PROJECT_STRUCTURE.md` | Code organization guide |
| `VALIDATION_SYSTEM.md` | Validation system architecture |

### `deploy/` - Deployment

**Purpose**: Kubernetes and container deployment configs.

| File | Content |
|------|---------|
| `kubernetes.yaml` | K8s manifests (Deployment, Service, RBAC) |
| `README.md` | Deployment instructions |

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Local environment variables (gitignored) |
| `.env.example` | Template for environment setup |
| `requirements.txt` | Python package dependencies |
| `Dockerfile` | Container image build instructions |
| `.gitignore` | Files excluded from git |

---

## 🚀 Quick Start

### Local Development

```bash
# 1. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

# 3. Start
python -m app.main
```

### Using Start Script

```bash
./start.sh
```

### Docker

```bash
# Build
docker build -t k8s-observability-agent .

# Run
docker run -d -p 8081:8081 --env-file .env k8s-observability-agent
```

### Kubernetes

```bash
kubectl apply -f deploy/kubernetes.yaml
kubectl port-forward svc/observability-agent 8081:8081
```

---

## 📝 Import Structure

### Package Imports (Internal)

Within the `app/` package, use relative imports:

```python
# In app/main.py
from .agent import ObservabilityAgent
from .models import ChatRequest
from .config import Config

# In app/agent.py
from .models import AgentResponse
from .tools import metrics_query, k8s_state_query_pods

# In app/tools/prometheus.py
from ..config import Config
```

### External Imports (Scripts/Tests)

Scripts and tests import from the `app` package:

```python
# In tests/test_agent.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import ChatRequest
from app.agent import ObservabilityAgent
```

---

## 🔄 Migration from Old Structure

### What Changed

**Before**:
```
.
├── app.py           # Main application
├── agent.py         # Agent logic
├── config.py        # Configuration
├── models.py        # Data models
├── prompts.py       # Prompts
├── tools/           # Tool adapters
├── check_prerequisites.py
├── fix_connections.py
├── chat.py
└── test_agent.py
```

**After**:
```
.
├── app/             # All application code
│   ├── main.py      # (was app.py)
│   ├── agent.py
│   ├── config.py
│   ├── models.py
│   ├── prompts.py
│   └── tools/
├── scripts/         # Utility scripts
├── tests/           # Test files
└── docs/            # Documentation
```

### Command Changes

| Old Command | New Command |
|-------------|-------------|
| `python app.py` | `python -m app.main` |
| `python scripts/validate_services.py` | `python scripts/validate_services.py` |
| `python chat.py` | `python scripts/chat.py` |
| `pytest test_agent.py` | `pytest tests/` |

---

## 📊 File Statistics

| Category | Count | Purpose |
|----------|-------|---------|
| **Core App** | 6 files | Main application logic |
| **Tool Adapters** | 5 files | External data sources |
| **Scripts** | 3 files | Utilities and helpers |
| **Tests** | 3 files | Testing and examples |
| **Docs** | 4 files | User and dev documentation |
| **Deploy** | 2 files | Kubernetes deployment |
| **Config** | 5 files | Environment and dependencies |
| **Total** | 28 files | Organized structure |

---

## 🎯 Design Principles

### 1. **Separation of Concerns**
- Core application (`app/`)
- Utilities (`scripts/`)
- Tests (`tests/`)
- Documentation (`docs/`)

### 2. **Package Structure**
- `app/` is a proper Python package
- Enables module-based execution: `python -m app.main`
- Clear import hierarchy with relative imports

### 3. **Scalability**
- Easy to add new tools in `app/tools/`
- Extensible prompt library in `app/prompts.py`
- Modular architecture for future features

### 4. **Developer Experience**
- Intuitive directory names
- Comprehensive documentation
- Quick start scripts
- Clear testing structure

---

## 🔍 Finding Things

### "Where do I...?"

| Task | Location |
|------|----------|
| **Start the agent** | `python -m app.main` or `./start.sh` |
| **Add a new tool** | Create adapter in `app/tools/` |
| **Modify prompts** | Edit `app/prompts.py` |
| **Add API endpoint** | Modify `app/main.py` |
| **Change configuration** | Edit `app/config.py` and `.env` |
| **Run tests** | `pytest tests/` |
| **Read docs** | Check `docs/USER_GUIDE.md` |
| **Deploy to K8s** | Use `deploy/kubernetes.yaml` |

---

## 📚 Related Documentation

- **[README.md](../README.md)** - Project overview
- **[USER_GUIDE.md](./docs/USER_GUIDE.md)** - Complete usage guide
- **[GETTING_STARTED.md](./docs/GETTING_STARTED.md)** - Setup instructions
- **[DEVELOPMENT.md](./docs/DEVELOPMENT.md)** - Contributing guidelines

---

## ✅ Best Practices

### Adding New Code

1. **New tool adapter**: Add to `app/tools/`, export from `__init__.py`
2. **New API endpoint**: Add to `app/main.py`
3. **New model**: Add to `app/models.py`
4. **New prompt**: Add to `app/prompts.py`
5. **New utility**: Add to `scripts/`
6. **New test**: Add to `tests/`

### Imports

- **Within app package**: Use relative imports (`.module`, `..package`)
- **From outside**: Use absolute imports (`from app.module import ...`)
- **Add project root to sys.path in scripts/tests if needed**

### Configuration

- **Never commit `.env`** (gitignored)
- **Update `.env.example`** when adding new variables
- **Use `Config` class** in `app/config.py` for all settings

---

**Last Updated**: December 2, 2025  
**Structure Version**: 2.0
