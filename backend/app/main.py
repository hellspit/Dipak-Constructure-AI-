from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.auth import router as auth_router
from app.email import router as email_router
from app.chatbot import router as chatbot_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Email Assistant API",
    description="AI-powered email assistant with Gmail integration",
    version="1.0.0"
)

# CORS middleware
# Build allowed origins list
allowed_origins = [
    settings.frontend_url,
    "http://localhost:3000",
    "http://localhost:3001",  # Alternative dev port
]

# Add production frontend URL if different from dev
if settings.frontend_url not in allowed_origins:
    allowed_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(email_router)
app.include_router(chatbot_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Email Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

