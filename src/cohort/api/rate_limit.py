"""Single shared `Limiter` instance — defined separately from `main.py` so
route modules can apply `@limiter.limit(...)` to individual endpoints without
a circular import.

Applied per-route via the decorator, not `SlowAPIMiddleware`'s automatic
default-limits-for-everything: FastAPI's `include_router` wraps included
routers in an internal mount with no `.endpoint`, so the middleware form
silently treats every route as exempt. The decorator form works.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from cohort.settings import get_settings

limiter = Limiter(key_func=get_remote_address)
DEFAULT_RATE_LIMIT = f"{get_settings().rate_limit_per_minute}/minute"
