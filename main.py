from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from endpoints.auth import router as auth_router
from endpoints.query import router as query_router
from endpoints.departments import router as departments_router
from endpoints.team import router as team_router
from endpoints.admin_auth import router as admin_auth_router
from database import create_tables
from contextlib import asynccontextmanager
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("Starting application...")
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't fail the startup if database creation fails
        pass
    yield
    # Shutdown (if needed)
    logger.info("Application shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Query Portal API",
    description="Backend API for Academic Tracker Query Portal",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - Allow all origins
# This must be added BEFORE any routes or other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using wildcard origin
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Global OPTIONS handler to ensure preflight requests receive CORS headers
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    """Catch-all OPTIONS handler for CORS preflight requests."""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            "Access-Control-Max-Age": "86400",
            "Content-Length": "0",
        }
    )
# Include routers
app.include_router(auth_router)
app.include_router(query_router)
app.include_router(departments_router)
app.include_router(team_router)
app.include_router(admin_auth_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Query Portal API is running",
        "status": "active",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

# CORS test endpoint
@app.get("/cors-test")
async def cors_test():
    """Test endpoint to verify CORS is working"""
    return {
        "status": "success",
        "message": "CORS is working correctly!",
        "cors_enabled": True,
        "timestamp": os.sys.version
    }

# Simple test endpoint for debugging
@app.get("/test")
async def test_endpoint():
    return {
        "message": "Test endpoint working",
        "environment": os.getenv("DEPLOY_ENV", "local"),
        "python_version": os.sys.version
    }

# Get API info endpoint
@app.get("/api/info")
async def api_info():
    return {
        "title": "Query Portal API",
        "version": "1.0.0",
        "description": "Backend API for Academic Tracker Query Portal",
        "endpoints": {
            "auth": {
                "signup": "POST /auth/signup",
                "login": "POST /auth/login",
                "get_users": "GET /auth/users",
                "get_user_by_id": "GET /auth/users/{user_id}",
                "get_user_by_email": "GET /auth/users/email/{email}"
            },
            "queries": {
                "create_query": "POST /queries/",
                "get_queries": "GET /queries/",
                "get_user_queries": "GET /queries/user/{user_id}",
                "get_query_by_id": "GET /queries/{query_id}",
                "update_query": "PUT /queries/{query_id}",
                "delete_query": "DELETE /queries/{query_id}",
                "get_stats": "GET /queries/stats/overview",
                "upload_attachment": "POST /queries/{query_id}/upload"
            },
            "departments": {
                "get_departments": "GET /departments/",
                "get_department": "GET /departments/{department_id}"
            }
        }
    }

# For local development only
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# End of main application file
