from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from .controllers import governance_controller, dlq_controller
from .rules import RuleEngine
from .services import EventEmitter
from .tracing import Tracer
from .utils.config import settings


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Governance Engine",
    description="CEO AI of the Autonomous Company OS - Governance and decision-making layer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
def _cors_allowed_origins() -> list:
    # SECURITY_REVIEW.md #1 - no wildcard with credentials. Set
    # ALLOWED_ORIGINS (comma-separated) when a browser client exists.
    import os
    return [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(governance_controller.router)
app.include_router(dlq_controller.router)

# Global clients
rule_engine: RuleEngine = None
event_emitter: EventEmitter = None
tracer: Tracer = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global rule_engine, event_emitter, tracer
    
    logger.info("service_starting", service=settings.service_name)
    
    # Initialize tracer
    tracer = Tracer(settings.service_name)
    
    # Initialize rule engine
    rule_engine = RuleEngine()
    logger.info("rule_engine_initialized")
    
    # Initialize event emitter
    event_emitter = EventEmitter(settings.rabbitmq_url)
    await event_emitter.connect()
    logger.info("event_emitter_initialized")
    
    logger.info("service_started", service=settings.service_name)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global event_emitter
    
    logger.info("service_stopping")
    
    if event_emitter:
        await event_emitter.disconnect()
    
    logger.info("service_stopped")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "healthy"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Governance Engine",
        "version": "1.0.0",
        "description": "CEO AI of the Autonomous Company OS",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    asyncio.run(uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True
    ))
