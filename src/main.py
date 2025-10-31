from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.logging_config import logger
from src.api.v1.router import api_router
from src.config.database_settings import database_lifespan, get_database_manager
from src.repositories.database import check_database_connection

logger.info("Starting COSC-4353 Volunteer Management API...")

# Create FastAPI application with database lifespan management
app = FastAPI(
    title="Volunteer Management System",
    description="Volunteer Service Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=database_lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # wild card for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

@app.get("/health/database")
async def database_health_check():
    """Database health check endpoint"""
    try:
        db_manager = get_database_manager()
        engine = db_manager.get_engine()
        is_connected = check_database_connection(engine)
        
        return {
            "database_status": "connected" if is_connected else "disconnected",
            "database_url": str(engine.url).replace(engine.url.password or "", "***") if engine.url.password else str(engine.url)
        }
    except Exception as e:
        return {
            "database_status": "error",
            "error": str(e)
        }
