"""Capture persistence mapping."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, desc, func, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database.session import Base
from server.domain.enums import ProcessingStatus


class CaptureModel(Base):
    __tablename__ = "captures"
    __table_args__ = (
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_captures_processing_status",
        ),
        Index(
            "ix_captures_device_captured_at_id",
            "device_id", desc("captured_at"), desc("id"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    device_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ProcessingStatus.PENDING.value,
        server_default=ProcessingStatus.PENDING.value,
    )
    # Object key semantics and requiredness belong to the ImageStorage milestone.
    image_object_key: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )

    device: Mapped["DeviceModel"] = relationship(back_populates="captures")
