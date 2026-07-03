"""Common lifecycle contract for all client groups."""

from abc import ABC, abstractmethod


class ManagedClient(ABC):
    @abstractmethod
    async def startup(self) -> None: ...

    @abstractmethod
    async def shutdown(self) -> None: ...
