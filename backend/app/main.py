from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import limiter, router
from app.database import SessionLocal
from app.seed import seed_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(title="Synthetic Network Analysis API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
app.include_router(router)
logger = logging.getLogger(__name__)


@app.middleware("http")
async def audit_api_requests(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/") and request.url.path not in {"/api/health", "/api/auth/login", "/api/auth/register"}:
        try:
            from app.models import AuditLog
            with SessionLocal() as db:
                db.add(AuditLog(user_id=getattr(request.state, "user_id", None), action="api_request", resource=request.url.path[:255], status_code=response.status_code))
                db.commit()
        except SQLAlchemyError:
            logger.exception("Could not persist API audit event for %s", request.url.path)
    return response
