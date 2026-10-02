"""Device persistence through an externally managed Session."""

from uuid import UUID

from sqlalchemy.orm import Session

from server.database.models import DeviceModel
from server.domain.entities import Device


class SqlAlchemyDeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, device: Device) -> None:
        self._session.add(
            DeviceModel(
                id=device.id,
                user_id=device.user_id,
                name=device.name,
                created_at=device.created_at,
            )
        )

    def get_by_id(self, device_id: UUID) -> Device | None:
        model = self._session.get(DeviceModel, device_id)
        if model is None:
            return None
        return Device(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            created_at=model.created_at,
        )
