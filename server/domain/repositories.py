"""Persistence interfaces used by application code."""

from typing import Protocol
from uuid import UUID

from server.domain.entities import Capture, Device, User


class UserRepository(Protocol):
    def add(self, user: User) -> None: ...

    def get_by_id(self, user_id: UUID) -> User | None: ...


class DeviceRepository(Protocol):
    def add(self, device: Device) -> None: ...

    def get_by_id(self, device_id: UUID) -> Device | None: ...


class CaptureRepository(Protocol):
    def add(self, capture: Capture) -> None: ...

    def get_by_id(self, capture_id: UUID) -> Capture | None: ...

    def claim_for_processing(self, capture_id: UUID) -> bool: ...

    def complete_processing(self, capture_id: UUID) -> bool: ...

    def fail_processing(self, capture_id: UUID) -> bool: ...
