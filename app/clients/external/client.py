"""External service client group (places + phone verification).

Each sub-service is a separate upstream with its own base URL, so unlike the
internal group they do not share a pooled httpx client; this group only sequences
their lifecycles behind one ManagedClient.
"""

from app.clients.external.place import Place
from app.clients.external.verification import Verification
from app.clients.lifecycle import ManagedClient
from app.core.config import Settings


class ExternalService(ManagedClient):
    def __init__(self, settings: Settings):
        self.place = Place(settings)
        self.verification = Verification(settings)

    async def startup(self) -> None:
        await self.place.startup()
        await self.verification.startup()

    async def shutdown(self) -> None:
        await self.verification.shutdown()
        await self.place.shutdown()
