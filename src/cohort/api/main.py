from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from cohort.api.middleware import MaxBodySizeMiddleware
from cohort.api.rate_limit import limiter
from cohort.api.routes import evidence, health, queue
from cohort.observability import configure_logging
from cohort.settings import get_settings

settings = get_settings()
configure_logging(settings.environment)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Opens the checkpointer once at process startup, so an interrupted
    case review survives a server restart — not just an in-memory pause
    within one process (`graph/builder.py`'s `checkpointer` parameter)."""
    async with AsyncSqliteSaver.from_conn_string(settings.checkpoint_db_path) as checkpointer:
        app.state.checkpointer = checkpointer
        yield


app = FastAPI(title="Cohort Risk & Review Lab", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(MaxBodySizeMiddleware, max_body_bytes=settings.max_request_body_bytes)
# The Next.js dev server (localhost:3000) is a different origin than the API
# (localhost:8000); without this, the browser's own CORS policy blocks every
# fetch/EventSource call the frontend makes, not just cross-origin ones a
# malicious site would attempt. Frontend origins are configured, not "*" —
# this endpoint carries synthetic PHI-shaped data and should never be
# fetchable from an arbitrary origin even though the data itself is fake.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router)
app.include_router(queue.router)
app.include_router(evidence.router)
