"""
FastAPI application for K8s Observability Agent.

Provides HTTP API endpoints:
- POST /chat: Main chat endpoint for asking questions
- GET /health: Health check endpoint
"""

import uuid
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Config, KubernetesClientManager
from .models import ChatRequest, ChatResponse, HealthResponse
from .agent import ObservabilityAgent

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.AGENT_LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("Starting K8s Observability Agent...")
    
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated")
        
        # Initialize Kubernetes client
        KubernetesClientManager.initialize()
        logger.info("Kubernetes client initialized")
        
        # Initialize agent
        app.state.agent = ObservabilityAgent()
        logger.info("Agent initialized")
        
        logger.info(f"Agent ready on port {Config.AGENT_PORT}")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down K8s Observability Agent...")


# Create FastAPI app
app = FastAPI(
    title="K8s Observability AI Agent",
    description="AI-powered observability agent for Kubernetes environments",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "request_id": str(uuid.uuid4())
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns the health status of the agent and its dependencies.
    """
    checks = {
        "agent": True,
        "kubernetes": False,
        "prometheus": False,
    }
    
    # Check Kubernetes connectivity
    try:
        core_v1 = KubernetesClientManager.get_core_v1_api()
        core_v1.list_namespace(limit=1)
        checks["kubernetes"] = True
    except Exception as e:
        logger.warning(f"Kubernetes health check failed: {str(e)}")
    
    # Check Prometheus connectivity
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{Config.PROMETHEUS_URL}/-/healthy")
            checks["prometheus"] = response.status_code == 200
    except Exception as e:
        logger.warning(f"Prometheus health check failed: {str(e)}")
    
    # Overall status
    status = "healthy" if all(checks.values()) else "degraded"
    
    return HealthResponse(
        status=status,
        version="0.1.0",
        checks=checks
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for asking observability questions.
    
    Args:
        request: ChatRequest with question and optional context
        
    Returns:
        ChatResponse with agent's answer and supporting data
    """
    request_id = str(uuid.uuid4())
    
    logger.info(f"[{request_id}] Received chat request: {request.question}")
    
    try:
        # Get agent from app state
        agent: ObservabilityAgent = app.state.agent
        
        # Process the query
        response = await agent.process_query(request)
        
        logger.info(f"[{request_id}] Request completed successfully")
        
        return ChatResponse(
            response=response,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to process query",
                "message": str(e),
                "request_id": request_id
            }
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "K8s Observability AI Agent",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint (stub).
    
    TODO: Implement Prometheus metrics export for the agent itself.
    """
    return {
        "message": "Metrics endpoint not yet implemented"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=Config.AGENT_PORT,
        log_level=Config.AGENT_LOG_LEVEL.lower(),
        reload=False
    )
