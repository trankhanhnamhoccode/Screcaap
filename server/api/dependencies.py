"""Compose application services for HTTP requests."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from server.database.repositories.capture import SqlAlchemyCaptureRepository
from server.database.repositories.device import SqlAlchemyDeviceRepository
from server.database.session import get_session_factory
from server.services.capture_service import CaptureService
from server.services.capture_read_service import CaptureReadService
from server.services.ports import ImageStorage, ProcessingQueue
from server.storage.s3 import create_minio_image_storage


def get_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


def get_image_storage() -> ImageStorage:
    return create_minio_image_storage()


def get_processing_queue() -> ProcessingQueue:
    # A real RQ target requires the deferred CaptureProcessor pipeline.
    raise HTTPException(status_code=503, detail={"code": "capture_processing_unavailable"})


def get_capture_service(
    processing_queue: Annotated[ProcessingQueue, Depends(get_processing_queue)],
    session: Annotated[Session, Depends(get_session)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> CaptureService:
    return CaptureService(
        device_repository=SqlAlchemyDeviceRepository(session),
        capture_repository=SqlAlchemyCaptureRepository(session),
        image_storage=image_storage,
        processing_queue=processing_queue,
        transaction=session,
    )


def get_capture_read_service(
    session: Annotated[Session, Depends(get_session)],
) -> CaptureReadService:
    return CaptureReadService(SqlAlchemyCaptureRepository(session))
