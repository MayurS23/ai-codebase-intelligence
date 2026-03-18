"""
main.py — FastAPI application entry point.
"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.api.routes import ingest, query, architecture

settings = get_settings()

app = FastAPI(
    title="AI Codebase Intelligence Platform",
    description="Understand any GitHub repository like a senior engineer.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow Streamlit frontend (and anything local) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(architecture.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "service": "AI Codebase Intelligence Platform",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
