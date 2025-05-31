from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

from .config.settings import settings
from .api.routes import upload, process, download

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Automatic video generation system for mathematical textbooks and papers",
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(process.router, prefix="/api", tags=["process"])
app.include_router(download.router, prefix="/api", tags=["download"])

# Serve static files
static_dir = Path("frontend/dist")
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )