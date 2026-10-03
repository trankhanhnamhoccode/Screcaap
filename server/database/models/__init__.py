"""Import mappings so SQLAlchemy and Alembic share complete metadata."""

from server.database.models.capture import CaptureModel
from server.database.models.device import DeviceModel
from server.database.models.ocr_result import OCRResultModel
from server.database.models.user import UserModel

__all__ = ["UserModel", "DeviceModel", "CaptureModel", "OCRResultModel"]
