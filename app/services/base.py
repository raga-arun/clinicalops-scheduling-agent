"""Base class for services that need shared infrastructure clients."""

from app.clients.provider import ClientProvider
from app.clients.registry import ClientRegistry


class BaseService:
    """Common wiring for services.

    Pulls the shared ClientRegistry from the app-scoped provider so concrete
    services can focus on task logic. Tenancy is applied inside the client
    layer (headers, key prefixes), never threaded through services here.
    """

    def __init__(self) -> None:
        self._clients: ClientRegistry = ClientProvider.get()
