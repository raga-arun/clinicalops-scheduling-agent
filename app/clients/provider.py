"""App-scoped access to the shared ClientRegistry singleton."""

from app.clients.registry import ClientRegistry


class ClientProvider:
    """Holds the process-wide ClientRegistry created at application startup.

    The registry owns live connection pools and is created once in the app
    lifespan. Services reach it through ``ClientProvider.get()`` so they never
    construct or receive it explicitly.
    """

    _registry: ClientRegistry | None = None

    @classmethod
    def set(cls, registry: ClientRegistry) -> None:
        cls._registry = registry

    @classmethod
    def get(cls) -> ClientRegistry:
        if cls._registry is None:
            raise RuntimeError(
                "ClientRegistry is not initialized; set it during app startup."
            )
        return cls._registry

    @classmethod
    def reset(cls) -> None:
        cls._registry = None
