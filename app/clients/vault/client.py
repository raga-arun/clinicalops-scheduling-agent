"""Vault client for tenant-scoped secret retrieval.

Skeleton: wire an async Vault client (e.g. httpx against the Vault HTTP API)
inside startup/shutdown and implement the read methods.
"""

from typing import Any

from app.clients.lifecycle import ManagedClient
from app.core.config import Settings


class VaultClient(ManagedClient):
    def __init__(self, settings: Settings):
        self._settings = settings.vault

    async def startup(self) -> None: ...

    async def shutdown(self) -> None: ...

    async def get_secret(self, path: str) -> dict[str, Any]:
        raise NotImplementedError
