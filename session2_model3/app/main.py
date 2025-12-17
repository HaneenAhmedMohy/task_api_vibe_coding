from fastapi import FastAPI
from .database import engine
from .models.task import Base
from .routers.tasks import router as tasks_router

app = FastAPI(
    title="Task Management API",
    description="A RESTful API for managing tasks with filtering capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
app.include_router(tasks_router)

# Create database tables
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/", tags=["root"])
def read_root():
    return {
        "message": "Task Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "tasks_endpoint": "/api/v1/tasks"
    }