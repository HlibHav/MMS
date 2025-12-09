"""
FastAPI Application

Main FastAPI application setup and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import discovery, scenarios, optimization, creative, data

app = FastAPI(
    title="Promo Scenario Co-Pilot API",
    description="AI-powered promotional campaign planning and optimization system",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(discovery.router, prefix="/api/v1/discovery", tags=["discovery"])
app.include_router(scenarios.router, prefix="/api/v1/scenarios", tags=["scenarios"])
app.include_router(optimization.router, prefix="/api/v1/optimization", tags=["optimization"])
app.include_router(creative.router, prefix="/api/v1/creative", tags=["creative"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Promo Scenario Co-Pilot API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
