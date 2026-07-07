"""Top-level registry composing every client group behind one lifecycle."""

from app.clients.external.client import ExternalService
from app.clients.internal.client import InternalAPIClients
from app.clients.lifecycle import ManagedClient
from app.clients.redis.redis_client import RedisClient
from app.clients.vault.client import VaultClient
from app.core.config import Settings


class ClientRegistry:
    def __init__(self, settings: Settings):
        self.internal = InternalAPIClients(settings)
        self.vault = VaultClient(settings)
        self.redis = RedisClient(settings)
        self.external = ExternalService(settings)
        self._managed: list[ManagedClient] = [
            self.internal,
            self.vault,
            self.redis,
            self.external,
        ]

    async def startup(self) -> None:
        for client in self._managed:
            await client.startup()

    async def shutdown(self) -> None:
        for client in reversed(self._managed):
            await client.shutdown()
