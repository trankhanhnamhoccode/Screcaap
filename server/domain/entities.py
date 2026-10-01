"""Small, persistence-independent domain representations."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from server.domain.enums import ProcessingStatus


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True)
class User:
    id: UUID
    created_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")


@dataclass(frozen=True)
class Device:
    id: UUID
    user_id: UUID
    name: str | None
    created_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")


@dataclass(frozen=True)
class Capture:
    id: UUID
    device_id: UUID
    captured_at: datetime
    processing_status: ProcessingStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.captured_at, "captured_at")
        _require_aware(self.created_at, "created_at")
        _require_aware(self.updated_at, "updated_at")
