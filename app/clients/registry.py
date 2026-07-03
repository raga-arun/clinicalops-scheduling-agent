"""Top-level registry composing every client group behind one lifecycle."""

from app.clients.internal.group import InternalAPIClients
from app.clients.lifecycle import ManagedClient
from app.clients.redis.redis_client import RedisClient
from app.clients.vault.vault_client import VaultClient
from app.core.config import Settings


class ClientRegistry:
    def __init__(self, settings: Settings):
        self.internal = InternalAPIClients(settings)
        self.vault = VaultClient(settings)
        self.redis = RedisClient(settings)
        self._managed: list[ManagedClient] = [self.internal, self.vault, self.redis]

    async def startup(self) -> None:
        for client in self._managed:
            await client.startup()

    async def shutdown(self) -> None:
        for client in reversed(self._managed):
            await client.shutdown()
