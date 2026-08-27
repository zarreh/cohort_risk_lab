"""Single shared `Limiter` instance — defined separately from `main.py` so
route modules can apply `@limiter.limit(...)` to individual endpoints without
a circular import.

Built on `zarreh_agentkit.api.rate_limit` (extracted substrate). Applied
per-route via the decorator, not `SlowAPIMiddleware`'s automatic
default-limits-for-everything: FastAPI's `include_router` wraps included
routers in an internal mount with no `.endpoint`, so the middleware form
silently treats every route as exempt. The decorator form works.
"""

from zarreh_agentkit.api.rate_limit import build_limiter, default_rate_limit

from cohort.settings import get_settings

limiter = build_limiter()
DEFAULT_RATE_LIMIT = default_rate_limit(get_settings())
