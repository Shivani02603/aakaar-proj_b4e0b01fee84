from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from datetime import datetime
from contextlib import asynccontextmanager
from database.config import init_db
from backend.routes.files import router as files_router
from backend.routes.sessions import router as sessions_router
from ai.routes import router as ai_router

# Initialize FastAPI app
app = FastAPI(
    title="Aakaar Project",
    description="AI-powered web application for document processing and querying.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://frontend.example.com"],  # Restrict origins for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Mount routers
app.include_router(files_router, prefix="/api/files")
app.include_router(sessions_router, prefix="/api/sessions")
app.include_router(ai_router, prefix="/api/ai")

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    yield
    # Shutdown logic
    pass

app.router.lifespan_context = lifespan

# AI_ROUTER_INJECTION_POINT — do not remove this line