from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.models.database import engine, Base
from app.models import task  # Import the Task model to ensure it's registered
from app.routers import tasks
from app.core.handlers import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Task Management API",
    description="A RESTful API for task management with comprehensive error handling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])


@app.get("/", tags=["root"])
async def read_root():
    """
    Root endpoint.

    Returns basic information about the API.
    """
    return {
        "message": "Welcome to Task Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns the health status of the API.
    """
    return {
        "status": "healthy",
        "service": "Task Management API",
        "version": "1.0.0"
    }