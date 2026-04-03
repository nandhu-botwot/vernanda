from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.models.database import init_db
from backend.api.routes_upload import router as upload_router
from backend.api.routes_calls import router as calls_router
from backend.api.routes_reports import router as reports_router
from backend.api.routes_analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables, ensure directories exist
    await init_db()
    settings.upload_path
    settings.processed_path
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Vernanda QA System",
    description="Automated Quality Assurance system for Veranda Race sales calls",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(calls_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
