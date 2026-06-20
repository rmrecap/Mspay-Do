import render_setup

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from starlette.exceptions import HTTPException as StarletteHTTPException
from routers.client import client
from routers.command import command
from routers.notification import notification
from routers.auth import auth
from os import getenv
from datetime import datetime
import secrets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    version="4.0",
    title="Mspay Do",
    description="Mspay Do",
    redoc_url=None,
)

# Configure CORS - restrict to specific origins if possible
origins = getenv("ALLOWED_ORIGINS", "*").split(",")
app.include_router(client.router)
app.include_router(command.router)
app.include_router(notification.router)
app.include_router(auth.router)
auth.check_auth()
app.mount("/v4", StaticFiles(directory="build", html=True), name="build")
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Settings(BaseModel):
    # Use environment variable for JWT secret, with strong fallback
    authjwt_secret_key: str = getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.authjwt_secret_key == "jaihind":
            logger.warning("⚠️ WARNING: Using default JWT secret! Set JWT_SECRET_KEY environment variable!")


# callback to get your configuration
@AuthJWT.load_config
def get_config():
    return Settings()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    if exc.status_code == 404:
        return HTMLResponse(open("build/index.html", "rb").read())
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/v4")
async def index(request: Request):
    return HTMLResponse(open("build/index.html", "rb").read())


@app.get("/")
async def root():
    return RedirectResponse("/v4/overview")


@app.get("/version")
async def version():
    return {"version": app.version}


@app.get("/health")
async def health():
    """
    Health check endpoint for keep-alive and monitoring.
    Used by Render, GitHub Actions, and monitoring services.
    Returns immediately without database access to avoid timeouts.
    """
    return JSONResponse({
        "status": "healthy",
        "version": app.version,
        "timestamp": datetime.now().isoformat(),
        "message": "API is running"
    })


@app.get("/status")
async def status(Authorize: AuthJWT = Depends()):
    """
    Detailed status endpoint (requires authentication).
    Shows API, database, and device connection stats.
    """
    Authorize.jwt_required()
    from utils.connection_resilience import get_connection_pool
    
    try:
        pool = get_connection_pool()
        stats = pool.get_stats()
        
        return JSONResponse({
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "api_version": app.version,
            "database_backend": "Firebase Realtime Database",
            "devices": {
                "total": stats["total_devices"],
                "online": stats["online_devices"],
                "offline": stats["offline_devices"],
            },
            "offline_devices": pool.get_offline_devices()[:10]  # Top 10 offline
        })
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return JSONResponse(
            {"status": "degraded", "error": str(e)},
            status_code=503
        )


@app.get("/ping")
async def ping():
    """Lightweight ping endpoint for connectivity checks"""
    return {"pong": True}
