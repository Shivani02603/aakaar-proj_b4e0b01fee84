from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from datetime import datetime
from database.config import init_db
from backend.main import general_exception_handler, validation_exception_handler, http_exception_handler, startup_event, shutdown_event
from backend.routes.files import router as files_router
from backend.routes.sessions import router as sessions_router

# Initialize FastAPI app
app = FastAPI(
    title="Aakaar Project",
    description="AI-powered web application backend",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow localhost:3000 for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(files_router, prefix="/api/files")
app.include_router(sessions_router, prefix="/api/sessions")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return await general_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return await general_exception_handler(request, exc)

# Lifespan context manager
@app.on_event("startup")
async def on_startup():
    await startup_event()
    init_db()

@app.on_event("shutdown")
async def on_shutdown():
    await shutdown_event()

# AI_ROUTER_INJECTION_POINT — do not remove this line