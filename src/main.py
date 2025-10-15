from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.logging_config import logger
from src.api.v1.router import api_router

logger.info("Starting COSC-4353 Volunteer Management API...")

# Create FastAPI application
app = FastAPI(
    title="Volunteer Management System",
    description="Volunteer Service Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
