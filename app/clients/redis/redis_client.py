"""Redis client for caching and conversation session state.

Skeleton: create a redis.asyncio pool in startup, close it in shutdown, and
implement the accessors. Keys should be namespaced by tenant id.
"""

from app.clients.lifecycle import ManagedClient
from app.core.config import Settings


class RedisClient(ManagedClient):
    def __init__(self, settings: Settings):
        self._settings = settings.redis

    async def startup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def get(self, key: str) -> str | None:
        raise NotImplementedError

    async def set(self, key: str, value: str, *, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError
