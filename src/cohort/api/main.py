from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from cohort.api.middleware import MaxBodySizeMiddleware
from cohort.api.rate_limit import limiter
from cohort.api.routes import health, queue
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

app.include_router(health.router)
app.include_router(queue.router)
